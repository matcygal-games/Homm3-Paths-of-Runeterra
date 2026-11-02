"""Create isolated candidate recipes from frozen native parent role contracts."""
from pathlib import Path
import hashlib,json,copy
S=Path(__file__).resolve().parent;P=S.parents[2];W=P.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def enc(v):return (json.dumps(v,indent=2,sort_keys=True)+'\n').encode()
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists() and p.read_bytes()!=b:raise ValueError('Frozen candidate differs: '+str(p))
 p.write_bytes(b)
def rel(p):return p.relative_to(P).as_posix()
def pin(p):return {'path':rel(p),'sha256':sha(p)}
def prepare(unit,version):
 receipt_path=S/f'{unit}-assembly-{version}.json';receipt=json.loads(receipt_path.read_text());assert not receipt['rejected_physical_coverage'];rows=receipt['records']
 slots={(z['role'],z.get('group'),z.get('frame')):r for r in rows for z in r['slots']}
 deps=[pin(S/'assemble_clean_cohorts.py'),pin(S/'prepare_clean_recipes.py'),pin(S/f'{unit}-attachments-{version}.json'),pin(S/'material-marks/generation-v3.json'),pin(S/'material-marks/master-v3.png'),pin(S/'material-marks/variants-v3.json'),pin(receipt_path)]
 deps+=[pin(p) for p in sorted((S/'material-marks/variants-v3').glob('*.png'))]
 for r in rows:
  for key in ('source','candidate','mask'):deps.append(pin(P/r[key]))
 deps=list({x['path']:x for x in deps}.values())
 cohort={'status':'authored configuration','unit':unit,'scope':'Complete clean painted2D crest-only native cohort; roots, original alpha and exterior pixels preserved. No gameplay/art/rights acceptance.','dependencies':deps,'assembly_receipt':rel(receipt_path),'source_ancestry':'Clean 20261024 painted2D identity/action masters checked against actual provider calls, never 3D guide sources. Source event history is retained separately.','native_verified':False,'release_accepted':False}
 cohort_path=S/f'{unit}-cohort-{version}.json';put(cohort_path,enc(cohort))
 outputs=[]
 for role in ('battle','map','large','small','attackLeft','attackRight'):
  oldpath=P/f'assets/history/regional-crests-20261025-v2/{unit}-{unit}-{role}.json';old=json.loads(oldpath.read_text());recipe=copy.deepcopy(old)
  recipe['source']=rel(cohort_path);recipe['source_sha256']=sha(cohort_path);recipe['depends_on']=[];recipe['dependencies']=[pin(cohort_path)]
  recipe['historical_provenance']=[{'kind':'historical_provenance','path':rel(oldpath),'sha256':sha(oldpath)}]
  recipe['generation']={'provider':'OpenAI built-in imagegen','image_generation_used':True,'model':None,'model_disclosure':'Exact backend model not exposed by built-in tool','painted_master':rel(S/'material-marks/master-v3.png'),'painted_master_sha256':sha(S/'material-marks/master-v3.png'),'route':'Genuine painted regional pigment/engraving angle variants on explicit existing material planes; original native body/source alpha/outside exact. No code glyph, official PNG stamp, body warp, 3D, new gear or pose substitution.','selection':'candidate only; coordinator alone integrates','native_visual_review':'pending','rights':'unresolved; release prohibited','visual_approval_granted':False}
  recipe['delivery']={'status':'built-unreviewed','runtime_verified':False,'source_check_report':rel(receipt_path),'visual_approval_granted':False};recipe['acceptance']='authored configuration; complete candidate technical conversion only, native/human art/rights approval pending';recipe['production_status']='delivered';recipe['status']='built-unreviewed';recipe['visual_approval_granted']=False
  if role in ('battle','map'):
   for g in recipe['groups']:
    for index,frame in enumerate(g['frames']):
     r=slots[(role,g['group'],index)];frame['source']=r['candidate'];frame['source_sha256']=r['candidate_sha256'];frame['sha256']=r['candidate_sha256'];frame.pop('generated_by',None)
  else:
   r=slots[(role,None,None)];recipe['source']=r['candidate'];recipe['source_sha256']=r['candidate_sha256'];recipe['sha256']=r['candidate_sha256']
  out=P/f'assets/candidates/regional-crests-clean-20261025-v1/recipes/{unit}-{role}.json';put(out,enc(recipe));outputs.append(pin(out))
 return outputs
if __name__=='__main__':
 import sys
 out=[]
 for value in sys.argv[1:]:unit,version=value.split(':');out+=prepare(unit,version)
 print(json.dumps({'candidate_recipes':out},indent=2))
