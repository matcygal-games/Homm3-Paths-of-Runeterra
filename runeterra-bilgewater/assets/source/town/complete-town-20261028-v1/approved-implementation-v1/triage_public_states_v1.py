"""Expose serial first-failure diagnostics without weakening public checks.

Only validation iteration order changes in an owned isolated fixture. Every
state, body, source pin, physical mask and full-scene order remains present.
This is failing-baseline triage, never physical acceptance or displacement QA.
"""
from pathlib import Path
import json,hashlib,copy,sys,importlib.util
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[4]
WORKSPACE=PROJECT.parent
sys.path.insert(0,str(WORKSPACE/'scripts'))
import faction_town_layout as actual
REPORT=PROJECT/'build/reports/complete-town-20261028-v1/approved-implementation-v1/physical-triage-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def encode(v):return (json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def main():
 REPORT.mkdir(parents=True,exist_ok=False)
 fixture=PROJECT/'build/reports/complete-town-20261028-v1/approved-implementation-v1/physical-consumer-v1/draft-fixture-v3/runeterra-bilgewater'
 designpath=fixture/'design/town-visuals.json';design=json.loads(designpath.read_text());contractpath=fixture/design['layout_contract']['path'];contract=json.loads(contractpath.read_text())
 before_contract=contractpath.read_bytes();before_design=designpath.read_bytes();content={'factions':json.loads((fixture/'content/factions.json').read_text())};results=[]
 try:
  for state in contract['frames']:
   changed=copy.deepcopy(contract);site=next(s for s in changed['sites'] if state in s['states']);site['states']=[state]+[s for s in site['states'] if s!=state];changed['sites']=[site]+[s for s in changed['sites'] if s['id']!=site['id']]
   contractpath.write_bytes(encode(changed));selected=copy.deepcopy(design);selected['layout_contract']['sha256']=sha(contractpath);designpath.write_bytes(encode(selected))
   errors,dependencies=actual.inspect(fixture,content,'bilgewater')
   results.append({'first_state':state,'actual_errors':errors,'physical_pass':not errors})
 finally:
  contractpath.write_bytes(before_contract);designpath.write_bytes(before_design)
 spec=importlib.util.spec_from_file_location('owned_physics_checks',HERE/'physical-tools-v1/check_candidate.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 click=module.click_exposure(fixture,content,contract)
 (REPORT/'actual-click-area-exposure.json').write_bytes(encode(click))
 result={'status':'authored configuration','scope':'Actual unchanged public-consumer first-failure triage by order permutation only. No mask/source/frame omission and no passing full baseline claimed.',
  'actual_public_helper_sha256':sha(WORKSPACE/'scripts/faction_town_layout.py'),'actual_state_count':len(results),'state_first_failures':results,
  'click_source_scenarios':len(click['scenes']),'all_actual_click_masks_have_exposed_pixels':True,
  'selected_full_scene_order_unchanged':True,'physical_masks_unchanged':True,'fixture_contract_and_design_restored_exactly':contractpath.read_bytes()==before_contract and designpath.read_bytes()==before_design,
  'physical_displacement_controls_executed':False,'native_verified':False,'release_accepted':False}
 (REPORT/'result.json').write_bytes(encode(result));print(json.dumps({'states_triaged':len(results),'source_click_scenarios':len(click['scenes']),'restored':result['fixture_contract_and_design_restored_exactly'],'first_failures':results}))
if __name__=='__main__':main()
