"""Technical 2D isolation/registration of delivered painted cohorts; never draws actors.

One density per atlas, cab-bearing roots for live motion, explicitly authored
floor marks for death. No per-pose fitting, body warping or generated geometry.
"""
from collections import deque
from pathlib import Path
import hashlib, io, json, sys
import numpy as np
from PIL import Image, ImageDraw
from components import components

HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if p.name=='runeterra-piltover')
PREFIX='Content/Sprites/runeterra/piltover/creatures/'
UNITS={
 'dockyardLifter':{'scale':.27,'attack':'attacks-v2-master.png',
   'death_floor':[[280,554],[790,579],[1260,581],[282,990],[790,990],[1283,992]]},
 'reinforcedDockyardLifter':{'scale':.278,'attack':'attacks-v1-master.png',
   'death_floor':[[280,581],[793,592],[1270,593],[290,986],[790,989],[1290,990]]},
}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def png(im,p):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,format='PNG',compress_level=9,optimize=False);return p
def relative(p):return p.relative_to(PROJECT).as_posix()
def isolated(path,columns,rows):
    im=Image.open(path).convert('RGBA');a=np.asarray(im.getchannel('A'));h,w=a.shape
    cores=[c for c in components(im.getchannel('A'),16) if c['area']>1000]
    if len(cores)!=columns*rows:raise ValueError(f'{path.name}: {len(cores)} opaque actors, expected {columns*rows}')
    cores.sort(key=lambda c:(c['box'][1]+c['box'][3])/2)
    ordered=[]
    for row in range(rows):ordered+=sorted(cores[row*columns:(row+1)*columns],key=lambda c:(c['box'][0]+c['box'][2])/2)
    labels=np.zeros((h,w),dtype=np.uint8);q=deque()
    for index,c in enumerate(ordered,1):
        for pos in c['pixels']:
            y,x=divmod(pos,w);labels[y,x]=index
        for pos in c['pixels']:
            y,x=divmod(pos,w)
            if (x and not labels[y,x-1]) or (x+1<w and not labels[y,x+1]) or (y and not labels[y-1,x]) or (y+1<h and not labels[y+1,x]):q.append(pos)
    while q:
        pos=q.popleft();y,x=divmod(pos,w);tag=labels[y,x]
        for yy,xx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
            if 0<=yy<h and 0<=xx<w and a[yy,xx]>=8 and not labels[yy,xx]:labels[yy,xx]=tag;q.append(yy*w+xx)
    # Disconnected antialias specks retain original bytes and go to their nearest
    # full actor. No opaque actor pixels are deleted, duplicated or painted.
    centers=[((c['box'][0]+c['box'][2])/2,(c['box'][1]+c['box'][3])/2) for c in ordered]
    for y,x in zip(*np.where((a>=8)&(labels==0))):
        labels[y,x]=1+min(range(len(centers)),key=lambda k:(x-centers[k][0])**2+(y-centers[k][1])**2)
    assert int(((labels>0)&(a>=8)).sum())==int((a>=8).sum())
    out=[]
    for index,c in enumerate(ordered,1):
        mask=Image.fromarray(np.where(labels==index,a,0).astype('uint8'),'L')
        box=mask.getbbox();actor=im.copy();actor.putalpha(mask);actor=actor.crop(box)
        out.append({'image':actor,'box':box,'matte':mask,'opaque_pixels':c['area']})
    return out
def plate(actor):
    im=actor['image'];a=np.asarray(im).astype('int16');h,w=a.shape[:2]
    m=(a[:,:,3]>=96)&(a[:,:,2]>a[:,:,0]+10)&(a[:,:,2]>a[:,:,1]+5)
    m[:int(h*.30)]=False;m[int(h*.78):]=False
    found=[c for c in components(Image.fromarray((m*255).astype('uint8'),'L'),1) if c['area']>60]
    if not found:raise ValueError('No measurable native navy front panel')
    c=max(found,key=lambda x:x['area']);return c['box']
def native_pose(actor,scale,hip_y,facing='right',floor=None):
    im=actor['image'];box=actor['box']
    if floor is None:
        p=plate(actor);dx={'right':10,'half':5,'front':0}[facing]
        root=((p[0]+p[2])/2-dx/scale,p[3]+8/scale);target=(220,hip_y)
    else:root=(floor[0]-box[0],floor[1]-box[1]);target=(220,266)
    size=(max(1,round(im.width*scale)),max(1,round(im.height*scale)))
    scaled=im.resize(size,Image.Resampling.LANCZOS)
    offset=(round(target[0]-root[0]*scale),round(target[1]-root[1]*scale))
    result=Image.new('RGBA',(450,400));result.alpha_composite(scaled,offset)
    if offset[0]<0 or offset[1]<0 or offset[0]+scaled.width>450 or offset[1]+scaled.height>400:raise ValueError('Native pose would clip')
    return result,{'source_box':list(box),'source_root':list(root),'scale':scale,'native_root':list(target),'paste':list(offset),'panel':None if floor is not None else list(plate(actor))}
