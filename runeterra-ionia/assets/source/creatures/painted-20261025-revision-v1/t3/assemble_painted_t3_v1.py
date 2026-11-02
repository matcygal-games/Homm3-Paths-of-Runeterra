"""Portable fixed-crop/fixed-root painted T3 source producer. No live recipes read.

Reproduce with: python <this file>. Requires Pillow. All creative bitmap pixels
come from pinned built-in imagegen PNGs. This script only crops, samples, places,
reflects, and writes deterministic native frames and candidate recipes.
"""
from pathlib import Path
import argparse,hashlib,io,json
from PIL import Image,ImageFilter,ImageOps
from collections import deque

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[4]
SELF=Path(__file__).resolve()
PREFIX=SOURCE.relative_to(PROJECT).as_posix()
UNITS=('vastayanScout','vastayanWarrior')
ROLES=('battle','map','large','small','attackLeft','attackRight')
GROUPS={0:['walk'+str(i) for i in range(6)],1:['fidget0','fidget1','fidget1','fidget2','fidget2','fidget3','fidget3'],2:['holding0','holding1'],3:['hit'+str(i) for i in range(3)],4:['defend'+str(i) for i in range(3)],5:['death'+str(i) for i in range(6)],7:['holding0','turnFront0','turnFront1'],8:['turnFront1','turnFront0','holding0'],11:['meleeUpper'+str(i) for i in range(6)],12:['meleeMiddle'+str(i) for i in range(6)],13:['meleeLower'+str(i) for i in range(6)],14:['shootUpper'+str(i) for i in range(6)],15:['shootMiddle'+str(i) for i in range(6)],16:['shootLower'+str(i) for i in range(6)],22:['death5']}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def local(name):
 if not isinstance(name,str) or '\\' in name or ':' in name or any(t in ('','.','..') for t in name.split('/')):raise ValueError('Unsafe source path')
 p=(PROJECT/name).resolve()
 scene_parents=(PROJECT/'assets/source/town/landscape-v1',PROJECT/'assets/source/town/landscape-v2')
 if not p.is_relative_to(SOURCE) and not any(p.is_relative_to(a) for a in scene_parents):raise ValueError('Input/output leaves owned family and declared own painted scene parents')
 return p
