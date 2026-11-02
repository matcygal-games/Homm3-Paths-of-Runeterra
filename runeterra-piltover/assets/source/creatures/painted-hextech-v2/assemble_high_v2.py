"""Technical painted2D conversion. No actor drawing, rigs, body warps or per-frame fits."""
from pathlib import Path
from collections import deque
from PIL import Image
import numpy as np,json,hashlib
from components import components
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if p.name=='runeterra-piltover')
CONFIG={
'armoredStomper':{'root':[197,266],'master':'identity-master-v1.png','motion':'motion-v1-master.png','action':'actions-v1-master.png','scales':{'motion':.25,'action':.30}},
'prismaticStomper':{'root':[197,266],'master':'identity-master-v1.png','motion':'motion-v1-master.png','action':'actions-v1-master.png','cast':'cast-v2-master.png','scales':{'motion':.25,'action':.29,'cast':.20}},
'hextechRampager':{'root':[220,266],'master':'identity-master-v1.png','motion':'motion-v1-master.png','action':'actions-v1-master.png','scales':{'motion':.35,'action':.32}},
'hextechDreadnought':{'root':[220,266],'master':'identity-master-v2.png','motion':'motion-v2-master.png','action':'actions-v2-master.png','shoot':'shoot-v3-master.png','scales':{'motion':.35,'action':.32,'shoot':.28}}
}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(PROJECT).as_posix()
def js(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def png(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,format='PNG',compress_level=9,optimize=False);return p
def isolate(path,columns,rows,needed=None):
 im=Image.open(path).convert('RGBA');w,h=im.size;a=np.asarray(im.getchannel('A'))
 cores=[c for c in components(im.getchannel('A'),32) if c['area']>1000]
 labels=np.zeros((h,w),dtype='uint8');q=deque();centers=[];slots={}
 for tag,c in enumerate(cores,1):
  x=(c['box'][0]+c['box'][2])/2;y=(c['box'][1]+c['box'][3])/2;centers.append((x,y))
  idx=min(rows-1,int(y/h*rows))*columns+min(columns-1,int(x/w*columns))
  if idx not in slots or c['area']>cores[slots[idx]-1]['area']:slots[idx]=tag
  for pos in c['pixels']:yy,xx=divmod(pos,w);labels[yy,xx]=tag
 for c in cores:
  for pos in c['pixels']:
   y,x=divmod(pos,w)
   if (x and not labels[y,x-1]) or (x+1<w and not labels[y,x+1]) or (y and not labels[y-1,x]) or (y+1<h and not labels[y+1,x]):q.append(pos)
 while q:
  pos=q.popleft();y,x=divmod(pos,w);tag=labels[y,x]
  for yy,xx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
   if 0<=yy<h and 0<=xx<w and a[yy,xx]>=8 and not labels[yy,xx]:labels[yy,xx]=tag;q.append(yy*w+xx)
 for y,x in zip(*np.where((a>=8)&(labels==0))):labels[y,x]=1+min(range(len(centers)),key=lambda k:(x-centers[k][0])**2+(y-centers[k][1])**2)
 assert int(((labels>0)&(a>=8)).sum())==int((a>=8).sum())
 wanted=list(range(columns*rows)) if needed is None else list(needed)
 out={}
 for idx in wanted:
  if idx not in slots:raise ValueError(f'{path.name}: missing independent actor {idx}, actual {sorted(slots)}')
  tag=slots[idx];mask=Image.fromarray(np.where(labels==tag,a,0).astype('uint8'),'L');box=mask.getbbox();actor=im.copy();actor.putalpha(mask)
  out[idx]={'image':actor.crop(box),'box':box,'matte':mask}
 return out
def landmark(actor,kind,front=False):
 im=actor['image'];a=np.asarray(im).astype('int16');h,w=a.shape[:2]
 if front:
  # Authored front central chassis/bearing, not feet or fitted silhouette.
  return [w*.50,h*.57],{'manual_front_bearing':True}
 m=(a[:,:,3]>=128)&(a[:,:,2]>a[:,:,0]+8)&(a[:,:,2]>a[:,:,1]+2)&(a[:,:,0]<120)&(a[:,:,1]<140)
 m[:int(h*.08)]=False;m[int(h*.72):]=False;m[:,:int(w*.18)]=False;m[:,int(w*.72):]=False
 cs=[c for c in components(Image.fromarray((m*255).astype('uint8'),'L'),1) if c['area']>30]
 if not cs:raise ValueError('No navy structural housing landmark')
 c=max(cs,key=lambda c:c['area']);x0,y0,x1,y1=c['box']
 # Project the physical forward chassis bearing from its fixed side armor
 # landmark. Use the rigid plate width, never the changing tail/limb bbox.
 dx=(1.10 if kind.startswith('hextech') else .65)*(x1-x0)
 return [(x0+x1)/2+dx,y1+(y1-y0)*.12],{'navy_housing_box':[x0,y0,x1,y1],'housing_bearing_dx':dx}
def registered(actor,scale,point,target):
 im=actor['image'];size=[max(1,round(im.width*scale)),max(1,round(im.height*scale))];im=im.resize(size,Image.Resampling.LANCZOS)
 off=[round(target[0]-point[0]*scale),round(target[1]-point[1]*scale)]
 if off[0]<0 or off[1]<0 or off[0]+size[0]>450 or off[1]+size[1]>400:raise ValueError('Native canvas clips whole actor')
 out=Image.new('RGBA',(450,400));out.alpha_composite(im,tuple(off));return out,{'source_crop':actor['box'],'source_root':point,'scale':scale,'native_root':target,'paste':off}
def scaled_role(im,size,scale,target,root,mirror=False):
 if mirror:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT);root=[450-root[0],root[1]]
 scaled=im.resize((round(450*scale),round(400*scale)),Image.Resampling.LANCZOS);off=[round(target[0]-root[0]*scale),round(target[1]-root[1]*scale)]
 ys,xs=np.where(np.asarray(scaled.getchannel('A'))>=8)
 if len(xs) and (xs.min()+off[0]<0 or xs.max()+off[0]>=size[0] or ys.min()+off[1]<0 or ys.max()+off[1]>=size[1]):raise ValueError('Role clips visible actor')
 out=Image.new('RGBA',tuple(size));out.alpha_composite(scaled,tuple(off));return out
