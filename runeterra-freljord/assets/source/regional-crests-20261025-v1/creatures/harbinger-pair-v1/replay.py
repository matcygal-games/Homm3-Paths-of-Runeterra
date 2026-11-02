"""Offline exact local material/60-context replay, without private references or caches."""
from pathlib import Path
import hashlib,importlib.util,json
S=Path(__file__).resolve().parent;P=S.parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def local(name):
 if ':' in name or '\\' in name or any(x in ('','.','..') for x in name.split('/')):raise ValueError('Unsafe dependency')
 path=(P/name).resolve()
 if not path.is_relative_to(P):raise ValueError('Source escape')
 return path
def module(name,file):
 spec=importlib.util.spec_from_file_location(name,S/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main():
 record=json.loads((S/'direct-inputs.json').read_text())
 for item in record['dependencies']:
  p=local(item['path'])
  if not p.is_file() or sha(p)!=item['sha256']:raise ValueError('Missing/stale input: '+item['path'])
 module('glyph_material','assemble_glyph_material_v3.py').main()
 assembler=module('physical_material','assemble_material.py');contexts=0
 for unit in ('harbingerOfThralls','rimewakeHarbinger'):
  plan=S/(unit+'-plan-v3.json');result=assembler.assemble(plan)
  if result!=json.loads(plan.with_name(plan.stem+'-assembly.json').read_text()):raise ValueError('Replay receipt differs: '+unit)
  contexts+=len(result['records'])
 print(json.dumps({'status':'authored configuration','contexts_replayed':contexts,'exact':True,'runtime_verified':False,'release_accepted':False}))
if __name__=='__main__':main()
