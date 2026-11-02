"""Assemble fixed-root native sprites from genuine painted whole-machine poses."""
from pathlib import Path
from copy import deepcopy
import argparse,hashlib,json
from PIL import Image,ImageOps
from shadow_mask_v1 import projected_shadow,embedded_shadow
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if p.name=='runeterra-piltover')
UNITS=('hextechRotorwing','hextechStormwing')
FIDGET=(0,1,1,2,2,3,3)
GROUPS={0:('movement',(3,4,5,6,7,8)),1:('movement',FIDGET),2:('movement',(0,)),3:('movement',(9,0)),4:('movement',(10,)),5:('combat',(12,13,14,15)),7:('movement',(0,11,12)),8:('movement',(12,11,0)),11:('combat',(0,1,2,3)),12:('combat',(4,5,6,7)),13:('combat',(8,9,10,11)),20:('flight',(0,1,2,3)),21:('flight',(4,5,6,7)),22:('combat',(15,))}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(PROJECT).as_posix()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save_json(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
def render(row,config,kind,group,canvas,pivot,multiplier=1.,mirror=False,encounter=False):
 p=PROJECT/row['image']
 if sha(p)!=row['sha256'] or sha(PROJECT/row['source'])!=row['source_sha256']:raise ValueError('Changed painted source '+row['image'])
 annotation=config[kind];scale=annotation['scale'];idx=row['index'];cx,cy=annotation['core_landmarks'][idx]
 px=cx+(0 if kind=='movement' and idx==12 else 20 if kind=='movement' and idx==11 else 40)
 if kind=='flight':py=annotation['projected_floors'][idx]
 elif kind=='combat' and idx>=12:py=annotation['death_projected_floor']
 else:py=cy+(config['movement_core_height'] if group==0 and kind=='movement' else config['holding_core_height'])/scale
 # Encounter uses the central cage landmark. With native CG~42 it agrees with
 # map CG~74 after the consumer's 32px canvas-width difference.
 if tuple(canvas)==(96,64) and mirror:px=cx-60
 if encounter:px=cx
 point=[px,py];density=scale*multiplier
 im=Image.open(p).convert('RGBA');im=im.resize((max(1,round(im.width*density)),max(1,round(im.height*density))),Image.Resampling.LANCZOS)
 local=[(point[j]-row['crop'][j])*density for j in (0,1)]
 off=[pivot[0]-round(local[0]),pivot[1]-round(local[1])]
 if mirror:im=ImageOps.mirror(im);off[0]=pivot[0]-(im.width-1-round(local[0]))
 bounds=im.getchannel('A').point(lambda a:255 if a>=8 else 0).getbbox()
 if bounds is None or not (0<=off[0]+bounds[0]<off[0]+bounds[2]<=canvas[0] and 0<=off[1]+bounds[1]<off[1]+bounds[3]<=canvas[1]):raise ValueError('Actor clips native canvas '+row['image']+' '+str((canvas,off,bounds)))
 out=Image.new('RGBA',tuple(canvas));out.alpha_composite(im,tuple(off))
 return out,{'source':row['image'],'source_sha256':row['sha256'],'raw_source':row['source'],'raw_source_sha256':row['source_sha256'],'source_landmark_core':[cx,cy],'source_projected_root':point,'cohort_scale':scale,'role_multiplier':multiplier,'native_root':list(pivot),'offset':off,'mirror':mirror,'alpha_treatment':row.get('alpha_treatment')}
def build(unit,plan,ledger):
 if unit not in UNITS:raise ValueError('Unknown owned creature identity before any I/O')
 config=plan['units'][unit];index_path=HERE/unit/'isolated-source-map-v1.json';cohorts=read(index_path)['cohorts']
 for kind,count in [('movement',16),('combat',16),('flight',8)]:
  if len(cohorts[kind])!=count or len(config[kind]['core_landmarks'])!=count:raise ValueError('Incomplete genuine cohort '+kind)
 native=HERE/'native'/unit;native.mkdir(parents=True,exist_ok=True)
 master=HERE/unit/config['master'];portrait=HERE/unit/'portrait-v1.png'
 generation=next(e['generation'] for e in ledger['entries'] if e['source']==rel(master))
 dependencies=[master,portrait,index_path,HERE/'pose-roots-v1.json',HERE/'generation-ledger-v1.json',HERE/'selected-cohorts-v1.json',HERE/'extract_sources.py',HERE/'shadow_mask_v1.py',Path(__file__)]
 dependencies+=sorted({PROJECT/r['source'] for rows in cohorts.values() for r in rows})
 common={'production_status':'painted-master-complete-unapproved','generation':dict(deepcopy(generation),painted_master=rel(master),painted_master_sha256=sha(master),action_ledger=rel(HERE/'generation-ledger-v1.json')),'production_inputs':[{'path':rel(p),'sha256':sha(p)} for p in dependencies]}
 recipes=[];registrations=[]
 def image_file(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
 def descriptor(p,i,canvas):return {'frame':i,'source':rel(p),'sha256':sha(p),'source_sha256':sha(p),'source_canvas':list(canvas)}
 def shadow_descriptor(p,im,pivot):
  shadow=p.with_name(p.stem+'-SHADOW.png');image_file(shadow,projected_shadow(im,pivot[1]))
  return {'shadow_source':rel(shadow),'shadow_sha256':sha(shadow),'shadow_source_canvas':list(im.size),'shadow_pivot':{'x':pivot[0],'y':pivot[1]}}
 def recipe(role,data):p=native/(role+'.recipe.json');save_json(p,dict(deepcopy(common),**data));recipes.append(rel(p))
 sequences=[]
 for group,(kind,order) in sorted(GROUPS.items()):
  frames=[]
  for i,idx in enumerate(order):
   im,receipt=render(cohorts[kind][idx],config,kind,group,(450,400),(220,266))
   p=native/'battle'/f'g{group:02d}-f{i:03d}.png';image_file(p,im);frames.append(dict(descriptor(p,i,(450,400)),**shadow_descriptor(p,im,(220,266))))
   registrations.append(dict(receipt,group=group,frame=i,native_frame=rel(p),sha256=sha(p),shadow_source=frames[-1]['shadow_source'],shadow_sha256=frames[-1]['shadow_sha256'],shadow_pivot=frames[-1]['shadow_pivot']))
  sequences.append({'group':group,'frames':frames,'generateShadow':0,'generateOverlay':0})
 recipe('battle',{'recipe_type':'vcmi_animation','output_path':f'Content/Sprites/runeterra/piltover/creatures/{unit}/battle.json','canvas':[450,400],'pivot':{'x':220,'y':266},'groups':sequences})
 frames=[]
 for i,idx in enumerate(FIDGET):
  im,receipt=render(cohorts['movement'][idx],config,'movement',2,(96,64),(80,60),config['map_scale_multiplier'],mirror=True)
  bbox=im.getchannel('A').point(lambda a:255 if a>=8 else 0).getbbox()
  if bbox[0]<32:raise ValueError('Map alpha exceeds two-column visible mask')
  p=native/'map'/f'g00-f{i:03d}.png';image_file(p,im);frames.append(dict(descriptor(p,i,(96,64)),**shadow_descriptor(p,im,(80,60))))
 recipe('map',{'recipe_type':'vcmi_animation','output_path':f'Content/Sprites/runeterra/piltover/creatures/{unit}/map.json','canvas':[96,64],'pivot':{'x':80,'y':60},'groups':[{'group':0,'frames':frames,'generateShadow':0,'generateOverlay':0}]})
 role_receipts={}
 for name,mirrored in [('attackLeft',False),('attackRight',True)]:
  im,receipt=render(cohorts['combat'][6],config,'combat',12,(64,64),(42,60),config['encounter_scale_multiplier'],mirror=mirrored,encounter=True)
  p=native/(name+'.png');image_file(p,embedded_shadow(im,60));role_receipts[name]=dict(receipt,shadow='Own actor-alpha projection fills only empty background pixels; every nonzero-alpha actor pixel preserved byte-exact')
  recipe(name,{'recipe_type':'raster','output_path':f'Content/Sprites/runeterra/piltover/creatures/{unit}/{name}.png','canvas':[64,64],'source':rel(p),'source_sha256':sha(p),'source_canvas':[64,64],'fit':'exact'})
 for name,canvas in [('large',(58,64)),('small',(32,32))]:
  im=ImageOps.fit(Image.open(portrait).convert('RGBA'),canvas,Image.Resampling.LANCZOS);p=native/(name+'.png');image_file(p,im)
  recipe(name,{'recipe_type':'raster','output_path':f'Content/Sprites/runeterra/piltover/creatures/{unit}/{name}.png','canvas':list(canvas),'source':rel(p),'source_sha256':sha(p),'source_canvas':list(canvas),'fit':'exact'})
 save_json(native/'registration.json',{'status':'authored configuration','unit':unit,'frames':registrations,'recipes':recipes,'encounter_roles':role_receipts,'method':plan['method'],'native_root':[220,266],'holding':'one fixed-body image; native10FPS holding repeats identical image','fidget':'Four genuine phases held1/2/2/2 in group1; .1 is randomchance perholdingloop, notseconds','flight':'g20/g21 real painted cohorts; static holding, rising/settling projected floor and rotating blades; no shooting groups','shadow':'Explicit grayscale/alpha sidecar from exact own painted silhouette, projected at fixed battle266/map60; automatic shadow disabled. Native rendering remains unobserved.','visual_approval_granted':False})
 return {'unit':unit,'recipes':recipes,'battle_frames':len(registrations)}
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--unit',choices=UNITS,nargs='+',required=True);args=parser.parse_args()
 plan=read(HERE/'pose-roots-v1.json');ledger=read(HERE/'generation-ledger-v1.json')
 print(json.dumps({'status':'authored configuration','units':[build(u,plan,ledger) for u in args.unit],'visual_approval_granted':False}))
if __name__=='__main__':main()
