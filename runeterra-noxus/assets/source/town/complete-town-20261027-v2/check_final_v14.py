"""Actual regional converter replay and bounded actual-pixel negative controls.

Writes only this worker's report tree. No staging, canonical edits, native game,
fake layout admission or replacement of source pixels occurs here.
"""
from pathlib import Path
from copy import deepcopy
import hashlib,importlib.util,json,sys,tempfile,io
from PIL import Image,ImageChops

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
WORKSPACE=ROOT.parent
REPORT=ROOT/'build/reports/complete-town-20261027-v2/conversion-final-v14'
CANDIDATE=HERE/'candidate-final-v14'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf8')
def import_path(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def main():
 compiler_path=ROOT/'scripts/art_compile.py';compiler=import_path('noxus_actual_converter',compiler_path)
 sys.path.insert(0,str(WORKSPACE/'scripts'));import faction_town_layout as layout
 selection=load(CANDIDATE/'selection.json');results=[];outputs={};compiled={}
 held=[ROOT/'content/factions.json',ROOT/'design/town-visuals.json']
 held.extend((ROOT/'assets/recipes/town').rglob('*.json'));before={p.relative_to(ROOT).as_posix():sha(p) for p in held}
 for name,pin in sorted(selection['recipes'].items()):
  p=CANDIDATE/'candidate-recipes'/name
  if sha(p)!=pin:raise ValueError('Candidate recipe changed '+name)
  try:
   data,receipt=compiler.plan(ROOT,p)
   for name,b in data.items():
    if name in outputs:raise ValueError('Duplicate actual converted output '+name)
    target=REPORT/'outputs'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b);outputs[name]=digest(b);compiled[name]=b
   results.append({'recipe':p.relative_to(ROOT).as_posix(),'ok':True,'outputs':receipt['outputs']})
  except Exception as error:results.append({'recipe':p.relative_to(ROOT).as_posix(),'ok':False,'error':str(error)})
 decoded=[]
 for r in selection['states']:
  state=r['state'];recipe=load(CANDIDATE/'candidate-recipes'/f'assets/recipes/town/structures/{state}-animation.json')
  data,receipt=compiler.plan(ROOT,CANDIDATE/'candidate-recipes'/f'assets/recipes/town/structures/{state}-animation.json')
  frames=[(n,b) for n,b in data.items() if n.endswith('.png')]
  if len(frames)!=1:raise ValueError('Wrong static frame count '+state)
  name,b=frames[0];actual=Image.open(io.BytesIO(b)).convert('RGBA');expected=Image.open(ROOT/r['native_layer']).convert('RGBA')
  if actual.tobytes()!=expected.tobytes():raise ValueError('Converted selected pixels differ '+state)
  decoded.append({'state':state,'native_frame':name,'frame_sha256':digest(b),'decoded_rgba_equal':True})
 negative=[]
 # Real PNG mutation and actual converter entry point, all in a bounded temporary
 # own source directory. These controls never mutate the selected source.
 with tempfile.TemporaryDirectory(prefix='converter-negative-',dir=HERE) as td:
  folder=Path(td);state=selection['states'][0];valid=CANDIDATE/'candidate-recipes/assets/recipes/town/structures/villageHall-animation.json';original=load(valid)
  png=folder/'actual-mutated.png';image=Image.open(ROOT/state['native_layer']).convert('RGBA');bb=image.getchannel('A').getbbox();x,y=bb[0],bb[1];a=image.getpixel((x,y));image.putpixel((x,y),((a[0]+1)%256,a[1],a[2],a[3]));image.save(png)
  bad=deepcopy(original);bad['groups'][0]['frames'][0]['source']=png.relative_to(ROOT).as_posix()
  tests=[('actual-source-byte-mutation-with-old-pin',bad)]
  bad=deepcopy(original);bad['generation'].pop('prompt');tests.append(('missing-genuine-generation-prompt',bad))
  rgb=folder/'actual-rgb.png';Image.open(ROOT/state['native_layer']).convert('RGB').save(rgb);bad=deepcopy(original);frame=bad['groups'][0]['frames'][0];frame.update(source=rgb.relative_to(ROOT).as_posix(),source_sha256=sha(rgb),sha256=sha(rgb));tests.append(('actual-rgb-animation-frame',bad))
  for label,recipe in tests:
   p=folder/(label+'.json');write(p,recipe)
   try:compiler.plan(ROOT,p)
   except compiler.CompileError as error:negative.append({'control':label,'rejected':True,'actual_consumer':'runeterra-noxus/scripts/art_compile.py:plan','error':str(error).replace(folder.name,'actual-negative-fixture')})
   else:raise ValueError('Actual converter accepted negative '+label)
 # Execute the exact shared spatial predicate against real source pixels. This
 # is a bounded predicate control, explicitly not a full public inspect pass.
 root=Image.open(HERE/'physical-v10/special1/foundation.png').convert('L');body=Image.open(HERE/'physical-v10/special1/body.png').convert('L')
 if layout._outside(root,body):raise ValueError('Unshifted foundation leaves real body')
 displaced=Image.new('L',(800,374));displaced.paste(root,(0,25))
 if not layout._outside(displaced,body):raise ValueError('Displaced actual foundation was not rejected')
 negative.append({'control':'actual-foundation-displaced-down25','rejected':True,'actual_consumer':'scripts/faction_town_layout.py:_outside','scope':'Exact predicate only; not full public inspect or dry-support admission.'})
 changed=[p.relative_to(ROOT).as_posix() for p in held if before[p.relative_to(ROOT).as_posix()]!=sha(p)]
 if changed:raise ValueError('Canonical inputs changed during bounded checks '+str(changed))
 sources={}
 for r in selection['states']:
  for key in ('master','native_layer'):
   p=ROOT/r[key];sources[r[key]]=sha(p)
 for p in (HERE/'physical-v10').rglob('*.png'):sources[p.relative_to(ROOT).as_posix()]=sha(p)
 for p in (HERE/'trace_contacts_v9.py',HERE/'semantic_ground_points_v1.py',HERE/'finalize_candidate_v2.py',HERE/'prepare_candidate_v14.py',HERE/'repair_conversion_v1.py',Path(__file__),CANDIDATE/'selection.json',CANDIDATE/'factions.candidate.json',HERE/'physical-v10/annotations.json'):
  sources[p.relative_to(ROOT).as_posix()]=sha(p)
 result={'status':'authored configuration','converter':compiler_path.relative_to(ROOT).as_posix(),'converter_sha256':sha(compiler_path),'shared_layout_helper_sha256':sha(WORKSPACE/'scripts/faction_town_layout.py'),'actual_recipe_count':len(results),'successful_recipes':sum(r['ok'] for r in results),'failed_recipes':[r for r in results if not r['ok']],'actual_output_count':len(outputs),'decoded_state_comparisons':decoded,'actual_negatives':negative,'held_canonical_inputs':before,'changed_canonical_inputs':changed,'outputs':outputs,'results':results,'native_verified':False,'release_accepted':False}
 write(REPORT/'receipt.json',result)
 write(CANDIDATE/'integration-plan-v1.json',{'status':'authored configuration','integration_allowed':False,'reason':'Actual independently traced painted-floor/flight/street plan, strict public inspect and independent geometry admission remain pending.','candidate_selection_sha256':sha(CANDIDATE/'selection.json'),'source_pins':sources,'recipe_pins':selection['recipes'],'actual_output_pins':outputs,'conversion_receipt_sha256':sha(REPORT/'receipt.json'),'canonical_preconditions':before,'proposed_changes':['Coordinator may inspect the candidate recipes and faction full-canvas state x0/y0/z placements after geometry admission.','No content economics, structure identities, prerequisites or special effects are changed.'],'blocked_requirements':['Complete faithful ground-contact masks and exact bounded source-case reviews.','Actual painted doorway/frontage and connected street approach for all36states, including corrected Rose entrance.','Level dry support, stairs/water exclusions and actual displaced-building full-consumer negative.','A complete hash-pinned silhouette-v2 contract admitted through actual inspect().'],'native_verified':False,'release_accepted':False})
 print(json.dumps({k:result[k] for k in ('actual_recipe_count','successful_recipes','failed_recipes','actual_output_count','actual_negatives','changed_canonical_inputs')}))
 if result['failed_recipes']:raise SystemExit(2)

if __name__=='__main__':main()
