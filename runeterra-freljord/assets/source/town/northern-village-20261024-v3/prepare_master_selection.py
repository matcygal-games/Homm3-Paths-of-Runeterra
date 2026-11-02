"""Admit reviewed source candidates to a new explicit canonical art version.

No active recipes/content/stage writes. Old masters/metadata remain untouched.
"""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def immutable(p,data):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists() and p.read_bytes()!=data:raise ValueError('Versioned source changed: '+rel(p))
 if not p.exists():p.write_bytes(data)
def save(p,v):immutable(p,(json.dumps(v,indent=2)+'\n').encode())
def main():
 prior=HERE/'preexisting-community-selection.json'
 if not prior.exists():immutable(prior,(ROOT/'assets/production/town/community-selection-v2.json').read_bytes())
 original=load(prior)['states'];rows={}
 hall=ROOT/'assets/source/town/coordinator-heraldry-20261024-v1'
 hallraw=load(hall/'generation-record.json');hallportable=hall/'portable-provenance.json';hallpins=load(hall/'frozen-handoff.json')
 for state,item in original.items():
  oldmaster=ROOT/item['master']['path'];source=oldmaster;oldgeneration=oldmaster.parent/'generation.json'
  if state in ('villageHall','townHall','cityHall','capitol'):
   source=hall/state/'master.png';proof=hall/state/'assembly.json'
   if sha(source)!=hallpins['files'][state+'\\master.png']:raise ValueError('Hall frozen master changed')
   prompt=hallraw['prompts'][state]
   generation={'tool':'image_gen.imagegen','provider':'OpenAI built-in imagegen','model':'Not exposed by the built-in tool','prompt':prompt,'status':'authored configuration','method':'Genuine imagegen local crest edit, technically bounded through preserved-alpha mask; architecture/outside pixels unchanged.','origin_master':rel(source),'origin_master_sha256':sha(source),'source_assembly_record':rel(proof),'source_assembly_record_sha256':sha(proof),'source_portable_provenance':rel(hallportable),'source_portable_provenance_sha256':sha(hallportable),'private_raw_generation_record_sha256':sha(hall/'generation-record.json'),'reference_url':'https://universe.leagueoflegends.com/images/freljord_crest_icon@2x.png','reference_use':'Private official region-emblem shape reference only; not a united royal-government claim or bundled icon.'}
  elif state.startswith('mageGuild'):
   source=HERE/'guild-family'/state/'master.png';proof=source.parent/'generation.json';generation=load(proof);prompt=generation['prompt']
   # Exact tool prompt, including its actual trailing-newline semantics.
   (source.parent/'prompt.txt').write_text(prompt,encoding='utf-8')
   generation.update(origin_master=rel(source),origin_master_sha256=sha(source),source_generation_record=rel(proof),source_generation_record_sha256=sha(proof),method='Independent genuinely painted northern lorekeeper family; replaces mismatching round pagoda ranks. No Blender/render input.')
  else:
   raw=load(oldgeneration);prompt=raw['prompt']
   generation={'tool':'image_gen.imagegen','provider':'OpenAI built-in imagegen','model':raw.get('model') or 'Not exposed by the built-in tool','prompt':prompt,'status':'authored configuration','method':'Existing genuinely painted master preserved byte-exact. Portable selected metadata supersedes raw machine locator fields, with raw record hash retained.','origin_master':rel(oldmaster),'origin_master_sha256':sha(oldmaster),'private_raw_generation_record_sha256':sha(oldgeneration)}
  master=oldmaster
  if source!=oldmaster:
   master=ROOT/'assets/source/town/buildings-v6'/state/'master.png'
   immutable(master,source.read_bytes());generation.update(master_sha256=sha(master),painted_master=rel(master),painted_master_sha256=sha(master),mode='RGBA',visual_approval_granted=False,rights='Unresolved; no release/redistribution approval inferred.')
   immutable(master.parent/'prompt.txt',prompt.encode());save(master.parent/'generation.json',generation)
  generation.update(master_sha256=sha(master),painted_master=rel(master),painted_master_sha256=sha(master),visual_approval_granted=False,rights='Unresolved; no release/redistribution approval inferred.')
  portable=HERE/'provenance'/state/'generation.json';save(portable,generation)
  immutable(portable.with_name('prompt.txt'),prompt.encode())
  rows[state]={'master':rel(master),'master_sha256':sha(master),'generation_record':rel(portable),'generation_record_sha256':sha(portable),'previous_master':rel(oldmaster),'previous_master_sha256':sha(oldmaster),'master_changed':sha(oldmaster)!=sha(master),'canonical_version':master.parts[-3]}
 save(HERE/'master-selection.json',{'status':'authored configuration','states':rows,'preserved_master_count':sum(not x['master_changed'] for x in rows.values()),'changed_master_count':sum(x['master_changed'] for x in rows.values()),'no_active_bindings':True})
 print(json.dumps({'preserved':sum(not x['master_changed'] for x in rows.values()),'changed':sum(x['master_changed'] for x in rows.values()),'master_selection_sha256':sha(HERE/'master-selection.json')}))
if __name__=='__main__':main()
