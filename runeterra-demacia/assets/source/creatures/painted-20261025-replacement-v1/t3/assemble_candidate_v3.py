"""Deterministic whole-pose technical assembly of genuinely painted Inciters."""
from pathlib import Path
from PIL import Image,ImageChops
import argparse,hashlib,json
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[4]
UNITS=('mageseekerInciter','seniorInciter')
GROUPS={0:['walk'+str(i) for i in range(6)],1:['hold','fidget1','fidget1','fidget2','fidget2','fidget3','fidget3'],2:['hold'],3:['hit','hold'],4:['defend','hold'],5:['die0','die1','die2','dead'],7:['hold','turn1','front'],8:['front','turn1','hold'],11:['up0','up1','up2','up2','up3','hold'],12:['level0','level1','level2','level2','level3','hold'],13:['down0','down1','down2','down2','down3','hold'],14:['shootUp'+str(i) for i in range(6)],15:['shootLevel'+str(i) for i in range(6)],16:['shootDown'+str(i) for i in range(6)],22:['dead']}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(PROJECT).as_posix()
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def checked(r):
 p=(PROJECT/r['source']).resolve()
 if not p.is_relative_to((PROJECT/'assets/source').resolve()) or not p.is_file() or sha(p)!=r['sha256']:raise ValueError('Painted source pin drift or escape '+str(p))
 return p
def actor(r):
 im=Image.open(checked(r)).convert('RGBA');mask=Image.open(checked(r['matte'])).convert('L')
 if im.size!=mask.size:raise ValueError('matte size')
 if 'pelvis_axis_annotation' in r:
  x,y=r['pelvis_axis_annotation']['source_pixel']
  if r['root'][0]!=x or im.getpixel((x,y))[3]<128:raise ValueError('Painted pelvis-axis registration changed or misses actor')
 im.putalpha(ImageChops.multiply(im.getchannel('A'),mask).point(lambda v:0 if v<32 else v));im=im.crop(r['crop']);s=r['scale'];rx=r['root'][0]-r['crop'][0];ry=r['root'][1]-r['crop'][1]
 return im.transform((450,400),Image.Transform.AFFINE,(1/s,0,rx-197/s,0,1/s,ry-266/s),Image.Resampling.BICUBIC)
def project(im,mirror=False,scale=.45,canvas=(96,64),anchor=(80,60)):
 sx=-scale if mirror else scale
 return im.transform(canvas,Image.Transform.AFFINE,(1/sx,0,197-anchor[0]/sx,0,1/scale,266-anchor[1]/scale),Image.Resampling.BICUBIC)
