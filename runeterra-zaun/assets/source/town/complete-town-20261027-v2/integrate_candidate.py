"""Coordinator-only reviewed candidate integration; default is read-only check.

Does not convert, stage, build, launch, install or publish. Active sources must
still match the sealed preconditions. --apply is for the coordinator to invoke.
"""
from pathlib import Path
import argparse,copy,hashlib,json,shutil
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];REPORT=ROOT/'build/reports/complete-town-20261027-v2'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--apply',action='store_true');args=ap.parse_args()
 seal=read(HERE/'integration-manifest.json')
 for name,pin in seal['candidate_files'].items():
  if not (ROOT/name).is_file() or sha(ROOT/name)!=pin:raise SystemExit('Candidate missing/changed: '+name)
 for name,pin in seal['active_preconditions'].items():
  if not (ROOT/name).is_file() or sha(ROOT/name)!=pin:raise SystemExit('Active input changed; root must review/reseal: '+name)
 for name,pin in seal['tool_preconditions'].items():
  if sha(ROOT.parent/name)!=pin:raise SystemExit('Shared consumer changed: '+name)
 selection=read(HERE/'selection.json');geometry=read(REPORT/'geometry-checks.json');negatives=read(REPORT/'actual-negative-checks.json')
 if not geometry['ok'] or not geometry['identical_outputs'] or not all(c['passed'] for c in negatives['checks']):raise SystemExit('Candidate execution evidence fails')
 bindings=selection['recipe_bindings'];factions=read(ROOT/'content/factions.json');before=copy.deepcopy(factions)
 for state,z in read(HERE/'content-z-patch.json')['values'].items():factions['zaun']['town']['structures'][state]['z']=z
 for state,z in read(HERE/'content-z-patch.json')['values'].items():before['zaun']['town']['structures'][state]['z']=z
 if before!=factions:raise AssertionError('Unexpected faction data mutation')
 summary={'status':'authored configuration','seal_sha256':sha(HERE/'integration-manifest.json'),'recipe_bindings':len(bindings),'output_count':geometry['output_count'],'coordinator_physical_review':'required; this script does not grant it','canonical_changes_applied':False,'stage_built':False,'native_verified':False,'release_accepted':False}
 if args.apply:
  backup=REPORT/'coordinator-integration-backup'/summary['seal_sha256']
  if backup.exists():raise SystemExit('Preserve existing backup; integration already attempted for this seal')
  for name in seal['active_preconditions']:
   target=backup/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
  for row in bindings:shutil.copy2(ROOT/row['candidate'],ROOT/row['active'])
  shutil.copy2(HERE/'town-visuals.candidate.json',ROOT/'design/town-visuals.json');write(ROOT/'content/factions.json',factions)
  summary['canonical_changes_applied']=True;write(REPORT/('coordinator-integration-'+summary['seal_sha256'][:16]+'.json'),summary)
 print(json.dumps(summary,sort_keys=True))
if __name__=='__main__':main()
