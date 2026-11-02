"""Candidate-only DMC1 painted-scene slicing and hidden-body restoration.

All creative pixels are approved-scene or built-in imagegen painted plates.
Masks, coordinate placement and exact-alpha composition are technical operations.
This script never edits current project selections or production outputs.
"""
from pathlib import Path
import argparse,hashlib,json
from PIL import Image,ImageDraw,ImageFilter,ImageChops

HERE=Path(__file__).resolve().parent
WORKSPACE=HERE
SIZE=(800,374)

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def load(p):return Image.open(p).convert('RGBA')
def polygons(items):
    out=Image.new('L',SIZE);d=ImageDraw.Draw(out)
    for poly in items:d.polygon([tuple(p) for p in poly],fill=255)
    return out

def assemble(output):
    if output.exists():raise ValueError('Use a fresh candidate output directory')
    output.mkdir(parents=True)
    traces=HERE/'traces.json';v=json.loads(traces.read_text());source=WORKSPACE/v['source']
    if digest(source)!=v['source_sha256']:raise ValueError('Approved source changed')
    src=load(source);empty=load(HERE/'art/empty-native.png')
    plates={n:load(HERE/'art'/f'underpaint-{n}-native.png') for n in ('rear','middle','tavern')}
    masks={};architectures={};union=Image.new('L',SIZE)
    for name,site in v['sites'].items():
        arch=polygons(site.get('architecture_polygons',site['polygons']))
        if name=='coast':arch=ImageChops.lighter(arch,polygons(site['ship_architecture_polygons']))
        previous=Image.open(HERE/'seed-masks'/f'{name}-art-mask.png').convert('L')
        art=ImageChops.lighter(previous,arch.filter(ImageFilter.MaxFilter(7)))
        art.save(output/f'{name}-art-mask.png');arch.save(output/f'{name}-architecture-mask.png')
        masks[name]=art;architectures[name]=arch;union=ImageChops.lighter(union,art)
    background=Image.composite(empty,src,union);background.save(output/'background.png')
    scene=background.copy();records=[];ordered=sorted(v['sites'],key=lambda n:v['sites'][n]['z'])
    for name in ordered:
        site=v['sites'][name];art=masks[name];front=Image.new('L',SIZE)
        for other in ordered:
            if v['sites'][other]['z']>site['z']:front=ImageChops.lighter(front,masks[other])
        hidden=ImageChops.multiply(art,front);visible=ImageChops.subtract(art,front)
        picture=src.copy();restorer=v['underpaint_assignments'].get(name)
        if hidden.getbbox():
            if restorer is None:raise ValueError('Hidden construction lacks painted restoration: '+name)
            picture=Image.composite(plates[restorer],picture,hidden)
        picture.putalpha(art);picture.save(output/f'{name}-full.png');scene.alpha_composite(picture)
        visible.save(output/f'{name}-visible-mask.png');hidden.save(output/f'{name}-hidden-mask.png')
        records.append({'site':name,'z':site['z'],'bounds':art.getbbox(),'visible_pixels':visible.histogram()[255],
                        'hidden_pixels':hidden.histogram()[255],'underpaint':restorer,
                        'frame_sha256':digest(output/f'{name}-full.png'),'architecture_mask_sha256':digest(output/f'{name}-architecture-mask.png')})
    scene.save(output/'fully-built.png')
    exact=ImageChops.difference(src.convert('RGB'),scene.convert('RGB')).getbbox() is None
    if not exact:raise ValueError('Fully built scene differs from approved visible painting')
    for selected in ordered:
        single=background.copy();single.alpha_composite(load(output/f'{selected}-full.png'));single.save(output/f'{selected}-alone.png')
    rows=[]
    for i,name in enumerate(ordered):
        box=masks[name].getbbox();x0=max(0,box[0]-5);y0=max(0,box[1]-5);x1=min(800,box[2]+5);y1=min(374,box[3]+5)
        frame=load(output/f'{name}-full.png');neutral=Image.new('RGBA',SIZE,(62,64,67,255));neutral.alpha_composite(frame)
        crop=neutral.crop((x0,y0,x1,y1));crop.thumbnail((390,220),Image.Resampling.NEAREST);rows.append((name,crop))
    sheet=Image.new('RGB',(1600,((len(rows)+3)//4)*250),(26,28,31));d=ImageDraw.Draw(sheet)
    for i,(name,pic) in enumerate(rows):x=i%4*400;y=i//4*250;sheet.paste(pic,(x,y+25));d.text((x+5,y+5),name,fill='white')
    sheet.save(output/'all-site-full-layers.png')
    report={'status':'authored configuration candidate','native_verified':False,'selected':False,'approved_fully_built_pixels_exact':exact,
            'source':{'path':v['source'],'sha256':digest(source)},'traces_sha256':digest(traces),'ordinary_land_sites':16,'optional_coastal_sites':1,
            'background_sha256':digest(output/'background.png'),'fully_built_sha256':digest(output/'fully-built.png'),'sites':records}
    dump(output/'receipt.json',report);return report

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    print(json.dumps(assemble(args.output.resolve()),indent=2))
