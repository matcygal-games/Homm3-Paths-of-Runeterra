"""Freeze the finite BL2 source delivery without selecting new acceptance rules."""
from pathlib import Path
import hashlib,json,sys,html
from PIL import Image,ImageChops
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[5];WORKSPACE=PROJECT.parent
REPORT=PROJECT/'build/reports/complete-town-20261028-v1/approved-implementation-v1/physical-refinement-v1'
OUT=HERE/'checkpoint-source-finish-v1';OUT.mkdir(exist_ok=False)
VIEW=REPORT/'checkpoint-source-finish-v1';VIEW.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def ref(p):return {'path':p.relative_to(PROJECT).as_posix(),'sha256':sha(p)}
def save(p,v):p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n',encoding='utf-8')
payload_path=HERE/'compiler-source-finish-v2/payload-and-compiler.json';payload=read(payload_path)
verification_path=REPORT/'source-finish-verification-v3/receipt.json';verification=read(verification_path)
two=read(HERE/'compiler-source-finish-v2/configured-two-pass.json')
refinement_path=HERE/'structural-source-finish-v1/source-refinement-receipt.json';refinement=read(refinement_path)
consumer_path=REPORT/'consumer-consumer-source-finish-v1/receipt.json';consumer=read(consumer_path)
triage_path=REPORT/'source-finish-all35-triage-v1.json';triage=read(triage_path)
assert verification['passed']==424 and verification['failed']==0
assert two['passes']==2 and two['exact_output_bytes_equal'] and payload['recipe_count']==155 and payload['actual_output_count']==235
prior=read(HERE/'compiler-source-finish-v1/payload-and-compiler.json')
assert {r['path']:r['sha256']for r in prior['outputs']}=={r['path']:r['sha256']for r in payload['outputs']}
approved=HERE.parent/'approved-full-source-v1.png'
assert sha(approved)=='4f8cac4f1801ed366e0bacd4934084e9b76e0d25c282b3f3b36fda3835cd0712'
compiled_full=REPORT/'source-finish-verification-v3/actual-compiled-full-native.png'
assert not ImageChops.difference(Image.open(compiled_full).convert('RGBA'),Image.open(approved).convert('RGBA')).getbbox()
sys.path.insert(0,str(WORKSPACE/'scripts'))
import faction_pipeline as fp
import faction_town_layout as layout
pipeline=fp.Pipeline(PROJECT,'runeterra-bilgewater','bilgewater')
canonical_design=read(PROJECT/'design/town-visuals.json')
existing_errors,existing_dependencies=fp.inspect_town_layout(pipeline,pipeline.content())
existing={'called':'faction_pipeline.inspect_town_layout(actual canonical Pipeline, current content)',
 'helper_sha256':sha(WORKSPACE/'scripts/faction_town_layout.py'),
 'pipeline_sha256':sha(WORKSPACE/'scripts/faction_pipeline.py'),
 'canonical_design':ref(PROJECT/'design/town-visuals.json'),
 'explicit_geometry_mode':canonical_design.get('layout_geometry_mode'),
 'silhouette_selected':layout.silhouette_selected(PROJECT),
 'errors':existing_errors,'dependency_count':len(existing_dependencies),
 'scope':'Actual existing geometry-dispatch result only, not a full CLI build/preflight or native game pass.'}
save(OUT/'actual-existing-geometry-dispatch.json',existing)
inventory={}
def add(p):
 p=p.resolve()
 if not p.is_relative_to(PROJECT.resolve()):raise ValueError('Non-regional source inventory target')
 inventory[p.relative_to(PROJECT).as_posix()]=sha(p)
def walk(v):
 if isinstance(v,dict):
  if isinstance(v.get('path'),str)and isinstance(v.get('sha256'),str):
   p=PROJECT/v['path']
   if p.is_file():
    if sha(p)!=v['sha256']:raise ValueError('Pinned source drift: '+str(p))
    add(p)
  for child in v.values():walk(child)
 elif isinstance(v,list):
  for child in v:walk(child)
