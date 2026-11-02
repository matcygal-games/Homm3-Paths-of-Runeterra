"""Versioned Elder-only painted conversion. Never mutate another actor or stage."""
from pathlib import Path
from copy import deepcopy
import hashlib,json
from PIL import Image,ImageOps
HERE=Path(__file__).resolve().parent;PROJECT=next(p for p in HERE.parents if p.name=='runeterra-ixtal');WORKSPACE=PROJECT.parent;REPORT=WORKSPACE/'build/reports/ixtal-implementation-20261026-v1/creature-art-t6-t7/elder-distinction-v4'
GROUPS={0:('movement',(4,5,6,7,8,9)),1:('holding',(0,1,1,2,2,0,0)),2:('holding',(0,)),3:('movement',(10,)),4:('movement',(11,)),5:('combat',(12,13,14,15)),7:('movement',(0,12,13)),8:('movement',(13,12,0)),11:('combat',(0,1,2,3)),12:('combat',(4,5,6,7)),13:('combat',(8,9,10,11)),22:('combat',(15,))}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(PROJECT).as_posix()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def bbox(im):return im.getchannel('A').point(lambda x:255 if x>=8 else 0).getbbox()
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
def render(row,annotation,root,canvas,multiplier=1.,mirror=False):
 assert row['selected'] and sha(PROJECT/row['image'])==row['sha256']and sha(PROJECT/row['source'])==row['source_sha256'],'Selected genuine source changed'
 actor=Image.open(PROJECT/row['image']).convert('RGBA');point=annotation['roots'][row['index']];scale=annotation['scale']*multiplier;local=[point[i]-row['crop'][i]for i in(0,1)];actor=actor.resize(tuple(max(1,round(n*scale))for n in actor.size),Image.Resampling.LANCZOS);offset=[root[i]-round(local[i]*scale)for i in(0,1)]
 if mirror:actor=ImageOps.mirror(actor);offset[0]=root[0]-(actor.width-1-round(local[0]*scale))
 b=bbox(actor);assert b and 0<=offset[0]+b[0]<offset[0]+b[2]<=canvas[0]and 0<=offset[1]+b[1]<offset[1]+b[3]<=canvas[1],('Whole native actor clips',row['image'],offset,b,canvas)
 out=Image.new('RGBA',canvas,(0,0,0,0));out.alpha_composite(actor,tuple(offset));return out,{'source':row['image'],'source_sha256':row['sha256'],'painted_sheet':row['source'],'painted_sheet_sha256':row['source_sha256'],'source_root':point,'cohort_scale':annotation['scale'],'role_scale_multiplier':multiplier,'native_root':root,'offset':offset,'mirror':mirror,'alpha_bbox_8':bbox(out)}
