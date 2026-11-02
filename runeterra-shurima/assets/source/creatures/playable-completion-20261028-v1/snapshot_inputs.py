"""Freeze genuine technical input recipes before coordinator selection changes."""
from pathlib import Path
import shutil,json,hashlib
S=Path(__file__).resolve().parent;P=S.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
for path in sorted((S/'recipe-payload').rglob('*.json')):
 target=S/'inputs/technical-recipes'/path.relative_to(S/'recipe-payload');target.parent.mkdir(parents=True,exist_ok=True)
 if target.exists() and target.read_bytes()!=path.read_bytes():raise RuntimeError('Frozen input already exists with different bytes: '+str(target))
 if not target.exists():shutil.copyfile(path,target)
 rows.append({'source':target.relative_to(P).as_posix(),'source_sha256':sha(target),'prior_path':path.relative_to(P).as_posix()})
extra={'ruinRunner-battle':P/'build/reports/painted-runners-production-20261024-v1/recipe-overlays/ruinRunner/battle.json','rockbear-battle':P/'build/reports/painted-rockbear-actions-20261023-v1/recipe-payload/rockbear/battle.json','shurimanArcher-battle':P/'assets/recipes/creatures/painted-v3/shurimanArcher/battle.json'}
for name,path in extra.items():
 target=S/'inputs/historical-2d-recipes'/(name+'.json');target.parent.mkdir(parents=True,exist_ok=True)
 if not target.exists():shutil.copyfile(path,target)
 elif target.read_bytes()!=path.read_bytes():raise RuntimeError('Changed frozen historical2D input')
 rows.append({'source':target.relative_to(P).as_posix(),'source_sha256':sha(target),'prior_path':path.relative_to(P).as_posix()})
target=S/'inputs/input-pins-v1.json';target.write_text(json.dumps({'status':'authored configuration','inputs':rows},indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({'frozen_inputs':len(rows),'input_pins_sha256':sha(target)}))
