"""Coordinator-only pinned integration. Default is read-only verification.

This worker never invokes --apply. It does not build, stage, run or publish.
"""
from pathlib import Path
import argparse,hashlib,json,shutil
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[5]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def execute(apply=False):
    plan=read(HERE/'plan.json')
    assert digest(Path(__file__))==plan['integrator_sha256'],'Integrator differs from frozen plan'
    assert digest(PROJECT.parent/'scripts/faction_town_layout.py')==plan['shared_geometry_helper_sha256'],'Shared helper drift'
    receipt=PROJECT/plan['verification_receipt']['path']
    assert digest(receipt)==plan['verification_receipt']['sha256'],'Executed verification changed'
    verification=read(receipt)
    assert all(verification[k] for k in ['conversion_ok','readonly_converter_ok','layout_ok','source_export_exact','source_export_helper_exact','restored_layout_ok'])
    assert verification['root_case_scenes_ok'] and verification['grail_case_regression_negative']['passed']
    assert all(r['passed'] for r in verification['converter_negatives']+verification['geometry_negatives'])
    for name,sha in plan['source_inventory'].items():assert digest(PROJECT/name)==sha,'Changed source: '+name
    pending=[]
    for row in plan['changes']:
        source=PROJECT/row['source'];target=PROJECT/row['destination']
        assert source.resolve().is_relative_to((PROJECT/'assets/source/town/complete-town-20261027-v2').resolve())
        assert target.resolve().is_relative_to(PROJECT.resolve())
        assert digest(source)==row['after_sha256']
        actual=digest(target) if target.is_file() else None
        assert actual in (row['before_sha256'],row['after_sha256']),'Changed canonical destination: '+row['destination']
        if actual!=row['after_sha256']:pending.append((source,target))
    if apply:
        for source,target in pending:
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    print(json.dumps({'status':'authored configuration','coordinator_apply_executed':apply,'pending_canonical_files':len(pending),'build_stage_native_publication_executed':False,'release_accepted':False},sort_keys=True))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args();execute(args.apply)
