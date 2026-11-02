"""Report-only candidate using actual existing town-art transforms and compiler.

No dispatcher, default recipe, manifest, staging or native execution writes.
"""
from pathlib import Path
from PIL import Image,ImageDraw
import importlib.util,hashlib,json,sys
sys.dont_write_bytecode=True
SOURCE=Path(__file__).resolve().parent;ROOT=SOURCE.parents[3]
REPORT=ROOT/'build/reports/painted-town-community-20261024-v1'
spec=importlib.util.spec_from_file_location('freljord_existing_town_art',ROOT/'scripts/prepare_town_art.py');art=importlib.util.module_from_spec(spec);spec.loader.exec_module(art)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()
def put(p,data):
 if p.exists():
  if p.read_bytes()!=data:raise ValueError('Preserve existing candidate bytes: '+rel(p))
 else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
def jput(p,v):put(p,art.encoded(v))
def prepare():
 layout_path=ROOT/'design/building-layout-community-v2.json';layout=art.read(layout_path)
 before=art.read(REPORT/'before-pins-v1.json');selected={r['state']:r['master'] for r in before['selected_states']}
 for state in ('dwellingLvl1','dwellingUpLvl1','dwellingLvl4','dwellingUpLvl4','dwellingLvl5','dwellingUpLvl5','special3'):selected[state]=f'assets/source/town/buildings-v4/{state}/master.png'
 for state in ('dwellingLvl7','dwellingUpLvl7'):selected[state]=f'assets/source/town/buildings-v5/{state}/master.png'
 names=art.read(ROOT/'content/factions.json')['freljord']['town']['buildings'];assert set(names)==set(selected) and len(names)==36
 for state in ('capitol','castle','mageGuild4'):selected[state]=f'assets/source/town/buildings-v5/{state}/master.png'
 dest=SOURCE/'prepared-v2';recipes=REPORT/'recipe-payload-v2';assert not dest.exists() and not recipes.exists()
 common={'status':'authored configuration','production_status':'painted-master-complete-unapproved','visual_approval_granted':False,'require_alpha':True,'canvas':[800,374],'credits':{'author':'Project-directed OpenAI built-in imagegen; deterministic technical assembly','license':None,'redistribution':'unresolved; release prohibited'},'acceptance':'Unselected painted community candidate; native visual/click and rights approval pending.','inputs':[{'path':rel(p),'sha256':sha(p)} for p in (layout_path,ROOT/'scripts/prepare_town_art.py',Path(__file__).resolve())]}
 allrecipes={};receipts=[];layers={}
 for state in names:
  site=next(s for s in layout['sites'] if state in s['states']);rect=site.get('state_rects',{}).get(state,site['rect'])
  if state=='grail':x,y,w,h=site['rect'];rect=[x+w-32,y+8,28,52]
  master=ROOT/selected[state];record=art.read(master.parent/'generation.json');image=art.load_rgba(master)
  native,conversion=art.place(image,rect);area,border=art.masks(native);folder=dest/'structures'/state
  data={'layer':art.png(native),'area':art.png(area),'border':art.png(border),'icon':art.png(art.icon(image))}
  paths={role:folder/(role+'.png') for role in data}
  for role,value in data.items():put(paths[role],value)
  gen=art.generation(ROOT,master.parent,master,record,conversion)
  gen['technical_producer']={'path':rel(Path(__file__).resolve()),'sha256':sha(Path(__file__).resolve()),'reused_existing_helper':{'path':'scripts/prepare_town_art.py','sha256':sha(ROOT/'scripts/prepare_town_art.py')}}
  descriptor={'source':rel(paths['layer']),'source_sha256':sha(paths['layer']),'sha256':sha(paths['layer']),'source_canvas':[800,374]}
  recipe={**common,'generation':gen,'recipe_type':'vcmi_animation','canvas':[800,374],'pivot':{'x':0,'y':0},'output_path':art.PREFIX+f'town/structures/{state}.json','groups':[{'group':0,'generateShadow':0,'generateOverlay':0,'frames':[descriptor]}]}
  allrecipes[recipes/'structures'/(state+'-animation.json')]=recipe
  for role in ('area','border'):
   allrecipes[recipes/'structures'/(state+'-'+role+'.json')]={**common,'recipe_type':'raster','fit':'exact','source':rel(paths[role]),'source_sha256':sha(paths[role]),'source_canvas':[800,374],'output_path':art.PREFIX+f'town/structures/{state}_{role}.png','generation':{'image_generation_used':False,'method':'Existing alpha128 silhouette/one-pixel outeredge; no painted pixel erasure','painted_source_provenance':gen,'references':[{'path':rel(paths['layer']),'sha256':sha(paths['layer'])}]}}
  receipt={'state':state,'site':site['id'],'master':selected[state],'master_sha256':sha(master),'native_layer':rel(paths['layer']),'native_layer_sha256':sha(paths['layer']),'prepared_icon':rel(paths['icon']),'icon_sha256':sha(paths['icon']),'native_alpha128_bbox':area.getchannel('A').getbbox(),'conversion':conversion,'z':site['z']}
  receipts.append(receipt);layers[state]=native;jput(folder/'preparation.json',receipt)
 allrecipes[recipes/'buildingIcons.json']=art.icon_recipe(ROOT,receipts)
 terrain=SOURCE/'terrain-v2/master.png';im=Image.open(terrain).convert('RGBA');factor=min(im.width/800,im.height/374);origin=((im.width-800*factor)/2,(im.height-374*factor)/2)
 background=im.transform((800,374),Image.Transform.AFFINE,(factor,0,origin[0],0,factor,origin[1]),Image.Resampling.BICUBIC);nativepath=SOURCE/'terrain-v2/native-v2.png';put(nativepath,art.png(background))
 gen=art.read(SOURCE/'terrain-v2/generation.json');gen.update(painted_master=rel(terrain),painted_master_sha256=sha(terrain),generation_record=rel(SOURCE/'terrain-v2/generation.json'),method='Uniform full-canvas affine cover with integer native output; source original preserved',uniform_inverse_factor=factor,source_crop_origin=origin,technical_producer={'path':rel(Path(__file__).resolve()),'sha256':sha(Path(__file__).resolve())})
 allrecipes[recipes/'background.json']={**common,'require_alpha':False,'recipe_type':'raster','fit':'exact','source':rel(nativepath),'source_sha256':sha(nativepath),'source_canvas':[800,374],'output_path':art.PREFIX+'town/background.png','generation':gen}
 for path,value in allrecipes.items():jput(path,value)
 jput(dest/'preparation.json',{'status':'authored configuration','layout_sha256':sha(layout_path),'states':receipts,'background':rel(nativepath),'background_sha256':sha(nativepath),'recipes':{rel(p):sha(p) for p in allrecipes},'native_execution':False,'visual_approval_granted':False})
 previews={}
 for label,upgraded,coast in (('empty',None,False),('early',False,False),('base-land',False,False),('upgraded-land',True,False),('base-coast',False,True),('upgraded-coast',True,True)):
  canvas=background.copy();chosen=[]
  if label!='empty':
   for site in layout['sites']:
    if not coast and not site['land']:continue
    opts=[s for s in site['states'] if s!='grail'];state=opts[-1] if upgraded else opts[0]
    if label=='early' and state not in ('villageHall','tavern','dwellingLvl1'):continue
    chosen.append((site['z'],state))
   for z,state in sorted(chosen):canvas.alpha_composite(layers[state])
  path=REPORT/(label+'-native800x374-v2.png');put(path,art.png(canvas));previews[label]={'path':rel(path),'sha256':sha(path),'states':[s for _,s in sorted(chosen)]}
 jput(REPORT/'candidate-assembly-v2.json',{'status':'authored configuration','prepared_states':len(receipts),'recipes':len(allrecipes),'new_painted_functional_states':12,'preserved_existing_painted_masters':24,'layout':rel(layout_path),'layout_sha256':sha(layout_path),'native_execution':False,'visual_approval_granted':False,'previews':previews})
 sys.path.insert(0,str(ROOT.parent/'scripts'));import faction_art_compile
 compiler=faction_art_compile.create_compiler('freljord');runs=[];proofs=[]
 for n in (1,2):
  pins={}
  for path in sorted(allrecipes):
   outputs,proof=compiler.plan(ROOT,path)
   if n==1:proofs.append(proof)
   for name,data in outputs.items():
    if name in pins:raise ValueError('Duplicate candidate output: '+name)
    put(REPORT/('compiler-v2-run'+str(n))/name,data);pins[name]=hashlib.sha256(data).hexdigest()
  runs.append(pins)
 assert runs[0]==runs[1]
 jput(REPORT/'compiler-receipts-v2.json',proofs)
 jput(REPORT/'shared-compiler-double-proof-v2.json',{'status':'authored configuration','actual_plan_calls':len(allrecipes)*2,'recipes_per_run':len(allrecipes),'physical_outputs_per_run':len(runs[0]),'byte_exact_two_actual_runs':True,'output_hashes':runs[0],'selected_for_build':False,'native_execution':False,'visual_approval_granted':False})
 print(json.dumps({'prepared_states':len(receipts),'recipes':len(allrecipes),'outputs_per_run':len(runs[0]),'byte_exact_actual_shared_plans':True,'default_recipe_writes':0,'native_execution':False}))
if __name__=='__main__':prepare()
