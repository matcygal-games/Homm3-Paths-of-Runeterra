"""Seal ready bounded source candidates; never mutate canonical or historical input."""
from pathlib import Path
import copy,json,sys
from PIL import Image
from assemble import HERE,PROJECT,read,dump,ref,rel,sha,APPROVED

REPORT=PROJECT/'build/reports/complete-town-20261028-v1/approved-implementation-v3'

def refs(value):
 if isinstance(value,dict):
  if isinstance(value.get('path'),str) and isinstance(value.get('sha256'),str):yield value
  for child in value.values():yield from refs(child)
 elif isinstance(value,list):
  for child in value:yield from refs(child)

def main():
 idx=read(HERE/'frame-index.json');recipes=read(HERE/'recipe-index.json')
 compiled=read(REPORT/'compiler-receipt.json');physical=read(REPORT/'physical-baseline-receipt.json')
 negative=read(REPORT/'physical-negatives-v3/receipt.json');replay=read(REPORT/'source-replay-v2/receipt.json');construction=read(REPORT/'construction-receipt.json')
 assert sha(HERE/'approved-full.png')==APPROVED==sha(REPORT/'compiled-approved-full.png')
 assert compiled['compiled_full_PNG_bytes_exact'] and compiled['compiled_decoded_RGBA_exact']
 assert physical['physical_pass'] and not physical['physical_baseline_errors'] and physical['actual_public_source_collector']['exact']
 assert negative['all_physical_controls_passed'] and negative['baseline_restored_byte_exact']
 assert replay['all_compiled_output_hashes_reproduced_exactly'] and replay['all_prepared_PNGs_reproduced_exactly']
 assert construction['actual_state_count']==35 and not construction['errors']
 boat=read(REPORT/'boat-ownership-receipt.json')
 assert boat['all_nine_observed_boat_feature_probes_pass'] and boat['unrelated34_state_layer_RGBA_unchanged']
 assert (len(recipes['recipes']),compiled['output_count'],replay['prepared_PNG_count'])==(155,235,184)
 assert sha(PROJECT/'content/factions.json')==physical['before_canonical_factions_sha256']==construction['factions_sha256']
 for row in recipes['recipes']:
  assert sha(PROJECT/row['candidate'])==row['sha256']
  assert sha(PROJECT/row['canonical'])==row['before_sha256'],'Canonical recipe drift: '+row['canonical']
 for name,digest in compiled['outputs'].items():assert sha(REPORT/'compiled'/name)==digest
 canonical=read(PROJECT/'content/factions.json');proposed=read(HERE/'factions-candidate.json');patched=copy.deepcopy(canonical);patches=[]
 for state in idx['frames']:
  before={k:canonical['ionia']['town']['structures'][state].get(k)for k in ('x','y','z')};after={k:proposed['ionia']['town']['structures'][state].get(k)for k in ('x','y','z')}
  patches.append({'building':state,'before':before,'after':after});patched['ionia']['town']['structures'][state].update(after)
 assert patched==proposed,'Non-drawing faction change or canonical drift'
 contract=read(PROJECT/physical['contract']['path']);sites={r['id']:r for r in contract['sites']}
 def site(name):
  s=sites[name];return {'box':s['box'],'z':s['depth'],'keys':s['states'],'entrance':s['entrance'],'silhouette_mask':s['silhouette_mask']}
 design=read(PROJECT/'design/town-visuals.json');design.update(status='authored configuration',visual_approval_granted=False,layout_geometry_mode='silhouette-v2',layout_contract=physical['contract'],canvas=[800,374],background=idx['background']['path'],ordinary_land_sites=16,optional_coastal_sites=1,sites={n:site(n)for n in sites if n not in ('coast','grail')},special_sites={n:site(n)for n in ('coast','grail')},building_masters={s:{'source_painting':r['source_painting'],'source_painting_sha256':r['source_painting_sha256'],'secondary_sources':r.get('secondary_sources',[])}for s,r in idx['frames'].items()},selection={'approved_full':idx['complete_scene'],'user_choice':'IL4 / Fully built; no further visible design changes','user_full_image_approved':True},review='Selected complete PNG is exact and source/compiler/physical checks executed successfully. Independent all-state art review and fresh native observation remain separate; this source candidate does not claim release acceptance.')
 assert len(design['sites'])==16 and len(design['special_sites'])==2
 dump(HERE/'town-visuals-candidate.json',design)
 old=HERE.parent/'approved-implementation-v1';oldpacket=read(old/'integration-packet.json');oldreport=PROJECT/'build/reports/complete-town-20261028-v1/approved-implementation-v1';oldcompiled=read(oldreport/'compiler-receipt.json')
 assert sha(old/'integration-packet.json')=='3dc79156dd2d438b3d25ece90e9dc819d413dcafca0ec8d9384f863c31ab94f3'
 for name,digest in oldpacket['source_inventory'].items():assert sha(PROJECT/name)==digest,'Held v1 source changed: '+name
 for name,digest in oldcompiled['outputs'].items():assert sha(oldreport/'compiled'/name)==digest,'Held v1 compiled changed: '+name
 prior=HERE.parent/'approved-implementation-v2';priorpacket=read(prior/'integration-packet.json');priorreport=PROJECT/'build/reports/complete-town-20261028-v1/approved-implementation-v2';priorcompiled=read(priorreport/'compiler-receipt.json')
 assert sha(prior/'integration-packet.json')=='8c6c512efbd7673724662c2dacf2d832c9f53ce847c2beb4ecfd104306086323'
 for name,digest in priorpacket['source_inventory'].items():assert sha(PROJECT/name)==digest,'Held v2 source changed: '+name
 for name,digest in priorcompiled['outputs'].items():assert sha(priorreport/'compiled'/name)==digest,'Held v2 compiled changed: '+name
 inventory={}
 for value in [read(HERE/'source-inputs.json'),contract]:
  for record in refs(value):
   path=PROJECT/record['path'];assert path.is_file() and sha(path)==record['sha256'],'Source reference drift: '+record['path'];inventory[record['path']]=record['sha256']
 for p in sorted((HERE/'prepared').rglob('*.png')):inventory[rel(p)]=sha(p)
 for p in sorted((HERE/'views').glob('*.png')):inventory[rel(p)]=sha(p)
 for row in recipes['recipes']:inventory[row['candidate']]=row['sha256']
 for n in ('approved-full.png','selection.json','frame-index.json','source-inputs.json','art-source-inputs.json','recipe-index.json','factions-candidate.json','town-visuals-candidate.json','FEASIBILITY.md','HANDOFF.md','REQUIREMENTS.json','seal_packet.py','verify_source_replay.py','verify_construction.py','verify_boat_ownership.py','consumer_replay.py','physical_negative_controls.py','physical-negative-plan.json'):
  inventory[rel(HERE/n)]=sha(HERE/n)
 metadata=[]
 for name in inventory:
  assert not Path(name).is_absolute() and '..' not in Path(name).parts
  assert not name.lower().endswith(('.blend','.blend1')) and '/private-' not in name.lower()
  if name.lower().endswith('.png'):
   with Image.open(PROJECT/name) as im:
    if im.info:metadata.append(name)
 assert not metadata,'Unexpected PNG metadata: '+str(metadata)
 reports={n:ref(REPORT/n)for n in ('compiler-receipt.json','construction-receipt.json','boat-ownership-receipt.json','physical-baseline-receipt.json','physical-negatives-v3/receipt.json','source-replay-v2/receipt.json')}
 guards={n:sha(PROJECT/n)for n in ('content/factions.json','design/town-visuals.json','assets/manifest.json')}
 packet={'status':'authored configuration','integration_allowed':True,'integration_scope':'Ready guarded town source candidate for coordinator integration and independent review; canonical/stage/native publication belongs to coordinator.','approved_full':idx['complete_scene'],'user_full_image_approved':True,'all_state_visual_approval_granted':False,'recipe_count':155,'compiled_output_count':235,'prepared_PNG_count':184,'construction_state_count':35,'ordinary_land_sites':16,'optional_coast_sites':1,'separate_grail_sites':1,'exact_compiled_approved_RGBA':True,'exact_compiled_approved_PNG_bytes':True,'reports':reports,'physical_baseline_errors':[],'source_collector':physical['actual_public_source_collector'],'all_four_physical_negatives_passed':True,'fresh_raw_source_replay_exact':True,'guarded_sources':guards,'faction_payload':ref(HERE/'factions-candidate.json'),'drawing_only_patches':patches,'design_payload':ref(HERE/'town-visuals-candidate.json'),'recipes':recipes['recipes'],'physical_contract':physical['contract'],'generated_manifest_delta':{'method':'Coordinator production CLI must regenerate actual manifest from selected recipes. These actual235 compiled hashes are guards, not a hand-written canonical manifest.','outputs':compiled['outputs']},'source_inventory':inventory,'preserved_v1':{'packet_sha256':sha(old/'integration-packet.json'),'source_files_checked':len(oldpacket['source_inventory']),'compiled_files_checked':len(oldcompiled['outputs']),'all_unchanged':True},'preserved_v2':{'packet_sha256':sha(prior/'integration-packet.json'),'source_files_checked':len(priorpacket['source_inventory']),'compiled_files_checked':len(priorcompiled['outputs']),'all_unchanged':True},'boat_ownership_repair':{'genuine_local_absence':boat['targeted_genuine_repair'],'nine_observed_feature_probes_pass':True,'other34_state_RGBA_unchanged':True,'actual_background_delta_bounds':boat['actual_background_change_bounds']},'open_items':[{'id':'independent-final-source-review','next_action':'Independent native-size contour/semantic review of this exact source and physical contract; source/compiler checks already pass.'},{'id':'fresh-native-town-verification','next_action':'After coordinator production build/stage, verify construction/clicks, service and replacement visibility, boat/Grail, save/reload and native appearance.'}],'canonical_modified':False,'native_execution':False,'runtime_verified':False,'release_accepted':False}
 dump(HERE/'integration-packet.json',packet)
 print(json.dumps({'packet':rel(HERE/'integration-packet.json'),'sha256':sha(HERE/'integration-packet.json'),'inventory_files':len(inventory),'physical_contract':physical['contract'],'integration_allowed':True,'approved_full_PNG':APPROVED,'old_v1_unchanged':True}))

if __name__=='__main__':main()
