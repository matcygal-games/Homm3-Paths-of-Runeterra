"""Create and execute own review recipes; never select or publish them."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys,shutil
from PIL import Image,ImageChops,ImageFilter,ImageDraw
S=Path(__file__).resolve().parent;P=S.parents[3];W=P.parent
R=P/'build/reports/complete-town-20261027-v2/derivation-v1'
sys.path.insert(0,str(W/'scripts'))
import faction_art_compile,faction_town_layout
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(P).as_posix()
def pin(p):return {'path':rel(p),'sha256':sha(p)}
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def bbox(im):return im.getchannel('A').point(lambda p:255 if p>=8 else 0).getbbox()

def recipes():
 reg=json.loads((S/'frame-registration-v1.json').read_text())['states'];plan=json.loads((S/'layout-acceptance-contract-v2.json').read_text())
 dependencies=[S/n for n in ['complete-town-master-v2-clean.png','complete-town-native-v2.png','prompt-v2.txt','silhouette-traces-v1.json','atlas-calibration-v1.json','functional-program-v2.json','assemble_complete_v2.py','build_geometry_v2.py','build_recipes_v2.py','frame-registration-v1.json']]
 for family in (S/'family-atlases').iterdir():
  if family.is_dir():
   suffix='v2' if family.name=='empty-terrain' else 'v1'
   dependencies.extend([family/('atlas-'+suffix+'.png'),family/('prompt-'+suffix+'.txt')])
 public_generation={'status':'authored configuration','provider':'OpenAI built-in image_gen','workflow':'Reviewed complete city first, exact visible master cuts, genuinely painted hidden faces and coherent predecessor families, matched painted absence terrain','master':pin(S/'complete-town-master-v2-clean.png'),'native_master':pin(S/'complete-town-native-v2.png'),'prompts':[pin(p)for p in dependencies if p.suffix=='.txt'],'native_verified':False,'release_accepted':False}
 dump(S/'source-generation-public-v2.json',public_generation);dependencies.append(S/'source-generation-public-v2.json')
 common={'status':'painted-candidate','production_status':'painted-master-complete-unapproved','visual_approval_granted':False,'credits':{'author':'Project-directed OpenAI built-in imagegen and deterministic 2D source conversion','license':None,'redistribution':'unresolved; release prohibited'},'generation':{'image_generation_used':True,'provider':'OpenAI builtin imagegen','model':'not exposed by tool','prompt':(S/'prompt-v2.txt').read_text(),'prompt_file':rel(S/'prompt-v2.txt'),'painted_master':rel(S/'complete-town-master-v2-clean.png'),'painted_master_sha256':sha(S/'complete-town-master-v2-clean.png'),'producer':rel(S/'assemble_complete_v2.py'),'producer_sha256':sha(S/'assemble_complete_v2.py'),'source_generation_ledger':rel(S/'source-generation-public-v2.json')},'dependencies':[pin(p)for p in sorted(set(dependencies))]}
 rows=[];icons={};entrances={n:v['entrance']for n,v in plan['silhouette_plan']['states'].items()}
 for state,r in reg.items():
  folder=S/'derived-ui'/state;folder.mkdir(parents=True,exist_ok=True)
  frame=S/'frames'/r['site']/(state+'.png');im=Image.open(frame).convert('RGBA');a=im.getchannel('A').point(lambda p:255 if p>=96 else 0)
  area=Image.new('RGBA',(800,374));area.paste((255,255,255,255),(0,0),a);area.save(folder/'area.png')
  edge=ImageChops.subtract(a.filter(ImageFilter.MaxFilter(3)),a);border=Image.new('RGBA',(800,374));border.paste((240,210,100,255),(0,0),edge);border.save(folder/'border.png')
  for name,size in [('campaign',(58,64)),('construction',(150,70))]:
   piece=im.crop(bbox(im));piece.thumbnail((size[0]-6,size[1]-6),Image.Resampling.LANCZOS);out=Image.new('RGBA',size);out.alpha_composite(piece,((size[0]-piece.width)//2,size[1]-piece.height-3));out.save(folder/(name+'.png'))
  prefix='Content/Sprites/runeterra/piltover/town/structures/'+state
  recipe={**common,'recipe_type':'vcmi_animation','canvas':[800,374],'pivot':dict(zip(('x','y'),entrances[state])),'generateShadow':0,'generateOverlay':0,'groups':[{'group':0,'frames':[{'source':rel(frame),'source_sha256':sha(frame),'source_canvas':[800,374]}]}],'output_path':prefix+'.json'}
  rp=S/'recipes-v2'/(state+'-animation.json');dump(rp,recipe);rows.append(rp)
  for role,size in [('area',(800,374)),('border',(800,374)),('campaign',(58,64))]:
   source=folder/(role+'.png');recipe={**common,'recipe_type':'raster','canvas':list(size),'size':list(size),'source_canvas':list(size),'source':rel(source),'source_sha256':sha(source),'fit':'exact','require_alpha':True,'output_path':prefix+'_'+role+'.png'}
   rp=S/'recipes-v2'/(state+'-'+role+'.json');dump(rp,recipe);rows.append(rp)
  icons[state]=folder/'construction.png'
 compiler=faction_art_compile.create_compiler('piltover');ids=compiler.indexed_building_ids(P)
 recipe={**common,'dependencies':common['dependencies']+[pin(p)for p in icons.values()],'recipe_type':'indexed_animation','canvas':[150,70],'pivot':{'x':75,'y':35},'generateShadow':0,'generateOverlay':0,'frames':[{'building':state,'frame':idx,'source':rel(icons[state]),'source_sha256':sha(icons[state]),'source_canvas':[150,70]}for state,idx in sorted(ids.items(),key=lambda pair:pair[1])],'output_path':'Content/Sprites/runeterra/piltover/town/buildingIcons.json'}
 rp=S/'recipes-v2/buildingIcons.json';dump(rp,recipe);rows.append(rp)
 bg=S/'background-native-v1.png';recipe={**common,'recipe_type':'raster','canvas':[800,374],'size':[800,374],'source_canvas':[800,374],'source':rel(bg),'source_sha256':sha(bg),'fit':'exact','require_alpha':False,'output_path':'Content/Sprites/runeterra/piltover/town/background.png'}
 rp=S/'recipes-v2/background.json';dump(rp,recipe);rows.append(rp)
 assert len(rows)==142
 targets={json.loads(p.read_text()).get('output_path'):p for p in (P/'assets/recipes/town').rglob('*.json')}
 mappings=[];outputs={};receipts=[]
 for rp in rows:
  recipe=json.loads(rp.read_text());out,receipt=compiler.plan(P,rp);again,_=compiler.plan(P,rp)
  assert out==again,'Non-deterministic converter '+rp.name
  for name,data in out.items():
   assert name not in outputs,'Duplicate output '+name
   outputs[name]=data
   dest=R/'candidate-generated'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
  receipts.append(receipt);mappings.append({'candidate':rel(rp),'sha256':sha(rp),'target':rel(targets[recipe['output_path']]),'output':recipe['output_path']})
 dump(R/'converter-receipts-v2.json',{'status':'authored configuration','recipes':len(rows),'outputs':len(outputs),'deterministic_repeat':True,'receipts':receipts,'output_sha256':{n:hashlib.sha256(b).hexdigest()for n,b in sorted(outputs.items())}})
 integration={'status':'authored configuration','selected':False,'canonical_town_visuals_candidate':pin(S/'town-visuals.candidate-v2.json'),'canonical_structures_candidate':pin(S/'town-structures.candidate-v2.json'),'contract':pin(S/'layout-acceptance-contract-v2.json'),'native_structure_count':35,'full_canvas_origin':[0,0],'recipe_map':mappings,'native_verified':False,'release_accepted':False}
 dump(S/'integration-candidate-v2.json',integration)
 return plan,outputs

def inspect_candidate(plan,outputs):
 fixture=R/'technical-consumer/runeterra-piltover';fixture.mkdir(parents=True,exist_ok=True)
 refs=[]
 def find(v):
  if isinstance(v,dict):
   if set(v)>={'path','sha256'}:refs.append(v)
   for x in v.values():find(x)
  elif isinstance(v,list):
   for x in v:find(x)
 find(plan)
 for r in refs:
  source=P/r['path'];dest=fixture/r['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
 for name in ['layout-acceptance-contract-v2.json']:
  source=S/name;dest=fixture/rel(source);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
 dest=fixture/'design/town-visuals.json';dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(S/'town-visuals.candidate-v2.json',dest)
 for name,data in outputs.items():
  dest=fixture/'assets/generated'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
 content=json.loads((S/'native-content-geometry.candidate-v2.json').read_text())
 errors,deps=faction_town_layout.inspect(fixture,content,'piltover')
 dump(R/'actual-consumer-v2.json',{'status':'authored configuration','consumer':'scripts/faction_town_layout.py inspect','consumer_sha256':sha(W/'scripts/faction_town_layout.py'),'errors':errors,'dependencies':len(deps),'native_executed':False,'release_accepted':False})
 print(json.dumps({'recipes':142,'outputs':len(outputs),'actual_consumer_errors':errors,'dependencies':len(deps)}))
 if errors:raise SystemExit(2)

if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--report-name',default='derivation-v1');args=parser.parse_args()
 if Path(args.report_name).name!=args.report_name:parser.error('report name must be one directory name')
 R=P/'build/reports/complete-town-20261027-v2'/args.report_name
 R.mkdir(parents=True,exist_ok=True)
 inspect_candidate(*recipes())
