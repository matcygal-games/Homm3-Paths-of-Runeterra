"""Bind reviewed native side-camera frames to the shared addon-only preview route.

The source faction retains its strict original creature schema. Only the tested
combined runtime addon receives animationPreview. This step filters descriptor
groups and adds explicit portable dependencies, without altering source pixels.
"""
import copy
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
P=next(p for p in HERE.parents if (p/'content/creatures.json').is_file())
GROUPS={0,1,2,3,4,12,18,20,21}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(P).as_posix()
def load(p):return json.loads(p.read_bytes())
def put(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n',encoding='utf-8')

def main():
    out=HERE/'preview-binding-v1'
    records={}
    for unit in ('shoreLeviathan','elderShoreLeviathan'):
        source=HERE/f'candidate-v2/{unit}/recipes/preview.json'
        preview=load(source)
        preview['groups']=[g for g in preview['groups'] if g['group'] in GROUPS]
        preview['output_path']=f'Content/Sprites/runeterra/bilgewater/creatures/{unit}/preview.json'
        for group in preview['groups']:
            for frame in group['frames']:
                frame['sha256']=frame['source_sha256']
        target=out/unit/'preview.json'
        put(target,preview)
        deps=[{'path':rel(source),'sha256':sha(source)},
              {'path':rel(Path(__file__)),'sha256':sha(Path(__file__))},
              {'path':rel(target),'sha256':sha(target)}]
        deps.extend({'path':f['source'],'sha256':f['source_sha256']} for g in preview['groups'] for f in g['frames'])
        battle=load(HERE/f'candidate-v2/{unit}/recipes/battle.json')
        byname={d['path']:d for d in battle['generation']['production_inputs']+deps}
        battle['generation']['production_inputs']=[byname[k] for k in sorted(byname)]
        final=out/unit/'battle.json'
        put(final,battle)
        records[unit]={'recipe':{'path':rel(target),'sha256':sha(target)},
                       'battle_recipe':{'path':f'assets/recipes/creatures/{unit}-battle.json','sha256':sha(final)}}
    put(out/'ui-preview-cameras.json',{'schema':1,'purpose':'native-fixed-ui-camera-v1','units':records})
    print(json.dumps(records,indent=2))

if __name__=='__main__':main()
