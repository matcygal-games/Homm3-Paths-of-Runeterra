"""Actual converter/public layout consumer in a direct isolated source fixture.

No staging/build/native launch or canonical input mutation. An attempt is an
immutable report directory; use a new --attempt after source corrections.
"""
from pathlib import Path
from copy import deepcopy
import argparse,hashlib,importlib.util,json,shutil,sys
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];WORKSPACE=ROOT.parent
sys.path.insert(0,str(WORKSPACE/'scripts'))
import faction_town_layout as admission
import faction_pipeline as fp
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf8')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--attempt',required=True);ap.add_argument('--contract',default='geometry-final-v1/town-layout.json');args=ap.parse_args()
 if not args.attempt.replace('-','').isalnum():raise ValueError('Simple unique report attempt required')
 report=ROOT/'build/reports/complete-town-20261027-v2'/('consumer-'+args.attempt)
 if report.exists():raise ValueError('Preserve previous executed evidence; choose a new attempt')
 fixture=report/'direct-source-fixture';fixture.mkdir(parents=True);candidate=HERE/'candidate-final-v3';selection=load(candidate/'selection.json');factions=load(candidate/'factions.candidate.json');contract_path=HERE/args.contract;contract=load(contract_path);name=contract_path.relative_to(ROOT).as_posix();pins={};copied={}
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
 def inspect_negative(label,mutator,expected=None):
  changed={};c=deepcopy(contract)
  def put(path,b):
   if path not in changed:changed[path]=path.read_bytes()
   path.write_bytes(b)
  def store_json(path,value):put(path,(json.dumps(value,indent=2)+'\n').encode())
  def image_move(reference,dx,dy):
   path=fixture/reference['path'];im=Image.open(path);moved=Image.new(im.mode,im.size);moved.paste(im,(dx,dy));import io;stream=io.BytesIO();moved.save(stream,format='PNG',compress_level=9);put(path,stream.getvalue());reference['sha256']=sha(path)
  try:
   mutator(c,put,store_json,image_move)
   store_json(fixture/name,c);d=deepcopy(design);d['layout_contract']['sha256']=sha(fixture/name);store_json(fixture/'design/town-visuals.json',d)
   observed,_=admission.inspect(fixture,content,'noxus')
   passed=bool(observed) and (expected is None or any(expected.lower()in e.lower()for e in observed));negative.append({'control':label,'passed':passed,'actual_consumer':'scripts/faction_town_layout.py:inspect','errors':observed})
   if not passed:raise ValueError('Actual public consumer accepted/misdiagnosed negative '+label)
  finally:
   for path,b in changed.items():path.write_bytes(b)
 def missing_approval(c,put,store_json,image_move):c['silhouette_plan']['foundation_occlusions']=[]
 def stale_bytes(c,put,store_json,image_move):
  ref=c['silhouette_plan']['states']['special1']['foundation_mask'];path=fixture/ref['path'];im=Image.open(path).convert('L');im.putpixel((0,0),255);import io;s=io.BytesIO();im.save(s,format='PNG');put(path,s.getvalue())
 def shifted_approval(c,put,store_json,image_move):image_move(c['silhouette_plan']['foundation_occlusions'][0]['mask'],1,0)
 def displaced_building(c,put,store_json,image_move):
  state='special1';dx,dy=252,87;image_move(c['frames'][state],dx,dy);r=c['silhouette_plan']['states'][state]
  for key in ('foundation_mask','body_mask','door_mask','approach_mask'):image_move(r[key],dx,dy)
  r['entrance']=[r['entrance'][0]+dx,r['entrance'][1]+dy]
  site=next(s for s in c['sites'] if state in s['states']);site['box'][0]+=dx;site['box'][1]+=dy;site['entrance']=[site['entrance'][0]+dx,site['entrance'][1]+dy];image_move(site['silhouette_mask'],dx,dy)
  structure=factions['noxus']['town']['structures'][state];definition=load(fixture/'assets/generated/Content/Sprites'/structure['animation']);groups=fp.utility('identity').animation_groups(definition,complete=True);selected=fixture/'assets/generated/Content/Sprites'/(definition.get('basepath','')+groups[0][0]);put(selected,(fixture/c['frames'][state]['path']).read_bytes())
 if not errors:
  inspect_negative('remove-all-foundation-projection-approvals',missing_approval,'foundation')
  inspect_negative('actual-source-mask-byte-mutation-old-pin',stale_bytes,'missing or changed')
  inspect_negative('actual-approval-mask-shifted-one-pixel',shifted_approval)
  inspect_negative('actual-building-and-physical-masks-displaced-onto-other-terrace-stairs',displaced_building,'foundation')
  restored,_=admission.inspect(fixture,content,'noxus')
  if restored:raise ValueError('Negative restoration failed '+str(restored))
 result={'status':'authored configuration','ok':not errors,'geometry_errors':errors,'actual_recipe_count':len(converted),'actual_output_count':len(outputs),'outputs':outputs,'actual_public_consumer':str((WORKSPACE/'scripts/faction_town_layout.py').relative_to(WORKSPACE)),'helper_sha256':sha(WORKSPACE/'scripts/faction_town_layout.py'),'contract_path':name,'contract_sha256':sha(contract_path),'candidate_selection_sha256':sha(candidate/'selection.json'),'direct_source_dependency_count':len(dependencies),'copied_source_pins':copied,'actual_negative_checks':negative,'negative_checks_run':bool(negative),'complete_runtime_or_visual_acceptance':False,'canonical_inputs_modified':False,'stage_built':False,'native_verified':False,'release_accepted':False};write(report/'receipt.json',result);print(json.dumps({k:result[k]for k in ('ok','geometry_errors','actual_recipe_count','actual_output_count','actual_negative_checks','direct_source_dependency_count')}))
 if errors:raise SystemExit(2)
if __name__=='__main__':main()
