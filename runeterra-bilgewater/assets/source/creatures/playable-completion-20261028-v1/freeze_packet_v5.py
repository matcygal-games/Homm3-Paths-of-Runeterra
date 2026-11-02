"""Freeze a guarded coordinator-only integration payload and bounded source closure."""
from pathlib import Path
import json,hashlib,os,sys,html
from PIL import Image
from split_painted_islands import islands
S=Path(__file__).resolve().parent;P=S.parents[3];W=P.parent;R=P/'build/reports/painted-creature-completion-20261028-v1/final-packet-v5';R.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(W/'scripts'));import source_export_guard
from faction_creature_preview import measure_rgba,native_crop_contract
U=['bilgeRat','seaDog','corsair','pirateMarksman','shellshotGunner','reefBombardier','krakenPriest','tideHierophant','boardingCaptain','fleetVeteran']
def sha(b):return hashlib.sha256(b).hexdigest()
def enc(o):return(json.dumps(o,sort_keys=True,indent=2)+'\n').encode()
def load(p):return json.loads(p.read_text())
def rel(p):return p.relative_to(P).as_posix()
def write(p,o):
 b=enc(o)
 if p.exists()and p.read_bytes()!=b:raise RuntimeError('Preserve frozen report '+str(p))
 if not p.exists():p.write_bytes(b)
manifest=P/'assets/manifest.json';entries=load(manifest)['assets'];creatures=load(P/'content/creatures.json');creatures=creatures.get('creatures',creatures)
changes=[];variants=[];offsets={};closure=set();source_review=[];body=[];outputs={}
for u in U:
 cfgp=S/u/'assembly-config-v5.json';cfg=load(cfgp);cohort=S/u/'cohort-candidate-v5.json';rep=P/f'build/reports/painted-creature-completion-20261028-v1/{u}/candidate-v5';receipt=rep/'actual-compiler-replay-v1.json';replay=load(receipt);outputs.update(replay['output_hashes'])
 variants.append({'unit':u,'config':rel(cfgp),'config_sha256':sha(cfgp.read_bytes()),'provenance':rel(cohort),'provenance_sha256':sha(cohort.read_bytes()),'receipt':rel(receipt),'receipt_sha256':sha(receipt.read_bytes()),'battle_frames':len(load(cohort)['frames']),'physical_outputs_per_pass':replay['outputs_per_pass'],'selected':False})
 for p in sorted((S/'proposed-recipes-v5'/u).glob('*.json')):
  r=load(p);name=r['output_path'];old=next(e for e in entries if e['output_path']==name);closure.add(p);g=r['generation'];closure.update(P/a['path']for a in g['production_inputs']);closure.add(P/g['provenance']);closure.add(P/g['painted_master'])
  for group in r.get('groups',[]):closure.update(P/f['source']for f in group['frames'])
  if r.get('source'):closure.add(P/r['source'])
  changes.append({'output_path':name,'expected_manifest_entry_sha256':sha(enc(old)),'expected_manifest_entry':old,'proposed_recipe':rel(p),'proposed_recipe_sha256':sha(p.read_bytes()),'compiled_sha256':replay['output_hashes'][name],'dimensions':r.get('canvas',r.get('size')),'group_frame_counts':{str(a['group']):len(a['frames'])for a in r.get('groups',[])}})
 for name,plate in cfg['plates'].items():
  p=S/plate['source'];im=Image.open(p).convert('RGBA');items=islands(im)
  if len(items)!=plate['expected_islands']:raise RuntimeError('Source island inventory changed')
  for pose,a in plate['poses'].items():
   box=items[a['island']]['box'];edge=box[0]==0 or box[1]==0 or box[2]==im.width or box[3]==im.height
   if edge:raise RuntimeError('Selected source key touches full master edge')
   source_review.append({'unit':u,'pose':pose,'source':rel(p),'source_sha256':sha(p.read_bytes()),'island':a['island'],'box':box,'source_dimensions':list(im.size),'touches_outer_edge':False})
 for group in [0,1,2]:
  for p in sorted((S/u/'native-v5/right').glob(f'g{group:02d}-*.png')):body.append({'unit':u,'group':group,'frame':rel(p),**measure_rgba(p.read_bytes(),[150,155,250,275])})
 if cfg.get('muzzle_measurements'):
  m=cfg['muzzle_measurements'];off={}
  for direction in ['upper','middle','lower']:
   off[direction+'X'],off[direction+'Y']=m[direction]['native_offset']
  offsets[u]={'expected_graphics_sha256':sha(enc(creatures[u]['graphics'])),'proposed_missile_patch':{'attackClimaxFrame':4,'offset':off},'source_measurements':m,'status':'design proposal','native_alignment':'not_run'}
