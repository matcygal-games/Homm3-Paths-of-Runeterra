"""Finite current art/ownership/compiler checks, distinct from road acceptance.

Runs actual configured products and native-source area-family exposure even
when a proposed source-only road diagnostic is HOLD. No game is launched and
no failing physical baseline is counted as a successful negative control.
"""
from pathlib import Path
import hashlib,json,importlib.util,sys
from PIL import Image,ImageChops,ImageOps
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[5];WORKSPACE=PROJECT.parent
REPORT=PROJECT/'build/reports/complete-town-20261028-v1/approved-implementation-v1/physical-refinement-v1/source-finish-verification-v3';REPORT.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(PROJECT).as_posix(),'sha256':sha(p)}
def read(p):return json.loads(p.read_text())
def save(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
index_path=HERE/'structural-source-finish-v1/states.json';index=read(index_path);receipt=read(HERE/'structural-source-finish-v1/source-refinement-receipt.json')
payload_path=HERE/'compiler-source-finish-v2/payload-and-compiler.json';payload=read(payload_path)
compiled=PROJECT/'build/reports/complete-town-20261028-v1/approved-implementation-v1/physical-refinement-v1/compiler-source-finish-v2/compiled'
content=read(HERE/'compiler-source-finish-v2/content/factions.json');town=content['bilgewater']['town']
checks=[]
def check(name,ok,details=None):
 checks.append({'check':name,'passed':bool(ok),'details':details})
 if not ok:raise AssertionError(name+': '+str(details))
for out in payload['outputs']:check('actual-compiler-product:'+out['path'],sha(compiled/out['path'])==out['sha256'])
actual_frames={}
for key,row in index['states'].items():
 structure=town['structures'][key];animation=read(compiled/'Content/Sprites'/structure['animation']);seq=next(s for s in animation['sequences']if s['group']==0)
 path=compiled/'Content/Sprites'/animation['basepath']/seq['frames'][0]
 check('actual-native-frame-PNG-byte-link:'+key,sha(path)==row['frame_sha256'])
 actual_frames[key]=Image.open(path).convert('RGBA')
 check('actual-native-area-source-link:'+key,sha(compiled/'Content/Sprites'/structure['area'])==row['area_sha256'])
 check('actual-native-border-source-link:'+key,sha(compiled/'Content/Sprites'/structure['border'])==row['border_sha256'])
for key,row in receipt['exact_restorations'].items():
 original=Image.open(PROJECT/row['original']['path']).convert('RGBA');current=actual_frames[key];t=receipt['whole_lower_registrations'].get(key,{}).get('transform',{});dx,dy=t.get('offset',[0,0])
 for x,y in row['exact_original_RGBA_pixels']:check('exact-original-sill-restored:'+key+':'+str([x,y]),current.getpixel((x+dx,y+dy))==original.getpixel((x,y)))
ancestor=read(PROJECT/receipt['ancestor']['path'])
for key,r in receipt['whole_lower_registrations'].items():
 source=Image.open(PROJECT/ancestor['states'][key]['frame']).convert('RGBA')
 # Guild originals first receive their exact original sill restoration.
 if key in receipt['exact_restorations']:
  original=Image.open(PROJECT/receipt['exact_restorations'][key]['original']['path']).convert('RGBA')
  for xy in receipt['exact_restorations'][key]['exact_original_RGBA_pixels']:source.putpixel(tuple(xy),original.getpixel(tuple(xy)))
 t=r['transform'];dx,dy=t['offset']
 if 'scale'in t:
  cx,cy=t['pivot'];s=t['scale'];expected=source.transform((800,374),Image.Transform.AFFINE,(1/s,0,cx-(cx+dx)/s,0,1/s,cy-(cy+dy)/s),Image.Resampling.BICUBIC)
 elif 'mirror_axis_twice_x'in t:
  expected=Image.new('RGBA',(800,374));expected.paste(ImageOps.mirror(source),(t['mirror_axis_twice_x']-799+dx,dy))
 else:expected=Image.new('RGBA',(800,374));expected.paste(source,(dx,dy))
 check('whole-lower-transform-exact-replay:'+key,expected.tobytes()==actual_frames[key].tobytes(),r)
fixture_mask=Image.open(HERE/'structural-source-finish-v1/base-cannon-public-fixture-ownership.png').convert('L')
check('base-Cannon-public-fixture-absent-from-constructible-alpha',not ImageChops.multiply(fixture_mask,actual_frames['dwellingLvl3'].getchannel('A')).getbbox())
bg=Image.open(compiled/'Content/Sprites'/town['townBackground']).convert('RGBA')
check('native-background-source-RGBA-link',bg.tobytes()==Image.open(PROJECT/index['background']).convert('RGBA').tobytes())
full=bg.copy()
for key in index['full_scene_states']:full.alpha_composite(actual_frames[key])
approved_path=HERE.parent/'approved-full-source-v1.png';approved=Image.open(approved_path).convert('RGBA')
changed=sum(any(v)for v in ImageChops.difference(full,approved).get_flattened_data());check('actual-compiled-fully-built-BL2-immutable-RGBA',changed==0,{'changed_pixels':changed,'approved_source':ref(approved_path)})
full.save(REPORT/'actual-compiled-full-native.png',compress_level=9,optimize=False)
support=read(HERE/'source-finish-physical-v2/support-and-source-roles.json')
for key,r in support['states'].items():check('declared-material-support-and-no-stairs:'+key,r['outside_effective_actual_support_pixels']==0 and r['structural_contact_on_stairs_pixels']==0,r)
spec=importlib.util.spec_from_file_location('actual_source_check',HERE/'check_candidate.py');source_check=importlib.util.module_from_spec(spec);spec.loader.exec_module(source_check)
fixture=PROJECT/'build/reports/complete-town-20261028-v1/approved-implementation-v1/physical-refinement-v1/fixture-v6/runeterra-bilgewater';contract=read(HERE/'contract-source-finish-v1/layout-contract.json')
click=source_check.click_exposure(fixture,{'factions':read(fixture/'content/factions.json')},contract)
save(REPORT/'actual-native-source-click-exposure.json',click);check('actual-35states-in36-native-inheritance-area-scenes',len(click['scenes'])==36)
baseline=read(PROJECT/'build/reports/complete-town-20261028-v1/approved-implementation-v1/physical-refinement-v1/consumer-consumer-source-finish-v1/receipt.json')
triage=read(PROJECT/'build/reports/complete-town-20261028-v1/approved-implementation-v1/physical-refinement-v1/source-finish-all35-triage-v1.json')
check('all35-current-states-retained-in-strict-traversal-diagnostics',triage['case_count']==35 and triage['all35states_and18sites_retained_each_case'])
report={'status':'authored configuration','source_index':ref(index_path),'configured_payload':ref(payload_path),'configured_two_pass':ref(HERE/'compiler-source-finish-v2/configured-two-pass.json'),'checks':checks,'passed':sum(c['passed']for c in checks),'failed':sum(not c['passed']for c in checks),'actual_compiled_full_RGBA_changed_pixels':changed,'exact_original_restored_pixels':sum(r['count']for r in receipt['exact_restorations'].values()),'declared_material_support_states':len(support['states']),'source_click_scenes':len(click['scenes']),'current_proposed_physical_baseline_passed':baseline['valid_complete_baseline'],'current_proposed_physical_errors':baseline['baseline_errors'],'actual_collector_members_on_diagnostic':baseline['actual_collector_member_count'],'geometry_diagnostic_scope':'New own-source proposed physical/road contract in an isolated working fixture, not canonical opt-in, not VCMI townscreen movement or a native gameplay defect. Existing configured compiler membership/grammar independently passes.','native_game_executed':False,'release_accepted':False,'source_entry_limits':receipt['current_source_limits']}
save(REPORT/'receipt.json',report);print(json.dumps({k:report[k]for k in ('passed','failed','actual_compiled_full_RGBA_changed_pixels','exact_original_restored_pixels','declared_material_support_states','source_click_scenes','current_proposed_physical_baseline_passed','actual_collector_members_on_diagnostic')}))