contract_path=HERE/'contract-source-finish-v1/layout-contract.json'
walk(read(contract_path))
for p in [payload_path,verification_path,refinement_path,consumer_path,triage_path,contract_path,
 HERE/'structural-source-finish-v1/states.json',HERE/'compiler-source-finish-v2/configured-two-pass.json',
 HERE/'compile_source_finish_v1.py',HERE/'finish_structural_sources_v1.py',Path(__file__)]:add(p)
for row in payload['recipes']:
 candidate=PROJECT/row['candidate'];assert sha(candidate)==row['sha256'];add(candidate)
 assert sha(PROJECT/row['target'])==row['before_sha256'],'Canonical recipe changed during freeze; rebase explicitly'
for row in payload['outputs']:
 p=REPORT/'compiler-source-finish-v2/compiled'/row['path'];assert sha(p)==row['sha256'];add(p)
add(PROJECT/payload['candidate_content'])
save(OUT/'pinned-files.json',{'status':'authored configuration','files':inventory,'count':len(inventory),
 'scope':'Direct current candidate refs, flat editable-source refs, payload producers, compiled bytes and executed evidence. No staging or protected original input copied.'})
change_rows=[]
current=read(PROJECT/'content/factions.json');candidate=read(PROJECT/payload['candidate_content'])
for state,row in read(HERE/'structural-source-finish-v1/states.json')['states'].items():
 old=current['bilgewater']['town']['structures'][state]['z'];new=candidate['bilgewater']['town']['structures'][state]['z']
 change_rows.append({'state':state,'before_z':old,'candidate_z':new})
save(OUT/'drawing-order-only-patch.json',{'target':'content/factions.json','target_before_sha256':sha(PROJECT/'content/factions.json'),
 'scope':'Only these35 drawing z fields. Recheck all unrelated authored content; do not overwrite current content wholesale.','rows':change_rows})
holds=[
 {'id':'source-entry-admission','scope':'New source-only visual/physical acceptance proposal',
  'states':['mageGuild3','dwellingLvl7','dwellingUpLvl7','dwellingLvl3','dwellingUpLvl3','marketplace','special3'],
  'finding':'Exact native source observations do not establish complete accessible entrances/servicing edges for these7 reviewed forms. Guild3 has gold portal but no exposed dry step; Leviathan base has no clear door and upgraded stair ends beside water; batteries/markets are open services with interrupted frontages, not painted closed-building doors.',
  'closure':'Review real source servicing contours and their explicit acceptance representation without labeling water, cliff, solid counter or structural support as a doorway. Other inherited route brushes remain provisional.'},
 {'id':'declared-material-vs-exhaustive-anatomy','scope':'Source material-role review',
  'states':['dwellingLvl3'],
  'finding':'All35 DECLARED retained material contact sets pass fixed support/no-stair tests. This does not certify the lower battery wheel/cradle contact set is exhaustive; exact source observations mark this interpretation medium/low confidence.',
  'closure':'Adjudicate actual wheel/cradle soles independently; do not grow support around endpoints or claim an unexecuted whole-town negative suite.'},
 {'id':'roost-cliff-connection','scope':'Bounded visible source-composition requirement under immutable full-image lock',
  'states':['dwellingLvl5','dwellingUpLvl5'],
  'coordinates':{'upper_landing':[624,108],'lower_stair':[591,172],'crop':[576,102,638,178]},
  'finding':'Studied source shows upper paving separated from lower stair by exposed cliff/ivy; the98pixel body-clear study cannot be repaired solely beneath opaque selected architecture. A1231pixel genuinely painted stair alternative exists but is UNSELECTED and not a full physical baseline.',
  'closure':'Preserve approved BL2 unchanged unless the coordinator/user explicitly selects a visible alternative. Report this bounded visual/access requirement as unresolved, not as VCMI movement/pathfinding failure.'},
 {'id':'whole-proposal-baseline','scope':'New source-only all35 town contract in isolated fixture',
  'finding':consumer['baseline_errors'],
  'closure':'Resolve/replace provisional true-frontage annotations and admitted depth/cover semantics, then execute whole35 positive and fully repinned displaced/stair/water/path-cut negatives. Current failed baseline is not counted as a successful negative control.'}
]
save(OUT/'remaining-acceptance-holds.json',{'status':'authored configuration','holds':holds,
 'native_gameplay_defect_proven':False,'townscreen_paths_are_engine_movement_paths':False})
