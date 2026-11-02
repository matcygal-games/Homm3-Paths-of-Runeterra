"""Portable candidate binding; every semantic replay input is an ordinary live edge."""
from pathlib import Path
import hashlib,json,copy
S=Path(__file__).resolve().parent;P=S.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def enc(v):return (json.dumps(v,indent=2,sort_keys=True)+'\n').encode()
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists() and p.read_bytes()!=b:raise ValueError('Frozen candidate differs: '+str(p))
 p.write_bytes(b)
def rel(p):return p.relative_to(P).as_posix()
def pin(p):return {'path':rel(p),'sha256':sha(p)}
def prepare(unit,version):
 rp=S/f'{unit}-assembly-{version}.json';r=json.loads(rp.read_text());assert not r['rejected_physical_coverage'];rows=r['records'];slots={(z['role'],z.get('group'),z.get('frame')):v for v in rows for z in v['slots']};t6=unit in ('sumpReclaimer','hydraulicReclaimer');generation='t6-cloth-generation-v2.json' if t6 else 'generation-v4.json';variantdir='t6-cloth-variants-v1' if t6 else 'variants-v3';master='t6-cloth-master-v1.png' if t6 else 'master-v3.png'
 deps=[pin(S/'assemble_t6_cohorts.py'),pin(S/'assemble_clean_cohorts.py'),pin(Path(__file__)),pin(S/f'{unit}-attachments-{version}.json'),pin(S/'material-marks'/generation),pin(S/'material-marks'/master),pin(S/'material-marks'/(variantdir+'.json')),pin(rp),pin(P/r['source_preparation'])]
 deps+=[pin(p) for p in sorted((S/'material-marks'/variantdir).glob('*.png'))]
 deps+=[pin(S/f'role-contracts-v1/{unit}-{role}.json') for role in ('battle','map','large','small','attackLeft','attackRight')]
 for v in rows:
  deps+=[pin(P/v[k]) for k in ('source','candidate','mask')]
 deps=list({x['path']:x for x in deps}.values());cohort={'status':'authored configuration','unit':unit,'scope':'Complete crest-only native source cohort; no stage/native/release acceptance','dependencies':deps,'body_lineage':'Clean independent painted2D 20261024 masters; actual provider input chains separately audited, no 3D-guide ancestors.','source_assembly_receipt':rel(rp),'visual_approval_granted':False,'runtime_verified':False,'release_accepted':False};cp=S/f'{unit}-cohort-portable-v1.json';put(cp,enc(cohort));outputs=[]
 for role in ('battle','map','large','small','attackLeft','attackRight'):
  template=S/f'role-contracts-v1/{unit}-{role}.json';recipe=json.loads(template.read_text());recipe.pop('contract_scope',None);recipe['production_status']='delivered';recipe['status']='built-unreviewed';recipe['visual_approval_granted']=False;recipe['acceptance']='authored configuration; complete candidate technical conversion only, native/human art/rights approval pending';recipe['depends_on']=[];recipe['dependencies']=[pin(cp),pin(template)];recipe['source']=rel(cp);recipe['source_sha256']=sha(cp)
  recipe['generation']={'provider':'OpenAI built-in imagegen','image_generation_used':True,'model':None,'model_disclosure':'Exact backend model not exposed by built-in tool','painted_master':rel(S/'material-marks'/master),'painted_master_sha256':sha(S/'material-marks'/master),'material_provenance':rel(S/'material-marks'/generation),'route':'Genuine painted regional material-angle layer on explicit existing anatomical surface; original full alpha and all exterior RGBA preserved, no body warp, code glyph, officialPNG stamp or 3D ancestor','selection':'candidate only; coordinator integrates','native_visual_review':'pending','rights':'unresolved; release prohibited','visual_approval_granted':False};recipe['delivery']={'status':'built-unreviewed','source_check_report':rel(rp),'runtime_verified':False,'visual_approval_granted':False}
  if role in ('battle','map'):
   for g in recipe['groups']:
    for i,f in enumerate(g['frames']):
     assert f.pop('native_frame_index')==i;v=slots[(role,g['group'],i)];f.update(source=v['candidate'],source_sha256=v['candidate_sha256'],sha256=v['candidate_sha256'])
  else:
   v=slots[(role,None,None)];recipe.update(source=v['candidate'],source_sha256=v['candidate_sha256'],sha256=v['candidate_sha256'])
  out=P/f'assets/candidates/regional-crests-clean-20261025-v1/recipes-t6-portable-v1/{unit}-{role}.json';put(out,enc(recipe));outputs.append(pin(out))
 return outputs
if __name__=='__main__':
 import sys
 out=[]
 for arg in sys.argv[1:]:u,v=arg.split(':');out+=prepare(u,v)
 print(json.dumps({'candidate_recipes':out},indent=2))