def recipe(unit,role,master,prompt,canvas):
 return {'recipe_type':'vcmi_animation' if role in ['battle','map','projectile'] else 'raster','output_path':'Content/Sprites/runeterra/piltover/creatures/'+unit+'/'+role+('.json' if role in ['battle','map','projectile'] else '.png'),'canvas':canvas,'production_status':'painted-master-complete-unapproved','generation':{'image_generation_used':True,'provider':'OpenAI built-in image_gen','model':'not exposed by tool','painted_master':rel(master),'painted_master_sha256':sha(master),'prompt':prompt.read_text(encoding='utf-8'),'method':'Coherent painted2D sources; technical alpha8 matte isolation, fixed structural housing roots and one uniform density per atlas, never body warps or per-frame fitting'},'acceptance':'authored configuration; native visual/motion and rights pending'}
def frames(paths,canvas):return [{'frame':i,'source':rel(p),'sha256':sha(p),'source_canvas':canvas} for i,p in enumerate(paths)]
def build(unit,c):
 src=HERE/unit;out=src/'candidate-v1';t7=unit.startswith('hextech');cfg={'motion':(c['motion'],4,4,None),'action':(c['action'],3 if t7 else 4,5 if t7 else 6,None if unit=='armoredStomper' or t7 else range(15))}
 for key in ['cast','shoot']:
  if key in c:cfg[key]=(c[key],3,3,None)
 atlases={k:isolate(src/name,cols,rows,needed) for k,(name,cols,rows,needed) in cfg.items()}
 ref=atlases['motion'][0];point,_=landmark(ref,unit);hip_y=266-(ref['image'].height-1-point[1])*c['scales']['motion']
 poses={};records={}
 for k,actors in atlases.items():
  for idx,actor in actors.items():
   death=k=='action' and 9<=idx<=14
   if death:
    # Explicit horizontal floor-contact marks per cohort row, stable world floor.
    # These are authored from source pose row/physical chassis, not per-pose fits.
    marks={'armoredStomper':[[525,587],[875,587],[1225,587],[175,750],[525,750],[875,750]],'prismaticStomper':[[543,556],[905,556],[1267,556],[181,704],[543,704],[905,704]],'hextechRampager':[[255,844],[767,844],[1279,844],[255,1004],[767,1004],[1279,1004]],'hextechDreadnought':[[255,870],[767,870],[1279,870],[255,1011],[767,1011],[1279,1011]]}
    absolute=marks[unit][idx-9];p=[absolute[0]-actor['box'][0],absolute[1]-actor['box'][1]];target=[c['root'][0],266];extra={'authored_source_floor_mark':absolute}
   else:
    p,extra=landmark(actor,unit,front=k=='motion' and idx==12 or k=='cast' and 3<=idx<=5);target=[c['root'][0],hip_y]
    if unit=='hextechRampager' and k=='motion' and idx==11:
     p=[215,157];extra={'authored_halfturn_forward_chassis_bearing':[215,157]}
   im,record=registered(actor,c['scales'][k],p,target);record.update(extra);label=f'{k}-{idx:02}';poses[label]=png(out/'frames'/f'{label}.png',im);records[label]=record
 groups={0:[f'motion-{i:02}' for i in range(4,10)],1:['motion-01','motion-02','motion-02','motion-03','motion-03','motion-10','motion-10'],2:['motion-00'],3:['motion-13','motion-14'],4:['motion-15'],5:[f'action-{i:02}' for i in range(9,15)],7:['motion-00','motion-11','motion-12'],8:['motion-12','motion-11','motion-00'],11:[f'action-{i:02}' for i in range(3)],12:[f'action-{i:02}' for i in range(3,6)],13:[f'action-{i:02}' for i in range(6,9)],22:['action-14']}
 if not t7:
  k='cast' if 'cast' in c else 'action';start=0 if k=='cast' else 15
  for group in [30,31,32]:groups[group]=[f'{k}-{i:02}' for i in range(start,start+3)];start+=3
 if 'shoot' in c:
  # Three genuine directional poses; deliberate three-tick windup hold aligns
  # painted release to source index3/native one-based climax4, then recoil.
  for group,start in [(14,0),(15,3),(16,6)]:groups[group]=[f'shoot-{start:02}']*3+[f'shoot-{start+1:02}',f'shoot-{start+2:02}']
 master=src/c['master'];ip=src/('identity-prompt-v2.txt' if c['master'].endswith('v2.png') else 'identity-prompt-v1.txt');rp=[]
 r=recipe(unit,'battle',master,ip,[450,400]);r.update(pivot=dict(zip(['x','y'],c['root'])),generateShadow=1,generateOverlay=1,groups=[{'group':g,'frames':frames([poses[x] for x in labels],[450,400])} for g,labels in groups.items()]);p=out/'recipes'/f'{unit}-battle.json';js(p,r);rp.append(p)
 maps=[]
 for i,label in enumerate(['motion-01','motion-02','motion-03','motion-10']):
  im=scaled_role(Image.open(poses[label]).convert('RGBA'),[96,64],.26 if t7 else .38,[80,60],c['root']);assert (np.asarray(im.getchannel('A'))[:,:32]<8).all();maps.append(png(out/'map'/f'f{i:03}.png',im))
 r=recipe(unit,'map',master,ip,[96,64]);r.update(pivot={'x':80,'y':60},generateShadow=1,generateOverlay=0,groups=[{'group':0,'frames':frames(maps,[96,64])}]);p=out/'recipes'/f'{unit}-map.json';js(p,r);rp.append(p)
 for tag,mirror in [('attackLeft',False),('attackRight',True)]:
  im=scaled_role(Image.open(poses['motion-15']).convert('RGBA'),[64,64],.32 if t7 else .50,[32,60],c['root'],mirror);p=png(out/'encounters'/f'{tag}.png',im);r=recipe(unit,tag,master,ip,[64,64]);r.update(source=rel(p),source_sha256=sha(p),source_canvas=[64,64],fit='exact',visual_facing='left' if mirror else 'right');p=out/'recipes'/f'{unit}-{tag}.json';js(p,r);rp.append(p)
 portrait=src/('portrait-v2-master.png' if unit=='hextechDreadnought' else 'portrait-v1-master.png');pp=src/('portrait-prompt-v2.txt' if unit=='hextechDreadnought' else 'portrait-prompt-v1.txt')
 for tag,size in [('large',[58,64]),('small',[32,32])]:
  im=Image.open(portrait).convert('RGBA')
  if tag=='small':im=im.crop((190,220,1090,1120))
  ratio=max(size[0]/im.width,size[1]/im.height);im=im.resize((round(im.width*ratio),round(im.height*ratio)),Image.Resampling.LANCZOS);x=(im.width-size[0])//2;y=(im.height-size[1])//2;im=im.crop((x,y,x+size[0],y+size[1]));p=png(out/'portraits'/f'{tag}.png',im);r=recipe(unit,tag,portrait,pp,size);r.update(source=rel(p),source_sha256=sha(p),source_canvas=size,fit='exact');p=out/'recipes'/f'{unit}-{tag}.json';js(p,r);rp.append(p)
 if unit=='hextechDreadnought':
  projectile=src/'projectile-v1-master.png';actors=isolate(projectile,5,5);missiles=[];measurements=[]
  # The native ordinary missile holds ONE angle frame during flight. Its
  # reverse-Y angle index is DOWN, DOWNRIGHT, RIGHT, UPRIGHT, UP; group1 is
  # engine-generated mirrored art. Other painted phases stay editable only.
  for frame,row in enumerate([4,3,2,1,0]):
   actor=actors[row*5+2];a=np.asarray(actor['image']);m=(a[:,:,0]>180)&(a[:,:,1]>220)&(a[:,:,2]>220)&(a[:,:,3]>=128);ys,xs=np.where(m)
   if len(xs)<5:raise ValueError('Projectile core center is not measurable')
   root=[float(xs.mean()),float(ys.mean())];scale=.14;size=[round(actor['image'].width*scale),round(actor['image'].height*scale)];im=actor['image'].resize(size,Image.Resampling.LANCZOS);off=[round(32-root[0]*scale),round(32-root[1]*scale)];canvas=Image.new('RGBA',(64,64));canvas.alpha_composite(im,tuple(off));missiles.append(png(out/'projectile'/f'angle-{frame}.png',canvas));measurements.append({'frame':frame,'source_row':row,'source_phase_zero_based':2,'source_crop':actor['box'],'source_white_core_centroid':root,'scale':scale,'native_core_center':[32,32]})
  r=recipe(unit,'projectile',projectile,src/'projectile-prompt-v1.txt',[64,64]);r.update(pivot={'x':32,'y':32},generateShadow=0,generateOverlay=0,groups=[{'group':0,'frames':frames(missiles,[64,64])}],native_angle_index=['DOWN','DOWN_RIGHT','RIGHT','UP_RIGHT','UP'],selected_painted_phase_zero_based=2,ordinary_missile_animation=False);p=out/'recipes'/f'{unit}-projectile.json';js(p,r);rp.append(p);js(out/'projectile-registration.json',measurements)
 if unit=='hextechDreadnought':
  measure=[]
  for direction,group,index,tip in [('upper',14,1,[232,194]),('middle',15,4,[249,223]),('lower',16,7,[248,245])]:
   record=records[f'shoot-{index:02}'];raw_tip=[round(record['source_crop'][0]+(tip[0]-record['paste'][0])/record['scale']),round(record['source_crop'][1]+(tip[1]-record['paste'][1])/record['scale'])];native=poses[f'shoot-{index:02}']
   measure.append({'direction':direction,'group':group,'release_frame_zero_based':3,'native_tip_pixels':tip,'original_tip_pixels':raw_tip,'source_frame':{'path':rel(src/c['shoot']),'sha256':sha(src/c['shoot']),'crop':record['source_crop']},'native_frame':{'path':rel(native),'sha256':sha(native)},'physical_landmark':'center of forward shoulder condenser iris at barrel lip, behind flash; never bolt/puff centroid','native_right_anchor':[197,265],'derived_right_offset':[tip[0]-197,tip[1]-265]})
  js(out/'shot-measurements-v2.json',{'units':[{'id':unit,'source_kind':'painted-native','source_master':{'path':rel(src/c['shoot']),'sha256':sha(src/c['shoot'])},'measurements':measure,'native_left_trajectory_verified':False,'source_pixel_review':'own artist inspected enlarged native physical iris; coordinator independently viewed same measured source pixels, no native playback claim'}]})
 inputs=[Path(__file__),HERE/'components.py',HERE/'provenance-high-v2.json',master,portrait,ip,pp,*[src/name for name,_,_,_ in cfg.values()]]
 for call in json.loads((HERE/'provenance-high-v2.json').read_text())['calls']:
  if call['unit']==unit:
   inputs.extend([PROJECT/call['master'],PROJECT/call['prompt'],*[PROJECT/x['path'] for x in call['own_image_inputs']]])
 if unit=='hextechDreadnought':inputs.extend([src/'projectile-v1-master.png',src/'projectile-prompt-v1.txt'])
 if unit=='hextechDreadnought':inputs.extend([out/'shot-measurements-v2.json',out/'projectile-registration.json'])
 pins={rel(p):sha(p) for p in inputs};reg=out/'registration.json';js(reg,{'status':'authored configuration','native_holding_ground':266,'structural_bearing_target_y':hip_y,'scales':c['scales'],'root_method':'same navy structural housing/bearing, uniform density per atlas; explicit front central bearing; corpse floor marks pending independent pixel review','poses':records,'source_sha256':pins})
 for p in rp:
  r=json.loads(p.read_text());r['production_inputs']=[{'path':n,'sha256':h} for n,h in sorted(pins.items())]+[{'path':rel(reg),'sha256':sha(reg)}];js(p,r)
 return {'unit':unit,'recipes':[{'path':rel(p),'sha256':sha(p)} for p in rp],'poses':len(poses),'battle_slots':sum(map(len,groups.values()))}
if __name__=='__main__':
 import argparse
 a=argparse.ArgumentParser();a.add_argument('--unit',choices=CONFIG);opt=a.parse_args();units=[opt.unit] if opt.unit else CONFIG
 rows=[build(u,CONFIG[u]) for u in units];js(HERE/'candidate-selection-high-v2.json',{'status':'authored configuration','units':rows,'selected_in_live_pipeline':False,'runtime_verified':False,'release_accepted':False});print(json.dumps(rows,indent=2))

