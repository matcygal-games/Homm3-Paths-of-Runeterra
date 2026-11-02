"""Register complete painted actors; create candidate recipes, never stage assets."""
import hashlib,json,sys
from pathlib import Path
from copy import deepcopy
from PIL import Image,ImageOps,ImageDraw
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if p.name=='runeterra-ixtal')
WORKSPACE=PROJECT.parent
REPORT=WORKSPACE/'build/reports/ixtal-implementation-20261026-v1/creature-art-t6-t7'
UNITS=('auroraHallunatis','crownedHallunatis','pairofant','elderPairofant')
FIDGET=(0,1,1,2,2,3,3)
GROUPS={0:('movement',(4,5,6,7,8,9)),1:('movement',FIDGET),2:('movement',(0,)),3:('movement',(10,0)),4:('movement',(11,)),5:('combat',(12,13,14,15)),7:('movement',(0,12,13)),8:('movement',(13,12,0)),11:('combat',(0,1,2,3)),12:('combat',(4,5,6,7)),13:('combat',(8,9,10,11)),22:('combat',(15,))}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def relative(p):return p.relative_to(PROJECT).as_posix()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
def bbox(im):return im.getchannel('A').point(lambda x:255 if x>=8 else 0).getbbox()
def render(row,annotation,root,canvas,multiplier=1.,mirror=False):
 source=PROJECT/row['image']
 assert sha(source)==row['sha256'] and sha(PROJECT/row['source'])==row['source_sha256'],'Changed painted source'
 actor=Image.open(source).convert('RGBA');point=annotation['roots'][row['index']];scale=annotation['scale']*multiplier
 local=[point[i]-row['crop'][i]for i in(0,1)]
 actor=actor.resize(tuple(max(1,round(n*scale))for n in actor.size),Image.Resampling.LANCZOS)
 offset=[root[i]-round(local[i]*scale)for i in(0,1)]
 if mirror:actor=ImageOps.mirror(actor);offset[0]=root[0]-(actor.width-1-round(local[0]*scale))
 b=bbox(actor)
 assert b and 0<=offset[0]+b[0]<offset[0]+b[2]<=canvas[0] and 0<=offset[1]+b[1]<offset[1]+b[3]<=canvas[1],('Whole actor clipping',row['image'],offset,b,canvas)
 final=Image.new('RGBA',canvas,(0,0,0,0));final.alpha_composite(actor,tuple(offset))
 return final,{'source':row['image'],'source_sha256':row['sha256'],'source_root':point,'cohort_scale':annotation['scale'],'role_scale_multiplier':multiplier,'native_root':list(root),'offset':offset,'mirror':mirror,'alpha_bbox_8':bbox(final)}
def public_ledger():
 rows=[];seen=set()
 for name in('generation-ledger-v3.json','generation-ledger-v5.json','generation-ledger-v6.json','generation-ledger-v7.json'):
  for raw in json.loads((REPORT/name).read_text())['generations']:
   r=deepcopy(raw)
   for key in('source','prompt'):
    if isinstance(r.get(key),str)and r[key].startswith('runeterra-ixtal/'):r[key]=r[key][len('runeterra-ixtal/'):]
   r['source_sha256']=sha(PROJECT/r['source'])
   if r['source']in seen:continue
   seen.add(r['source']);rows.append(r)
 p=HERE/'generation-ledger-v1.json';write(p,{'status':'authored configuration','provider':'OpenAI built-in imagegen','model':'not exposed by tool','visual_approval_granted':False,'generations':rows});return p
