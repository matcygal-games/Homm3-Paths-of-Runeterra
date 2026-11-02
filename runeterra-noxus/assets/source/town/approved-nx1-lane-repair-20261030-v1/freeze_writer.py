"""Final source-candidate writer release; no canonical/stage mutation."""
from pathlib import Path
import json,hashlib
import assemble_candidate as A
ROOT=A.ROOT;HERE=A.HERE;REPORT=A.REPORT
def main():
 canonical=A.read(HERE/'canonical-before-v5.json')
 drift=[name for name,pin in canonical.items()if A.sha(ROOT/name)!=pin]
 if drift:raise ValueError('Canonical changed during writer task: '+str(drift))
 checks=A.read(REPORT/'strict-source-tests.json');history=A.read(REPORT/'historical-checks.json');conversion=A.read(REPORT/'actual-conversion.json');strict=A.read(HERE/'strict-contract-v1/executed-check.json')
 assert checks['passed']and history['passed']and not strict['actual_strict_consumer_errors']and not strict['preflight_failures']
 files=set()
 for folder in ['candidate','decomposition-v5','strict-contract-v1','construction-v5','recipe-templates-v5']:
  files.update(p for p in(HERE/folder).rglob('*')if p.is_file()and'__pycache__'not in p.parts)
 files.update(p for p in HERE.iterdir()if p.is_file()and p.suffix in ('.py','.json','.txt','.png'))
 files.update(p for p in REPORT.iterdir()if p.is_file()and p.name!='writer-release.json')
 physical=HERE.parent/'approved-nx1-physical-20261030-v1';files.add(physical/'prototype_roofs.py');files.update((physical/'structures').rglob('layer.png'))
 prior=HERE.parent/'approved-nx1-finish-20261030-v1';files.add(prior/'selected/selection.json');files.add(prior/'terrain/background.png');files.add(prior/'terrain/coastal-water-mask.png')
 selected=A.read(HERE/'candidate/selection.json')
 for row in selected['states']:files.add(ROOT/row['painted_master'])
 original=HERE.parent/'approved-nx1-20261029-v1';files.add(original/'approved-master.png');files.add(original/'approved-native.png')
 pins={p.relative_to(ROOT).as_posix():A.sha(p)for p in sorted(files)}
 receipt={'status':'authored configuration','writer_released':True,'candidate_frozen_for_independent_review':True,'selection_sha256':A.sha(HERE/'candidate/selection.json'),'contract_sha256':A.sha(HERE/'strict-contract-v1/town-layout.json'),'native_full_sha256':A.sha(HERE/'decomposition-v5/full.png'),'original_approved_native_sha256':A.sha(original/'approved-native.png'),'approved_diff':selected['approved_diff'],'executed_strict_tests':checks['actual_executed_tests'],'executed_historical_tests':history['actual_executed_tests'],'actual_converted_recipes':conversion['recipes'],'actual_buffers':conversion['buffers'],'actual_consumer_sha256':checks['consumer_sha256'],'non_access_foundation_projection_cases':strict['foundation_projection_cases'],'canonical_inputs_unchanged':True,'no_shared_consumer_or_stage_or_native_modified':True,'pins':pins,'next':'Independent review; coordinator selection through integrate-v5.py only after GO. Native and final human/rights acceptance remain pending.'}
 A.write(REPORT/'writer-release.json',receipt);print(json.dumps({k:v for k,v in receipt.items()if k not in ('pins','approved_diff')},indent=2));print('writer-release SHA256',A.sha(REPORT/'writer-release.json'))
if __name__=='__main__':main()
