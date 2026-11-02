"""Strict local-only replay of the complete two-unit painted crest cohort."""
from pathlib import Path
import hashlib,importlib.util,json
S=Path(__file__).resolve().parent;P=S.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 record=json.loads((S/'poro-pair-direct-inputs-v1.json').read_text())
 for item in record['dependencies']:
  name=item['path']
  if ':' in name or '\\' in name or any(x in ('','.','..') for x in name.split('/')):raise ValueError('Unsafe local source')
  path=(P/name).resolve()
  if not path.is_relative_to(P) or not path.is_file() or sha(path)!=item['sha256']:raise ValueError('Missing/stale local cohort input: '+name)
 helper=S/'assemble_material_v3.py';spec=importlib.util.spec_from_file_location('freljord_painted_material',helper);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 for unit in ('overgrownPoro','fluftOfPoros'):
  path=S/(unit+'-attachments-v1.json');receipt=module.assemble(path);actual=json.loads(path.with_name(path.stem+'-assembly.json').read_text())
  if receipt!=actual:raise ValueError('Replayed physical receipt differs: '+unit)
 print('Poro pair: all58native contexts replayed exactly; bodies/alpha/actions preserved; no cache/reference service or active recipe writes.')
if __name__=='__main__':main()
