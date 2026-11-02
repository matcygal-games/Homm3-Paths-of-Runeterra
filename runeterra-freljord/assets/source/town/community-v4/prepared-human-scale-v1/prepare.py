"""Three-state report-only rear human-scale correction using immutable masters."""
from pathlib import Path
from copy import deepcopy
from PIL import Image,ImageDraw
import hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
SOURCE=Path(__file__).resolve().parent;ROOT=SOURCE.parents[4];REPORT=ROOT/'build/reports/painted-town-human-scale-20261024-v1'
RECTS={'villageHall':[292,118,70,50],'townHall':[290,114,74,54],'mageGuild1':[463,141,69,64]}
DOORS={'villageHall':[296,105,314,139],'townHall':[296,106,313,137],'mageGuild1':[478,158,489,182]}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(data):return hashlib.sha256(data).hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def put(p,data):
 if p.exists():raise ValueError('Preserve prior successor bytes: '+rel(p))
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
def validate_rect(site,rect):
 if not isinstance(rect,list) or len(rect)!=4 or any(type(v) is not int for v in rect):raise ValueError('integer rect required')
 x,y,w,h=rect;a,b,c,d=site['rect']
 if min(w,h)<=0 or x<a or y<b or x+w>a+c or y+h>b+d:raise ValueError('rect leaves existing plot')
 if y+h!=b+d:raise ValueError('same bottom root required')
 if abs(x+w/2-(a+c/2))>.5:raise ValueError('same horizontal root required')
 return True