full=Image.open(compiled_full).convert('RGBA')
empty=Image.open(HERE/'structural-source-finish-v1/empty-native.png').convert('RGBA')
proposal=Image.open(HERE/'route-conflict-v1/full-proposal-only.png').convert('RGBA')
crops={'roost-cliff':(576,102,638,178),'archive-portal':(488,101,524,137),
 'leviathan-stair':(99,150,148,190),'battery-apron':(230,165,322,190),
 'market-frontage':(400,297,554,325),'black-market-frontage':(88,296,174,323)}
for name,box in crops.items():
 for label,scene in [('approved',full),('empty',empty)]:scene.crop(box).save(VIEW/(name+'-'+label+'-1x.png'))
proposal.crop(crops['roost-cliff']).save(VIEW/'roost-cliff-UNSELECTED-stair-1x.png')
for name,scene in [('full',full),('empty',empty),('base',Image.open(HERE/'structural-source-finish-v1/base-native.png'))]:scene.save(VIEW/(name+'-native.png'))
packet={'status':'authored configuration','source_candidate_complete_with_limits':True,
 'approved_full':ref(approved),'approved_full_RGBA_changed_pixels':0,
 'source_index':ref(HERE/'structural-source-finish-v1/states.json'),
 'configured_payload':ref(payload_path),'configured_two_pass':ref(HERE/'compiler-source-finish-v2/configured-two-pass.json'),
 'source_verification':ref(verification_path),'source_refinement':ref(refinement_path),
 'configured_logical':155,'configured_physical':235,'configured_actual_required_inventory':387,
 'compiler_passes':2,'compiler_bytes_identical_between_passes':True,
 'compiler_v1_v2_all235_output_hashes_identical':True,
 'recipe_changes':142,'untouched_recipe_producers':13,
 'executed_source_checks':{'passed':424,'failed':0},'source_click_scenarios':36,
 'exact_original_material_pixels_restored':38,'whole_lower_form_registrations':6,
 'all16_approved_selected_forms_positions_scales_unchanged':True,
 'ordinary_sites':16,'optional_coastal_site':True,'one_site_per_creature_tier':True,
 'current_existing_geometry_dispatch':ref(OUT/'actual-existing-geometry-dispatch.json'),
 'proposed_geometry_contract_DO_NOT_SELECT_WITHOUT_REVIEW':ref(contract_path),
 'proposed_diagnostic_actual_consumer':ref(consumer_path),'proposed_diagnostic_passed':False,
 'all35_retained_traversal_diagnostic':ref(triage_path),
 'all35_positive_or_complete_meaningful_physical_negatives_claimed':False,
 'actual_diagnostic_collector_members':996,'declared_source_dependencies_byte_verified':995,
 'drawing_order_patch':ref(OUT/'drawing-order-only-patch.json'),
 'remaining_acceptance_holds':ref(OUT/'remaining-acceptance-holds.json'),
 'pinned_files':ref(OUT/'pinned-files.json'),
 'preview':ref(VIEW/'full-native.png'),
 'unselected_visible_stair_proposal':ref(HERE/'route-conflict-v1/conflict-and-alternative.json'),
 'adoption_instructions':['Root owns canonical adoption. Apply142 guarded recipe changes and drawing z fields only after source-owner review.',
  'Final runtime output235 bytes exactly match prior executed fixture source235 bytes; source-only physical proposal is explicitly not canonical.',
  'Do not introduce layout_geometry_mode or select the new HOLD contract to claim physical acceptance.',
  'Do not publish the unselected visible stair or alter approved4f8 full.',
  'Actual complete CLI build/preflight and current-stage native verification remain coordinator operations.'],
 'native_game_executed':False,'staged_or_published':False,'release_accepted':False}
