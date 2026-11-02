"""Execute existing converter twice in memory; persist only own fixture buffers."""
from pathlib import Path
import importlib.util,json,hashlib,sys
import assemble_candidate as A
ROOT=A.ROOT;HERE=A.HERE;REPORT=A.REPORT;FIX=REPORT/'strict-source-fixture'
spec=importlib.util.spec_from_file_location('nx1_lane_actual_compiler',ROOT/'scripts/art_compile.py');compiler=importlib.util.module_from_spec(spec);spec.loader.exec_module(compiler)
def main():
 outputs={};receipts=[]
 for recipe in sorted((HERE/'candidate/recipes/assets/recipes/town').rglob('*.json')):
  first,receipt=compiler.plan(ROOT,recipe);second,_=compiler.plan(ROOT,recipe)
  if first!=second:raise AssertionError('Nondeterministic conversion: '+str(recipe))
  for name,data in first.items():
   if name in outputs:raise AssertionError('Duplicate output '+name)
   outputs[name]=hashlib.sha256(data).hexdigest();dest=FIX/'assets/generated'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
  receipts.append(receipt)
 assert(len(receipts),len(outputs))==(110,182)
 A.write(REPORT/'actual-conversion.json',{'status':'authored configuration','mode':'Existing production converter plan, each recipe executed twice; buffers written only to isolated own source-check fixture','recipes':len(receipts),'buffers':len(outputs),'outputs':outputs,'receipts':receipts,'canonical_generated_or_stage_mutated':False});print(json.dumps({'recipes':len(receipts),'buffers':len(outputs),'fixture':str(FIX)}))
if __name__=='__main__':main()
