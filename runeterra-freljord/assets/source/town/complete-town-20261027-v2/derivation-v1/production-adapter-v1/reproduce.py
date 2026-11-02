"""Execute unchanged actual CLI in a complete isolated workspace copy.

Only assets/validate commands are used; no staging/build/native/publication.
Copies are direct files, not aliases to live canonical writable paths.
"""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,time
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[5];WORKSPACE=PROJECT.parent
REPORT=PROJECT/'build/reports/complete-town-20261027-v2/production-adapter-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def main():
    attempt=REPORT/('actual-cli-%03d'%(1+len(list(REPORT.glob('actual-cli-*')))));attempt.mkdir(parents=True,exist_ok=False)
    workspace=attempt/'workspace';project=workspace/'runeterra-freljord'
    ignore=shutil.ignore_patterns('__pycache__','.pytest_cache')
    for folder in ('assets','content','design','scripts','docs','tests'):
        shutil.copytree(PROJECT/folder,project/folder,ignore=ignore)
    for p in PROJECT.iterdir():
        if p.is_file():shutil.copyfile(p,project/p.name)
    for p in (PROJECT/'review').rglob('*.json'):
        dst=project/p.relative_to(PROJECT);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst)
    shutil.copytree(WORKSPACE/'scripts',workspace/'scripts',ignore=ignore)
    shutil.copytree(WORKSPACE/'runeterra-demacia/scripts',workspace/'runeterra-demacia/scripts',ignore=ignore)
    shutil.copytree(WORKSPACE/'vcmi-develop/vcmi-develop/config',workspace/'vcmi-develop/vcmi-develop/config',ignore=ignore)
    for p in WORKSPACE.iterdir():
        if p.is_file() and p.suffix in ('.txt','.md'):shutil.copyfile(p,workspace/p.name)
    proposal=read(HERE/'proposal.json')
    for row in proposal['actions']:
        target=project/row['destination'];assert sha(target)==row['before_sha256']
        if row['operation']=='delete':target.unlink()
        else:shutil.copyfile(PROJECT/row['source'],target)
    # Cold town cache: actual indexed compiler may consume no generated icon
    # or stale town PNG. Other categories retain matching canonical own assets.
    town=project/'assets/generated/Content/Sprites/runeterra/freljord/town'
    assert town.resolve().is_relative_to(project.resolve())
    if town.exists():shutil.rmtree(town)
    commands=[]
    for args in (['--faction','freljord','assets','--resume'],['--faction','freljord','validate']):
        command=[sys.executable,str(workspace/'scripts/runeterra.py'),*args];started=time.time()
        result=subprocess.run(command,cwd=workspace,capture_output=True)
        label='assets'if'assets'in args else'validate';stdout=attempt/(label+'.stdout.log');stderr=attempt/(label+'.stderr.log');stdout.write_bytes(result.stdout);stderr.write_bytes(result.stderr)
        commands.append({'command':command,'exit_code':result.returncode,'elapsed_seconds':round(time.time()-started,3),'stdout_sha256':sha(stdout),'stderr_sha256':sha(stderr)})
    v={'scope':'Unchanged actual scripts/runeterra.py CLI dispatch with full current regional content, recipes, manifest and source closure, cold town cache','commands':commands,'canonical_changed':False,'build_stage_native_executed':False,'proposal_sha256':sha(HERE/'proposal.json'),'workspace':str(workspace)}
    for name in ('assets-validation','validation'):
        p=project/'build/reports'/(name+'.json')
        if p.exists():
            value=read(p);write(attempt/(name+'.json'),value);v[name]={'ok':value['ok'],'errors':value['errors'],'error_count':len(value['errors'])}
    write(attempt/'EXECUTION.json',v)
    print(json.dumps({**v,'assets-validation':v.get('assets-validation',{}),'validation':v.get('validation',{})},indent=2))
if __name__=='__main__':main()