def main():
 roots_path=HERE/'pose-roots-v1.json';index_path=HERE/'isolated-source-map-v1.json';ledger_path=HERE/'generation-ledger-v1.json';roots=json.loads(roots_path.read_text());cohorts=roots['cohorts'];index=json.loads(index_path.read_text())['cohorts'];ledger=json.loads(ledger_path.read_text());native=HERE/'native';creature=json.loads((PROJECT/'content/creatures.json').read_text())['elderPairofant'];background=PROJECT/'assets/source/ui/recruit-painted-v1/master-v1.png'
 for c,rows in index.items():assert len(rows)==len(cohorts[c]['roots'])
 for row in ledger['generations']:
  assert sha(PROJECT/row['source'])==row['source_sha256']and sha(PROJECT/row['prompt'])==row['prompt_sha256']
  assert all(sha(PROJECT/ref['path'])==ref['sha256']for ref in row['input_references'])
 master=HERE/'holding-v2.png';dependencies=[roots_path,index_path,ledger_path,HERE/'extract-cohorts.py',Path(__file__),HERE.parents[1]/'extract_sources.py',background]+sorted(HERE.glob('*.png'))+sorted(HERE.glob('*.prompt.txt'))+sorted({PROJECT/ref['path']for row in ledger['generations']for ref in row['input_references']})
 common={'production_status':'painted-master-complete-unapproved','generation':{'image_generation_used':True,'provider':'OpenAI built-in imagegen','model':'not exposed by tool','prompt':(HERE/'holding-v2.prompt.txt').read_text().strip(),'painted_master':rel(master),'painted_master_sha256':sha(master),'action_source_ledger':rel(ledger_path),'action_source_ledger_sha256':sha(ledger_path),'method':roots['method']},'production_inputs':[{'path':rel(p),'sha256':sha(p)}for p in sorted(set(dependencies))]};recipes=[]
 def descriptor(p,f):return{'frame':f,'source':rel(p),'source_sha256':sha(p),'sha256':sha(p),'source_canvas':list(Image.open(p).size)}
 def recipe(role,v):
  p=native/'recipes'/(role+'.json');write(p,dict(deepcopy(common),**v));recipes.append(rel(p))
 groups=[];registration=[]
 for g,(c,order)in sorted(GROUPS.items()):
  sequence=[]
  for f,i in enumerate(order):
   actual_c,actual_i=('holding',0)if(g==7 and f==0)or(g==8 and f==2)else(c,i);im,r=render(index[actual_c][actual_i],cohorts[actual_c],roots['battle_root'],(450,400));p=native/'battle'/f'g{g:02d}-f{f:03d}.png';save(p,im);sequence.append(descriptor(p,f));r.update(group=g,frame=f,cohort=actual_c,source_index=actual_i,native_frame=rel(p),sha256=sha(p));registration.append(r)
  if g==3:
   im,r=render(index['holding'][0],cohorts['holding'],roots['battle_root'],(450,400));p=native/'battle/g03-f001.png';save(p,im);sequence.append(descriptor(p,1));r.update(group=3,frame=1,cohort='holding',source_index=0,native_frame=rel(p),sha256=sha(p));registration.append(r)
  groups.append({'group':g,'frames':sequence,'generateShadow':1,'generateOverlay':0})
 recipe('battle',{'recipe_type':'vcmi_animation','output_path':'Content/Sprites/'+creature['graphics']['animation'],'canvas':[450,400],'pivot':dict(zip(('x','y'),roots['battle_root'])),'groups':groups})
 mapframes=[]
 for f,i in enumerate((0,1,1,2,2,0,0)):
  im,r=render(index['holding'][i],cohorts['holding'],roots['map_root'],(96,64),roots['map_scale_multiplier'],True);assert bbox(im)[0]>=32,'Map visible mask footprint';p=native/'map'/f'g00-f{f:03d}.png';save(p,im);mapframes.append(descriptor(p,f))
 recipe('map',{'recipe_type':'vcmi_animation','output_path':'Content/Sprites/'+creature['graphics']['map'],'canvas':[96,64],'pivot':dict(zip(('x','y'),roots['map_root'])),'groups':[{'group':0,'frames':mapframes,'generateShadow':1,'generateOverlay':0}]})
 for role,key,mirror in(('attackLeft','mapAttackFromLeft',False),('attackRight','mapAttackFromRight',True)):
  im,r=render(index['combat'][6],cohorts['combat'],[32,60],(64,64),roots['encounter_scale_multiplier'],mirror);p=native/(role+'.png');save(p,im);recipe(role,{'recipe_type':'raster','output_path':'Content/Sprites/'+creature['graphics'][key],'canvas':[64,64],'source':rel(p),'source_sha256':sha(p),'source_canvas':[64,64],'fit':'exact'})
 pc=roots['portrait'];r=index[pc['cohort']][pc['index']];a=Image.open(PROJECT/r['image']).convert('RGBA');c=pc['crop'];head=a.crop(tuple(c[j]-r['crop'][j%2]for j in range(4)));bg=Image.open(background).convert('RGBA').crop((100,50,1045,995))
 for role,key,size in(('large','iconLarge',(58,64)),('small','iconSmall',(32,32))):
  im=ImageOps.fit(bg,size,Image.Resampling.LANCZOS);im.alpha_composite(ImageOps.fit(head,size,Image.Resampling.LANCZOS));p=native/(role+'.png');save(p,im);recipe(role,{'recipe_type':'raster','output_path':'Content/Sprites/'+creature['graphics'][key],'canvas':list(size),'source':rel(p),'source_sha256':sha(p),'source_canvas':list(size),'fit':'exact','portrait_source_crop':pc,'background':rel(background)})
 write(native/'registration-v1.json',{'status':'authored configuration','unit':'elderPairofant','frames':registration,'method':roots['method'],'battle_root':roots['battle_root'],'group3':'movement10 real hit recoil followed by compact hold','group4':'movement11 braced defend','excluded_source_pose':'holding3 clipped at provider edge; not selected','visual_approval_granted':False,'native_execution_performed':False})
 write(HERE/'candidate-recipes-v1.json',{'status':'authored configuration','unit':'elderPairofant','replaces_only':'previous six Elder Pairofant roles; do not select duplicate producers','recipes':recipes,'visual_approval_granted':False})
 holding=Image.open(native/'battle/g02-f000.png').convert('RGBA')
 for height in(120,130):
  ui=Image.open(PROJECT/f'assets/source/ui/recruit-painted-v1/native-{height}.png').convert('RGBA');ui.alpha_composite(holding.crop((170,155,270,155+height)));save(REPORT/f'elder-recruitment-{height}-v1.png',ui)
 print(json.dumps({'recipes':len(recipes),'battle_frames':len(registration),'holding_bbox_8':bbox(holding),'source_bytes_total':sum(p.stat().st_size for p in HERE.parents[1].rglob('*')if p.is_file())}))
if __name__=='__main__':main()
