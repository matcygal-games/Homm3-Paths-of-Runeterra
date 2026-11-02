"""Freeze review-only selection; does not select active production inputs."""
from pathlib import Path
import json,hashlib,importlib.util
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];REPORT=ROOT/'build/reports/painted-town-community-20261024-v1'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()
def write(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def main():
 d=read(ROOT/'design/town-visuals-painted-community-20261024-v1.candidate.json');inputs=set()
 for r in d['states']:inputs.update([r['master'],r['provenance']])
 for p in (HERE/'background').iterdir():
  if p.is_file() and p.name not in ['water-annotation.png','buildable-floor-annotation.png']:inputs.add(rel(p))
 for b in d['recipe_bindings']:inputs.add(b['active'])
 inputs.update(['design/town-visuals.json','assets/source/town/chemtech-v4-buildings/selection.json','scripts/zaun_painted_town.py','scripts/zaun_coastal_state_v1.py'])
 for p in HERE.glob('*.py'):inputs.add(rel(p))
 pins={name:sha(ROOT/name) for name in sorted(inputs)}
 write(HERE/'preflight-selection.json',{'status':'authored configuration','inputs':pins,'rule':'Every selected master, provenance, helper and original template pin is checked before any prepare writes; parent integration intentionally invalidates original-template replay.'})
 files={rel(p):sha(p) for p in sorted(HERE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name!='selection.json'}
 selected={'status':'authored configuration','revision':HERE.name,'selected_background':'background/master-v3.png','selected_background_sha256':sha(HERE/'background/master-v3.png'),'candidate_design':rel(ROOT/'design/town-visuals-painted-community-20261024-v1.candidate.json'),'candidate_design_sha256':sha(ROOT/'design/town-visuals-painted-community-20261024-v1.candidate.json'),'site_count':20,'state_count':36,'active_recipe_binding_count':len(d['recipe_bindings']),'states':d['states'],'recipe_bindings':d['recipe_bindings'],'source_file_sha256':files,'external_input_sha256':pins,'shared_converter':{'path':'../scripts/faction_artifacts.py','sha256':sha(ROOT.parent/'scripts/faction_artifacts.py')},'no_active_selection_performed':True,'visual_approval_granted':False,'runtime_verified':False,'release_accepted':False}
 write(HERE/'selection.json',selected)
 spec=importlib.util.spec_from_file_location('candidate_prepare',HERE/'prepare.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 m.preflight();mutated=dict(pins);name=d['states'][0]['master'];mutated[name]='0'*64
 rejected=False
 try:m.preflight(mutated)
 except ValueError:rejected=True
 marker={rel(p):sha(p) for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
 original=m.load
 def bad_load(p):
  value=original(p)
  if p==HERE/'preflight-selection.json':value=dict(value);value['inputs']=mutated
  return value
 m.load=bad_load;source_plan_rejected=False
 try:m.source_plan()
 except ValueError:source_plan_rejected=True
 after={rel(p):sha(p) for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
 result={'ok':rejected and source_plan_rejected and marker==after,'master_pin_mismatch_rejected':rejected,'actual_source_plan_rejected_before_writes':source_plan_rejected,'source_bytes_unchanged':marker==after,'selection_sha256':sha(HERE/'selection.json'),'selected_background_sha256':selected['selected_background_sha256'],'candidate_design_sha256':selected['candidate_design_sha256'],'pinned_source_file_count':len(files),'input_count':len(pins),'visual_approval_granted':False}
 write(REPORT/'seal-and-preflight-validation.json',result);print(json.dumps(result));return 0 if result['ok'] else 2
if __name__=='__main__':raise SystemExit(main())
