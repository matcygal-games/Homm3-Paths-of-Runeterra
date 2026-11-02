"""Fixed-scale technical assembly of frozen painted2D Archer keys; no art approval."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
import hashlib
import json
import math
from PIL import Image, ImageDraw, ImageOps

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[4]
OLD=PROJECT/'assets/source/creatures/painted-v2/shurimanArcher'
REPORT=PROJECT/'build/reports/painted-archer-completion-20261024-v1'
RECIPES=PROJECT/'assets/recipes/creatures/painted-v3/shurimanArcher'
SCALE=76/1131
CANVAS=(450,400)
ROOT=(196,267)
GROUP_COUNTS={0:6,1:2,2:1,3:2,4:1,5:3,7:1,8:1,11:2,12:2,13:2,14:5,15:5,16:5}
WALK=[OLD/'masters/g00-f000-v1.png',SOURCE/'masters/walk-passing-a-v1.png',
      SOURCE/'masters/walk-late-swing-a-v1.png',SOURCE/'masters/walk-opposite-contact-v2.png',
      SOURCE/'masters/walk-opposite-passing-v1.png',SOURCE/'masters/walk-opposite-swing-v1.png']
PHASES=['near-forward contact','near support/far passing','near support/far late swing',
        'far-forward contact/near trailing thigh in front','far support/near passing','far support/near late swing']

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(PROJECT).as_posix()
def encoded(v):return (json.dumps(v,indent=2,sort_keys=True)+'\n').encode()
def store(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()!=data:raise RuntimeError('Preserve changed existing candidate: '+str(path))
    else:path.write_bytes(data)
def put(path,v):store(path,encoded(v))
def png(path,image):
    import io
    buf=io.BytesIO();image.save(buf,format='PNG',compress_level=9)
    store(path,buf.getvalue())
def opaque(im):return im.getchannel('A').point(lambda a:255 if a>=200 else 0)
def edge(im):
    a=im.getchannel('A');w,h=im.size
    return max(a.crop(b).getextrema()[1] for b in [(0,0,w,1),(0,h-1,w,h),(0,0,1,h),(w-1,0,w,h)])
def contact(im,group,frame):
    # Foot/ground bands were inspected in the retained source images. This
    # measures contact only; no opaque width/height is used for scale fitting.
    band=(0,900,im.width,im.height) if group==5 else (150,950,im.width-40,im.height)
    b=opaque(im).crop(band).getbbox()
    if b is None:raise RuntimeError('No inspected physical contact in ground band')
    return [625+(im.width-1254)/2,band[1]+b[3]-1],list(band)
def transform(im,canvas,target_root,source_root,scale):
    clean=im.copy();clean.putalpha(im.getchannel('A').point(lambda a:0 if a<16 else a))
    factor=4
    tx=target_root[0]-source_root[0]*scale;ty=target_root[1]-source_root[1]*scale
    inverse=(1/(scale*factor),0,-tx/scale,0,1/(scale*factor),-ty/scale)
    big=clean.transform((canvas[0]*factor,canvas[1]*factor),Image.Transform.AFFINE,inverse,Image.Resampling.BICUBIC)
    return big.resize(canvas,Image.Resampling.LANCZOS)
def root_mirror(im,x):
    out=Image.new('RGBA',im.size)
    out.paste(ImageOps.mirror(im),(round(2*x-(im.width-1)),0))
    return out
def tile(im,label):
    out=Image.new('RGB',(150,155),(98,105,94));view=im.crop((121,157,271,302))
    out.paste(view,(0,0),view);ImageDraw.Draw(out).text((3,143),label,fill='white');return out
def gif(images,path,label,duration=140):
    import io
    frames=[]
    for im in images:
        bg=Image.new('RGB',im.size,(98,105,94));bg.paste(im,(0,0),im)
        ImageDraw.Draw(bg).text((8,8),'UNAPPROVED SOURCE PREVIEW / '+label,fill='white');frames.append(bg)
    buf=io.BytesIO();frames[0].save(buf,format='GIF',save_all=True,append_images=frames[1:],duration=duration,loop=0,optimize=False,disposal=2)
    store(path,buf.getvalue())
def descriptor(path):
    return {'source':rel(path),'source_sha256':sha(path),'source_canvas':list(Image.open(path).size)}

def main():
    REPORT.mkdir(parents=True,exist_ok=True);RECIPES.mkdir(parents=True,exist_ok=True)
    frames={};records=[];groups=[]
    for group,count in GROUP_COUNTS.items():
        frames[group]=[];seq=[]
        for frame in range(count):
            master=OLD/'masters'/f'g{group:02d}-f{frame:03d}-v1.png'
            if group==0:master=WALK[frame]
            elif group==4:master=SOURCE/'masters/defend-left-bow-v1.png'
            elif (group,frame)==(15,1):master=OLD/'masters/g15-f001-v2.png'
            im=Image.open(master).convert('RGBA');source_root,band=contact(im,group,frame)
            out=transform(im,CANVAS,ROOT,source_root,SCALE)
            path=SOURCE/'native-v3/right'/f'g{group:02d}-f{frame:03d}.png';png(path,out)
            reverse=ImageOps.mirror(out)
            png(SOURCE/'native-v3/reverse'/path.name,reverse)
            seq.append(descriptor(path));frames[group].append(out)
            row={'group':group,'frame':frame,'master':rel(master),'master_sha256':sha(master),
                 'source_canvas':list(im.size),'physical_source_root':source_root,'contact_measurement_band':band,
                 'fixed_pixel_scale':SCALE,'source_canvas_x_registration':'625+(canvas_width-1254)/2; no anatomical fit',
                 'native_root':list(ROOT),'native_frame':descriptor(path),'native_alpha200_bbox':list(opaque(out).getbbox()),
                 'native_border_alpha_max':edge(out),'pose_fit_or_body_resize':False}
            if group==0:row['support_phase']=PHASES[frame]
            records.append(row)
        groups.append({'group':group,'frames':seq})
    # Portable ledger: source recipe closure uses own paths/hashes only. Private
    # tool paths remain exclusively in REPORT/raw-tool-receipts.
    generated=[]
    for master in sorted((SOURCE/'masters').glob('*.png')):
        prompt=SOURCE/'prompts'/f'{master.stem}.txt';raw=REPORT/'raw-tool-receipts'/f'{master.stem}.json'
        generated.append({'source':rel(master),'sha256':sha(master),'canvas':list(Image.open(master).size),
                          'prompt_file':rel(prompt),'prompt_sha256':sha(prompt),
                          'private_generation_receipt_sha256':sha(raw)})
    provenance={
      'status':'authored configuration','unit':'shurimanArcher','image_generation_used':True,
      'provider':'OpenAI built-in imagegen','model':'not exposed by built-in tool',
      'source_master':rel(OLD/'masters/g02-f000-v1.png'),'source_master_sha256':sha(OLD/'masters/g02-f000-v1.png'),
      'retained_v2_generation_ledger':rel(OLD/'painted-generation-provenance-v1.json'),
      'retained_v2_generation_ledger_sha256':sha(OLD/'painted-generation-provenance-v1.json'),
      'generated_v3_masters':generated,'battle_cohort':records,
      'technical_producer':{'source':rel(Path(__file__)),'sha256':sha(Path(__file__))},
      'battle_canvas':list(CANVAS),'battle_root':list(ROOT),'common_battle_scale_numerator':76,'common_battle_scale_denominator':1131,
      'native_reverse':{'operation':'Full450px canvas reverse, actual CreatureAnimation reverse->verticalFlip',
                        'local_root':[253,267],'native_same_hex_x_shift':-58,'same_hex_root':[195,267]},
      'alpha_processing':'alpha<16→0 uniformly; all other source alpha and painted shadows retained',
      'opaque_body_fitting':False,'native_execution':False,'visual_approval_granted':False,'release_accepted':False}
    put(SOURCE/'cohort-conversion-v3.json',provenance)
    generation={'image_generation_used':True,'provider':'OpenAI built-in imagegen',
      'model':'not exposed by built-in tool','method':'Separate original painted2D action keys; one physical pixel scale and explicit source contact/canvas registration',
      'painted_master':rel(OLD/'masters/g02-f000-v1.png'),'painted_master_sha256':sha(OLD/'masters/g02-f000-v1.png'),
      'prompt':'Exact portable per-key prompts and original source hashes are in the pinned v2/v3 generation ledgers; one standalone action per image, no atlas.',
      'provenance':rel(SOURCE/'cohort-conversion-v3.json')}
    base={'unit':'shurimanArcher','production_status':'painted-master-complete-unapproved',
          'status':'authored configuration','visual_approval_granted':False,'generation':generation,
          'acceptance':'Complete technical source cohort only; native motion, projectile alignment, independent visual/rights/release review remain pending.',
          'credits':{'author':'Project-directed OpenAI built-in imagegen; deterministic technical2D assembly',
                     'license':None,'redistribution':'unresolved; release prohibited'}}
    prefix='Content/Sprites/runeterra/shurima/creatures/shurimanArcher/'
    battle={**base,'recipe_type':'vcmi_animation','output_path':prefix+'battle.json','canvas':list(CANVAS),
            'pivot':{'x':196,'y':267},'generateShadow':0,'generateOverlay':1,'groups':groups}
    put(RECIPES/'battle.json',battle)
    standing=Image.open(OLD/'masters/g02-f000-v1.png').convert('RGBA')
    attack_master=OLD/'masters/g15-f002-v1.png';attack=Image.open(attack_master).convert('RGBA')
    map_scale=.04;map_root=(64,60)
    standing_root,_=contact(standing,2,0);attack_root,_=contact(attack,15,2)
    extra={'map-000':transform(standing,(96,64),map_root,standing_root,map_scale),
           'attackRight':transform(attack,(96,64),map_root,attack_root,map_scale)}
    extra['attackLeft']=root_mirror(extra['attackRight'],64)
    crop_box=(350,0,1100,850)
    for role,size in [('large',(58,64)),('small',(32,32))]:
        crop=standing.crop(crop_box);ratio=min(size[0]/crop.width,size[1]/crop.height)
        dims=(round(crop.width*ratio),round(crop.height*ratio));view=crop.resize(dims,Image.Resampling.LANCZOS)
        image=Image.new('RGBA',size);image.paste(view,((size[0]-dims[0])//2,(size[1]-dims[1])//2));extra[role]=image
    for name,im in extra.items():png(SOURCE/'resources-v3'/f'{name}.png',im)
    resource_record={'status':'authored configuration','adventure_canvas':[96,64],'adventure_root':[64,60],
      'adventure_uniform_scale':map_scale,'standing_source':rel(OLD/'masters/g02-f000-v1.png'),
      'standing_source_sha256':sha(OLD/'masters/g02-f000-v1.png'),'reaction_source':rel(attack_master),'reaction_source_sha256':sha(attack_master),
      'portrait_fixed_source_crop':list(crop_box),'portrait_sizes':[[58,64],[32,32]],'opaque_body_fitting':False,
      'outputs':[{**descriptor(SOURCE/'resources-v3'/f'{name}.png'),'border_alpha_max':edge(im)} for name,im in extra.items()],
      'visual_approval_granted':False,'native_execution':False}
    put(SOURCE/'companion-conversion-v3.json',resource_record)
    for role in ('map','large','small','attackLeft','attackRight'):
        generation2={**generation,'provenance':rel(SOURCE/'companion-conversion-v3.json')}
        recipe={**base,'generation':generation2,'output_path':prefix+role+('.json' if role=='map' else '.png')}
        if role=='map':recipe.update(recipe_type='vcmi_animation',canvas=[96,64],pivot={'x':64,'y':60},generateShadow=0,generateOverlay=1,
                 groups=[{'group':0,'frames':[descriptor(SOURCE/'resources-v3/map-000.png')]}])
        else:recipe.update(recipe_type='raster',**descriptor(SOURCE/'resources-v3'/f'{role}.png'),
                           size=list(extra[role].size),fit='exact',require_alpha=True)
        put(RECIPES/f'{role}.json',recipe)
    # Actual strict API; outputs are held in memory and copied only to REPORT.
    sys.path.insert(0,str(PROJECT.parent/'scripts'));import faction_art_compile
    compiler=faction_art_compile.create_compiler('shurima');runs=[];strict_receipts=[]
    for run in (1,2):
        pins={}
        for path in sorted(RECIPES.glob('*.json')):
            outputs,receipt=compiler.plan(PROJECT,path)
            if run==1:strict_receipts.append(receipt)
            for name,data in outputs.items():
                pins[name]=hashlib.sha256(data).hexdigest()
                if run==1:store(REPORT/'strict-compiler-output-proof'/name,data)
        runs.append(pins)
    if len(strict_receipts)!=6 or runs[0]!=runs[1]:raise RuntimeError('Strict resource/determinism failure')
    put(REPORT/'strict-six-resource-proof-v3.json',{
      'status':'authored configuration','strict_api':"faction_art_compile.create_compiler('shurima').plan(actual project, actual recipes)",
      'compiler_sha256':sha(PROJECT.parent/'scripts/faction_art_compile.py'),'resource_count':len(strict_receipts),
      'output_count':len(runs[0]),'two_plans_byte_exact':runs[0]==runs[1],'outputs':runs[0],
      'recipe_pins':[{ 'source':rel(p),'sha256':sha(p)} for p in sorted(RECIPES.glob('*.json'))],
      'receipts':strict_receipts,'production_writes':False,'manifest_selected':False,'visual_approval_granted':False,'native_execution':False})
    for facing in ('right','native-left-samehex'):
        tiles=[]
        for group,images in frames.items():
            views=images
            if facing!='right':
                views=[]
                for im in images:
                    view=Image.new('RGBA',CANVAS);view.paste(ImageOps.mirror(im),(-58,0));views.append(view)
            for i,im in enumerate(views):tiles.append(tile(im,f'g{group:02d} f{i:03d}'))
            if len(views)>1:gif(views,REPORT/f'g{group:02d}-{facing}-native.gif',f'g{group:02d} {facing}',180 if group==5 else 140)
        sheet=Image.new('RGB',(900,math.ceil(len(tiles)/6)*155),(45,48,44))
        for i,t in enumerate(tiles):sheet.paste(t,((i%6)*150,(i//6)*155))
        png(REPORT/f'all-actions-{facing}-native1x.png',sheet)
    board=Image.new('RGB',(420,270),(35,35,35));d=ImageDraw.Draw(board)
    for i,(name,im) in enumerate([('map',extra['map-000']),('map opposite',root_mirror(extra['map-000'],64)),
                                ('attackRight',extra['attackRight']),('attackLeft',extra['attackLeft']),('large',extra['large']),('small',extra['small'])]):
        x=(i%3)*140;y=(i//3)*135;board.paste(im,(x,y+22),im);d.text((x+2,y+2),name,fill='white')
    png(REPORT/'companions-native1x.png',board)
    original=PROJECT.parent/'runeterra-targon/references/native-20261023-v1/frames/clcbow/g02-f000.png'
    comparison=Image.new('RGB',(450,175),(98,105,94))
    left=Image.new('RGBA',CANVAS);left.paste(ImageOps.mirror(frames[2][0]),(-58,0))
    for i,(im,label) in enumerate([(Image.open(original).convert('RGBA'),'Original CLCBOW'),(frames[2][0],'Archer R'),(left,'Archer L native')]):comparison.paste(tile(im,label),(i*150,15))
    png(REPORT/'native-original-comparison-private.png',comparison)
    print(json.dumps({'strict_resources':6,'compiled_outputs':len(runs[0]),'deterministic':runs[0]==runs[1],
                      'battle_action_keys':len(records),'proof_sha256':sha(REPORT/'strict-six-resource-proof-v3.json'),
                      'art_approval':False,'production_writes':False}))

if __name__=='__main__':main()