def main():
 ledger=public_ledger();roots_path=HERE/'pose-roots-v1.json';roots=json.loads(roots_path.read_text());recipes=[];units=[]
 background=PROJECT/'assets/source/ui/recruit-painted-v1/master-v1.png';bg=Image.open(background).convert('RGBA')
 for unit in UNITS:
  folder=HERE/unit;index_path=folder/'isolated-source-map-v1.json';index=json.loads(index_path.read_text())['cohorts'];config=roots['units'][unit]
  for cohort,rows in index.items():
   assert len(config[cohort]['roots'])==len(rows),(unit,cohort)
   config[cohort].update(source=rows[0]['source'],source_sha256=rows[0]['source_sha256'])
  native=HERE/'native'/unit;master=folder/('holding-v3.png' if unit=='elderPairofant' else 'holding-v2.png');prompt=master.with_suffix('.prompt.txt').read_text().strip()
  deps=[ledger,roots_path,index_path,HERE/'generation-reference-map-v1.json',HERE/'extract_sources.py',Path(__file__),background]+sorted({PROJECT/r['source']for rows in index.values()for r in rows})+sorted(folder.glob('*.prompt.txt'))
  common={'production_status':'painted-master-complete-unapproved','generation':{'image_generation_used':True,'provider':'OpenAI built-in imagegen','model':'not exposed by tool','prompt':prompt,'painted_master':relative(master),'painted_master_sha256':sha(master),'action_source_ledger':relative(ledger),'action_source_ledger_sha256':sha(ledger),'method':'Whole painted source actors, uniformly resampled per coherent cohort and registered with manual anatomical roots. No limb warp, rig, render, code-drawn actor, per-frame zoom or approval implied.'},'production_inputs':[{'path':relative(p),'sha256':sha(p)}for p in deps]}
  def desc(p,f,size):return {'frame':f,'source':relative(p),'sha256':sha(p),'source_sha256':sha(p),'source_canvas':list(size)}
  def recipe(role,data):
   p=native/(role+'.recipe.json');write(p,dict(deepcopy(common),**data));recipes.append(relative(p))
  groups=dict(GROUPS);groups[1]=('holding',FIDGET);groups[2]=('holding',(0,))
  if unit=='elderPairofant':groups[1]=('holding',(0,1,1,2,2,0,0))
  if unit=='pairofant':groups[5]=('death',(0,1,2,3));groups[22]=('death',(3,))
  if unit.endswith('Hallunatis'):groups[20]=('flight',(0,1,2,3));groups[21]=('flight',(4,5,6,7))
  frames=[];registration=[]
  for group,(cohort,order)in sorted(groups.items()):
   sequence=[]
   for f,i in enumerate(order):
    actual_cohort,actual_index=('holding',0)if(group==3 and f==1)or(group==7 and f==0)or(group==8 and f==2)else(cohort,i)
    im,rec=render(index[actual_cohort][actual_index],config[actual_cohort],tuple(roots['battle_root']),(450,400));p=native/'battle'/f'g{group:02d}-f{f:03d}.png';save(p,im);sequence.append(desc(p,f,im.size));rec.update(group=group,frame=f,cohort=actual_cohort,source_index=actual_index,native_frame=relative(p),sha256=sha(p));registration.append(rec)
   frames.append({'group':group,'frames':sequence,'generateShadow':1,'generateOverlay':0})
  recipe('battle',{'recipe_type':'vcmi_animation','output_path':f'Content/Sprites/runeterra/ixtal/creatures/{unit}/battle.json','canvas':[450,400],'pivot':dict(zip(('x','y'),roots['battle_root'])),'groups':frames})
  mapframes=[]
  for f,i in enumerate(FIDGET):
   if unit=='elderPairofant'and i==3:i=0
   im,rec=render(index['holding'][i],config['holding'],tuple(roots['map_root']),(96,64),config['map_scale_multiplier'],True)
   assert bbox(im)[0]>=32,('Outside mapMask VA footprint',unit,bbox(im))
   p=native/'map'/f'g00-f{f:03d}.png';save(p,im);mapframes.append(desc(p,f,im.size))
  recipe('map',{'recipe_type':'vcmi_animation','output_path':f'Content/Sprites/runeterra/ixtal/creatures/{unit}/map.json','canvas':[96,64],'pivot':dict(zip(('x','y'),roots['map_root'])),'groups':[{'group':0,'frames':mapframes,'generateShadow':1,'generateOverlay':0}]})
  for role,mirrored in(('attackLeft',False),('attackRight',True)):
   im,rec=render(index['combat'][6],config['combat'],(32,60),(64,64),config['encounter_scale_multiplier'],mirrored);p=native/(role+'.png');save(p,im)
   recipe(role,{'recipe_type':'raster','output_path':f'Content/Sprites/runeterra/ixtal/creatures/{unit}/{role}.png','canvas':[64,64],'source':relative(p),'source_sha256':sha(p),'source_canvas':[64,64],'fit':'exact'})
  pc=config['portrait'];r=index[pc['source']][pc['index']];actor=Image.open(PROJECT/r['image']).convert('RGBA');c=pc['crop'];local=(c[0]-r['crop'][0],c[1]-r['crop'][1],c[2]-r['crop'][0],c[3]-r['crop'][1]);head=actor.crop(local)
  for role,size in(('large',(58,64)),('small',(32,32))):
   im=ImageOps.fit(bg.crop((100,50,1045,995)),size,Image.Resampling.LANCZOS);headim=ImageOps.fit(head,size,Image.Resampling.LANCZOS);im.alpha_composite(headim);p=native/(role+'.png');save(p,im)
   recipe(role,{'recipe_type':'raster','output_path':f'Content/Sprites/runeterra/ixtal/creatures/{unit}/{role}.png','canvas':list(size),'source':relative(p),'source_sha256':sha(p),'source_canvas':list(size),'fit':'exact','portrait_crop':{'painted_source':r['source'],'full_source_crop':c,'background':relative(background),'background_crop':[100,50,1045,995]}})
  holding=Image.open(native/'battle/g02-f000.png').convert('RGBA');save(REPORT/(unit+'-holding-native-v2.png'),holding)
  for height in(120,130):
   back=Image.open(PROJECT/f'assets/source/ui/recruit-painted-v1/native-{height}.png').convert('RGBA');back.alpha_composite(holding.crop((170,155,270,155+height)));save(REPORT/(unit+f'-recruitment-{height}-v1.png'),back)
  write(native/'registration-v1.json',{'status':'authored configuration','unit':unit,'method':roots['method'],'battle_root':roots['battle_root'],'frames':registration,'portrait_source_crop':pc,'visual_approval_granted':False,'native_motion_observed':False,'recruitment_crop_known_risk':'Horizontal two-hex silhouettes may be cut by the native100px UI viewport; full canvases and exact viewport composites are supplied for review.'})
  units.append({'unit':unit,'battle_frames':len(registration),'battle_groups':sorted(groups),'holding_alpha_bbox_8':bbox(holding),'whole_actor_canvas_clip_count':0,'body_root':roots['battle_root'],'uniform_cohort_scales':{k:v['scale']for k,v in config.items()if isinstance(v,dict)and 'scale'in v},'native_motion_observed':False})
 write(HERE/'candidate-recipes-v1.json',{'status':'authored configuration','recipes':recipes,'visual_approval_granted':False})
 write(REPORT/'native-candidate-v1.json',{'status':'authored configuration','units':units,'recipes':recipes,'source_bytes':sum(p.stat().st_size for p in HERE.rglob('*')if p.is_file()),'budget_bytes':150*1024*1024,'visual_approval_granted':False,'native_motion_observed':False})
 print(json.dumps({'units':units,'recipes':len(recipes),'source_bytes':sum(p.stat().st_size for p in HERE.rglob('*')if p.is_file())},indent=2))
if __name__=='__main__':main()