def descriptor(p,**extra):return {'source':rel(p),'sha256':sha(p),'source_sha256':sha(p),**extra}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--report',type=Path);args=ap.parse_args();plan=json.loads((HERE/'assembly-plan-v3.json').read_text());selection={};paths=[];units={}
 direct=[p for p in HERE.glob('*') if p.is_file() and (p.name.endswith('-public.png') or p.name in ('assembly-plan-v1.json','assembly-plan-v3.json','all-prompts-v1.json','all-prompts-v2.json','public-source-ledger-v1.json','shot-measurements-v3.json','assemble_candidate_v3.py'))]
 direct+=sorted((HERE/'mattes').glob('*.png'));pins=[{'path':rel(p),'sha256':sha(p)} for p in sorted(direct)]
 for unit in UNITS:
  native=HERE/'native-v3'/unit;native.mkdir(parents=True,exist_ok=True);poses={name.split('/')[1]:actor(r) for name,r in plan['poses'].items() if name.startswith(unit+'/')};groups=[]
  for g,names in GROUPS.items():
   fs=[]
   for f,n in enumerate(names):
    p=native/f'g{g:02d}-f{f:03d}.png';poses[n].save(p);fs.append(descriptor(p))
   groups.append({'group':g,'frames':fs})
  assert poses['dead'].tobytes()!=poses['hold'].tobytes()
  assert Image.open(native/'g22-f000.png').convert('RGBA').tobytes()==Image.open(native/'g05-f003.png').convert('RGBA').tobytes()
  generation={'image_generation_used':True,'provider':'OpenAI built-in imagegen','model':'not exposed','method':'Fresh genuine painted2D whole-body action sources; pinned whole-actor matte, fixed source-sheet density and root transform only; no3D/limbwarp/procedural actor','painted_master':rel(HERE/(('inciter' if unit==UNITS[0] else 'senior')+'-holding-master-v1-public.png')),'native_playback':'not_run','release_accepted':False}
  generation['painted_master_sha256']=sha(PROJECT/generation['painted_master'])
  common={'unit':unit,'generation':generation,'producer_inputs':pins,'status':'built-unreviewed','visual_approval_granted':False,'acceptance':'authored configuration; candidate source pixels; native motion/final art/rights pending','credits':'Original project-directed built-in imagegen painted2D. Reference images private, not bundled. Rights approval unresolved.'}
  out=f'Content/Sprites/runeterra/demacia/creatures/{unit}/';recipes={}
  recipes['battle']={**common,'recipe_type':'vcmi_animation','output_path':out+'battle.json','canvas':[450,400],'pivot':{'x':197,'y':266},'generateOverlay':1,'generateShadow':1,'groups':groups}
  mapframes=[]
  for f,name in enumerate(['hold','fidget1','fidget2','fidget3','turn1','front']):
   src=native/f'map-parent-f{f:03d}.png';poses[name].save(src);p=native/f'map-f{f:03d}.png';project(poses[name],True).save(p);mapframes.append(descriptor(p,projection_contract={'source':rel(src),'source_sha256':sha(src),'pivot':[197,266],'anchor':[80,60],'canvas':[96,64],'scale':.45,'mirrored':True}))
  recipes['map']={**common,'recipe_type':'vcmi_animation','output_path':out+'map.json','canvas':[96,64],'pivot':{'x':80,'y':60},'generateOverlay':0,'generateShadow':2,'groups':[{'group':0,'frames':mapframes}]}
  for role,mirror in [('attackLeft',False),('attackRight',True)]:
   src=native/(role+'-parent.png');poses['turn1'].save(src);p=native/(role+'.png');project(poses['turn1'],mirror,canvas=(64,64),anchor=(48,60)).save(p)
   recipes[role]={**common,'recipe_type':'raster','output_path':out+role+'.png','source':rel(p),'source_sha256':sha(p),'size':[64,64],'fit':'contain','require_alpha':True,'projection_contract':{'source':rel(src),'source_sha256':sha(src),'pivot':[197,266],'anchor':[48,60],'canvas':[64,64],'scale':.45,'mirrored':mirror,'source_facing':'right'}}
  portrait=checked(plan['portraits'][unit]);im=Image.open(portrait)
  for role,size in [('large',[58,64]),('small',[32,32])]:
   h=im.height;w=round(h*size[0]/size[1])
   if w>im.width:w=im.width;h=round(w*size[1]/size[0])
   x=(im.width-w)//2;y=0
   recipes[role]={**common,'recipe_type':'raster','output_path':out+role+'.png','source':rel(portrait),'source_sha256':sha(portrait),'size':size,'crop':[x,y,x+w,y+h],'fit':'contain','require_alpha':False}
  for role,r in recipes.items():
   p=HERE/'candidates-v3'/f'{unit}-{role}.json';dump(p,r);selection[r['output_path']]=rel(p);paths.append(p)
  units[unit]={'battle_frames':sum(len(v) for v in GROUPS.values()),'pivot':[197,266],'corpse_exact_final_death':True,'turn':'g7 genuine side-to-front; engine flips;g8 reverse same half-turn','native_verified':False,'gait_review':'pending native six-frame anatomy review','release_climax_zero_based':3}
 # Shared finite staff bolt: one genuine painted source, technical five-angle sampling.
 source=HERE/'staff-bolt-master-v1-public.png';im=Image.open(source).convert('RGBA');bbox=im.getchannel('A').point(lambda v:255 if v>=128 else 0).getbbox();tile=im.crop(bbox);tile.thumbnail((24,12),Image.Resampling.LANCZOS);projectile_frames=[]
 for f,angle in enumerate([90,45,0,-45,-90]):
  p=HERE/'native-v3'/f'inciterBolt-{f}.png';canvas=Image.new('RGBA',(32,32));rot=tile.rotate(angle,Image.Resampling.BICUBIC,expand=True);canvas.alpha_composite(rot,((32-rot.width)//2,(32-rot.height)//2));canvas.save(p);projectile_frames.append(descriptor(p))
 r={'recipe_type':'vcmi_animation','output_path':'Content/Sprites/runeterra/demacia/projectiles/inciterBolt.json','canvas':[32,32],'pivot':{'x':16,'y':16},'generateOverlay':0,'generateShadow':0,'groups':[{'group':0,'frames':projectile_frames}],'producer_inputs':pins,'generation':{'image_generation_used':True,'provider':'OpenAI built-in imagegen','painted_master':rel(source),'painted_master_sha256':sha(source),'method':'Genuine painted white-gold physical staff-bolt adaptation; finite technical rotations only'},'status':'built-unreviewed','acceptance':'authored configuration; native release and projectile visibility pending'}
 p=HERE/'candidates-v3/inciterBolt-projectile.json';dump(p,r);selection[r['output_path']]=rel(p);paths.append(p)
 result={'status':'authored configuration; unselected source candidates','candidates':selection,'recipe_sha256':{rel(p):sha(p) for p in paths},'units':units};dump(HERE/'candidate-selection-v3.json',result)
 if args.report:dump(args.report,result)
 print(json.dumps({'recipes':len(paths),'units':units,'selection_sha256':sha(HERE/'candidate-selection-v3.json')}))
if __name__=='__main__':main()
