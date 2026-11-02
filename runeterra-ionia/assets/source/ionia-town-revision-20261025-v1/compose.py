"""Portable painted2D town conversion only. No generation/cache/live recipe/stage writes."""
from pathlib import Path
import hashlib,io,json
from PIL import Image,ImageChops,ImageFilter,ImageDraw
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def local(name):
    if not isinstance(name,str) or ':' in name or '\\' in name or any(p in ('','.','..') for p in name.split('/')):raise ValueError('Unsafe local source path')
    p=PROJECT/name
    for q in (p,*p.parents):
        if q==PROJECT:break
        if q.is_symlink() or (hasattr(q,'is_junction') and q.is_junction()):raise ValueError('Reparse source rejected')
    p=p.resolve()
    if not p.is_relative_to(PROJECT):raise ValueError('Source escape')
    return p
def png_bytes(im):
    b=io.BytesIO();im.convert('RGBA').save(b,format='PNG');return b.getvalue()
def crop(im):
    box=im.getchannel('A').point(lambda v:255 if v>16 else 0).getbbox()
    if not box:raise ValueError('Empty painted building')
    return im.crop(box),box
def fit(im,size):
    scale=min(size[0]/im.width,size[1]/im.height)
    return im.resize((max(1,round(im.width*scale)),max(1,round(im.height*scale))),Image.Resampling.LANCZOS)
def relative(path):return path.relative_to(PROJECT).as_posix()
def products(config,plan):
    output={};prepared=HERE/'prepared-v1'
    def put(path,image):output[relative(path)]=png_bytes(image)
    bg=config['background'];original=Image.open(local(bg['original']['path'])).convert('RGBA');edited=Image.open(local(bg['edited']['path'])).convert('RGBA');mask=Image.open(local(bg['mask']['path'])).convert('L')
    if edited.size!=original.size:
        if list(edited.size)!=bg['edited_raw_canvas'] or list(original.size)!=bg['original_canvas']:raise ValueError('Unexpected edited landscape camera')
        edited=edited.resize(original.size,Image.Resampling.LANCZOS)
    if mask.size!=original.size:raise ValueError('Landscape ROI dimensions changed')
    master=Image.composite(edited,original,mask);master.putalpha(original.getchannel('A'));put(HERE/'background-v1/selected-master-v2.png',master)
    before,after=original.tobytes(),master.tobytes()
    if any(before[4*i:4*i+4]!=after[4*i:4*i+4] for i,m in enumerate(mask.tobytes()) if not m):raise ValueError('Background outside genuine paint ROI changed')
    background=master.convert('RGB').resize((800,374),Image.Resampling.LANCZOS).convert('RGBA');put(prepared/'town/background.png',background)
    for key,e in plan['per_state_geometry'].items():
        master=Image.open(local(e['master']['path'])).convert('RGBA');sprite,box=crop(master)
        if list(box)!=e['master_crop']:raise ValueError('Building crop no longer matches measured plan')
        x,y,w,h=plan['sites'][e['site']]['box'];piece=fit(sprite,(w,h));origin=[x+(w-piece.width)//2,y+h-piece.height]
        if list(piece.size)!=e['native_size'] or origin!=e['native_origin']:raise ValueError('Measured whole-building scale/root changed')
        layer=Image.new('RGBA',(800,374));layer.alpha_composite(piece,origin);put(prepared/'town/structures'/key/'layer.png',layer)
        alpha=layer.getchannel('A').point(lambda a:255 if a>=128 else 0);area=Image.new('RGBA',(800,374),(255,255,255,0));area.putalpha(alpha);put(prepared/'town/structures'/key/'area.png',area)
        border=Image.new('RGBA',(800,374),(255,220,90,0));border.putalpha(ImageChops.subtract(alpha.filter(ImageFilter.MaxFilter(3)),alpha));put(prepared/'town/structures'/key/'border.png',border)
        campaign=Image.new('RGBA',(58,64));small=fit(sprite,(56,62));campaign.alpha_composite(small,((58-small.width)//2,64-small.height));put(prepared/'town/structures'/key/'campaign.png',campaign)
        icon=Image.new('RGBA',(150,70));small=fit(sprite,(146,66));icon.alpha_composite(small,((150-small.width)//2,68-small.height));put(prepared/'town/structures'/key/'icon.png',icon)
    for height in (120,130):put(prepared/'ui'/f'creatureBackground{height}.png',background.crop((350,40,600,300)).resize((100,height),Image.Resampling.LANCZOS))
    for state,master_pin in config['adventure_icon_masters'].items():
        sprite,_=crop(Image.open(local(master_pin['path'])).convert('RGBA'))
        for variant in ('built','normal'):
            for scale,size in [('large',(58,64)),('small',(48,32))]:
                icon=background.resize(size,Image.Resampling.LANCZOS);town=fit(sprite,(size[0]-2,size[1]-3));icon.alpha_composite(town,((size[0]-town.width)//2,size[1]-town.height))
                if variant=='built':
                    d=ImageDraw.Draw(icon);d.line((size[0]-10,2,size[0]-3,9),fill=(210,48,32),width=2);d.line((size[0]-10,9,size[0]-3,2),fill=(210,48,32),width=2)
                put(prepared/'town/icons'/f'{state}_{variant}_{scale}.png',icon)
    return output
def replay():
    record=json.loads((HERE/'source-inputs-v1.json').read_text())
    for e in record['dependencies']:
        p=local(e['path'])
        if not p.is_file() or sha(p)!=e['sha256']:raise ValueError('Missing/stale producer input: '+e['path'])
    config=json.loads((HERE/'assembly-config-v1.json').read_text());plan=json.loads(local(config['plan']['path']).read_text());result=products(config,plan);expected=json.loads((HERE/'expected-products-v1.json').read_text())['products']
    actual={name:hashlib.sha256(data).hexdigest() for name,data in sorted(result.items())}
    if actual!=expected:raise ValueError('Replayed products differ from frozen native source manifest')
    # Validate every target before the first output mutation. Never touch unrelated/live files.
    for name,data in result.items():
        p=local(name)
        if not p.is_relative_to(HERE):raise ValueError('Output leaves owned candidate source')
        if p.exists() and p.read_bytes()!=data:raise ValueError('Existing frozen output differs: '+name)
    for name,data in result.items():
        p=local(name);p.parent.mkdir(parents=True,exist_ok=True)
        if not p.exists():p.write_bytes(data)
    return {'status':'authored configuration','source_products':len(result),'all_products_exact':True,'native_execution':False,'release_accepted':False}
if __name__=='__main__':print(json.dumps(replay(),sort_keys=True))
