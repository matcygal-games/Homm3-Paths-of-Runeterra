"""Bind fresh painted native sources to current six-role contracts, never live paths."""
from pathlib import Path
import json,copy
from prepare_pose_sources import S,P,W,R,sha,enc,put,png,rel
def pin(p):return {'path':rel(p),'sha256':sha(p)}
def run():
 receipt_path=S/'native-assembly-receipt-v2.json';receipt=json.loads(receipt_path.read_text());records=receipt['records'];outputs=[]
 for unit in ('zaunThug','chemPunk'):
  rows=[r for r in records if r['unit']==unit];slots={(r['role'],r.get('group'),r.get('frame')):r for r in rows};inputs=[S/'source-inventory-v1.json',S/'isolated-source-receipt-v1.json',S/'registration-plan-v2.json',receipt_path,S/'prepare_pose_sources.py',S/'assemble_native_v2.py',Path(__file__),S/'reproduce.py',S/'clean-standing-lineage-v1.json']
  inputs+=sorted((S/unit).glob('*-generation-v*.json'));inputs+=[S/'role-contracts-v1'/f'{unit}-{role}.json' for role in ('battle','map','large','small','attackLeft','attackRight')]
  iso=json.loads((S/'isolated-source-receipt-v1.json').read_text())
  for r in iso['records']:
   if r['unit']==unit:inputs+=[P/r[k] for k in ('master','isolated','ownership_mask')]
  inputs+=[P/r['native'] for r in rows];deps=list({rel(p):pin(p) for p in inputs}.values());cohort={'status':'authored configuration','unit':unit,'dependencies':deps,'scope':'Fresh genuine2D complete native action/auxiliary candidate. No old guided pixels, clipped final source, body warp or live integration.','canonical_role_slots':len(rows),'native_source_bindings':rows,'source_review':'Worker inspected all104 battle frames and10 auxiliary views at native size; external final art/native/rights acceptance pending.','runtime_verified':False,'release_accepted':False};cp=S/unit/'cohort-v1.json';put(cp,enc(cohort))
  for role in ('battle','map','large','small','attackLeft','attackRight'):
   template=S/'role-contracts-v1'/f'{unit}-{role}.json';recipe=json.loads(template.read_text());recipe.pop('contract_scope',None);recipe['production_status']='delivered';recipe['status']='built-unreviewed';recipe['visual_approval_granted']=False;recipe['acceptance']='authored configuration; actual conversion is not native/final art/rights/release acceptance';recipe['credits']={'author':'Runeterra project using OpenAI built-in imagegen; genuine painted2D and deterministic technical assembly','license':None,'redistribution':'unresolved; release prohibited'};recipe['generation']={'provider':'OpenAI built-in imagegen','image_generation_used':True,'model':None,'model_disclosure':'Exact backend model not exposed by the built-in tool','route':'Clean independent standing identity lineage; newly painted whole2D action cohorts, deterministic owned-pose isolation and fixed native root conversion; no old guided action inputs, 3D, body warps or idle pose substitution','painted_master':rel(S/unit/'identity-v1.png'),'painted_master_sha256':sha(S/unit/'identity-v1.png'),'native_visual_review':'pending','rights':'unresolved; release prohibited','visual_approval_granted':False};recipe['depends_on']=[];recipe['dependencies']=[pin(cp),pin(template)];recipe['delivery']={'status':'built-unreviewed','source_check_report':rel(receipt_path),'runtime_verified':False,'visual_approval_granted':False};recipe['source']=rel(cp);recipe['source_sha256']=sha(cp)
   if role in ('battle','map'):
    for g in recipe['groups']:
     count=g.pop('frame_count');g['frames']=[]
     for i in range(count):
      r=slots[(role,g['group'],i)] if role=='battle' else slots[('map',None,None)];g['frames'].append({'source':r['native'],'source_sha256':r['native_sha256'],'sha256':r['native_sha256'],'source_canvas':recipe['canvas']})
   else:
    r=slots[(role,None,None)];recipe.update(source=r['native'],source_sha256=r['native_sha256'],sha256=r['native_sha256'])
   out=P/f'assets/candidates/regional-crests-clean-t1-20261025-v1/recipes/{unit}-{role}.json';put(out,enc(recipe));outputs.append(pin(out))
 print(json.dumps({'candidate_recipes':outputs},indent=2))
if __name__=='__main__':run()
