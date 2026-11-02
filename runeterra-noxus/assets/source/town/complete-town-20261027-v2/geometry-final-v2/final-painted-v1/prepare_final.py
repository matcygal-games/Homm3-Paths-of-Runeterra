"""Bind the independently reviewed fixed geometry to the current whole paint."""
from pathlib import Path
import json,hashlib,shutil
F=Path(__file__).resolve().parent;G=F.parent/'coherent-paving-guide-v1';R=F.parents[5];T=F.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(R).as_posix(),'sha256':sha(p)}
def main():
 bg=T/'coherent-paving-repaint-v1/surface-painted-native-v1.png';index=T/'native-transforms-v14/states.json';lineage=T/'coherent-paving-repaint-v1/source-assets-index-v1.json'
 assert sha(bg)=='3e049c20df7009209ba424c46a450581d0097b35d1daa216f59e2df4600f0a5b';assert sha(index)=='e5101798a4336583495f9fbcb04ad780e54cca81275677b94e191ac69f233023'
 out=F/'contract/terrain-trace';out.mkdir(parents=True,exist_ok=False)
 for name in('support.png','stairs.png','water.png','land.png','walkable-plane.png'):shutil.copyfile(G/'structural-contract/terrain-trace'/name,out/name)
 trace=json.loads((G/'structural-contract/terrain-trace/background-plane-trace-v6.json').read_text());trace['source']=ref(bg);trace['scope']='Final whole-scene paint, same exact independently reviewed functional geometry and all five public links. Fresh source-plane review required and supplied separately; no automatic art acceptance from old geometry.';trace['exportable_paint_provenance']={'index':ref(lineage),'files':json.loads(lineage.read_text())['files']};(out/'background-plane-trace-v6.json').write_text(json.dumps(trace,indent=2)+'\n')
 s=(G/'build_structural_contract.py').read_text();s=s.replace("HERE=GUIDE/'structural-contract'","HERE=GUIDE/'contract'").replace("geometry-final-v2/coherent-paving-guide-v1'","geometry-final-v2/final-painted-v1'")
 # Current contract metadata explicitly closes every owned paint producer
 # input through the existing recursive selected-source collector.
 s=s.replace("'source_background_trace':ref(trace_path)","'source_background_trace':ref(trace_path),'source_surface_paint':trace['exportable_paint_provenance']")
 (F/'build_final_contract.py').write_text(s)
 s=(F.parent/'check_consumer.py').read_text();s=s.replace('HERE=Path(__file__).resolve().parent;TOWN=HERE.parent;ROOT=HERE.parents[4];WORKSPACE=ROOT.parent',"FINAL=Path(__file__).resolve().parent;HERE=FINAL/'contract';TOWN=FINAL.parents[1];ROOT=FINAL.parents[5];WORKSPACE=ROOT.parent");s=s.replace("('consumer-'+args.attempt)","('final-painted-v1/consumer-'+args.attempt)")
 (F/'check_final_consumer.py').write_text(s)
 print(json.dumps({'prepared':str(F),'new_background':ref(bg),'state_index':ref(index),'source_provenance':ref(lineage),'physical_masks_identical_to_structural_authoring_positive':True}))
if __name__=='__main__':main()