closure.update([Path(__file__),S/'test_final_candidates_v5.py'])
privacy=source_export_guard.check(P,files={P.name+'/'+rel(p):p.read_bytes()for p in sorted(closure)})
write(R/'selected-source-export-admission-v5.json',privacy)
if not privacy['source_export_eligible']:raise RuntimeError('Actual selected source export admission failed: '+repr(privacy['errors']))
tests=load(R/'executed-tests-v5.json')
if not tests['successful']:raise RuntimeError('Executed v5 regressions have not passed')
write(R/'selected-source-body-and-stock-crop-v5.json',{'status':'authored configuration','source_key_inventory':source_review,'selected_source_keys_touching_master_edge':0,'actual_native_crop_consumer':native_crop_contract(W),'stock_crop_frames':body,'stock_crop_outside_pixels':sum(a['outside_pixels']for a in body),'native_execution':False,'visual_approval_granted':False})
native=['client/battle/BattleStacksController.cpp','client/battle/BattleAnimationClasses.cpp','client/battle/CreatureAnimation.cpp','client/widgets/MiscWidgets.cpp','client/widgets/Images.cpp']
packet={'status':'authored configuration','selected':False,'apply_automatically':False,'scope':'Ten Bilgewater ordinary creature variants only; approved BL2 town and all hero/content/canonical files untouched','expected_manifest_sha256':sha(manifest.read_bytes()),'variant_count':len(variants),'recipe_count':len(changes),'physical_outputs_per_compile_pass':len(outputs),'variants':variants,'changes':changes,'graphics_offset_proposals':offsets,'native_consumer_pins':[{'workspace_path':'vcmi-develop/vcmi-develop/'+n,'sha256':sha((W/'vcmi-develop/vcmi-develop'/n).read_bytes())}for n in native],'source_closure_files':len(closure),'source_export_admission':{'path':rel(R/'selected-source-export-admission-v5.json'),'sha256':sha((R/'selected-source-export-admission-v5.json').read_bytes()),'eligible':True},'executed_regressions':{'path':rel(R/'executed-tests-v5.json'),'sha256':sha((R/'executed-tests-v5.json').read_bytes()),**tests},'source_crop_evidence':{'path':rel(R/'selected-source-body-and-stock-crop-v5.json'),'sha256':sha((R/'selected-source-body-and-stock-crop-v5.json').read_bytes())},'rebuild':'For each listed config run project Python -B assets/source/creatures/playable-completion-20261028-v1/assemble_from_config_v3.py <config>; actual faction converter.plan executes twice; coordinator alone publishes canonical recipes/manifest/assets and production CLI stage','limitations':['In-game appearance, intermediate turn quarter handedness, loop gait/root continuity and source-sized crest acceptance are still pending; exact displayed facing boundary algebra and stock source crop are tested','Physical muzzle offsets are proposed from original painted release poses; live native event/projectile alignment still needs observation','Source privacy admission is bounded to complete selected input/output closure; whole-faction archive admission remains coordinator work','Rights/artist approvals and release acceptance have not been granted; no game process or approved-town asset was changed']}
write(R/'root-integration-packet-v5.json',packet)
write(R/'physical-output-hashes-v5.json',outputs)
cards=[]
for u in U:
 rep=P/f'build/reports/painted-creature-completion-20261028-v1/{u}/candidate-v5';src=S/u/'native-v5/companions'
 link=lambda p:html.escape(os.path.relpath(p,R).replace(os.sep,'/'),quote=True)
 cards.append('<section><h2>'+u+'</h2><p><a href="'+link(rep/'index.html')+'">All native action frames and motions</a></p><div class="row"><img class="portrait" src="'+link(src/'large.png')+'"><img class="map" src="'+link(src/'map.png')+'"><img class="map" src="'+link(src/'attackLeft.png')+'"><img class="map" src="'+link(src/'attackRight.png')+'"><img src="'+link(rep/'g00.gif')+'"><img src="'+link(rep/'g12.gif')+'"><img src="'+link(rep/'g05.gif')+'"></div><img class="board" src="'+link(rep/'native-contact-sheet-v1.png')+'"></section>')
page='<!doctype html><html><meta charset="utf-8"><title>Bilgewater ten painted creature candidates</title><style>body{background:#1c2725;color:#eee;font:16px system-ui;margin:30px}a{color:#a7e1e2}.row{display:flex;align-items:center;gap:12px;flex-wrap:wrap}.row img{background:#566052;image-rendering:pixelated}.portrait{width:128px;height:128px}.map{transform:none;min-width:64px}.board{max-width:100%}section{border-top:1px solid #567;margin-top:25px}</style><h1>Bilgewater: ten painted creature candidates</h1><p><strong>Authored configuration; unselected.</strong>64 recipes and948 real physical outputs per compile pass. Editable original painted masters, exact prompts and deterministic native frames. No town or hero changes. Native appearance/gait/crest/event alignment and release approval remain separate.</p><p><a href="root-integration-packet-v5.json">Guarded integration packet</a> · <a href="executed-tests-v5.json">Executed regressions</a> · <a href="selected-source-export-admission-v5.json">Actual source privacy admission</a> · <a href="selected-source-body-and-stock-crop-v5.json">Source outline/crop evidence</a></p>'+''.join(cards)+'</html>'
p=R/'index.html';raw=page.encode()
if p.exists()and p.read_bytes()!=raw:raise RuntimeError('Preserve frozen gallery')
if not p.exists():p.write_bytes(raw)
print(json.dumps({'variants':len(variants),'recipes':len(changes),'outputs_per_pass':len(outputs),'selected_source_keys':len(source_review),'stock_frames':len(body),'stock_outside_pixels':sum(a['outside_pixels']for a in body),'source_closure_files':len(closure),'privacy_errors':len(privacy['errors']),'tests_run':tests['tests_run'],'packet_sha256':sha((R/'root-integration-packet-v5.json').read_bytes()),'gallery':rel(R/'index.html')}))
