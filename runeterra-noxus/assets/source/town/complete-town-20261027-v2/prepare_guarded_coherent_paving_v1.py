"""Prepare exact coordinator payloads. Canonical source is never written here."""
from pathlib import Path
from copy import deepcopy
import argparse,hashlib,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];W=ROOT.parent;C=HERE/'candidate-coherent-paving-v1';REPORT=ROOT/'build/reports/complete-town-20261027-v2/integration-coherent-paving-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf8'))
def data(v):return (json.dumps(v,indent=2)+'\n').encode()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data(v))
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--admission-inputs',required=True);args=ap.parse_args();inputs=load(ROOT/args.admission_inputs)
 # Every final review/consumer receipt is supplied as exact path/hash by its owner.
 for key in ('contract','consumer_positive','consumer_negatives','independent_review'):
  r=inputs[key];assert sha(ROOT/r['path'])==r['sha256'],key
 reviewcopy=REPORT/'independent-source-review-copy.json';reviewcopy.parent.mkdir(parents=True,exist_ok=True);reviewcopy.write_bytes((ROOT/inputs['independent_review']['path']).read_bytes())
 assert inputs['independent_source_admitted'] is True
 consumer=load(ROOT/inputs['consumer_positive']['path']);negatives=load(ROOT/inputs['consumer_negatives']['path'])
 assert inputs['actual_consumer_positive'] is True and inputs['actual_consumer_negatives_rejected'] is True
 assert consumer['ok'] is True and not consumer['geometry_errors']
 assert consumer['contract_sha256']==inputs['contract']['sha256'] and consumer['candidate_selection_sha256']==sha(C/'selection.json')
 assert consumer['helper_sha256']==sha(W/'scripts/faction_town_layout.py')
 assert negatives['negative_checks_run'] is True and negatives['baseline_is_valid_for_negative_attribution'] is True
 assert negatives['ok'] is True
 assert negatives['contract_sha256']==inputs['contract']['sha256']
 assert negatives['candidate_selection_sha256']==sha(C/'selection.json')
 assert negatives['helper_sha256']==sha(W/'scripts/faction_town_layout.py')
 assert negatives['actual_negative_checks'] and all(r['passed'] is True for r in negatives['actual_negative_checks'])
 assert len(negatives['actual_negative_checks'])==7
 expected_negative_baseline={'contract_sha256':inputs['contract']['sha256'],'candidate_selection_sha256':sha(C/'selection.json'),'helper_sha256':sha(W/'scripts/faction_town_layout.py')}
 for control in negatives['actual_negative_checks']:
  assert control['baseline_pins']==expected_negative_baseline
  assert control['environment_unchanged'] is True
  assert control['fixed_environment_sha256']['background']=='3e049c20df7009209ba424c46a450581d0097b35d1daa216f59e2df4600f0a5b'
 s=load(C/'selection.json');index=load(HERE/'native-transforms-v14/states.json');assert len(index['states'])==36 and s['ordinary_land_sites']==17
 conversion=load(ROOT/'build/reports/complete-town-20261027-v2/conversion-coherent-paving-v1/receipt.json');assert conversion['successful_recipes']==110 and conversion['actual_output_count']==182 and not conversion['failed_recipes']
 assert conversion['converter_sha256']==sha(ROOT/'scripts/art_compile.py')
 assert all(r['decoded_rgba_equal']for r in conversion['decoded_state_comparisons'])
 current=load(ROOT/'content/factions.json');patched=deepcopy(current);proposed=load(C/'factions.candidate.json')['noxus']['town']['structures'];old=current['noxus']['town']['structures'];assert set(old)==set(proposed)
 fields=[]
 for state in old:
  for key in set(old[state])|set(proposed[state]):
   if old[state].get(key)!=proposed[state].get(key):
    assert key in ('x','y','z'),(state,key);fields.append({'pointer':'/noxus/town/structures/'+state+'/'+key,'before':old[state].get(key),'after':proposed[state].get(key)})
 patched['noxus']['town']['structures']=proposed;restored=deepcopy(patched);restored['noxus']['town']['structures']=old;assert restored==current
 visual=load(ROOT/'design/town-visuals.json');visual.update(status='authored configuration',derivation='Complete-town V2 with preserved36 architecture masters and fixed recorded poses; ONE globally registered genuine painted2D background surface master unifies paving, roads, stairs and masonry light/materials through the complete protected-surface mask. Prior patchwork appearance is preserved only as user-rejected history.',selected_source=ref(C/'selection.json')['path'],selected_source_sha256=sha(C/'selection.json'),layout_geometry_mode='silhouette-v2',layout_contract=inputs['contract'],terrain=s['terrain'],siteCount=19,stateCount=36)
 visual['canvas']['currentState']='Reviewed complete-city painted sources; actual compiler and strict source geometry executed. Native gameplay and release acceptance remain separate.'
 visual['assetBinding']['currentState']='Town source candidate compiled110recipes to182outputs in an isolated actual-compiler fixture. Canonical production freshness and native visual acceptance require the coordinator build and observation.'
 visual['composition_constraints']='Organic central avenue and connected dry courts/steps; complete physical feet on actual level landings, retaining masonry below floor edges, full gate and own-stair visibility. External coast water remains marine; no ordinary land exemption.'
 visual['native_visual_acceptance']='Pending current production-fresh native town/click observation; all prior town visual approval is invalidated by this source change.'
 visual['sites']=[{'id':site['id'],'buildings':site['states'],'states':len(site['states']),'native_z':next(r['native_z']for r in s['states']if r['state']==site['states'][0]),'source_states':{r['state']:r for r in s['states']if r['state']in site['states']}}for site in s['sites']]
 visual['entrance_projection']=ref(HERE/'native-transforms-v14/states.json')['path'];visual['source_visual_review']=ref(reviewcopy)['path'];visual['preserved_master_inventory']=ref(HERE/'native-transforms-v14/states.json')['path'];visual['final_source_evidence_coherent_paving_v1']=inputs
 mappings=[]
 def payload(target,b,source=None):
  canonical=ROOT/target;assert canonical.is_file(),target;dest=REPORT/'canonical-payload'/target;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b);row={'target':target,'before_sha256':sha(canonical),'after_sha256':sha(dest),'payload':ref(dest)}
  if source:row['candidate']=ref(source)
  mappings.append(row)
 payload('content/factions.json',data(patched),C/'factions.candidate.json');payload('design/town-visuals.json',data(visual))
 for name,pin in s['recipes'].items():
  p=C/'candidate-recipes'/name;assert sha(p)==pin;payload(name,p.read_bytes(),p)
 closure={};seen=set()
 closure['scripts/art_compile.py']=sha(ROOT/'scripts/art_compile.py')
 closure[reviewcopy.relative_to(ROOT).as_posix()]=sha(reviewcopy)
 def collect(v):
  if isinstance(v,dict):
   if isinstance(v.get('path'),str) and isinstance(v.get('sha256'),str) and (ROOT/v['path']).is_file():assert sha(ROOT/v['path'])==v['sha256'],'Pinned source drift '+v['path']
   for item in v.values():collect(item)
  elif isinstance(v,list):
   for item in v:collect(item)
  elif isinstance(v,str):
   p=ROOT/v
   if p.is_file() and p.resolve().is_relative_to(ROOT.resolve()):
    rel=p.relative_to(ROOT).as_posix();closure[rel]=sha(p)
    if p.suffix=='.json' and rel.startswith(HERE.relative_to(ROOT).as_posix()+'/') and rel not in seen:
     seen.add(rel)
     try:collect(load(p))
     except (UnicodeDecodeError,json.JSONDecodeError):pass
 collect(s);collect(index);collect(inputs);collect(load(HERE/'coherent-paving-repaint-v1/source-assets-index-v1.json'))
 for name in s['recipes']:collect(load(C/'candidate-recipes'/name))
 for sub,name in [('upper-left-proposal','provenance-v5.json'),('upper-left-proposal','generation-tool-records.json'),('lower-proposal','provenance-v1.json'),('lower-proposal','generation-records.json'),('menagerie-proposal','generation-record-v2.json')]:
  p=HERE/'terrain-repairs-v6'/sub/name;closure[p.relative_to(ROOT).as_posix()]=sha(p);collect(load(p))
 for sub in ('upper-left-proposal','lower-proposal'):
  for p in (HERE/'terrain-repairs-v6'/sub).glob('*.py'):closure[p.relative_to(ROOT).as_posix()]=sha(p)
 for p in [HERE/'compose_repairs_v6.py',HERE/'build_transform_packet_v7.py',HERE/'prepare_coherent_candidate_v1.py',HERE/'check_coherent_candidate_v1.py',HERE/'reproduce_crimson_patch_v6.py',HERE/'apply_guarded_coherent_paving_v1.py',Path(__file__),C/'selection.json',HERE/'entry-spans-v3/entries.json',ROOT/'build/reports/complete-town-20261027-v2/conversion-coherent-paving-v1/receipt.json']:
  closure[p.relative_to(ROOT).as_posix()]=sha(p)
 # Freeze actual helper and compiler versions too; no gate alterations.
 workpins={'scripts/faction_town_layout.py':sha(W/'scripts/faction_town_layout.py')}
 for key in ('contract','consumer_positive','consumer_negatives','independent_review'):
  p=(ROOT/inputs[key]['path']).resolve()
  if not p.is_relative_to(ROOT.resolve()):workpins[p.relative_to(W.resolve()).as_posix()]=sha(p)
 manifest={'status':'authored configuration','selected_for_coordinator':True,'canonical_files':mappings,'source_pins':closure,'workspace_pins':workpins,'content_field_changes':fields,'admission':inputs,'counts':{'recipes':110,'converted_outputs':182,'states':36,'ordinary_land_sites':17,'dwelling_sites':7,'canonical_files':len(mappings)},'apply_policy':'Coordinator only. Preflight EVERY canonical-before, candidate, payload, source and helper hash before any write. Reject drift. Source payload integration does not stage/build/install or grant native/release acceptance.','native_verified':False,'release_accepted':False}
 write(REPORT/'integration-manifest-v6.json',manifest);print(json.dumps({'manifest':ref(REPORT/'integration-manifest-v6.json'),'canonical_files':len(mappings),'source_pins':len(closure),'content_fields':len(fields)}))
if __name__=='__main__':main()
