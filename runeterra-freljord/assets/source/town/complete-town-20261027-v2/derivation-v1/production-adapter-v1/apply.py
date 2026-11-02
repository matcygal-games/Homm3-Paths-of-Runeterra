"""Coordinator-only exact payload apply. Default is read-only checking."""
from pathlib import Path
import argparse,hashlib,json,shutil
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[5];WORKSPACE=PROJECT.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main(apply=False):
    packet=read(HERE/'packet.json');assert sha(Path(__file__))==packet['applier_sha256']
    assert packet['actual_cli_assets']['exit_code']==0
    for name,digest in packet['actual_cli_code_sha256'].items():assert sha(WORKSPACE/'scripts'/name)==digest,'Consumer code drift: '+name
    ref=packet['reviewed_physical_contract'];assert sha(PROJECT/ref['path'])==ref['sha256']
    for name,digest in packet['source_pins'].items():assert sha(PROJECT/name)==digest,'Candidate source drift: '+name
    pending=[]
    for row in packet['actions']:
        name=row['destination'];target=PROJECT/name
        assert name=='assets/manifest.json' or name.startswith('assets/recipes/town/') and name.endswith('.json')
        assert target.resolve()==target.absolute() and target.resolve().is_relative_to(PROJECT.resolve())
        if target.exists():assert target.stat().st_nlink==1 and not target.is_symlink()
        actual=sha(target)if target.is_file()else None
        if row['operation']=='delete':
            assert name.startswith('assets/recipes/town/icons/') and actual in (None,row['before_sha256'])
            if actual is not None:pending.append((row,None,target))
        else:
            source=PROJECT/row['source'];assert sha(source)==row['after_sha256']
            assert actual in (row['before_sha256'],row['after_sha256']),'Canonical payload drift: '+name
            if actual!=row['after_sha256']:pending.append((row,source,target))
    if apply:
        for row,source,target in pending:
            if row['operation']=='delete':target.unlink()
            else:shutil.copyfile(source,target)
    print(json.dumps({'read_only':not apply,'coordinator_applied':apply,'pending_guarded_actions':len(pending),'build_stage_native_executed':False,'release_accepted':False},sort_keys=True))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args();main(args.apply)
