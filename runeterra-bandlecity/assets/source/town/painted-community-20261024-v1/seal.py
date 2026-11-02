"""Seal reviewable source candidate for coordinator integration; no active writes."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n',encoding='utf-8')
handoff=json.loads((HERE/'coordinator-handoff.json').read_text())
files=set();bindings=[]
for site in handoff['sites']:
    for state in site['states']:
        master=ROOT/site['source'][state];files.add(master)
        for name in ['generation.json','prompt.txt']:
            if (master.parent/name).is_file():files.add(master.parent/name)
        for name in ['layer.png','area.png','border.png','hall-icon.png','campaign.png']:files.add(HERE/'structures'/state/name)
for name in ['master.png','native.png','generation.json','prompt.txt','water-annotation.png']:files.add(HERE/'background'/name)
for path in handoff['recipe_paths']:
    source=ROOT/path;files.add(source)
    active='assets/recipes/town/'+source.relative_to(HERE/'recipes').as_posix()
    bindings.append({'candidate':path,'active':active,'sha256':sha(source)})
selection={'schema_version':1,'revision':HERE.name,'status':'authored configuration','visual_approval_granted':False,
    'sites':handoff['sites'],'terrain':handoff['terrain'],'recipe_bindings':bindings,
    'files':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)},
    'preparation_policy':'Validate entire selected closure and active recipes before writes; never replay historical hardcoded masters.'}
write(HERE/'selection.json',selection)
candidate=ROOT/'design/town-visuals-painted-community-20261024-v1.candidate.json'
design=json.loads(candidate.read_text());design['selected_sources']={'path':(HERE/'selection.json').relative_to(ROOT).as_posix(),
    'sha256':sha(HERE/'selection.json'),'terrain_master':handoff['terrain']['master'],
    'terrain_master_sha256':handoff['terrain']['master_sha256'],'terrain_native':handoff['terrain']['native'],
    'terrain_native_sha256':handoff['terrain']['native_sha256']}
write(candidate,design)
print(json.dumps({'selection_sha256':sha(HERE/'selection.json'),'selected_files':len(files),'recipe_bindings':len(bindings),'candidate_design_sha256':sha(candidate)}))
