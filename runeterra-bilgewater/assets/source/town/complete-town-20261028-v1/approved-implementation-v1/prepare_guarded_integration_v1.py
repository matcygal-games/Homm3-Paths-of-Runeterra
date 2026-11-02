"""Produce scoped coordinator patches without writing canonical input files.

Manifest replacements bind each town entry independently, preserving concurrent
creature work. Faction changes are drawing z values only. Physical selection is
deliberately held until the real public consumer passes its exact contract.
"""
from pathlib import Path
import json,hashlib,copy
from PIL import Image,ImageChops
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[4]
REPORT=PROJECT/'build/reports/complete-town-20261028-v1/approved-implementation-v1/integration-v1'
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def valuepin(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def ref(p):return {'path':p.relative_to(PROJECT).as_posix(),'sha256':sha(p)}
def save(p,v):p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
def apply_manifest(value,patch):
 result=copy.deepcopy(value);lookup={a['id']:a for a in result['assets']}
 for row in patch:
  if valuepin(lookup[row['id']])!=row['before_value_sha256']:raise ValueError('Town manifest entry changed: '+row['id'])
 for row in patch:
  index=next(n for n,a in enumerate(result['assets']) if a['id']==row['id']);result['assets'][index]=copy.deepcopy(row['after'])
 return result

def main():
 REPORT.mkdir(parents=True,exist_ok=False);out=HERE/'integration-v1';out.mkdir(exist_ok=False)
 payload=load(HERE/'town-compiler-approved-v2/payload-and-compiler.json')
 receipts=load(HERE/'town-compiler-approved-v2/compiler-receipts.json')
 cohort=load(HERE/'states-hidden-support-v2.json')
 manifest_path=PROJECT/'assets/manifest.json';manifest=load(manifest_path)
 outputpins={r['path']:r['sha256'] for r in payload['outputs']}
 recipes={r['target']:r for r in payload['recipes']}
 patches=[]
 for asset in manifest['assets']:
  source=asset.get('source',{});target=source.get('recipe')
  if target not in recipes:continue
  after=copy.deepcopy(asset);after['sha256']=outputpins[after['output_path']]
  after['source']['recipe_sha256']=recipes[target]['sha256']
  after['dimensions']=[800,374] if asset['role'] in ['town-structure-animation','town-background','town-area-mask','town-border'] else after.get('dimensions')
  patches.append({'id':asset['id'],'before_value_sha256':valuepin(asset),'after':after})
 if len(patches)!=155:raise ValueError('Expected exactly155 selected town manifest entries')
 proposed=apply_manifest(manifest,patches)
 outsiders=[a for a in manifest['assets'] if a['id'] not in {p['id'] for p in patches}]
 if outsiders!=[a for a in proposed['assets'] if a['id'] not in {p['id'] for p in patches}]:raise ValueError('Unrelated asset changed')
 # Genuine concurrency regression: allow a foreign creature update, but reject
 # a changed town producer instead of overwriting either silently.
 concurrent=copy.deepcopy(manifest)
 foreign=next(a for a in concurrent['assets'] if a['id'] not in {p['id'] for p in patches})
 foreign['concurrent_unit_worker_marker']='preserve this independent update'
 merged=apply_manifest(concurrent,patches)
 preserved=next(a for a in merged['assets'] if a['id']==foreign['id'])==foreign
 stale=copy.deepcopy(manifest);target=next(a for a in stale['assets'] if a['id']==patches[0]['id']);target['sha256']='0'*64
 try:apply_manifest(stale,patches)
 except ValueError:rejected=True
 else:rejected=False
 if not preserved or not rejected:raise ValueError('Scoped integration regression failed')
 faction_path=PROJECT/'content/factions.json';factions=load(faction_path)
 zpatch=[]
 for key,row in cohort['states'].items():
  structure=factions['bilgewater']['town']['structures'][key]
  zpatch.append({'pointer':'/bilgewater/town/structures/'+key+'/z','before':structure.get('z'),'after':row['z'],'before_structure_value_sha256':valuepin(structure)})
 design_path=PROJECT/'design/town-visuals.json';design=load(design_path);sites={}
 for key,row in cohort['states'].items():sites.setdefault(row['site'],[]).append(key)
 proposed_sites={}
 for name,keys in sites.items():
  mask=Image.new('L',(800,374))
  for key in keys:mask=ImageChops.lighter(mask,Image.open(PROJECT/cohort['states'][key]['frame']).getchannel('A').point(lambda a:255 if a>=8 else 0))
  x0,y0,x1,y1=mask.getbbox();proposed_sites[name]={'box':[x0,y0,x1-x0,y1-y0],'z':cohort['states'][keys[0]]['z'],'keys':keys}
 design_proposal={'before':ref(design_path),'source_cohort':ref(HERE/'states-hidden-support-v2.json'),
  'proposed_background':cohort['background'],'approved_complete_scene':load(HERE/'approved-selection.json')['approved_full'],
  'proposed_sites':proposed_sites,'unchanged_keys':sorted(set(design)-{'background','sites','identity','review','visual_approval_granted'}),
  'layout_geometry_mode':'silhouette-v2','layout_contract':None,
  'blocking_reason':'The actual35-state physical contract, truthful planes, shared clear paths and real displacement negative controls are still pending; do not adopt an unpinned or empty contract.'}
 save(out/'manifest-town-entry-patch.json',{'status':'authored configuration','baseline_manifest':ref(manifest_path),'operation':'replace exact155 entries by ID after per-entry semantic SHA guard; preserve all other entries verbatim','entries':patches})
 save(out/'faction-drawing-patch.json',{'status':'authored configuration','baseline_factions':ref(faction_path),'scope':'35 actual town drawing z fields only; preserve gameplay, building IDs/ancestry/economy/units/heroes','changes':zpatch})
 save(out/'town-design-proposal.json',design_proposal)
 packet={'status':'authored configuration','scope':'Coordinator-only guarded source integration packet; no canonical writes, staging or runtime.',
  'admissible_for_canonical_integration':False,'required_remaining_boundary':'Exact physical source contract and unchanged public consumer, collector, click exposure and real recompiled displacement controls, followed by independent review.',
  'approved_full_sha256':cohort['approved_full_sha256'],'approved_full_changed_pixels':0,
  'producer_payload':ref(HERE/'town-compiler-approved-v2/payload-and-compiler.json'),'compiler_receipts':ref(HERE/'town-compiler-approved-v2/compiler-receipts.json'),
  'source_verification':ref(PROJECT/'build/reports/complete-town-20261028-v1/approved-implementation-v1/source-verification-v1/result.json'),
  'manifest_patch':ref(out/'manifest-town-entry-patch.json'),'drawing_patch':ref(out/'faction-drawing-patch.json'),'design_proposal':ref(out/'town-design-proposal.json'),
  'actual155_recipe_count':len(recipes),'actual235_output_count':len(outputpins),'drawing_field_count':len(zpatch),
  'scoped_merge_tests':{'concurrent_foreign_creature_entry_preserved':preserved,'changed_town_entry_rejected':rejected},
  'native_verified':False,'release_accepted':False}
 save(out/'integration-packet.json',packet);save(REPORT/'integration-packet.json',packet)
 print(json.dumps({'packet':str(out/'integration-packet.json'),'sha256':sha(out/'integration-packet.json'),'town_entries':len(patches),'drawing_fields':len(zpatch),'admissible':False}))
if __name__=='__main__':main()
