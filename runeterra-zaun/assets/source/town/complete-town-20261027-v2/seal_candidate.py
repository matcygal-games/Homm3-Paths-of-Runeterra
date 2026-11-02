"""Seal resumable source candidate and coordinator preconditions; no integration."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];REPORT=ROOT/'build/reports/complete-town-20261027-v2'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def main():
 selection=read(HERE/'selection.json');geometry=read(REPORT/'geometry-checks.json');checks=read(REPORT/'actual-negative-checks.json')
 if not geometry['ok'] or not geometry['identical_outputs'] or not all(c['passed'] for c in checks['checks']):raise SystemExit('Cannot seal failed execution checks')
 source_checks=[]
 from PIL import Image
 import numpy as np
 plan=read(HERE/'derived-state-plan.json');master=np.asarray(Image.open(HERE/'complete-design/native-v2.png').convert('RGBA'))
 for family in read(HERE/'family-specs.json')['families']:
  state=family['states'][-1];row=next(r for r in plan['states'] if r['state']==state);mask=np.asarray(Image.open(ROOT/row['visible_master_mask']))>0;layer=np.asarray(Image.open(ROOT/row['native_layer']).convert('RGBA'))
  if not np.array_equal(layer[mask,:3],master[mask,:3]):raise SystemExit('Developed visible master pixels changed: '+state)
  source_checks.append({'state':state,'exact_visible_master_rgb_pixels':int(mask.sum()),'equal':True})
 write(REPORT/'source-rgb-checks.json',{'status':'authored configuration','master_sha256':sha(HERE/'complete-design/native-v2.png'),'checks':source_checks,'states_compared':len(source_checks),'native_verified':False,'release_accepted':False})
 review={'status':'authored configuration','whole_master_sha256':sha(HERE/'complete-design/native-v2.png'),'whole_master_checkpoint':read(HERE/'complete-design/review-checkpoint.json')['root_review'],'source_scope':'All36 native layers, base/upgraded/mixed and independent workshop/clinic/pressure-cell removals, explicit full contact polylines and visible entrance anchors. Genuine whole-master RGB cuts plus new painted2D lower/hidden faces; no V1 body fallback.','actual_converters':geometry,'actual_negative_checks':'actual-negative-checks.json','original_reference':'Private read-only original Castle tbcscas3/g00-f000.png inspected at native322x211; HoMM3 painted oblique architecture/material/native pixel detail authority. No original pixels enter own art.','coordinator_physical_review':'pending updated full-contact/threshold/7projection review','independent_review':'pending final candidate review','native_visual_review':'pending fresh coordinator integration/stage','human_art_approval':False,'rights_approval':False,'release_accepted':False}
 write(REPORT/'SOURCE_REVIEW.json',review)
 files={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(HERE.rglob('*')) if p.is_file() and p.name!='integration-manifest.json' and '__pycache__' not in p.parts}
 for name in ('geometry-checks.json','actual-negative-checks.json','source-rgb-checks.json','SOURCE_REVIEW.json','all-state-root-review.json'):
  p=REPORT/name;files[p.relative_to(ROOT).as_posix()]=sha(p)
 active={row['active']:sha(ROOT/row['active']) for row in selection['recipe_bindings']}
 for name in ('design/town-visuals.json','content/factions.json'):active[name]=sha(ROOT/name)
 tools={name:sha(ROOT.parent/name) for name in ('scripts/faction_town_layout.py','scripts/faction_artifacts.py')}
 seal={'status':'authored configuration','candidate_files':files,'active_preconditions':active,'tool_preconditions':tools,'active_integration':False,'physical_source_review_pending':True,'native_verified':False,'release_accepted':False}
 write(HERE/'integration-manifest.json',seal)
 pins={name:sha(HERE/name) for name in ('integration-manifest.json','selection.json','town-layout.json','contact_traces.py','town-visuals.candidate.json','content-z-patch.json','integrate_candidate.py')}
 write(REPORT/'FINAL-CANDIDATE-PINS.json',{'status':'authored configuration','pins':pins,'recipe_bindings':len(selection['recipe_bindings']),'compiled_outputs':geometry['output_count'],'converter_runs':2,'actual_checks_passed':checks['checks_passed'],'root_cases':len(read(HERE/'town-layout.json')['silhouette_plan']['foundation_occlusions']),'master_rgb_states_checked':len(source_checks),'coordinator_visual_review':'pending','native_verified':False,'release_accepted':False})
 print(json.dumps(pins,sort_keys=True))
if __name__=='__main__':main()
