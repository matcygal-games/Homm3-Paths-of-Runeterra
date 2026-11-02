"""One-time numeric contract extraction. Never reads historical sprite pixels."""
from pathlib import Path
import hashlib,json
SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[4]
REPORT=PROJECT/'build/reports/ionia-revision-20261025-v1/t3-art'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
guards={}; contracts={}
for unit in ('vastayanScout','vastayanWarrior'):
 for role in ('battle','map','large','small','attackLeft','attackRight'):
  p=PROJECT/f'assets/recipes/creatures/{unit}-{role}.json';r=json.loads(p.read_text());guards[p.relative_to(PROJECT).as_posix()]=sha(p)
  template={k:r[k] for k in ('recipe_type','output_path','canvas','size','pivot','generateOverlay','generateShadow') if k in r}
  if 'groups' in r:template['groups']=[{'group':g['group'],'frame_count':len(g['frames'])} for g in r['groups']]
  template.update({'unit':unit,'role':role,'scope':'Numeric native contract only. All prior visual lineage intentionally absent.'})
  contracts[f'{unit}/{role}']=template
for role in ('towerLarge','towerSmall'):
 p=PROJECT/f'assets/recipes/siege/{role}.png.json';r=json.loads(p.read_text());guards[p.relative_to(PROJECT).as_posix()]=sha(p)
 contracts[f'siege/{role}']={k:r[k] for k in ('recipe_type','output_path','canvas','size') if k in r}
 contracts[f'siege/{role}']['role']=role
write(SOURCE/'native-contracts-v1.json',contracts)
write(REPORT/'old-live-recipe-hashes-v1.json',{'scope':'Historical recipe bytes only. Not input to painted producer. Coordinator controls live hashes.','sha256':guards})
print(json.dumps({'contracts':len(contracts),'live_recipe_hashes':len(guards),'source_contracts_sha256':sha(SOURCE/'native-contracts-v1.json')}))
