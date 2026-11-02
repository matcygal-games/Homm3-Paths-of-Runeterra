"""Actual converter/public layout consumer in a direct isolated source fixture.

No staging/build/native launch or canonical input mutation. An attempt is an
immutable report directory; use a new --attempt after source corrections.
"""
from pathlib import Path
from copy import deepcopy
from collections import deque
import argparse,hashlib,importlib.util,json,shutil,sys
from PIL import Image,ImageChops
GUIDE=Path(__file__).resolve().parent;HERE=GUIDE/'structural-contract';TOWN=GUIDE.parents[1];ROOT=GUIDE.parents[5];WORKSPACE=ROOT.parent
sys.path.insert(0,str(WORKSPACE/'scripts'))
import faction_town_layout as admission
import faction_pipeline as fp
import faction_production as production
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf8')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--attempt',required=True);ap.add_argument('--contract',default='town-layout.json');ap.add_argument('--candidate',default='candidate-final-v5');ap.add_argument('--workspace');args=ap.parse_args()
 if not args.attempt.replace('-','').isalnum():raise ValueError('Simple unique report attempt required')
 if '/' in args.candidate or '\\' in args.candidate or args.candidate in ('.','..'):raise ValueError('Direct town candidate directory required')
 report=ROOT/'build/reports/complete-town-20261027-v2/geometry-final-v2'/('coherent-paving-guide-v1/consumer-'+args.attempt)
 if report.exists():raise ValueError('Preserve previous executed evidence; choose a new attempt')
 fixture=(ROOT/'build/reports/complete-town-20261027-v2/geometry-final-v2'/args.workspace).resolve()if args.workspace else report/'direct-source-fixture'
 if not fixture.is_relative_to((ROOT/'build/reports/complete-town-20261027-v2/geometry-final-v2').resolve()):raise ValueError('Reusable fixture must stay in owned report subtree')
 fixture.mkdir(parents=True,exist_ok=bool(args.workspace));candidate=TOWN/args.candidate;selection=load(candidate/'selection.json');factions=load(candidate/'factions.candidate.json');contract_path=HERE/args.contract;contract=load(contract_path);name=contract_path.relative_to(ROOT).as_posix();pins={};copied={}
 def visit(value):
  if isinstance(value,dict):
   if isinstance(value.get('path'),str):
    p=ROOT/value['path']
    if sha(p)!=value['sha256']:raise ValueError('Declared source changed '+value['path'])
    target=fixture/value['path'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target);copied[value['path']]=sha(target)
   for v in value.values():visit(v)
  elif isinstance(value,list):
   for v in value:visit(v)
 visit(contract);write(fixture/name,contract);write(fixture/'content/factions.json',factions);design=deepcopy(load(ROOT/'design/town-visuals.json'));design.update(layout_geometry_mode='silhouette-v2',layout_contract={'path':name,'sha256':sha(fixture/name)});write(fixture/'design/town-visuals.json',design)
 spec=importlib.util.spec_from_file_location('actual_noxus_compiler',ROOT/'scripts/art_compile.py');compiler=importlib.util.module_from_spec(spec);spec.loader.exec_module(compiler);converted=[];outputs={}
 for relative,pin in sorted(selection['recipes'].items()):
  p=candidate/'candidate-recipes'/relative
  if sha(p)!=pin:raise ValueError('Candidate recipe changed '+relative)
  data,record=compiler.plan(ROOT,p)
  for output,b in data.items():
   target=fixture/'assets/generated'/output;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b);outputs[output]=sha(target)
  converted.append(record)
 content={'factions':factions};errors,dependencies=admission.inspect(fixture,content,'noxus');negative=[];initial_contract_bytes=(fixture/name).read_bytes();initial_design_bytes=(fixture/'design/town-visuals.json').read_bytes()
 # Exercise the actual recursive reference and editable-source collector even
 # when physical admission fails. Byte closure grants no physical acceptance.
 declared_dependencies=admission.dependency_paths(fixture)
 exported=production._current_town_layout_source_entries(fp.Pipeline(fixture,'runeterra-noxus','noxus'),{})
 closure={str(path.relative_to(fixture).as_posix()):sha(path) for path in declared_dependencies}
 for relative,pin in closure.items():
  if hashlib.sha256(exported['runeterra-noxus/'+relative]).hexdigest()!=pin:raise ValueError('Actual collector byte closure mismatch '+relative)
 def inspect_negative(label,mutator,expected=None):
  changed={};c=deepcopy(contract);fixed={key:sha(fixture/contract['silhouette_plan'][key]['path'])for key in ('support_mask','stairs_mask','water_mask','paths_mask')};fixed['background']=sha(fixture/contract['background']['path'])
  def put(path,b):
   if path not in changed:changed[path]=path.read_bytes()
   path.write_bytes(b)
  def store_json(path,value):put(path,(json.dumps(value,indent=2)+'\n').encode())
  def image_move(reference,dx,dy):
   path=fixture/reference['path'];im=Image.open(path);moved=Image.new(im.mode,im.size);moved.paste(im,(dx,dy));import io;stream=io.BytesIO();moved.save(stream,format='PNG',compress_level=9);put(path,stream.getvalue());reference['sha256']=sha(path)
  try:
   control_facts=mutator(c,put,store_json,image_move)or{}
   store_json(fixture/name,c);d=deepcopy(design);d['layout_contract']['sha256']=sha(fixture/name);store_json(fixture/'design/town-visuals.json',d)
   observed,_=admission.inspect(fixture,content,'noxus')
   case_folder=report/'negative-cases'/label
   for path in changed:
    target=case_folder/'changed-inputs'/path.relative_to(fixture);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(path.read_bytes())
   baseline_pins={'contract_sha256':sha(contract_path),'candidate_selection_sha256':sha(candidate/'selection.json'),'helper_sha256':sha(WORKSPACE/'scripts/faction_town_layout.py')}
   write(case_folder/'raw-consumer-result.json',{'errors':observed,'baseline_pins':baseline_pins,'control_facts':control_facts,'mutated_contract_sha256':sha(fixture/name),'changed_input_sha256':{path.relative_to(fixture).as_posix():sha(path)for path in changed}})
   current={key:sha(fixture/c['silhouette_plan'][key]['path'])for key in ('support_mask','stairs_mask','water_mask','paths_mask')};current['background']=sha(fixture/c['background']['path']);passed=bool(observed) and (expected is None or any(expected.lower()in e.lower()for e in observed))and current==fixed;negative.append({'control':label,'passed':passed,'actual_consumer':'scripts/faction_town_layout.py:inspect','errors':observed,'environment_unchanged':current==fixed,'fixed_environment_sha256':fixed})
   negative[-1]['baseline_pins']=baseline_pins
   negative[-1]['control_facts']=control_facts
   if not passed:raise ValueError('Actual public consumer accepted/misdiagnosed negative '+label)
  finally:
   for path,b in changed.items():path.write_bytes(b)
 def missing_approval(c,put,store_json,image_move):c['silhouette_plan']['foundation_occlusions']=[]
 def stale_bytes(c,put,store_json,image_move):
  ref=c['silhouette_plan']['states']['special1']['foundation_mask'];path=fixture/ref['path'];im=Image.open(path).convert('L');im.putpixel((0,0),255);import io;s=io.BytesIO();im.save(s,format='PNG');put(path,s.getvalue())
 def shifted_approval(c,put,store_json,image_move):image_move(c['silhouette_plan']['foundation_occlusions'][0]['mask'],1,0)
 def displaced_building(c,put,store_json,image_move,dx=0,dy=-15):
  state='special1';image_move(c['frames'][state],dx,dy);r=c['silhouette_plan']['states'][state]
  for key in ('foundation_mask','body_mask','door_mask','approach_mask'):image_move(r[key],dx,dy)
  r['entrance']=[r['entrance'][0]+dx,r['entrance'][1]+dy]
  site=next(s for s in c['sites'] if state in s['states']);site['box'][0]+=dx;site['box'][1]+=dy;site['entrance']=[site['entrance'][0]+dx,site['entrance'][1]+dy];image_move(site['silhouette_mask'],dx,dy)
  structure=factions['noxus']['town']['structures'][state];definition=load(fixture/'assets/generated/Content/Sprites'/structure['animation']);groups=fp.utility('identity').animation_groups(definition,complete=True);selected=fixture/'assets/generated/Content/Sprites'/(definition.get('basepath','')+groups[0][0]);put(selected,(fixture/c['frames'][state]['path']).read_bytes())
  root=Image.open(fixture/r['foundation_mask']['path']).convert('L')
  return {'state':state,'whole_source_and_physical_mask_translation':[dx,dy],'actual_translated_root_pixels':root.histogram()[255],'actual_root_on_fixed_public_stairs':ImageChops.multiply(root,Image.open(fixture/c['silhouette_plan']['stairs_mask']['path']).convert('L')).histogram()[255],'actual_root_on_fixed_external_water':ImageChops.multiply(root,Image.open(fixture/c['silhouette_plan']['water_mask']['path']).convert('L')).histogram()[255],'actual_root_outside_fixed_level_support':ImageChops.subtract(root,Image.open(fixture/c['silhouette_plan']['support_mask']['path']).convert('L')).histogram()[255],'actual_generated_selected_frame_matches_mutated_source':sha(selected)==sha(fixture/c['frames'][state]['path'])}
 def blocked_real_entry(c,put,store_json,image_move):
  # An isolated source/frame mutation inserts a foreground opaque pixel over
  # the actual rear castle arch. Roots, floors, stairs and walking stay fixed.
  # Every affected source/body/site/overlap reference is recalculated so the
  # public consumer must detect the entry occlusion rather than a stale pin.
  import io
  front='mageGuild4';rear='castle';physical=c['silhouette_plan']['states'];door=Image.open(fixture/physical[rear]['door_mask']['path']).convert('L');rearbody=Image.open(fixture/physical[rear]['body_mask']['path']).convert('L');frame=Image.open(fixture/c['frames'][front]['path']).convert('RGBA')
  candidates=[(x,y)for y in range(73,111)for x in range(430,478)if door.getpixel((x,y))and rearbody.getpixel((x,y))and not frame.getpixel((x,y))[3]]
  if not candidates:raise ValueError('No real protected castle arch witness found')
  point=candidates[0];frame.putpixel(point,(90,70,60,255))
  def save_reference(reference,image):
   stream=io.BytesIO();image.save(stream,format='PNG',compress_level=9);path=fixture/reference['path'];put(path,stream.getvalue());reference['sha256']=sha(path)
  save_reference(c['frames'][front],frame);save_reference(physical[front]['body_mask'],frame.getchannel('A').point(lambda a:255 if a>=128 else 0))
  site_images={}
  for site in c['sites']:
   union=Image.new('L',(800,374))
   for state in site['states']:
    native=Image.open(fixture/c['frames'][state]['path']).convert('RGBA');union=ImageChops.lighter(union,native.getchannel('A').point(lambda a:255 if a>=8 else 0))
   site_images[site['id']]=union
   if front in site['states']:
    save_reference(site['silhouette_mask'],union);bb=union.getbbox();site['box']=[bb[0],bb[1],bb[2]-bb[0],bb[3]-bb[1]]
  for row in c['silhouette_plan']['overlaps']:save_reference(row['mask'],ImageChops.multiply(site_images[row['behind']],site_images[row['front']]))
  structure=factions['noxus']['town']['structures'][front];definition=load(fixture/'assets/generated/Content/Sprites'/structure['animation']);groups=fp.utility('identity').animation_groups(definition,complete=True);selected=fixture/'assets/generated/Content/Sprites'/(definition.get('basepath','')+groups[0][0]);put(selected,(fixture/c['frames'][front]['path']).read_bytes())
  scene=Image.open(fixture/c['background']['path']).convert('RGBA')
  for state in c['silhouette_plan']['complete_scene_states']:scene.alpha_composite(Image.open(fixture/c['frames'][state]['path']).convert('RGBA'))
  save_reference(c['silhouette_plan']['complete_scene'],scene)
  return {'actual_front_source':front,'protected_rear_entry':rear,'actual_added_opaque_source_pixel':list(point),'prior_front_alpha_at_pixel':0,'new_front_alpha_at_pixel':255,'actual_rear_full_entry_pixel':door.getpixel(point),'floors_stairs_water_and_streets_unchanged':True}
 def displaced_onto_actual_stairs(c,put,store_json,image_move):
  # Choose from current actual traced stair components. Historical stairs may
  # have been removed by genuine terrain repair; fixed old coordinates could
  # otherwise turn this control into an unrelated unsupported-ground test.
  stairs=Image.open(fixture/c['silhouette_plan']['stairs_mask']['path']).convert('L');pixels=stairs.load();remaining={(x,y)for y in range(374)for x in range(800)if pixels[x,y]};components=[]
  while remaining:
   start=min(remaining,key=lambda p:(p[1],p[0]));remaining.remove(start);queue=deque([start]);points=[]
   while queue:
    x,y=queue.popleft();points.append((x,y))
    for point in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
     if point in remaining:remaining.remove(point);queue.append(point)
   components.append(points)
  state='special1';root=Image.open(fixture/c['silhouette_plan']['states'][state]['foundation_mask']['path']).convert('L');rb=root.getbbox();frame=Image.open(fixture/c['frames'][state]['path']).convert('RGBA');fb=frame.getchannel('A').point(lambda a:255 if a>=8 else 0).getbbox();candidates=[]
  for points in components:
   xs=[p[0]for p in points];ys=[p[1]for p in points];dx=(min(xs)+max(xs))//2-(rb[0]+rb[2])//2;dy=(min(ys)+max(ys))//2-(rb[1]+rb[3])//2
   if not(0<=fb[0]+dx<fb[2]+dx<=800 and 0<=fb[1]+dy<fb[3]+dy<=374):continue
   shifted=Image.new('L',root.size);shifted.paste(root,(dx,dy));hit=ImageChops.multiply(shifted,stairs).histogram()[255]
   if hit>=10:candidates.append((-hit,dx*dx+dy*dy,dy,dx))
  if not candidates:raise ValueError('No current actual stair component supports a bounded real-source negative')
  _,_,dy,dx=min(candidates);facts=displaced_building(c,put,store_json,image_move,dx=dx,dy=dy)
  if facts['actual_root_on_fixed_public_stairs']<10:raise ValueError('Actual public stair negative lost its current stair contact')
  return facts
 if False: # USER HOLD: authoring structural replay only; final negatives prohibited.
  inspect_negative('remove-all-foundation-projection-approvals',missing_approval,'foundation')
  inspect_negative('actual-source-mask-byte-mutation-old-pin',stale_bytes,'missing or changed')
  inspect_negative('actual-approval-mask-shifted-one-pixel',shifted_approval)
  inspect_negative('actual-building-and-physical-masks-displaced-onto-retaining-face',displaced_building,'foundation')
  inspect_negative('actual-building-and-physical-masks-displaced-onto-actual-public-stairs',displaced_onto_actual_stairs,'foundation')
  inspect_negative('actual-building-and-physical-masks-displaced-onto-external-water',lambda *a:displaced_building(*a,dx=714,dy=60),'foundation')
  inspect_negative('actual-foreground-selected-source-covers-protected-rear-castle-arch',blocked_real_entry,'door')
  restored,_=admission.inspect(fixture,content,'noxus')
  if restored:raise ValueError('Negative restoration failed '+str(restored))
 result={'status':'authored configuration','ok':not errors,'geometry_errors':errors,'baseline_is_valid_for_negative_attribution':False,'authoring_structural_check_only':True,'user_rejected_materials':True,'visual_approval':False,'final_admission_on_hold':True,'actual_recipe_count':len(converted),'actual_output_count':len(outputs),'outputs':outputs,'actual_public_consumer':str((WORKSPACE/'scripts/faction_town_layout.py').relative_to(WORKSPACE)),'helper_sha256':sha(WORKSPACE/'scripts/faction_town_layout.py'),'contract_path':name,'contract_sha256':sha(contract_path),'candidate_selection_sha256':sha(candidate/'selection.json'),'direct_source_dependency_count':len(dependencies),'declared_source_dependency_count':len(declared_dependencies),'actual_collector_exported_member_count':len(exported),'actual_collector_byte_closure':closure,'copied_source_pins':copied,'actual_negative_checks':negative,'negative_checks_run':bool(negative),'negative_checks_blocked_reason':'User rejected surface appearance; authoring structural replay only. Final negatives and admission held.','fixture_workspace':str(fixture),'fixture_bytes':sum(p.stat().st_size for p in fixture.rglob('*')if p.is_file()),'complete_runtime_or_visual_acceptance':False,'canonical_inputs_modified':False,'stage_built':False,'native_verified':False,'release_accepted':False};write(report/'receipt.json',result);print(json.dumps({k:result[k]for k in ('ok','geometry_errors','actual_recipe_count','actual_output_count','actual_negative_checks','direct_source_dependency_count','declared_source_dependency_count','actual_collector_exported_member_count','fixture_bytes')}))
 if errors:raise SystemExit(2)
if __name__=='__main__':main()
