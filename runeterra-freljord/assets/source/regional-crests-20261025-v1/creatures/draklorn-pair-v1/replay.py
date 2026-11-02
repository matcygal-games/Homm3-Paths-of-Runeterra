"""Offline frozen material replay; no active recipes, stages, references or caches."""
from pathlib import Path
import hashlib, importlib.util, io, json
from PIL import Image
S=Path(__file__).resolve().parent
P=S.parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 record=json.loads((S/'direct-inputs.json').read_text())
 for item in record['dependencies']:
  name=item['path']
  if ':' in name or '\\' in name or any(x in ('','.','..') for x in name.split('/')):raise ValueError('Unsafe dependency')
  path=(P/name).resolve()
  if not path.is_relative_to(P) or not path.is_file() or sha(path)!=item['sha256']:raise ValueError('Missing/stale input: '+name)
 atlas=Image.open(S/'material-atlas-v1.png').convert('RGBA')
 for item in json.loads((S/'material-crops.json').read_text()):
  buf=io.BytesIO();atlas.crop(tuple(item['crop'])).save(buf,format='PNG')
  if buf.getvalue()!=(S/item['output']).read_bytes():raise ValueError('Painted material crop differs')
 spec=importlib.util.spec_from_file_location('material',S/'assemble_material.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 contexts=0
 for unit in ('draklornAttendant','draklornInquisitor'):
  plan=S/(unit+'-plan.json');result=module.assemble(plan)
  if result!=json.loads(plan.with_name(plan.stem+'-assembly.json').read_text()):raise ValueError('Replayed receipt differs')
  contexts+=len(result['records'])
 print(json.dumps({'status':'authored configuration','contexts_replayed':contexts,'exact':True,'runtime_verified':False,'release_accepted':False}))
if __name__=='__main__':main()
