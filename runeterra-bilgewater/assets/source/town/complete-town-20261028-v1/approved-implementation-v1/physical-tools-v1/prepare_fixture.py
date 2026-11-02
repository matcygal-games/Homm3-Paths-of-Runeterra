"""Copy exact town-only producer bytes into an owned isolated physics fixture.

This does not manufacture generated art, stage a faction, adopt recipes, or
relax whole-mod freshness. Actual recipe/compiled receipts are mandatory.
"""
from pathlib import Path
import argparse,hashlib,json,re,sys
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[5]
WORKSPACE=PROJECT.parent
REPORT=PROJECT/'build/reports/complete-town-20261028-v1/approved-implementation-v1/physical-consumer-v1'
sys.path.insert(0,str(WORKSPACE/'scripts'))
import faction_town_layout as actual


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def encoded(v):return (json.dumps(v,indent=2,sort_keys=True)+'\n').encode()
def pinned(name,pin):
 p=actual._direct_reference_path(PROJECT,name)
 if sha(p)!=pin:raise ValueError('Released producer bytes changed: '+name)
 return p

def main():
 a=argparse.ArgumentParser(description=__doc__)
 a.add_argument('--payload',required=True);a.add_argument('--payload-sha256',required=True)
 a.add_argument('--compiled-root',required=True);a.add_argument('--compiler-receipts',required=True)
 a.add_argument('--compiler-receipts-sha256',required=True)
 a.add_argument('--contract',required=True);a.add_argument('--contract-sha256',required=True)
 a.add_argument('--out-name',required=True);args=a.parse_args()
 if not re.fullmatch('[a-z0-9-]+',args.out_name):raise ValueError('Unique simple fixture name required')
 payload_path=pinned(args.payload,args.payload_sha256);payload=load(payload_path)
 contract_path=pinned(args.contract,args.contract_sha256);contract=load(contract_path)
 receipts_path=pinned(args.compiler_receipts,args.compiler_receipts_sha256)
 compiled=(PROJECT/args.compiled_root).resolve()
 if not compiled.is_relative_to(PROJECT/'build/reports'):raise ValueError('Actual compiled input must be own town report')
 fixture=REPORT/args.out_name/'runeterra-bilgewater';fixture.mkdir(parents=True,exist_ok=False)
 inventory={}
 visited_json=set()
 def copy(path,target):
  target_path=fixture/target
  if not target_path.resolve().is_relative_to(fixture):raise ValueError('Unsafe fixture target')
  data=path.read_bytes()
  if target in inventory and inventory[target]!=sha(path):raise ValueError('Different bytes target same fixture source')
  target_path.parent.mkdir(parents=True,exist_ok=True);target_path.write_bytes(data);inventory[target]=sha(path)
 def declared(name,pin):
  path=pinned(name,pin);copy(path,name)
  if False and path.suffix=='.json' and name not in visited_json:
   visited_json.add(name);refwalk(load(path))
 def refwalk(value):
  if isinstance(value,dict):
   if isinstance(value.get('path'),str) and isinstance(value.get('sha256'),str):
    declared(value['path'],value['sha256'])
   # These names are the actual existing compiler's reported source records.
   if isinstance(value.get('source'),str) and isinstance(value.get('source_sha256'),str):
    declared(value['source'],value['source_sha256'])
   # Referenced authored JSONs also declare direct named input/SHA pairs
   # (frame, alpha_mask, source, underlap index), distinct from runtime hooks.
   for key,pin in value.items():
    if key.endswith('_sha256') and isinstance(pin,str) and len(pin)==64:
     name=value.get(key[:-7])
     if isinstance(name,str) and name.startswith(('assets/','design/','content/','build/reports/')):
      declared(name,pin)
   for child in value.values():refwalk(child)
  elif isinstance(value,list):
   for child in value:refwalk(child)
 for row in payload['recipes']:
  source=pinned(row['candidate'],row['sha256']);copy(source,row['target'])
 for row in payload['outputs']:
  name=row['path'];source=actual._direct_reference_path(compiled,name)
  if sha(source)!=row['sha256']:raise ValueError('Actual compiler output changed: '+name)
  copy(source,'assets/generated/'+name)
 content=pinned(payload['candidate_content'],payload['candidate_content_sha256']);copy(content,'content/factions.json')
 refwalk(load(receipts_path));refwalk(contract)
 contract_name=contract_path.relative_to(PROJECT).as_posix();copy(contract_path,contract_name)
 design={'layout_geometry_mode':'silhouette-v2','layout_contract':{'path':contract_name,'sha256':sha(contract_path)}}
 dest=fixture/'design/town-visuals.json';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(encoded(design));inventory['design/town-visuals.json']=sha(dest)
 receipt={'status':'authored configuration','scope':'Exact actual town-only producer bytes and isolated authored layout selection; not faction freshness, native or release acceptance.',
  'payload':{'path':args.payload,'sha256':sha(payload_path)},'compiler_receipts':{'path':args.compiler_receipts,'sha256':sha(receipts_path)},
  'contract':{'path':contract_name,'sha256':sha(contract_path)},'fixture':fixture.relative_to(PROJECT).as_posix(),
  'source_inventory':inventory,'recursively_pinned_authoring_jsons':sorted(visited_json),'public_consumer_run':False,'native_executed':False,'release_accepted':False}
 (REPORT/(args.out_name+'-preparation.json')).write_bytes(encoded(receipt))
 print(json.dumps({'fixture':str(fixture),'copied_files':len(inventory),'contract_sha256':sha(contract_path)}))

if __name__=='__main__':main()
