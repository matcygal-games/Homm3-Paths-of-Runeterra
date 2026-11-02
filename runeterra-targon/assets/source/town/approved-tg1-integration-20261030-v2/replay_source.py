"""Reproduce selected TG1 artwork/native bytes without stages or3D."""
from pathlib import Path
import hashlib,json,subprocess,sys

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
WORKSPACE=PROJECT.parent

def main():
    selected=HERE.parent/'approved-tg1-implementation-20261030-v19'
    for name in ('assemble_source.py',):
        subprocess.run([sys.executable,'-B','-W','error',str(selected/name)],check=True)
    sys.path.insert(0,str(WORKSPACE/'scripts'))
    from faction_art_compile import create_compiler
    compiler=create_compiler('targon')
    ledger=json.loads((PROJECT/'assets/production/source-export.json').read_bytes())['painted_town_sources']
    outputs={}
    for name,pin in sorted(ledger['canonical_recipes'].items()):
        path=PROJECT/name
        if hashlib.sha256(path.read_bytes()).hexdigest()!=pin:raise ValueError('Canonical recipe changed: '+name)
        native,_=compiler.plan(PROJECT,path)
        if native.keys()&outputs.keys():raise ValueError('Duplicate native town producer')
        outputs.update(native)
    expected=json.loads((selected/'candidate-selection-final.json').read_bytes())['native_output_pins']
    if any(hashlib.sha256(outputs[name]).hexdigest()!=pin for name,pin in expected.items()):
        raise ValueError('Replayed canonical output differs from reviewed TG1')
    print(json.dumps({'status':'authored configuration','canonical_recipes':len(ledger['canonical_recipes']),
      'native_outputs':len(outputs),'reviewed_TG1_outputs':len(expected),'staging_or_game_writes':False}))

if __name__=='__main__':main()