save(OUT/'HANDOFF.json',packet)
text='''# BL2 source checkpoint

The user-selected fully built BL2 image is unchanged: **0 decoded RGBA pixel differences**. Current source candidate restores38 original material pixels, retains tight Corsair supports and actual Roost shoes, preserves six genuine painted hidden floor sources, registers six lower forms as complete layers, and separates the public Cannon torch/rail from the constructible battery. No new visible artwork is selected.

Actual configured compiler: **155 required logical producers /235 physical products**, two identical passes,142 changed recipes and13 preserved producers. Current source verification: **424 passed /0 failed**, including36 native-inheritance source click scenarios. This is authored configuration, not native gameplay or release acceptance.

The new source-only physical contract remains **HOLD**. Actual unchanged helper613 rejects the current Blacksmith approach/network annotation. All35 traversal diagnostics retain18 sites and35 states; these failures are not successful negative controls. The diagnostic collector contains996 members and verifies995 declared unique dependency bytes. Townscreen roads do not implement hero or army movement; this diagnostic does not prove a native gameplay defect. Existing canonical geometry-dispatch evidence is recorded separately in the source packet.

Seven independently inspected forms have unaccepted servicing/entry contours; lower Cannon exhaustive wheel/cradle bearing interpretation remains uncertain. The bounded Roost cliff-to-stair connection cannot be painted invisibly in the studied corridor. A genuinely painted1231pixel stair alternative is preserved separately, **UNSELECTED**. The approved4f8 full remains final.

Root owns integration. Use HANDOFF.json and the guarded recipe payload, apply only35 drawing z fields, preserve unrelated source edits. Do not select the new HOLD geometry contract or the visible alternative as part of source adoption. Current complete game build/runtime testing is a separate coordinator operation.
'''
(VIEW/'REPORT.md').write_text(text,encoding='utf-8')
parts=['<!doctype html><meta charset="utf-8"><title>BL2 locked source checkpoint</title><style>body{background:#171c22;color:#eee;font:16px system-ui;max-width:1250px;margin:30px auto}img{image-rendering:pixelated;border:1px solid #566}section{margin:30px 0}.row{display:flex;gap:20px;flex-wrap:wrap}figcaption{max-width:500px}a{color:#91ceff}</style>',
 '<h1>Bilgewater BL2 — locked source checkpoint</h1><p>Authored configuration. Approved full image unchanged. Actual configured155/235 compiler passes twice;424 source checks pass. New source-only physical/access diagnostic remains HOLD. These images are assembled source views, not native screenshots.</p><p><a href="REPORT.md">Evidence and limits</a></p>']
for name in ['full','empty','base']:parts.append('<section><h2>'+name.title()+'</h2><img width="800" height="374" src="'+name+'-native.png"></section>')
parts.append('<h2>Exact native crops — remaining source observations</h2><p>Displayed at native resolution. Browser zoom may magnify them; no invented stair/floor is selected.</p>')
for name,box in crops.items():
 parts.append('<section><h3>'+html.escape(name)+'</h3><p>Native box '+str(list(box))+'</p><div class="row">')
 for label in ['approved','empty']:parts.append('<figure><img src="'+name+'-'+label+'-1x.png"><figcaption>'+label+'</figcaption></figure>')
 if name=='roost-cliff':parts.append('<figure><img src="roost-cliff-UNSELECTED-stair-1x.png"><figcaption>UNSELECTED genuine stair proposal; no publication or current-full change.</figcaption></figure>')
 parts.append('</div></section>')
(VIEW/'index.html').write_text('\n'.join(parts),encoding='utf-8')
print(json.dumps({'packet':ref(OUT/'HANDOFF.json'),'preview':ref(VIEW/'index.html'),'existing_geometry_dispatch':existing,'pinned_files':len(inventory),'checks':424,'failed':0},indent=2))