def rel(p):return Path(p).relative_to(PROJECT).as_posix()
def encoded(v):return (json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode()
def png(im):
 out=io.BytesIO();im.save(out,format='PNG',compress_level=9,optimize=False);return out.getvalue()
def write(p,data,verify=False):
 p=Path(p);data=data if isinstance(data,bytes) else encoded(data)
 if verify:
  if not p.is_file() or p.read_bytes()!=data:raise ValueError('Frozen output differs: '+rel(p))
 else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 return hashlib.sha256(data).hexdigest()
def affine_project(im,pivot=(197,266),scale=.5,mirrored=False,canvas=(96,64),anchor=(80,60)):
 sx=-scale if mirrored else scale
 return im.convert('RGBA').transform(canvas,Image.Transform.AFFINE,(1/sx,0,pivot[0]-anchor[0]/sx,0,1/scale,pivot[1]-anchor[1]/scale),Image.Resampling.BICUBIC)
def pose_image(unit,name,images):
 pose=unit['poses'][name];item=unit['sources'][pose['source_key']];master=images[item['source']]
 box=pose['crop'];tile=master.crop(tuple(box));s=item['scale'];rx,ry=pose['root'];rx-=box[0];ry-=box[1]
 # Technical source-cell isolation: retain the existing painted connected actor,
 # remove neighboring-cell fragments only. Never fit/rescale to an opaque box.
 # Two-pixel mask growth retains the source antialias fringe unchanged. A128
 # connected core prevents low-alpha provider backdrop haze linking two cells.
 if 'seed' in pose:
  alpha=tile.getchannel('A');pixels=alpha.tobytes();w,h=tile.size
  sx,sy=pose['seed'];sx-=box[0];sy-=box[1];todo=deque([(int(sx),int(sy))]);seen=set();keep=bytearray(w*h)
  while todo:
   x,y=todo.popleft()
   if not (0<=x<w and 0<=y<h):continue
   index=y*w+x
   if index in seen:continue
   seen.add(index)
   if pixels[index]<128:continue
   keep[index]=255;todo.extend(((x-1,y),(x+1,y),(x,y-1),(x,y+1)))
  if not any(keep):raise ValueError('Actor seed misses painted body: '+name)
  mask=Image.frombytes('L',(w,h),bytes(keep)).filter(ImageFilter.MaxFilter(5))
  from PIL import ImageChops
  tile.putalpha(ImageChops.multiply(alpha,mask))
 return tile.transform((450,400),Image.Transform.AFFINE,(1/s,0,rx-197/s,0,1/s,ry-266/s),Image.Resampling.BICUBIC)
def check_plan(plan,contracts):
 if set(plan['units'])!=set(UNITS):raise ValueError('Wrong family units')
 for key,unit in plan['units'].items():
  expected={x for seq in GROUPS.values() for x in seq}
  if set(unit['poses'])!=expected:raise ValueError('Missing/extra genuine semantic poses')
  cells={}
  for role,p in unit['poses'].items():
   if p['semantic']!=role:raise ValueError('Pose role mismatch: '+role)
   if p['source_key'] not in unit['sources']:raise ValueError('Missing pose source')
   cell=(p['source_key'],tuple(p['crop']))
   if cell in cells:raise ValueError('Distinct roles alias a painted cell: '+role+' / '+cells[cell])
   cells[cell]=role
  for g in contracts[key+'/battle']['groups']:
   if g['frame_count']!=len(GROUPS[g['group']]):raise ValueError('Native group length mismatch')
  if unit['portrait_source'] not in unit['sources']:raise ValueError('Portrait source missing')
def assemble(plan_path=None,verify=False):
 plan_path=Path(plan_path) if plan_path else SOURCE/'assembly-plan-v1.json'
 if not plan_path.resolve().is_relative_to(SOURCE):raise ValueError('Plan leaves owned family')
 plan=json.loads(plan_path.read_text());contracts_path=SOURCE/'native-contracts-v1.json'
 if sha(contracts_path)!=plan['contracts_sha256']:raise ValueError('Native numeric contract changed')
 contracts=json.loads(contracts_path.read_text());check_plan(plan,contracts)
 files={rel(SELF),rel(plan_path),rel(contracts_path),PREFIX+'/prompts.json',PREFIX+'/tool-receipts-v1.json',PREFIX+'/public-inputs-ledger-v1.json',PREFIX+'/requirements-pillow-v1.txt',PREFIX+'/REPRODUCE.txt'}
 # Preserve raw imagegen masters and rejected fresh2D versions as source history.
 # There are no old rendered images in this namespace. Direct pins deliberately
 # close these files too; the shared scanner does not expand nested JSON ledgers.
 files.update(rel(p) for p in SOURCE.glob('*-public.png'))
 images={}
 for unit in plan['units'].values():
  for item in unit['sources'].values():
   p=local(item['source'])
   if not p.is_file() or sha(p)!=item['source_sha256']:raise ValueError('Painted source missing/stale: '+item['source'])
   im=Image.open(p);im.load()
   if im.mode!='RGBA' or list(im.size)!=item['source_canvas']:raise ValueError('Painted source canvas/mode mismatch')
   if im.getchannel('A').getextrema()[0]>=8:raise ValueError('Painted master lacks a native-transparent background')
   images[item['source']]=im;files.add(item['source'])
 if 'projectile' in plan:
  item=plan['projectile'];p=local(item['source'])
  if not p.is_file() or sha(p)!=item['source_sha256']:raise ValueError('Fresh painted arrow missing/stale')
  im=Image.open(p).convert('RGBA');im.load()
  if list(im.size)!=item['source_canvas']:raise ValueError('Painted arrow canvas changed')
  images[item['source']]=im;files.add(item['source'])
 if 'portrait_scene' in plan:
  scene=plan['portrait_scene'];p=local(scene['source'])
  if sha(p)!=scene['source_sha256']:raise ValueError('Own painted portrait scene changed')
  images[scene['source']]=Image.open(p).convert('RGBA');files.add(scene['source'])
  for item in scene['ancestry_pins']:
   if sha(local(item['path']))!=item['sha256']:raise ValueError('Own painted scene ancestry changed')
   files.add(item['path'])
 gait_expected={}
 if 'gait_registration' in plan:
  item=plan['gait_registration'];path=local(item['source'])
  if sha(path)!=item['source_sha256']:raise ValueError('Whole6 painted gait review binding changed')
  files.add(item['source']);gait_expected={(r['unit'],r['frame']):r['native_RGBA_sha256'] for r in json.loads(path.read_text())['records']}
 pins=[{'path':name,'sha256':sha(local(name))} for name in sorted(files)]
 results={};recipes={};native={};records=[];unit_common={}
 for key,unit in plan['units'].items():
  base=SOURCE/'native'/key
  poses={n:pose_image(unit,n,images) for n in unit['poses']}
  for f in range(6):
   if gait_expected and hashlib.sha256(poses['walk'+str(f)].tobytes()).hexdigest()!=gait_expected[(key,f)]:raise ValueError('Gait decodedRGBA differs from actual six-pose review')
  for g,names in GROUPS.items():
   for f,name in enumerate(names):
    p=base/f'g{g:02d}-f{f:03d}.png';checksum=write(p,png(poses[name]),verify);native[(key,g,f)]=(p,checksum)
    records.append({'unit':key,'group':g,'frame':f,'semantic':name,'source':unit['poses'][name],'output':rel(p),'sha256':checksum})
  generation={'image_generation_used':True,'provider':'OpenAI built-in imagegen','model':'not exposed by built-in tool','prompt':'Exact per-call prompts and actual tool inputs in pinned prompts.json and tool-receipts-v1.json. New image-based painted2D anatomy/actions; deterministic fixed crop/root/affine only.','painted_master':unit['sources'][unit['portrait_source']]['source'],'painted_master_sha256':unit['sources'][unit['portrait_source']]['source_sha256'],'method':'Fresh painted2D sources; no mesh/render visual inputs or frame warps','native_playback':'not_run','release_accepted':False}
  common={'status':'built-unreviewed','acceptance':'authored configuration; native motion, final art and rights review pending','production_status':'painted-master-complete-unapproved','visual_approval_granted':False,'credits':{'author':'Project-directed OpenAI built-in imagegen painted2D; deterministic assembly','license':None,'redistribution':'unresolved; release prohibited'},'generation':generation,'producer_inputs':pins,'unit':key}
  unit_common[key]=common
  for role in ROLES:
   contract=contracts[key+'/'+role];recipe={**common,'recipe_type':contract['recipe_type'],'output_path':contract['output_path']}
   if role=='battle':
    recipe.update({k:contract[k] for k in ('canvas','pivot','generateOverlay','generateShadow')})
    recipe['groups']=[{'group':g,'frames':[{'source':rel(native[(key,g,i)][0]),'source_sha256':native[(key,g,i)][1],'sha256':native[(key,g,i)][1],'source_canvas':[450,400]} for i in range(len(seq))]} for g,seq in GROUPS.items()]
   elif role=='map':
    recipe.update({k:contract[k] for k in ('canvas','pivot','generateOverlay','generateShadow')})
    frames=[]
    map_poses=[('fidget0',1,0),('fidget1',1,1),('fidget2',1,3),('fidget3',1,5),('holding0',2,0),('holding1',2,1)]
    for f,(pose_name,g,i) in enumerate(map_poses):
     src,src_sha=native[(key,g,i)];out=base/f'map-f{f:03d}.png';checksum=write(out,png(affine_project(poses[pose_name],mirrored=True)),verify)
     frames.append({'source':rel(out),'source_sha256':checksum,'sha256':checksum,'source_canvas':[96,64],'projection_contract':{'source':rel(src),'source_sha256':src_sha,'pivot':[197,266],'scale':.5,'mirrored':True,'anchor':[80,60],'canvas':[96,64]}})
    recipe['groups']=[{'group':0,'frames':frames}]
   else:
    size=contract.get('size',contract.get('canvas'));out=base/(role+'.png')
    if role.startswith('attack'):
     src,src_sha=native[(key,7,1)];mirrored=role=='attackLeft';picture=affine_project(poses['turnFront0'],mirrored=mirrored)
     recipe['projection_contract']={'source':rel(src),'source_sha256':src_sha,'pivot':[197,266],'scale':.5,'source_facing':'right','mirrored':mirrored,'anchor':[80,60],'canvas':[96,64]}
    else:
     image=images[unit['sources'][unit['portrait_source']]['source']];picture=image.crop(tuple(unit['portrait_crops'][role]));scale=min(size[0]/picture.width,size[1]/picture.height);picture=picture.resize((round(picture.width*scale),round(picture.height*scale)),Image.Resampling.LANCZOS)
     scene=plan['portrait_scene'];background=images[scene['source']].crop(tuple(scene['crops'][key][role]));layer=ImageOps.fit(background,tuple(size),Image.Resampling.LANCZOS);layer.alpha_composite(picture,((size[0]-picture.width)//2,(size[1]-picture.height)//2));picture=layer
     recipe['portrait_background']={'source':scene['source'],'source_sha256':scene['source_sha256'],'source_canvas':scene['source_canvas'],'crop':scene['crops'][key][role],'ancestry_pins':scene['ancestry_pins'],'scope':'Existing own painted2D Ionian scene; close highresolution head/chest crop, no UI frame'}
    checksum=write(out,png(picture),verify);recipe.update({'size':size,'source':rel(out),'source_sha256':checksum,'source_canvas':size,'require_alpha':role.startswith('attack'),'fit':'exact'})
   rp=SOURCE/'candidates'/f'{key}-{role}.json';write(rp,recipe,verify);recipes[contract['output_path']]=rel(rp);results[rel(rp)]=sha(rp)
 for role,portrait in (('towerLarge','large'),('towerSmall','small')):
  contract=contracts['siege/'+role];p=SOURCE/'native/vastayanScout'/f'{portrait}.png';im=Image.open(p).convert('RGBA');out=SOURCE/'native/siege'/f'{role}.png';checksum=write(out,png(im),verify)
  recipe={**unit_common['vastayanScout'],'unit':'vastayanScout','recipe_type':'raster','output_path':contract['output_path'],'size':contract['canvas'],'source':rel(out),'source_sha256':checksum,'source_canvas':contract['canvas'],'require_alpha':False,'fit':'exact','alias_contract':{'source':rel(p),'source_sha256':sha(p),'relationship':'Exact newly painted configured Scout scenic close-portrait duplicate; no old tower pixels'}}
  rp=SOURCE/'candidates'/f'{role}.png.json';write(rp,recipe,verify);recipes[contract['output_path']]=rel(rp);results[rel(rp)]=sha(rp)
 if 'projectile' in plan:
  arrow=plan['projectile'];im=images[arrow['source']].crop(tuple(arrow['crop']));ratio=arrow['native_length']/im.width;im=im.resize((arrow['native_length'],max(1,round(im.height*ratio))),Image.Resampling.LANCZOS);centered=Image.new('RGBA',(40,40));centered.alpha_composite(im,((40-im.width)//2,(40-im.height)//2))
  for key in UNITS:
   contract=contracts[key+'/projectile'];frames=[]
   for f,angle in enumerate(contract['trajectory_angles']):
    out=SOURCE/'native'/key/f'projectile-f{f:03d}.png';picture=centered.rotate(angle,Image.Resampling.BICUBIC,expand=False,center=(20,20));checksum=write(out,png(picture),verify);frames.append({'source':rel(out),'source_sha256':checksum,'sha256':checksum,'source_canvas':[40,40],'angle_degrees':angle})
   recipe={**unit_common[key],'recipe_type':'vcmi_animation','output_path':contract['output_path'],'canvas':[40,40],'pivot':{'x':20,'y':20},'generateOverlay':0,'generateShadow':0,'physical_projectile':True,'trajectory_angles':contract['trajectory_angles'],'groups':[{'group':0,'frames':frames}],'generation':{'image_generation_used':True,'provider':'OpenAI built-in imagegen','model':'not exposed by built-in tool','prompt':'Fresh ordinary woodshaft/steelpoint/ivoryfletching arrow: exact prompt and actual native style-only tool input in pinned prompts.json/tool-receipts-v1.json. Uniform28px technical reduction then fixed five rotations only.','painted_master':arrow['source'],'painted_master_sha256':arrow['source_sha256'],'method':'New painted2D physical arrow; no old rendered/procedural arrow pixels'},'projectile_contract':arrow}
   rp=SOURCE/'candidates'/f'{key}-projectile.json';write(rp,recipe,verify);recipes[contract['output_path']]=rel(rp);results[rel(rp)]=sha(rp)
 write(SOURCE/'candidate-selection-v1.json',{'status':'authored configuration','scope':'Finite16candidate recipes only; coordinator controls selection/build/native acceptance. Whole6 gait has coordinator source direction GO; native motion and independent art review remain pending.','candidates':recipes,'recipe_sha256':results},verify)
 write(SOURCE/'frame-lineage-v1.json',{'status':'authored configuration','scope':'Actual fixed-crop painted-pose lineage, no artistic acceptance','records':records},verify)
 return {'candidate_recipes':len(recipes),'battle_frames':len(records),'recipe_sha256':results,'producer_sha256':sha(SELF)}
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--plan',type=Path);parser.add_argument('--verify',action='store_true');args=parser.parse_args();print(json.dumps(assemble(args.plan,args.verify),sort_keys=True))
