"""Portable technical tower binding from frozen selected own knife portraits."""
from pathlib import Path
from copy import deepcopy
import json,hashlib
SELF=Path(__file__).resolve();S=SELF.parent
P=next(p for p in SELF.parents if p.name=='runeterra-noxus')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(P).as_posix()
def load(p):return json.loads(p.read_text(encoding='utf8'))
def put(p,d):
 b=(json.dumps(d,indent=2,sort_keys=True)+'\n').encode('utf8');p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists() and p.read_bytes()!=b:raise ValueError('Preserve changed candidate/version it: '+rel(p))
 p.write_bytes(b)
def walk(v):
 if isinstance(v,dict):
  for x in v.values():yield from walk(x)
 elif isinstance(v,list):
  for x in v:yield from walk(x)
 else:yield v
def main():
 contract_path=S/'binding-contract-v1.json';c=load(contract_path)
 assert c['configured_shooter']=='guildKnifeThrower' and len(c['rows'])==2
 inputs={rel(SELF):sha(SELF),rel(contract_path):sha(contract_path)}
 originals=[]
 for row in c['rows']:
  pin=row['selected_portrait_template'];p=P/pin['path'];assert sha(p)==pin['sha256']
  template=load(p);inputs[rel(p)]=sha(p);originals.append((row,template))
  for value in walk(template):
   if isinstance(value,str) and value.startswith('assets/source/'):
    source=(P/value).resolve();assert source.is_relative_to((P/'assets/source').resolve()) and source.is_file(),value
    inputs[rel(source)]=sha(source)
 recipes=[]
 for row,template in originals:
  role=row['role'];expected=[58,64]if role=='large'else[32,32]
  assert template.get('unit')=='guildKnifeThrower' and template['size']==expected and row['native_size']==expected
  fresh=deepcopy(template)
  fresh.update(output_path=row['output_path'],role='siege-image',shooter='guildKnifeThrower',
    id='noxus.siege.tower'+role.capitalize(),title='Guild Knife-Thrower siege tower '+role+' portrait',
    semantics='Exact own configured Guild Knife-Thrower portrait; removes retired Axe Reckoner appearance. Native shooter, projectile and combat rules remain unchanged.')
  fresh['generation']['painted_source_provenance']={'method':'Exact technical rebinding of selected own configured shooter portrait; no new image generation or art edit','configured_shooter':'guildKnifeThrower','selected_portrait_recipe':row['selected_active_portrait']['path'],'selected_portrait_recipe_sha256':row['selected_active_portrait']['sha256'],'frozen_editable_portrait_template':row['selected_portrait_template'],'selected_portrait_source':template['source'],'selected_portrait_source_sha256':template['source_sha256'],'binding_producer':{'path':rel(SELF),'sha256':sha(SELF)}}
  fresh['dependencies']=[{'path':n,'sha256':h}for n,h in sorted(inputs.items())]
  target=S/'recipes'/('tower'+role.capitalize()+'.json');put(target,fresh)
  recipes.append({'path':rel(target),'sha256':sha(target),'active_recipe':row['active_tower_recipe'],'recorded_before_live_sha256':row['recorded_before_live_sha256']})
 selection={'status':'authored configuration','candidate_only':True,'configured_shooter':'guildKnifeThrower','producer':{'path':rel(SELF),'sha256':sha(SELF)},'direct_live_inputs':[{'path':n,'sha256':h}for n,h in sorted(inputs.items())],'recipes':recipes,'no_creature_or_content_changes':True,'no_new_art_pixels':True}
 put(S/'selection-v1.json',selection)
 print(json.dumps({'recipes':len(recipes),'direct_live_inputs':len(inputs),'selection_sha256':sha(S/'selection-v1.json')},indent=2))
if __name__=='__main__':main()

