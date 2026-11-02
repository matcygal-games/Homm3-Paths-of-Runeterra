"""Whole-painted-pose isolation and fixed-cohort native registration only.

No body drawing, articulated warping, 3D inputs or canonical selection/writes.
"""
from pathlib import Path
import argparse, hashlib, io, json, sys
import numpy as np
from PIL import Image, ImageOps, ImageFilter, ImageDraw

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[4]
WORKSPACE=PROJECT.parent
REPORT=WORKSPACE/'reports/bilgewater-flying-and-leviathans-20261028-v1'
CANVAS=(450,400);ROOT=(218,266)

def sha(value):return hashlib.sha256(value if isinstance(value,bytes) else value.read_bytes()).hexdigest()
def rel(p):return p.relative_to(PROJECT).as_posix()
def encoded(v):return (json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def put(p,data):
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists()and p.read_bytes()!=data:raise ValueError('Preserve historical candidate; version changed output '+str(p))
    if not p.exists():p.write_bytes(data)
def record(p,v):put(p,encoded(v))
def clean(im):
    a=np.array(im.convert('RGBA'));a[a[:,:,3]>=250,3]=255;a[a[:,:,3]==0,:3]=0
    return Image.fromarray(a)
def png(im):
    f=io.BytesIO();clean(im).save(f,format='PNG',compress_level=9,optimize=False);return f.getvalue()
def save(p,im):put(p,png(im))
def descriptor(p):return {'source':rel(p),'source_sha256':sha(p),'source_canvas':list(Image.open(p).size)}
def box(im):return im.getchannel('A').point(lambda v:255 if v>=128 else 0).getbbox()

def islands(im):
    a=np.array(im.getchannel('A'));parent=[];runs=[];previous=[]
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for y,row in enumerate(a):
        bounds=np.flatnonzero(np.diff(np.r_[False,row>=128,False].astype(np.int8)));current=[]
        for s,e in zip(bounds[::2],bounds[1::2]):
            i=len(parent);parent.append(i);runs.append((y,int(s),int(e),i));current.append((s,e,i))
            for ps,pe,pi in previous:
                if pe<s:continue
                if ps>e:break
                x,z=find(i),find(pi)
                if x!=z:parent[z]=x
        previous=current
    grouped={}
    for y,s,e,i in runs:grouped.setdefault(find(i),[]).append((y,s,e))
    result=[]
    for lines in grouped.values():
        if sum(e-s for y,s,e in lines)<1000:continue
        b=[min(s for y,s,e in lines),min(y for y,s,e in lines),max(e for y,s,e in lines),max(y for y,s,e in lines)+1]
        result.append({'box':b,'lines':lines})
    return sorted(result,key=lambda q:(q['box'][1],q['box'][0]))

def isolate(im,item):
    a=np.array(im);mask=np.zeros((im.height,im.width),dtype=np.uint8)
    for y,s,e in item['lines']:mask[y,s:e]=255
    # Preserve the actual painted antialias fringe without retaining a distant
    # neighboring actor or invisible source RGB. This draws no creative pixels.
    mask=np.array(Image.fromarray(mask).filter(ImageFilter.MaxFilter(5)))
    a[:,:,3]=np.minimum(a[:,:,3],mask)
    return clean(Image.fromarray(a))

def transform(im,source_root,scale,canvas=CANVAS,root=ROOT):
    # One authored camera scale per plate, never bounds-fit a particular action.
    factor=4;tx=root[0]-source_root[0]*scale;ty=root[1]-source_root[1]*scale
    inverse=(1/(scale*factor),0,-tx/scale,0,1/(scale*factor),-ty/scale)
    out=im.transform((canvas[0]*factor,canvas[1]*factor),Image.Transform.AFFINE,inverse,Image.Resampling.BICUBIC)
    return clean(out.resize(canvas,Image.Resampling.LANCZOS))

def root_mirror(im,x):
    out=Image.new('RGBA',im.size);out.paste(ImageOps.mirror(im),(round(2*x-(im.width-1)),0));return clean(out)

def review(unit,groups,companions,report):
    crop=(85,105,365,290);cw,ch=280,205
    sheet=Image.new('RGB',(max(len(x)for x in groups.values())*cw,len(groups)*ch),(60,57,50));d=ImageDraw.Draw(sheet)
    for row,(g,frames)in enumerate(sorted(groups.items())):
        views=[]
        for col,im in enumerate(frames):
            native=im.crop(crop);sheet.paste(native,(col*cw,row*ch+20),native);d.text((col*cw+3,row*ch+3),f'{unit} g{g} f{col}',fill='white')
            bg=Image.new('RGB',(cw,185),(60,57,50));bg.paste(native,(0,0),native);views.append(bg)
        if len(views)>1:
            b=io.BytesIO();views[0].save(b,format='GIF',save_all=True,append_images=views[1:],duration=100,loop=0,optimize=False,disposal=2);put(report/f'g{g:02d}.gif',b.getvalue())
    save(report/'native-actions.png',sheet)
    page=Image.new('RGB',(500,100),(60,57,50));dr=ImageDraw.Draw(page)
    x=0
    for name,im in companions.items():page.paste(im,(x,25),im);dr.text((x,3),name,fill='white');x+=100
    save(report/'native-companions.png',page)
    put(report/'index.html',('<!doctype html><meta charset="utf-8"><title>'+unit+' painted source candidate</title><style>body{background:#272924;color:#eee;font:16px system-ui}img{max-width:100%}a{color:#c9d9ec}</style><h1>'+unit+'</h1><p>Authored configuration. Native-scale assembled source pixels, not in-game screenshots. Native visual/motion, crest and rights acceptance remain separate.</p><img src="native-companions.png"><p>'+''.join('<a href="g%02d.gif">group%d motion</a> '%(g,g)for g in groups if len(groups[g])>1)+'</p><img src="native-actions.png"><p><a href="compiler-replay.json">Actual two-pass compiler replay</a></p>').encode())

def main(config):
    cfg=json.loads(config.read_text());unit=cfg['unit'];version=cfg.get('version',1)
    if unit not in ['cliffwing','stormwing','shoreLeviathan','elderShoreLeviathan']:raise ValueError('Wrong ownership')
    out=HERE/unit/f'native-v{version}';report=REPORT/unit/f'candidate-v{version}';recipes=HERE/f'proposed-recipes-v{version}'/unit
    poses={};raw={};records={};deps=[Path(__file__),config]
    for name,plate in cfg['plates'].items():
        p=HERE/plate['source'];im=Image.open(p).convert('RGBA');items=islands(im)
        if sha(p)!=plate['sha256']or len(items)!=plate['expected_islands']:raise ValueError('Inspected painted source changed '+name)
        deps.extend([p,p.with_name(p.name.replace('-raw.png','-prompt.txt'))])
        for label,entry in plate['poses'].items():
            item=items[entry['island']];actor=isolate(im,item);root=entry['root']
            raw[label]=actor
            poses[label]=transform(actor,root,plate['scale'])
            records[label]={'painted_master':rel(p),'painted_master_sha256':sha(p),'source_island':entry['island'],'source_island_box':item['box'],'source_root':root,'plate_camera_scale':plate['scale'],'per_pose_bounds_fit':False,'battle_root':list(ROOT)}
    # The complete front pose is root-reflected before the native facing flip.
    # This keeps asymmetrical physical harness/light pixels continuous at the
    # actual ReverseAnimation TURN_L -> facing/reposition -> TURN_R boundary.
    poses['turnJoin']=Image.new('RGBA',CANVAS)
    poses['turnJoin'].paste(ImageOps.mirror(poses[cfg['turn_front']]),(-14,0))
    records['turnJoin']={**records[cfg['turn_front']],'technical_reflection_for_native_facing_change':True,'full_canvas_mirror_then_translate_x':-14,'actual_native_two_hex_world_position_delta_x':-14}
    groups={};frames=[];recipe_groups=[]
    for name,labels in cfg['groups'].items():
        g=int(name);groups[g]=[];seq=[]
        for f,label in enumerate(labels):
            im=poses[label];path=out/'right'/f'g{g:02d}-f{f:03d}.png';save(path,im);save(out/'reverse'/path.name,ImageOps.mirror(im));seq.append(descriptor(path));groups[g].append(im)
            frames.append({'group':g,'frame':f,'pose':label,**records[label],'output':descriptor(path),'opaque128_box':box(im)})
        recipe_groups.append({'group':g,'frames':seq})
    c=cfg['companions'];actor=raw[c['map_pose']];aroot=records[c['map_pose']]['source_root'];enc=raw[c['encounter_pose']];eroot=records[c['encounter_pose']]['source_root']
    companions={'map':transform(actor,aroot,c['scale'],(96,64),(76,60)),'attackLeft':transform(enc,eroot,c['scale'],(64,64),(44,60))}
    companions['attackRight']=root_mirror(companions['attackLeft'],44)
    bgp=HERE/'portrait-background-v1-raw.png';bg=Image.open(bgp).convert('RGBA');deps.extend([bgp,HERE/'portrait-background-v1-prompt.txt'])
    close=raw[c['portrait_pose']].crop(tuple(c['portrait_crop']))
    for role,size in [('large',(64,64)),('small',(32,32))]:
        im=bg.resize(size,Image.Resampling.LANCZOS);scale=min(size[0]/close.width,size[1]/close.height);head=close.resize((round(close.width*scale),round(close.height*scale)),Image.Resampling.LANCZOS);im.alpha_composite(head,((size[0]-head.width)//2,size[1]-head.height));companions[role]=clean(im)
    for role,im in companions.items():save(out/'companions'/f'{role}.png',im)
    deps=sorted(set(deps));pins=[{'path':rel(p),'sha256':sha(p)}for p in deps]
    ledger=HERE/unit/f'source-generation-v{version}.json'
    record(ledger,{'schema_version':1,'status':'authored configuration','selected':False,'unit':unit,'workflow':'genuine-painted-2d-imagegen','derived_from_blender':False,'user_rejected':False,'image_origins':[{'path':rel(HERE/p['source']),'sha256':p['sha256'],'provider':'OpenAI built-in imagegen','model':'not exposed by built-in tool'}for p in cfg['plates'].values()],'source_files':pins,'frames':frames,'native_execution':False,'release_accepted':False,'limitations':cfg['limitations'],'native_consumer':cfg['native_consumer'],'turn_join':{'source_group7_end':'painted front','source_group8_start':'full-canvas mirror of same painted front translated left14px','display_group7_end':'worldpos_right+front','display_group8_start':'worldpos_right-14 + full_mirror(translate(full_mirror(front),-14))','exact_display_join_expected':True}})
    generation={'image_generation_used':True,'provider':'OpenAI built-in imagegen','model':'not exposed by built-in tool','prompt':'Exact effective per-master prompts are pinned in production_inputs. Original painted 2D full-pose action sources; fixed-cohort technical isolation/registration only. No geometry, 3D rendering, limb warping or copied original-game pixels.','painted_master':rel(HERE/next(iter(cfg['plates'].values()))['source']),'painted_master_sha256':next(iter(cfg['plates'].values()))['sha256'],'provenance':rel(ledger),'provenance_sha256':sha(ledger),'workflow':'genuine-painted-2d-imagegen','derived_from_blender':False,'production_inputs':pins}
    common={'production_status':'painted-master-complete-unapproved','unit':unit,'generation':generation,'status':'authored configuration','selected':False,'acceptance':'Native playback, visual/crest approval and rights remain pending; compiler tests do not grant acceptance.','credits':{'author':'Project-directed OpenAI built-in imagegen; deterministic technical painted 2D assembly','license':None,'redistribution':'unresolved; release prohibited'}}
    prefix=f'Content/Sprites/runeterra/bilgewater/creatures/{unit}/'
    record(recipes/'battle.json',{**common,'recipe_type':'vcmi_animation','output_path':prefix+'battle.json','canvas':list(CANVAS),'pivot':{'x':ROOT[0],'y':ROOT[1]},'generateShadow':1,'generateOverlay':1,'groups':recipe_groups})
    for role,im in companions.items():
        p=out/'companions'/f'{role}.png'
        if role=='map':r={**common,'recipe_type':'vcmi_animation','output_path':prefix+'map.json','canvas':[96,64],'pivot':{'x':76,'y':60},'generateShadow':1,'generateOverlay':0,'groups':[{'group':0,'frames':[descriptor(p)]}]}
        else:r={**common,'recipe_type':'raster','output_path':prefix+role+'.png','size':list(im.size),'fit':'exact',**descriptor(p)}
        record(recipes/f'{role}.json',r)
    sys.path.insert(0,str(WORKSPACE/'scripts'));import faction_art_compile
    compiler=faction_art_compile.create_compiler('bilgewater');maps=[];receipts=[]
    for replay in (1,2):
        hashes={}
        for p in sorted(recipes.glob('*.json')):
            outputs,receipt=compiler.plan(PROJECT,p)
            for path,data in outputs.items():
                if replay==1:put(report/'compiled'/path,data)
                hashes[path]=sha(data)
            receipts.append({'pass':replay,**receipt})
        maps.append(hashes)
    if maps[0]!=maps[1]:raise ValueError('Actual converter replay changed bytes')
    record(report/'compiler-replay.json',{'status':'authored configuration','deterministic':True,'recipe_count':6,'physical_outputs':len(maps[0]),'output_sha256':maps[0],'receipts':receipts,'native_execution':False,'release_accepted':False})
    review(unit,groups,companions,report)
    record(report/'assembly.json',{'unit':unit,'configuration':rel(config),'configuration_sha256':sha(config),'battle_canvas':list(CANVAS),'battle_root':list(ROOT),'group_counts':{str(g):len(fs)for g,fs in groups.items()},'production_inputs':pins,'source_generation_ledger':rel(ledger),'source_generation_ledger_sha256':sha(ledger),'proposed_recipes':[{'path':rel(p),'sha256':sha(p)}for p in sorted(recipes.glob('*.json'))],'limitations':cfg['limitations']})
    print(json.dumps({'unit':unit,'recipes':6,'physical_outputs':len(maps[0]),'deterministic':True,'source_only':True,'report':str(report/'index.html')}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('config',type=Path);main(p.parse_args().config.resolve())
