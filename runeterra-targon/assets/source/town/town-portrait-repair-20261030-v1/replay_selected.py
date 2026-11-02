"""Reproduce current TG1 scene plus repaired scenic portrait derivatives."""
from pathlib import Path
import hashlib,json,subprocess,sys
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[3];WORKSPACE=PROJECT.parent
def main():
    subprocess.run([sys.executable,'-B',str(HERE/'derive_portraits.py')],check=True)
    subprocess.run([sys.executable,'-B',str(PROJECT/'assets/source/town/approved-tg1-integration-20261030-v3/replay_source.py')],check=True)
    sys.path.insert(0,str(WORKSPACE/'scripts'))
    from faction_art_compile import create_compiler
    compiler=create_compiler('targon')
    expected=json.loads((HERE/'expected-portrait-pins.json').read_bytes())
    actual={}
    for path in sorted((PROJECT/'assets/recipes/town/icons').glob('*.json')):
        outputs,_=compiler.plan(PROJECT,path);actual.update({name:hashlib.sha256(raw).hexdigest()for name,raw in outputs.items()})
    if actual!=expected:raise ValueError('Repaired scenic portrait replay differs')
    print(json.dumps({'status':'authored configuration','portrait_outputs':len(actual),'native_TG1_scene_preserved':True}))
if __name__=='__main__':main()
