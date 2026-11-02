"""Read-only repeat of the actual64recipe converter after coordinator integration.

The original assembler's guarded proposal is a preserved manifest snapshot.
Replaying these frozen recipes does not rewrite that proposal or canonical assets.
"""
from pathlib import Path
import hashlib,json,sys
S=Path(__file__).resolve().parent;P=S.parents[3];W=P.parent
sys.path.insert(0,str(W/'scripts'));import faction_art_compile
packet=P/'build/reports/painted-creature-completion-20261028-v1/final-packet-v5/root-integration-packet-v5.json'
p=json.loads(packet.read_text());compiler=faction_art_compile.create_compiler('bilgewater')
def sha(b):return hashlib.sha256(b).hexdigest()
passes=[]
for replay in [1,2]:
 outputs={}
 for row in p['changes']:
  recipe=P/row['proposed_recipe']
  if sha(recipe.read_bytes())!=row['proposed_recipe_sha256']:raise RuntimeError('Frozen recipe pin changed')
  planned,receipt=compiler.plan(P,recipe)
  if sha(planned[row['output_path']])!=row['compiled_sha256']:raise RuntimeError('Compiled primary output changed')
  outputs.update({name:sha(raw)for name,raw in planned.items()})
 passes.append(outputs)
expected=json.loads((packet.parent/'physical-output-hashes-v5.json').read_text())
if passes[0]!=passes[1]or passes[0]!=expected:raise RuntimeError('Frozen actual compiler output changed')
print(json.dumps({'status':'authored configuration','packet_sha256':sha(packet.read_bytes()),'actual_recipes':len(p['changes']),'actual_outputs_per_pass':len(expected),'replays':2,'deterministic':True,'canonical_writes':False,'native_execution':False,'visual_approval_granted':False},sort_keys=True))
