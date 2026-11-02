"""Metadata-only portrait provenance extension; no art or canonical writes."""
from pathlib import Path
import json,hashlib,argparse
HERE=Path(__file__).resolve().parent;P=HERE.parents[3]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def encoded(v):return(json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+'\n').encode()
def plans():
 inputs=json.loads((HERE/'inputs.json').read_text(encoding='utf-8-sig'));outputs={}
 for row in inputs['recipes']:
  path=P/row['input_recipe']
  if sha(path)!=row['input_recipe_sha256']:raise ValueError('Changed pinned metadata parent: '+row['input_recipe'])
  recipe=json.loads(path.read_text(encoding='utf-8-sig'))
  for change in row['updates']:
   node=recipe
   for key in change['node_path']:node=node[int(key)]if isinstance(node,list)else node[key]
   if node.get('source')!=change['source_path']or sha(P/change['source_path'])!=change['source_sha256']:raise ValueError('Changed actual portrait parent')
   if node.get('source_sha256')or node.get('sha256'):raise ValueError('Overlay cannot overwrite an existing checksum')
   node['source_sha256']=change['source_sha256']
  additions=[{'path':str(path.relative_to(P)).replace('\\','/'),'sha256':sha(path)}for path in(Path(__file__),HERE/'inputs.json',P/row['input_recipe'])]
  recipe.setdefault('production_inputs',[]).extend(additions)
  recipe['generation']['metadata_overlay']={'method':'Bind actual already-pinned portrait master; image bytes unchanged','producer':str(Path(__file__).relative_to(P)).replace('\\','/'),'producer_sha256':sha(__file__),'parent_recipe':row['input_recipe'],'parent_recipe_sha256':row['input_recipe_sha256']}
  outputs[row['output_recipe']]=encoded(recipe)
 return outputs
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
 for name,raw in plans().items():
  path=P/name
  if not path.is_relative_to(HERE/'recipes'):raise ValueError('Output escaped metadata source namespace')
  if args.check:
   if not path.is_file()or path.read_bytes()!=raw:raise ValueError('Stale metadata overlay')
  else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
 print(json.dumps({'status':'authored configuration','recipes':len(plans()),'pixels_modified':False,'canonical_modified':False}))
if __name__=='__main__':main()