def main():
 assert not (SOURCE/'structures').exists() and not REPORT.exists()
 REPORT.mkdir(parents=True)
 helper=ROOT/'scripts/prepare_town_art.py';helperpin=sha(helper)
 spec=importlib.util.spec_from_file_location('existing_town_art',helper);art=importlib.util.module_from_spec(spec);spec.loader.exec_module(art);assert sha(helper)==helperpin
 def jput(p,v):put(p,art.encoded(v))
 layoutpath=ROOT/'design/building-layout.json';oldlayout=read(layoutpath);layoutpin=sha(layoutpath);candidate=deepcopy(oldlayout)
 for site in candidate['sites']:
  for state in site['states']:
   if state in RECTS:validate_rect(site,RECTS[state]);site.setdefault('state_rects',{})[state]=RECTS[state]
 candidate['scope']='Unselected three-state rear human-scale successor; preserve current Grail rect, all final monuments, all other sites and native functionality. Root integrates separately.'
 candidatepath=ROOT/'design/building-layout-human-scale-v3.json';jput(candidatepath,candidate)
 before={rel(layoutpath):layoutpin};active={};native={};sourcepins={}
 for p in sorted((ROOT/'assets/recipes/town').rglob('*.json')):before[rel(p)]=sha(p)
 for p in sorted((ROOT/'assets/recipes/town/structures').glob('*-animation.json')):
  state=p.stem.removesuffix('-animation');v=read(p);active[state]=v;f=v['groups'][0]['frames'][0];path=ROOT/f['source'];assert sha(path)==f['source_sha256'];native[state]=Image.open(path).convert('RGBA')
 plans={};receipts=[];changes={};iconpaths={}
 for state,rect in RECTS.items():
  beforegen=active[state]['generation'];master=ROOT/beforegen['painted_master'];sourcepins[rel(master)]=sha(master);assert sha(master)==beforegen['painted_master_sha256']
  im=art.load_rgba(master);layer,conversion=art.place(im,rect);layer2,conversion2=art.place(im,rect);assert art.png(layer)==art.png(layer2) and conversion==conversion2
  area,border=art.masks(layer);icon=art.icon(im);folder=SOURCE/'structures'/state;paths={r:folder/(r+'.png') for r in ('layer','area','border','icon')};data={'layer':art.png(layer),'area':art.png(area),'border':art.png(border),'icon':art.png(icon)}
  oldicon=next(f for f in read(ROOT/'assets/recipes/town/buildingIcons.json')['frames'] if f['building']==state);assert data['icon']==(ROOT/oldicon['source']).read_bytes()
  for role,value in data.items():put(paths[role],value)
  gen=deepcopy(beforegen);gen['conversion']=conversion;gen['technical_producer']={'path':rel(Path(__file__).resolve()),'sha256':sha(Path(__file__).resolve()),'reused_existing_helper':{'path':rel(helper),'sha256':helperpin}}
  inputs=[{'path':rel(candidatepath),'sha256':sha(candidatepath)},{'path':rel(Path(__file__).resolve()),'sha256':sha(Path(__file__).resolve())},{'path':rel(helper),'sha256':helperpin}]
  animation=deepcopy(active[state]);animation['generation']=gen;animation['inputs']=inputs
  frame=animation['groups'][0]['frames'][0];frame.update(source=rel(paths['layer']),source_sha256=digest(data['layer']),sha256=digest(data['layer']))
  local={REPORT/f'recipe-payload/structures/{state}-animation.json':animation}
  for role in ('area','border'):
   mask=read(ROOT/f'assets/recipes/town/structures/{state}-{role}.json');mask.update(source=rel(paths[role]),source_sha256=digest(data[role]),inputs=inputs);mask['generation']={'image_generation_used':False,'method':'Existing alpha128 silhouette/onepixel outeredge of uniformly rescaled same master; all RGBA painted pixels preserved','painted_source_provenance':gen,'references':[{'path':rel(paths['layer']),'sha256':digest(data['layer'])}]};local[REPORT/f'recipe-payload/structures/{state}-{role}.json']=mask
  plans.update(local);iconpaths[state]=paths['icon'];native[state]=layer
  previous=beforegen['conversion'];ratio=conversion['uniform_scale']/previous['uniform_scale'];box=DOORS[state];ox,oy=previous['placed_origin'];nx,ny=conversion['placed_origin'];predicted=[nx+(box[0]-ox)*ratio,ny+(box[1]-oy)*ratio,nx+(box[2]-ox)*ratio,ny+(box[3]-oy)*ratio]
  changes[state]={'before_native_door_box':box,'measurement_uncertainty_native_pixels':2,'new_rect':rect,'before_conversion':previous,'new_conversion':conversion,'uniform_scale_ratio':ratio,'predicted_transformed_same_door_box':predicted,'predicted_door_height':predicted[3]-predicted[1],'actual_new_slab_measurement':'Pending independent pixel review; transformed coordinates are a source geometry prediction, not a new observation.','unchanged_master_sha256':sha(master)}
  receipt={'state':state,'site':next(s['id'] for s in candidate['sites'] if state in s['states']),'master':rel(master),'master_sha256':sha(master),'native_layer':rel(paths['layer']),'native_layer_sha256':digest(data['layer']),'conversion':conversion,'prepared_icon':rel(paths['icon']),'icon_sha256':digest(data['icon']),'sources':{rel(paths[r]):digest(v) for r,v in data.items()},'recipes':{f'assets/recipes/town/structures/{p.name}':digest(art.encoded(v)) for p,v in local.items()},'selection':{'layout_sha256':sha(candidatepath),'helper_sha256':helperpin,'master_sha256':sha(master)},'native_execution':False,'visual_approval_granted':False}
  jput(folder/'preparation.json',receipt);receipts.append(receipt)
 atlas=read(ROOT/'assets/recipes/town/buildingIcons.json');oldatlas=deepcopy(atlas)
 for f in atlas['frames']:
  if f['building'] in iconpaths:f['source']=rel(iconpaths[f['building']])
 atlas['generation']['human_scale_successor']={'method':'Only3byte-exact icon source references relocate; native world scale changes do not shrink150x70constructioncards','producer':rel(Path(__file__).resolve()),'producer_sha256':sha(Path(__file__).resolve())};plans[REPORT/'recipe-payload/buildingIcons.json']=atlas
 assert all(a==b for a,b in zip(oldatlas['frames'],atlas['frames']) if a['building'] not in RECTS)
 for p,v in plans.items():jput(p,v)
 sys.path.insert(0,str(ROOT.parent/'scripts'));import faction_art_compile
 compiler=faction_art_compile.create_compiler('freljord');runs=[]
 for number in (1,2):
  pins={}
  for p in sorted(plans):
   outputs,proof=compiler.plan(ROOT,p)
   for name,data in outputs.items():assert name not in pins;put(REPORT/f'compiler-run{number}'/name,data);pins[name]=digest(data)
  runs.append(pins)
 assert runs[0]==runs[1]
 jput(REPORT/'compiler-repeat-v1.json',{'actual_plan_calls':len(plans)*2,'recipes_per_run':len(plans),'physical_files_per_run':len(runs[0]),'byte_exact_two_actual_runs':True,'output_hashes':runs[0],'native_execution':False})
 backgroundrecipe=read(ROOT/'assets/recipes/town/background.json');background=Image.open(ROOT/backgroundrecipe['source']).convert('RGBA');structures=read(ROOT/'content/factions.json')['freljord']['town']['structures'];composites={}
 for label,up,coast in (('early',False,False),('base-land',False,False),('base-coast',False,True),('upgraded-land',True,False),('upgraded-coast',True,True)):
  canvas=background.copy();chosen=[]
  for s in candidate['sites']:
   if not coast and not s['land']:continue
   opts=[v for v in s['states'] if v!='grail'];state=opts[-1] if up else opts[0]
   if label=='early' and state not in ('villageHall','tavern','dwellingLvl1'):continue
   chosen.append(state)
  for state in sorted(chosen,key=lambda n:structures[n]['z']):canvas.alpha_composite(native[state])
  p=REPORT/(label+'-native1x-v1.png');put(p,art.png(canvas));composites[label]={'path':rel(p),'sha256':sha(p),'states':chosen}
  if up:
   old=ROOT/f'build/reports/painted-town-community-20261024-v1/{label}-native800x374-v2.png';assert canvas.tobytes()==Image.open(old).convert('RGBA').tobytes();composites[label]['pixels_identical_to_preceding_full_upgrade']=True
 # Fixedworld crops provide both actual1x and nearest-neighbor3x diagnostic, never altered assets.
 board=Image.new('RGBA',(800,240),(48,54,61,255));draw=ImageDraw.Draw(board)
 diagnostics=[('villageHall',(240,90,414,170)),('townHall',(240,90,414,170)),('mageGuild1',(435,125,560,207)),('dwellingLvl2',(605,309,769,371))]
 for n,(state,box) in enumerate(diagnostics):
  crop=native[state].crop(box);board.alpha_composite(crop,(n*200,30));draw.text((n*200+2,4),state,fill='white')
  if state in changes:draw.text((n*200+2,130),'predicted door %.1fpx'%changes[state]['predicted_door_height'],fill='white')
  else:draw.text((n*200+2,130),'reviewed door15px +/-2',fill='white')
 put(REPORT/'human-scale-native1x-v1.png',art.png(board));put(REPORT/'human-scale-diagnostic3x-v1.png',art.png(board.resize((2400,720),Image.Resampling.NEAREST)))
 finalboard=Image.new('RGBA',(750,180),(48,54,61,255));draw=ImageDraw.Draw(finalboard)
 for n,state in enumerate(('cityHall','capitol','mageGuild4')):
  site=next(s for s in candidate['sites'] if state in s['states']);x,y,w,h=site['rect'];finalboard.alpha_composite(native[state].crop((x,y,x+w,y+h)),(n*250,25));draw.text((n*250+2,3),state+' UNCHANGED',fill='white')
 put(REPORT/'final-monuments-openings-native1x-v1.png',art.png(finalboard));put(REPORT/'final-monuments-openings-diagnostic4x-v1.png',art.png(finalboard.resize((3000,720),Image.Resampling.NEAREST)))
 negative={}
 for state in RECTS:
  site=next(s for s in candidate['sites'] if state in s['states']);bad=deepcopy(RECTS[state]);bad[1]-=1
  try:validate_rect(site,bad)
  except ValueError as e:negative[state+'_moved_bottom_rejected']=str(e)
  else:raise AssertionError(state)
 malformed=deepcopy(plans[REPORT/'recipe-payload/structures/villageHall-animation.json']);malformed['groups'][0]['frames'][0]['source_sha256']='0'*64;malformed['groups'][0]['frames'][0]['sha256']='0'*64;p=REPORT/'negative-frame-hash.json';jput(p,malformed)
 try:compiler.plan(ROOT,p)
 except ValueError as e:negative['actual_compiler_drift_rejected']=str(e)
 else:raise AssertionError('frame drift accepted')
 for name,pin in before.items():assert sha(ROOT/name)==pin,name
 for name,pin in sourcepins.items():assert sha(ROOT/name)==pin,name
 assert sha(helper)==helperpin
 copyplan=[]
 for p in sorted(plans):
  dest=ROOT/'assets/recipes/town'/p.relative_to(REPORT/'recipe-payload');copyplan.append({'source':rel(p),'sha256':sha(p),'destination':rel(dest),'before_sha256':before[rel(dest)]})
 jput(REPORT/'result-v1.json',{'status':'authored configuration','baseline_layout_sha256':layoutpin,'candidate_layout':rel(candidatepath),'candidate_layout_sha256':sha(candidatepath),'same_native_plot_bottoms':{'civic-hall':168,'mage-guild':205},'source_master_hashes_unchanged':sourcepins,'changes':changes,'negative_controls':negative,'actual_recipe_count':len(plans),'strict_repeat_byte_exact':True,'unaffected_native_states_preserved':33,'icon_pixels_all36_unchanged':True,'unaffected33atlas_frame_records_exact':True,'composites':composites,'current_default_recipe_and_layout_pins_unchanged':before,'helper_sha256_before_and_after':helperpin,'final_opening_interpretation':'Frontand sideopening diagnostics supplied. Large mainportal is architecturally different from small sidebays, but no canonical humanheight or authenticated ceremonial-door classification is inferred from pixels. Finalmonument geometry unchanged as requested; independent visual scale interpretation remains explicit.','native_execution':False,'visual_approval_granted':False,'production_or_stage_writes':False})
 jput(REPORT/'integration-plan-v1.json',{'root_executes_only':True,'layout_source':rel(candidatepath),'layout_sha256':sha(candidatepath),'layout_destination':'design/building-layout.json','layout_before_sha256':layoutpin,'recipe_replacements':copyplan,'structure_position_or_function_updates':None,'required_helper_behavior':'Respect explicit perstate state_rects on existing site; coordinator helper repair separately owned. No x/y/z, cost, prerequisite, buildingkey, replacementchain, finalmonument or Grail changes.'})
 pins=[candidatepath,Path(__file__).resolve(),*(p for p in SOURCE.rglob('*') if p.is_file()),*(p for p in (REPORT/'recipe-payload').rglob('*') if p.is_file()),REPORT/'result-v1.json',REPORT/'integration-plan-v1.json',REPORT/'compiler-repeat-v1.json']
 jput(REPORT/'source-manifest-v1.json',{'files':{rel(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(set(pins))},'native_execution':False,'visual_approval_granted':False})
 print(json.dumps({'report':rel(REPORT),'candidate_layout_sha256':sha(candidatepath),'source_manifest_sha256':sha(REPORT/'source-manifest-v1.json'),'result_sha256':sha(REPORT/'result-v1.json'),'recipes':len(plans),'physical_files_per_run':len(runs[0]),'predicted_door_heights':{s:round(v['predicted_door_height'],2) for s,v in changes.items()},'negative_controls':len(negative),'native_execution':False}))
if __name__=='__main__':main()