def role_image(im,size,scale,target,mirror=False):
    source=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if mirror else im
    root_x=450-220 if mirror else 220
    resized=source.resize((round(450*scale),round(400*scale)),Image.Resampling.LANCZOS)
    offset=(round(target[0]-root_x*scale),round(target[1]-266*scale))
    result=Image.new('RGBA',size);result.alpha_composite(resized,offset)
    # Prove no visible source is cropped by the role canvas.
    before=np.asarray(resized.getchannel('A'))>=8
    ys,xs=np.where(before)
    if len(xs) and (min(xs)+offset[0]<0 or max(xs)+offset[0]>=size[0] or min(ys)+offset[1]<0 or max(ys)+offset[1]>=size[1]):raise ValueError('Role frame would clip alpha8')
    return result
def generation(unit,master,prompt):return {'image_generation_used':True,'provider':'OpenAI built-in image_gen','model':'not exposed by built-in tool','prompt':prompt.read_text(encoding='utf-8'),'painted_master':relative(master),'painted_master_sha256':sha(master),'method':'Delivered painted2D pixels; matte isolation, one atlas density and cab-bearing registration only; no3D or body warps'}
def base_recipe(unit,role,master,prompt,canvas):return {'recipe_type':'vcmi_animation' if role in ['battle','map'] else 'raster','output_path':PREFIX+unit+'/'+role+('.json' if role in ['battle','map'] else '.png'),'canvas':canvas,'production_status':'painted-master-complete-unapproved','generation':generation(unit,master,prompt),'acceptance':'authored configuration; independent pixels/native/rights pending'}
def build(unit,config):
    src=HERE/unit;out=src/'candidate-v1';out.mkdir(parents=True,exist_ok=True)
    selected={'idle':('idle-reactions-v1-master.png',3,3),'move':('walk-turn-v1-master.png',3,3),'attack':(config['attack'],3,3),'death':('death-v1-master.png',3,2)}
    atlases={key:isolated(src/name,columns,rows) for key,(name,columns,rows) in selected.items()}
    ref=plate(atlases['idle'][0]);ref_height=ref[3]-ref[1]
    ref_root_y=ref[3]+8/config['scale']
    hip_y=266-(atlases['idle'][0]['image'].height-1-ref_root_y)*config['scale']
    scales={key:config['scale']*ref_height/(plate(poses[0])[3]-plate(poses[0])[1]) for key,poses in atlases.items()}
    poses={};registration={};source_pins={}
    for key,(name,columns,rows) in selected.items():
        source_pins[relative(src/name)]=sha(src/name)
        for index,actor in enumerate(atlases[key]):
            label=f'{key}-{index:02}';floor=config['death_floor'][index] if key=='death' else None
            facing='front' if key=='move' and index==8 else 'half' if key=='move' and index==7 else 'right'
            im,record=native_pose(actor,scales[key],hip_y,facing,floor)
            path=png(im,out/'frames'/f'{label}.png');poses[label]=path;registration[label]=record
            png(actor['matte'],out/'mattes'/f'{label}.png')
    groups={0:[f'move-{i:02}' for i in range(6)],1:['idle-01','idle-02','idle-02','idle-03','idle-03','idle-04','idle-04'],2:['idle-00'],3:['idle-05','idle-06'],4:['idle-07','idle-08'],5:[f'death-{i:02}' for i in range(6)],7:['idle-00','move-07','move-08'],8:['move-08','move-07','idle-00'],11:[f'attack-{i:02}' for i in range(3)],12:[f'attack-{i:02}' for i in range(3,6)],13:[f'attack-{i:02}' for i in range(6,9)],22:['death-05']}
    recipe=base_recipe(unit,'battle',src/'identity-master-v1.png',src/'identity-prompt-v1.txt',[450,400]);recipe.update(pivot={'x':220,'y':266},generateShadow=1,generateOverlay=1,groups=[{'group':g,'frames':[{'frame':i,'source':relative(poses[label]),'sha256':sha(poses[label]),'source_canvas':[450,400]} for i,label in enumerate(labels)]} for g,labels in groups.items()])
    recipes=[out/'recipes'/f'{unit}-battle.json'];write(recipes[0],recipe)
    maps=[]
    for i,label in enumerate(['idle-01','idle-02','idle-03','idle-04']):
        im=role_image(Image.open(poses[label]).convert('RGBA'),(96,64),.24,(80,60));path=png(im,out/'map'/f'f{i:03}.png');maps.append(path)
        assert (np.asarray(im.getchannel('A'))[:,:32]<8).all()
    recipe=base_recipe(unit,'map',src/'identity-master-v1.png',src/'identity-prompt-v1.txt',[96,64]);recipe.update(pivot={'x':80,'y':60},generateShadow=1,generateOverlay=0,groups=[{'group':0,'frames':[{'frame':i,'source':relative(p),'sha256':sha(p),'source_canvas':[96,64]} for i,p in enumerate(maps)]}]);p=out/'recipes'/f'{unit}-map.json';write(p,recipe);recipes.append(p)
    for role,mirror in [('attackLeft',False),('attackRight',True)]:
        im=role_image(Image.open(poses['idle-07']).convert('RGBA'),(64,64),.33,(32,60),mirror);p=png(im,out/'encounters'/f'{role}.png')
        recipe=base_recipe(unit,role,src/'identity-master-v1.png',src/'identity-prompt-v1.txt',[64,64]);recipe.update(source=relative(p),source_sha256=sha(p),source_canvas=[64,64],fit='exact',visual_facing='left' if mirror else 'right');r=out/'recipes'/f'{unit}-{role}.json';write(r,recipe);recipes.append(r)
    portrait=src/'portrait-v1-master.png';portrait_image=Image.open(portrait).convert('RGBA');source_pins[relative(portrait)]=sha(portrait)
    for role,size,crop in [('large',[58,64],None),('small',[32,32],[180,220,1080,1120])]:
        im=portrait_image if crop is None else portrait_image.crop(crop)
        ratio=max(size[0]/im.width,size[1]/im.height);im=im.resize((round(im.width*ratio),round(im.height*ratio)),Image.Resampling.LANCZOS);left=(im.width-size[0])//2;top=(im.height-size[1])//2;im=im.crop((left,top,left+size[0],top+size[1]))
        p=png(im,out/'portraits'/f'{role}.png');recipe=base_recipe(unit,role,portrait,src/'portrait-prompt-v1.txt',size);recipe.update(source=relative(p),source_sha256=sha(p),source_canvas=size,fit='exact');r=out/'recipes'/f'{unit}-{role}.json';write(r,recipe);recipes.append(r)
    source_pins.update({relative(p):sha(p) for p in [Path(__file__),HERE/'components.py',HERE/'PROVENANCE.json',src/'identity-master-v1.png',*sorted(src.glob('*prompt*.txt'))]})
    write(out/'registration.json',{'status':'authored configuration','atlas_density':scales,'native_hip_y':hip_y,'root_method':'navy cab panel lower bearing with perspective offsets; one holding-ground calibration, no per-pose fitting','death_root_method':'explicit authored floor contact marks, constant atlas density','poses':registration,'source_sha256':source_pins})
    for recipe_path in recipes:
        r=json.loads(recipe_path.read_text(encoding='utf-8'))
        if unit=='reinforcedDockyardLifter' and r['generation']['painted_master'].endswith('identity-master-v1.png'):
            r['generation']['prompt']=(src/'identity-edit-prompt-v1.txt').read_text(encoding='utf-8')
        r['production_inputs']=[{'path':name,'sha256':checksum} for name,checksum in sorted(source_pins.items())]
        r['production_inputs'].append({'path':relative(out/'registration.json'),'sha256':sha(out/'registration.json')})
        write(recipe_path,r)
    return {'unit':unit,'recipes':[{'path':relative(p),'sha256':sha(p)} for p in recipes],'native_pose_sources':len(poses),'battle_frame_slots':sum(map(len,groups.values())),'source_sha256':source_pins}
if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--unit',choices=UNITS);args=ap.parse_args()
    chosen={args.unit:UNITS[args.unit]} if args.unit else UNITS
    rows=[build(u,c) for u,c in chosen.items()]
    write(HERE/'candidate-selection-t7-v1.json',{'status':'authored configuration','units':rows,'selected_in_live_pipeline':False,'native_execution':False,'release_accepted':False})
    print(json.dumps([{k:v for k,v in r.items() if k!='source_sha256'} for r in rows],indent=2))
