"""Prepare Zaun town candidates through its existing delivered-recipe pipeline.

No staging, manifest, active recipe/content or native writes. Frozen placement
is the authority; deterministic scale/masks/composition are technical only.
"""
from pathlib import Path
import json,hashlib,copy,sys,shutil,argparse
from PIL import Image,ImageChops,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
REPORT=ROOT/'build/reports/industrial-neighborhood-20261025-v3'
PLAN=HERE/'live-placement-plan.json'
PLAN_SHA='ebc0f8ca5a08869bae5a7a3ad205bc5cab43a61832d85454e856f3febf292333'
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT.parent/'scripts'))
import zaun_coastal_state_v1 as coastal
import faction_artifacts as converter
PREFIX='Content/Sprites/runeterra/zaun/'
Z_OVERRIDES={'dwellingConstruct':359,'shipyard':361}
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
def write(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def save(p,im):
 p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9,optimize=False)
def prepare(background=None,background_generation=None):
 if sha(PLAN)!=PLAN_SHA:raise ValueError('Frozen prepaint plan changed')
 plan=read(PLAN);by={r['state']:r for r in plan['states']}
 olddesign=read(ROOT/'design/town-visuals.json');sites=copy.deepcopy(olddesign['sites'])
 recipes=[];bindings=[];layers={};rows=[];terrain={'water_polygon':plan['planned_inlet_polygon'],'buildable_floor_polygon':[[0,0],[799,0],[799,373],[0,373]],'support_status':'unassessed until actual painted background review'}
 for site in sites:
  sid=site['id'];ss=site['buildings'];sr={}
  for state in ss:
   row=copy.deepcopy(by[state]);row['prepaint_z']=row['native_z'];row['native_z']=Z_OVERRIDES.get(sid,row['native_z']);master=ROOT/row['master']
   if sha(master)!=row['master_sha256']:raise ValueError('Frozen painted master changed: '+state)
   # The frozen full-canvas prepared image includes every roof, stair and shadow.
   src=ROOT/row['native_layer']
   if sha(src)!=row['native_layer_sha256']:raise ValueError('Prepared full-subject layer changed: '+state)
   layer=Image.open(src).convert('RGBA');layers[state]=layer
   surfaces=coastal.surfaces(layer);folder=HERE/'structures'/state
   for kind,im in surfaces.items():save(folder/(kind+'.png'),im)
   provenance={
    'status':'authored configuration','provider':'OpenAI built-in imagegen','model':None,
    'model_disclosed':False,'image_generation_used':True,'new_image_generation_used':False,
    'generation_route':'Preserved selected own painted 2D master; whole-source uniform contain and native placement only.',
    'painted_master':row['master'],'painted_master_sha256':sha(master),'source_crop':row['source_crop'],
    'historical_receipt_sha256':row['historical_provenance']['sha256'],
    'historical_provenance':row['historical_provenance'],
    'historical_receipt_note':'Unchanged prior provider receipt retained privately at original authored source; not rewritten or claimed as new generation.',
    'composition_rectangle':row['composition_rectangle'],'native_offset':row['native_offset'],
    'native_size':row['native_size'],'mirror_x':row['mirror_x'],
    'placement_plan':rel(PLAN),'placement_plan_sha256':PLAN_SHA,
    'technical_helper':rel(HERE/'prepare.py'),'technical_helper_sha256':sha(HERE/'prepare.py'),
    'credits':{'author':'OpenAI built-in imagegen; original selected Zaun prompts and historical source retained','license':None,'redistribution':'unresolved; release prohibited'},
    'visual_approval_granted':False,'runtime_verified':False,'release_accepted':False}
   historical=row['historical_provenance']
   if sha(ROOT/historical['path'])!=historical['sha256']:raise ValueError('Exact archived generation receipt changed')
   provenance['historical_prompt']=read(ROOT/historical['path']).get('prompt')
   provenance_path=HERE/'provenance'/f'{state}.json';write(provenance_path,provenance)
   dependencies=[{'path':row['master'],'sha256':sha(master)},
    {'path':rel(provenance_path),'sha256':sha(provenance_path)},
    {'path':rel(HERE/'prepare.py'),'sha256':sha(HERE/'prepare.py')},
    {'path':'scripts/zaun_coastal_state_v1.py','sha256':sha(ROOT/'scripts/zaun_coastal_state_v1.py')},row['historical_provenance']]
   if state=='ship':
    dependencies.append({'path':by['shipyard']['master'],'sha256':by['shipyard']['master_sha256']})
   for kind in ['animation','area','border','construction']:
    active=f'assets/recipes/town/construction/{state}.json' if kind=='construction' else f'assets/recipes/town/structures/{state}-{kind}.json'
    recipe=read(ROOT/active);surface=folder/('layer.png' if kind=='animation' else kind+'.png')
    recipe.update({'source_sha256':sha(surface),'generation':provenance,'dependencies':dependencies,
      'identity_review':rel(REPORT/'source-pixel-review.json'),'native_visual_review':'pending','visual_approval_granted':False})
    if kind=='animation':
     recipe['groups'][0]['frames']=[{'source':rel(surface),'sha256':sha(surface)}]
     recipe['building_contract']['full_canvas_placement']={'x':0,'y':0,'z':row['native_z']}
     recipe['building_contract']['native_ground_contact']=row['composition_rectangle']
    else:recipe['source']=rel(surface)
    target=HERE/'recipes'/Path(active).relative_to('assets/recipes');write(target,recipe)
    recipes.append(target);bindings.append({'active':active,'candidate':rel(target),'sha256':sha(target)})
   row.update({'native_layer':rel(folder/'layer.png'),'native_layer_sha256':sha(folder/'layer.png'),
    'provenance':rel(provenance_path),'provenance_sha256':sha(provenance_path)})
   rows.append(row);sr[state]=row
  first=sr[ss[0]];site.update({'composition_rectangle':first['composition_rectangle'],'native_z':first['native_z'],'source_states':sr})
 data=copy.deepcopy(olddesign);data['sites']=sites
 data['status']='authored configuration'
 data['selected_sources']={'kind':'painted2D-industrial-neighborhood','revision':HERE.name,'selection':rel(HERE/'selection.json')}
 data['visualDirection']='One connected Zaun iron-and-glass neighborhood, organic streets/alleys/industrial platforms and inhabited edges. Much larger physically grand rear institutions; readable front façades. Neon chemical green is localized glass/lamps, with purple Shimmer/cloth and brown rust. No universal near/far size ratio, plot-grid or three horizontal terrace bands.'
 data['derivation']='All36 selected building states preserve their21 painted master files and exact crop selectors. Whole-source uniform scaling/placement and alpha-derived masks/icons follow the finite prepaint plan; the separate genuinely painted background must match the actual full foundations and doors.'
 data['layoutPolicy'].update({'authority':'Latest25October2026 user industrial-neighborhood/large-rear/real-door correction',
  'composition':data['visualDirection'],'selectedSourcePlan':rel(PLAN),'selectedSourcePlanSha256':PLAN_SHA,
  'coordinatorPixelReview':rel(REPORT/'source-pixel-review.json'),'geometryEvidence':rel(REPORT/'geometry-validation.json'),
  'independentSourceReview':'pending current-neighborhood finite source review','nativeComposition':rel(REPORT/'grail-native.png'),
  'nativeReview':'pending current-stage native review','supersedes':'The user-rejected sparse rocky town/foreground-to-background universal scaling quota; native hallSlots are a separate consumer.'})
 write(HERE/'town-visuals.candidate.json',data)
 if background:
  bg=ROOT/background
  if Image.open(bg).size!=(800,374):raise ValueError('Background must be native800x374')
  generation=read(ROOT/background_generation) if background_generation else None
  if not generation:raise ValueError('Genuine painted background generation receipt required')
  mask_names=[name for name in generation.get('source_pins',{}) if name.endswith('/water-mask-v2.png')]
  if len(mask_names)!=1:raise ValueError('Exact selected painted shoreline assembly mask required')
  mask_name=mask_names[0];mask_path=ROOT/mask_name
  if sha(mask_path)!=generation['source_pins'][mask_name]:raise ValueError('Background shore mask changed')
  water=Image.open(mask_path).convert('L')
  terrain.update({'water_mask':mask_name,'water_mask_sha256':sha(mask_path),'painted_background':background,'painted_background_sha256':sha(bg),
   'support_status':'Selected painted-shore assembly mask tested; actual all-state ground/door pixels require separate independent review.'})
  findings=[]
  for row in rows:
   apron=Image.new('L',(800,374));ImageDraw.Draw(apron).rectangle(row['visible_front_apron'],fill=255)
   wet_apron=ImageChops.multiply(apron,water).histogram()[255]
   foot=Image.open(ROOT/row['foundation_mask']).convert('L').point(lambda a:255 if a>=1 else 0)
   wet_foot=ImageChops.multiply(foot,water).histogram()[255]
   row['footing_water_pixels']=wet_foot if row['site']!='shipyard' else None
   row['footing_outside_buildable_floor_pixels']=wet_foot if row['site']!='shipyard' else None
   row['apron_water_pixels']=wet_apron
   row['terrain_support_status']='Selected painted-shore mask measured; actual ground/door pixels remain separately reviewed.'
   findings.append({'state':row['state'],'site':row['site'],'wet_front_apron_pixels':wet_apron,'wet_lower_foundation_pixels':wet_foot,'coastal_pile_exception':row['site']=='shipyard'})
  if any(f['wet_front_apron_pixels'] or (f['wet_lower_foundation_pixels'] and not f['coastal_pile_exception']) for f in findings):raise ValueError('Actual selected shore mask intersects a dry entrance/foundation: '+str(findings))
  write(REPORT/'geometry-validation.json',{'status':'authored configuration','background':background,'background_sha256':sha(bg),'actual_shore_mask':mask_name,'actual_shore_mask_sha256':sha(mask_path),'states':findings,'all_dry_land_foundations_and_aprons_clear':True,'actual_pixel_support_review':'pending; mask metrics alone do not approve painted support','native':False,'release_accepted':False})
  recipe=read(ROOT/'assets/recipes/town/background.json')
  recipe.update({'source':background,'source_sha256':sha(bg),'generation':generation,
   'dependencies':[{'path':background,'sha256':sha(bg)},{'path':background_generation,'sha256':sha(ROOT/background_generation)}],
   'identity_review':rel(REPORT/'source-pixel-review.json'),'native_visual_review':'pending','visual_approval_granted':False})
  target=HERE/'recipes/town/background.json';write(target,recipe);recipes.append(target);bindings.append({'active':'assets/recipes/town/background.json','candidate':rel(target),'sha256':sha(target)})
  data['selected_sources']['background']=background;write(HERE/'town-visuals.candidate.json',data)
 outputs=[]
 for run in [1,2]:
  scratch=REPORT/f'compiler-run-{run}/runeterra-zaun';receipts=[];construction={}
  for path in recipes:
   recipe=read(path);source=recipe.get('source') or recipe['groups'][0]['frames'][0]['source']
   dst=scratch/source;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/source,dst)
   active=next(b['active'] for b in bindings if b['candidate']==rel(path));dest=scratch/active;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
   receipt=converter.CONVERTERS[recipe['recipe_type']](scratch,recipe,PREFIX,False,{},check=False);receipts.append({'recipe':active,'sha256':sha(path),'receipt':receipt})
   if '/construction/' in active:construction[recipe['building']]=receipt['sha256']
  index=read(ROOT/'assets/recipes/town/buildingIcons.json')
  for frame in index['frames']:
   frame['sha256']=construction[frame['building']];frame['producer_sha256']=sha(HERE/'recipes/town/construction'/f"{frame['building']}.json")
  index['generation']={'image_generation_used':True,'new_image_generation_used':False,'provider':'OpenAI built-in imagegen','model':None,'model_disclosed':False,'route':'Indexed native assembly of36 separately pinned selected painted own building construction icons','visual_approval_granted':False}
  index['dependencies']=[];index['identity_review']=rel(REPORT/'source-pixel-review.json')
  indexpath=HERE/'recipes/town/buildingIcons.json';write(indexpath,index)
  receipt=converter.convert_indexed(scratch,index,PREFIX,False,{},check=False);receipts.append({'recipe':'assets/recipes/town/buildingIcons.json','sha256':sha(indexpath),'receipt':receipt})
  inventory={p.relative_to(scratch/'assets/generated').as_posix():sha(p) for p in sorted((scratch/'assets/generated').rglob('*')) if p.is_file()}
  outputs.append(inventory);write(REPORT/f'compiler-run-{run}-receipts.json',receipts)
 if outputs[0]!=outputs[1]:raise ValueError('Compiler outputs differ between two passes')
 bindings.append({'active':'assets/recipes/town/buildingIcons.json','candidate':rel(indexpath),'sha256':sha(indexpath)})
 data['assetBinding']['status']=f'{len(bindings)} bounded town recipes prepared with the actual existing Zaun converter; technical execution does not grant art/native/rights approval.'
 write(HERE/'town-visuals.candidate.json',data)
 compiled_plan={'status':'authored configuration','canvas':[800,374],'siteCount':20,'stateCount':36,'sites':sites,'states':rows,
  'native_z_overrides':Z_OVERRIDES,'native_z_override_note':'Disambiguate independent same-ground families in the native draw order; no master, footprint, door or prepared pixel changes.',
  'terrain':terrain,
  'coast_semantics':plan['coast_semantics'],'visual_approval_granted':False,'runtime_verified':False,'release_accepted':False}
 write(HERE/'compiled-plan.json',compiled_plan)
 write(HERE/'selection.json',{'status':'authored configuration','revision':HERE.name,'canvas':[800,374],'siteCount':20,'stateCount':36,
  'candidate_design':rel(HERE/'compiled-plan.json'),'candidate_design_sha256':sha(HERE/'compiled-plan.json'),
  'layout':rel(HERE/'town-visuals.candidate.json'),'layout_sha256':sha(HERE/'town-visuals.candidate.json'),
  'placement_plan':rel(PLAN),'placement_plan_sha256':PLAN_SHA,'states':rows,'recipe_bindings':bindings,
  'background':background,'background_sha256':sha(ROOT/background) if background else None,
  'native_z_overrides':Z_OVERRIDES,'all_current_master_bytes_preserved':True,'visual_approval_granted':False,'runtime_verified':False,'release_accepted':False})
 write(REPORT/'compiler-determinism.json',{'ok':True,'recipe_count':len(bindings),'physical_outputs':len(outputs[0]),'runs':2,'outputs':outputs[0],
  'converter':'scripts/faction_artifacts.py DELIVERED existing Zaun pipeline','converter_sha256':sha(ROOT.parent/'scripts/faction_artifacts.py'),'background_is_final_candidate':bool(background)})
 if background:
  for variant in ['base','upgraded','coastal','moored','grail']:
   scene=Image.open(ROOT/background).convert('RGBA')
   for site in sorted(sites,key=lambda s:s['native_z']):
    sid=site['id'];state=site['buildings'][0 if variant=='base' else -1]
    if sid=='codeOfProgress' and variant!='grail':continue
    if sid=='shipyard':state='ship' if variant in ['moored','grail'] else 'shipyard' if variant=='coastal' else None
    if state:scene.alpha_composite(layers[state])
   save(REPORT/f'{variant}-native.png',scene)
 print(json.dumps({'recipes':len(bindings),'outputs':len(outputs[0]),'two_pass_identical':True,'background':background,'selection_sha256':sha(HERE/'selection.json')}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--background');p.add_argument('--background-generation');a=p.parse_args();prepare(a.background,a.background_generation)
