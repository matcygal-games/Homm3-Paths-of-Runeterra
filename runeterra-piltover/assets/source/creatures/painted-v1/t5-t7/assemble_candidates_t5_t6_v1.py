"""Painted cohorts registered by authored hip/deck marks, not per-frame fits."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
from assemble_candidates_v1 import isolated,sha,write,png,relative,base_recipe
HERE=Path(__file__).resolve().parent
CONFIG={
'forgeEngineer':{'scales':[.28,.43,.29],'root':[197,266],
'motion':[[173,170],[499,170],[826,170],[1151,170],[173,477],[500,477],[825,477],[1155,477],[176,772],[500,772],[825,775],[1152,775],[170,1065],[485,1057],[822,1060],[1150,1060]],
'action':[[155,190],[430,190],[715,190],[990,190],[155,420],[430,420],[715,420],[990,420],[155,660],[430,746],[715,744],[1000,744],[150,942],[430,943],[730,948],[1000,865],[150,1090],[430,1090],[715,1090],[1000,1090],[150,1300],[430,1300],[715,1300],[1000,1300]],
'attack':[[270,230],[770,230],[1280,230],[270,560],[770,560],[1280,560],[270,900],[770,900],[1280,900]]},
'masterForgeEngineer':{'scales':[.24,.50,.29],'root':[197,266],
'motion':[[155,204],[418,204],[698,204],[975,204],[150,558],[424,558],[704,558],[985,558],[155,900],[420,900],[700,900],[977,900],[155,1245],[418,1230],[699,1225],[980,1230]],
'action':[[150,150],[430,150],[710,150],[990,150],[150,365],[430,365],[710,365],[990,365],[150,570],[430,661],[725,669],[1000,678],[150,885],[420,878],[710,884],[990,800],[150,1025],[430,1025],[710,1025],[990,1025],[150,1235],[430,1235],[710,1235],[990,1235]],
'attack':[[220,290],[650,290],[1085,290],[220,650],[650,650],[1085,650],[220,1015],[650,1015],[1085,1015]]},
'aerialSurveyor':{'scales':[.31,.36,.24],'root':[220,266],
'motion':[[185,206],[569,206],[953,206],[1337,206],[190,458],[580,458],[965,458],[1350,458],[190,708],[580,708],[965,708],[1350,708],[190,955],[580,955],[965,955],[1350,955]],
'action':[[200,159],[590,159],[965,159],[1360,159],[200,320],[590,320],[965,320],[1360,320],[200,490],[590,520],[965,522],[1360,510],[208,672],[580,672],[965,673],[1360,649],[200,810],[590,810],[965,810],[1360,810],[200,976],[590,976],[965,976],[1360,976]],
'attack':[[260,330],[770,330],[1280,330],[260,660],[770,660],[1280,660],[260,985],[770,985],[1280,985]]},
'aerialPioneer':{'scales':[.32,.36,.24],'root':[220,266],
'motion':[[185,209],[569,209],[953,209],[1337,209],[190,461],[580,461],[965,461],[1350,461],[190,717],[580,717],[965,717],[1350,717],[240,967],[580,967],[965,967],[1350,967]],
'action':[[200,160],[590,160],[965,160],[1360,160],[200,327],[590,327],[965,327],[1360,327],[200,505],[590,530],[965,532],[1360,529],[200,693],[590,695],[965,698],[1360,665],[200,818],[590,818],[965,818],[1360,818],[200,988],[590,988],[965,988],[1360,988]],
'attack':[[260,320],[770,320],[1280,320],[260,650],[770,650],[1280,650],[260,985],[770,985],[1280,985]]}
}
def select_actions(path):
 from collections import deque
 from components import components
 im=Image.open(path).convert('RGBA');w,h=im.size;a=np.asarray(im.getchannel('A'))
 cores=[c for c in components(im.getchannel('A'),16) if c['area']>1000]
 labels=np.zeros((h,w),dtype='uint8');q=deque();centers=[];slots={}
 for tag,c in enumerate(cores,1):
  x=(c['box'][0]+c['box'][2])/2;y=(c['box'][1]+c['box'][3])/2;centers.append((x,y))
  idx=min(5,int(y/h*6))*4+min(3,int(x/w*4))
  if idx>=9 and (idx not in slots or c['area']>cores[slots[idx]-1]['area']):slots[idx]=tag
  for pos in c['pixels']:yy,xx=divmod(pos,w);labels[yy,xx]=tag
 for tag,c in enumerate(cores,1):
  for pos in c['pixels']:
   y,x=divmod(pos,w)
   if (x and not labels[y,x-1]) or (x+1<w and not labels[y,x+1]) or (y and not labels[y-1,x]) or (y+1<h and not labels[y+1,x]):q.append(pos)
 while q:
  pos=q.popleft();y,x=divmod(pos,w);tag=labels[y,x]
  for yy,xx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
   if 0<=yy<h and 0<=xx<w and a[yy,xx]>=8 and not labels[yy,xx]:labels[yy,xx]=tag;q.append(yy*w+xx)
 for y,x in zip(*np.where((a>=8)&(labels==0))):labels[y,x]=1+min(range(len(centers)),key=lambda k:(x-centers[k][0])**2+(y-centers[k][1])**2)
 assert int(((labels>0)&(a>=8)).sum())==int((a>=8).sum())
 result={}
 for idx,tag in slots.items():
  mask=Image.fromarray(np.where(labels==tag,a,0).astype('uint8'),'L');box=mask.getbbox();actor=im.copy();actor.putalpha(mask);result[idx]={'image':actor.crop(box),'box':box,'matte':mask}
 for idx in range(9,24):
  if idx not in result:raise ValueError(f'{path}: missing actor cell {idx}')
 return result
def registered(actor,scale,point,target):
 box=actor['box'];im=actor['image'];size=(round(im.width*scale),round(im.height*scale));resized=im.resize(size,Image.Resampling.LANCZOS)
 offset=(round(target[0]-(point[0]-box[0])*scale),round(target[1]-(point[1]-box[1])*scale))
 if offset[0]<0 or offset[1]<0 or offset[0]+size[0]>450 or offset[1]+size[1]>400:raise ValueError('Native actor clip')
 out=Image.new('RGBA',(450,400));out.alpha_composite(resized,offset);return out,{'source_box':box,'source_root':point,'target':target,'scale':scale,'paste':offset}
def role(im,size,scale,target,root,mirror=False):
 if mirror:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT);root=(450-root[0],root[1])
 resized=im.resize((round(450*scale),round(400*scale)),Image.Resampling.LANCZOS);off=(round(target[0]-root[0]*scale),round(target[1]-root[1]*scale))
 ys,xs=np.where(np.asarray(resized.getchannel('A'))>=8)
 if len(xs) and (xs.min()+off[0]<0 or xs.max()+off[0]>=size[0] or ys.min()+off[1]<0 or ys.max()+off[1]>=size[1]):raise ValueError('Role clip')
 out=Image.new('RGBA',size);out.alpha_composite(resized,off);return out
def build(unit,c):
 src=HERE/unit;out=src/'candidate-v1';fly=unit.startswith('aerial')
 cohorts={'motion':isolated(src/'motion-v1-master.png',4,4),'action':select_actions(src/'actions-v1-master.png'),'attack':isolated(src/'attacks-v2-master.png',3,3)}
 scales=dict(zip(cohorts,c['scales']));ref=cohorts['motion'][0];hip_target_y=266-(ref['box'][3]-c['motion'][0][1])*scales['motion']
 if fly:hip_target_y=250
 poses={};regs={}
 for key,actors in cohorts.items():
  for idx,actor in (actors.items() if isinstance(actors,dict) else enumerate(actors)):
   point=c[key][idx];dead=key=='action' and 9<=idx<=14;target=(c['root'][0],266 if dead else hip_target_y)
   im,reg=registered(actor,scales[key],point,target);label=f'{key}-{idx:02}';poses[label]=png(im,out/'frames'/f'{label}.png');regs[label]=reg
 groups={0:[f'motion-{i:02}' for i in range(4,10)],1:['motion-01','motion-02','motion-02','motion-03','motion-03','motion-10','motion-10'],2:['motion-00'],3:['motion-13','motion-14'],4:['motion-15'],5:[f'action-{i:02}' for i in range(9,15)],7:['motion-00','motion-11','motion-12'],8:['motion-12','motion-11','motion-00'],11:[f'attack-{i:02}' for i in range(3)],12:[f'attack-{i:02}' for i in range(3,6)],13:[f'attack-{i:02}' for i in range(6,9)],22:['action-14']}
 if fly:groups.update({20:[f'action-{i:02}' for i in range(15,18)],21:[f'action-{i:02}' for i in range(18,21)]})
 else:groups.update({30:[f'action-{i:02}' for i in range(15,18)],31:[f'action-{i:02}' for i in range(18,21)],32:[f'action-{i:02}' for i in range(21,24)]})
 rp=[];identity=src/'identity-master-v1.png';prompt=src/'identity-prompt-v1.txt'
 r=base_recipe(unit,'battle',identity,prompt,[450,400]);r.update(pivot=dict(zip(['x','y'],c['root'])),generateShadow=1,generateOverlay=1,groups=[{'group':g,'frames':[{'frame':i,'source':relative(poses[label]),'sha256':sha(poses[label]),'source_canvas':[450,400]} for i,label in enumerate(labels)]} for g,labels in groups.items()]);p=out/'recipes'/f'{unit}-battle.json';write(p,r);rp.append(p)
 # Four quiet map fidgets retain full body and common fixed root.
 scale=.24 if fly else .44;maps=[]
 for i,label in enumerate(['motion-01','motion-02','motion-03','motion-10']):
  im=role(Image.open(poses[label]).convert('RGBA'),[96,64],scale,[80,60],c['root']);assert (np.asarray(im.getchannel('A'))[:,:32]<8).all();maps.append(png(im,out/'map'/f'f{i:03}.png'))
 r=base_recipe(unit,'map',identity,prompt,[96,64]);r.update(pivot={'x':80,'y':60},generateShadow=1,generateOverlay=0,groups=[{'group':0,'frames':[{'frame':i,'source':relative(p),'sha256':sha(p),'source_canvas':[96,64]} for i,p in enumerate(maps)]}]);p=out/'recipes'/f'{unit}-map.json';write(p,r);rp.append(p)
 for tag,mirror in [('attackLeft',False),('attackRight',True)]:
  im=role(Image.open(poses['motion-15']).convert('RGBA'),[64,64],.30 if fly else .50,[32,60],c['root'],mirror);p=png(im,out/'encounters'/f'{tag}.png');r=base_recipe(unit,tag,identity,prompt,[64,64]);r.update(source=relative(p),source_sha256=sha(p),source_canvas=[64,64],fit='exact',visual_facing='left' if mirror else 'right');p=out/'recipes'/f'{unit}-{tag}.json';write(p,r);rp.append(p)
 portrait=src/'portrait-v1-master.png'
 for tag,size in [('large',[58,64]),('small',[32,32])]:
  im=Image.open(portrait).convert('RGBA')
  if tag=='small':im=im.crop((180,160,1080,1060))
  ratio=max(size[0]/im.width,size[1]/im.height);im=im.resize((round(im.width*ratio),round(im.height*ratio)),Image.Resampling.LANCZOS);left=(im.width-size[0])//2;top=(im.height-size[1])//2;im=im.crop((left,top,left+size[0],top+size[1]));p=png(im,out/'portraits'/f'{tag}.png');r=base_recipe(unit,tag,portrait,src/'portrait-prompt-v1.txt',size);r.update(source=relative(p),source_sha256=sha(p),source_canvas=size,fit='exact');p=out/'recipes'/f'{unit}-{tag}.json';write(p,r);rp.append(p)
 inputs=[Path(__file__),HERE/'assemble_candidates_v1.py',HERE/'components.py',HERE/'PROVENANCE.json',identity,portrait,*sorted(src.glob('*prompt*.txt')),src/'motion-v1-master.png',src/'actions-v1-master.png',src/'attacks-v2-master.png']
 pins={relative(p):sha(p) for p in inputs}
 reg=out/'registration.json';write(reg,{'status':'authored configuration','method':'authored anatomical hip/board deck marks; one scale per cohort, no per-pose bbox fit or body warp','root_annotations':c,'native_hip_y':hip_target_y,'poses':regs,'source_sha256':pins})
 for p in rp:
  r=json.loads(p.read_text());r['production_inputs']=[{'path':name,'sha256':checksum} for name,checksum in sorted(pins.items())]+[{'path':relative(reg),'sha256':sha(reg)}];write(p,r)
 return {'unit':unit,'recipes':[{'path':relative(p),'sha256':sha(p)} for p in rp],'native_pose_sources':len(poses),'battle_frame_slots':sum(map(len,groups.values())),'source_sha256':pins}
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--unit',choices=CONFIG);a=ap.parse_args();chosen={a.unit:CONFIG[a.unit]} if a.unit else CONFIG;rows=[build(u,c) for u,c in chosen.items()];write(HERE/'candidate-selection-t5-t6-v1.json',{'status':'authored configuration','units':rows,'selected_in_live_pipeline':False,'runtime_verified':False,'release_accepted':False});print(json.dumps([{k:v for k,v in row.items() if k!='source_sha256'} for row in rows],indent=2))

