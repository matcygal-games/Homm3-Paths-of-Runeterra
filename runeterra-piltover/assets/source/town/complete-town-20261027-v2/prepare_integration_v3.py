"""Prepare guarded coordinator payloads under reports; never edit canonical files."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys
import numpy as np
from PIL import Image

S=Path(__file__).resolve().parent
P=S.parents[3]
W=P.parent
R=P/'build/reports/complete-town-20261027-v2/derivation-contact-repair-v1'
sys.path.insert(0,str(W/'scripts'))
import faction_town_layout as layout

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def encoded(v):return (json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(encoded(v))
def pin(p):return {'path':p.relative_to(P).as_posix(),'sha256':sha(p)}

def main():
 candidate=load(S/'integration-candidate-v2.json')
 plan=load(S/'layout-acceptance-contract-v2.json')
 reg=load(S/'frame-registration-v1.json')['states']
 traces=load(S/'silhouette-traces-v1.json')['sites']
 assert len(plan['frames'])==35 and plan['ordinary_land_sites']==16
 assert len([s for s in plan['sites']if s['id']not in ('coast','grail')])==16
 for tier in range(1,8):
  assert sum({'dwellingLvl'+str(tier),'dwellingUpLvl'+str(tier)}<=set(s['states'])for s in plan['sites'])==1
 # Current canonical content is the guard baseline. Only reviewed structure
 # depths/geometry enter its explicit candidate payload; gameplay stays exact.
 content=load(P/'content/factions.json')
 structures=load(S/'town-structures.candidate-v2.json')
 old=content['piltover']['town']['structures']
 assert set(old)==set(structures)
 fields=[]
 for state in sorted(old):
  for key in set(old[state])|set(structures[state]):
   if old[state].get(key)!=structures[state].get(key):
    assert key in ('x','y','z'),(state,key)
    fields.append({'pointer':'/piltover/town/structures/'+state+'/'+key,'before':old[state].get(key),'after':structures[state].get(key)})
 patched=deepcopy(content);patched['piltover']['town']['structures']=structures
 own=deepcopy(patched);own['piltover']['town']['structures']=old
 assert own==content
 mappings=[]
 def payload(target,data,source=None):
  canonical=P/target
  dest=R/'canonical-payload'/target
  dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
  row={'target':target,'before_sha256':sha(canonical),'after_sha256':sha(dest),'payload':pin(dest)}
  if source:row['candidate']=pin(source)
  mappings.append(row)
 payload('content/factions.json',encoded(patched),S/'town-structures.candidate-v2.json')
 payload('design/town-structures.fragment.json',(S/'town-structures.candidate-v2.json').read_bytes(),S/'town-structures.candidate-v2.json')
 payload('design/town-visuals.json',(S/'town-visuals.candidate-v2.json').read_bytes(),S/'town-visuals.candidate-v2.json')
 for row in candidate['recipe_map']:
  source=P/row['candidate'];assert sha(source)==row['sha256']
  payload(row['target'],source.read_bytes(),source)
 assert len(mappings)==145 and len({r['target']for r in mappings})==145
 fixture=R/'technical-consumer/runeterra-piltover'
 errors,deps=layout.inspect(fixture,{'factions':patched},'piltover')
 assert not errors,errors
 assert set(deps)==set(layout.dependency_paths(fixture))
 converter=load(R/'converter-receipts-v2.json')
 for path,digest in converter['output_sha256'].items():assert sha(R/'candidate-generated'/path)==digest
 negative=load(R/'negative-controls-v3.json');assert negative['passed'] and negative['tests_run']==9
 # Expose exactly what the source-derived contact band includes/excludes.
 contacts={}
 for state,r in reg.items():
  frame=S/'frames'/r['site']/(state+'.png');alpha=np.asarray(Image.open(frame).convert('RGBA'))[:,:,3]>=128
  root=traces[r['site']].get('state_doors',{}).get(state,traces[r['site']]['door'])
  lower=[]
  for x in range(800):
   ys=np.flatnonzero(alpha[:,x])
   if len(ys):lower.append([x,int(ys[-1])])
  omitted=[point for point in lower if point[1]<root[1]-12]
  repaired=[point for point in lower if point[1]>root[1]+10]
  contacts[state]={'frame':pin(frame),'door_anchor':root,'opaque_bottom_columns':len(lower),'bottom_y_range':[min(p[1]for p in lower),max(p[1]for p in lower)],'excluded_high_roof_or_side_columns':omitted,'restored_lower_plinth_columns':repaired,'foundation':plan['silhouette_plan']['states'][state]['foundation_mask']}
  if state in ('blacksmith','castle','cityHall','mageGuild3','marketplace','special3'):
   native=Image.open(S/'complete-town-native-v2.png').convert('RGBA')
   foundation=np.asarray(Image.open(P/plan['silhouette_plan']['states'][state]['foundation_mask']['path']))>0
   color=np.zeros((374,800,4),dtype=np.uint8);color[foundation]=(0,255,255,210)
   native.alpha_composite(Image.fromarray(color,'RGBA'))
   native.save(R/('complete-root-'+state+'.png'))
 dump(R/'contact-coverage-v1.json',{'status':'authored configuration','scope':'Exact alpha128 per-column bottom audit; opaque edges are not inferred architectural semantics. All declared contacts still need source-pixel review.','states':contacts})
 manifest={'status':'authored configuration','selected':False,'canonical_files':mappings,'content_field_changes':fields,'apply_policy':'Coordinator only. Verify EVERY before_sha256 and all payload/candidate pins before any canonical write. Reject source drift; do not run this preparation tool to overwrite a prior review receipt. Preserve prior accepted inputs. Payloads are authored inputs prepared for explicit integration, not generated canonical content.','protected_inputs_written':False,'stage_built':False,'native_executed':False,'release_accepted':False}
 dump(R/'integration-manifest-v3.json',manifest)
 receipt={'status':'authored configuration','candidate_ready_for_coordinator_integration':True,'manifest':pin(R/'integration-manifest-v3.json'),'candidate':pin(S/'integration-candidate-v2.json'),'contract':pin(S/'layout-acceptance-contract-v2.json'),'helper':{'path':'../scripts/faction_town_layout.py','sha256':sha(W/'scripts/faction_town_layout.py')},'native_master':pin(S/'complete-town-native-v2.png'),'converter_receipt':pin(R/'converter-receipts-v2.json'),'actual_consumer':pin(R/'actual-consumer-v2.json'),'negative_controls':pin(R/'negative-controls-v3.json'),'contact_coverage':pin(R/'contact-coverage-v1.json'),'preparer':pin(Path(__file__)),'counts':{'canonical_files':len(mappings),'ordinary_land_sites':16,'optional_coast':1,'optional_grail':1,'dwelling_sites':7,'states':35,'recipes':142,'converted_outputs':212,'actual_consumer_dependencies':len(deps),'focused_tests_executed':9},'remaining':['Coordinator integration and fresh production stage','Independent current source-pixel review and final human art acceptance','Native HALL/clicks/tooltips, early/full/upgraded/coastal and construction-state observation on matching fresh stage','Town animation/effect review where applicable, siege/adventure/UI coherence outside this assigned town-layer candidate','Redistribution and release acceptance'], 'native_executed':False,'release_accepted':False}
 dump(R/'final-source-receipt-v3.json',receipt)
 print(json.dumps({'ready':True,'canonical_files':len(mappings),'dependencies':len(deps),'receipt_sha256':sha(R/'final-source-receipt-v3.json'),'manifest_sha256':sha(R/'integration-manifest-v3.json')}))

if __name__=='__main__':main()
