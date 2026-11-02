"""Bound native-consumer checks and guarded proposal; never edits live selection."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps
import copy,hashlib,importlib.util,json,sys
import assemble_packets as common
SOURCE=common.SOURCE;PROJECT=common.PROJECT;REPORT=common.REPORT
def load_module(path,name):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def semantic_errors(battle,companions):
 errors=[];groups={r['group']:r['frames'] for r in battle['groups']}
 if groups[22][-1]['source_sha256']!=groups[5][-1]['source_sha256']:errors.append('DEAD22 differs from final DEATH5')
 for role in ('attackLeft','attackRight'):
  if companions[role].get('source_canvas')!=[64,64]:errors.append(role+' encounter canvas must64x64')
 for g in (11,12,13):
  if len(groups[g])==6 and groups[g][2]['source_sha256']!=groups[g][3]['source_sha256']:errors.append('Six-frame contact lost at native HIT3')
 return errors
def main():
 manifest_path=PROJECT/'assets/manifest.json';before=common.sha(manifest_path);manifest=load(manifest_path)
 policy=load_module(PROJECT/'scripts/art_policy.py','shurima_delivery_policy')
 sys.path.insert(0,str(PROJECT.parent/'scripts'));import faction_art_compile
 compiler=faction_art_compile.create_compiler('shurima');paths=sorted((SOURCE/'recipe-payload').rglob('*.json'));outputs={};receipts=[];checks=[];errors=[];output_recipes={}
 for path in paths:
  recipe=load(path);problems=policy.recipe_errors(PROJECT,recipe)
  checks.append({'name':'actual regional source policy '+common.rel(path),'passed':not problems,'errors':problems});errors.extend(problems)
  pair=[]
  for n in (1,2):
   generated,receipt=compiler.plan(PROJECT,path);pair.append({name:hashlib.sha256(data).hexdigest() for name,data in generated.items()})
   if n==1:
    receipts.append(receipt)
    for name,data in generated.items():
     dest=REPORT/'compiled'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
  checks.append({'name':'shared compiler deterministic '+common.rel(path),'passed':pair[0]==pair[1]})
  for name,pin in pair[0].items():
   if name in outputs:errors.append('Overlapping output '+name)
   outputs[name]=pin
  output_recipes[recipe['output_path']]=path
 units=sorted(load(PROJECT/'content/creatures.json'));muts=[];standing=[];coverage=[]
 for unit in units:
  recipes={p.stem:load(p) for p in (SOURCE/'recipe-payload'/unit).glob('*.json')}
  checks.append({'name':'actual six creature roles '+unit,'passed':set(recipes)=={'battle','map','large','small','attackLeft','attackRight'}})
  battle=recipes['battle'];groups={r['group']:r['frames'] for r in battle['groups']}
  actual=semantic_errors(battle,recipes);errors.extend(unit+': '+p for p in actual);checks.append({'name':'native consumer semantic contract '+unit,'passed':not actual,'errors':actual})
  bad=copy.deepcopy(battle);next(g for g in bad['groups'] if g['group']==22)['frames']=[groups[2][0]]
  muts.append({'unit':unit,'mutation':'terminal corpse substituted with holding','rejected':any('DEAD22' in e for e in semantic_errors(bad,recipes))})
  badroles=copy.deepcopy(recipes);badroles['attackRight']['source_canvas']=[96,64]
  muts.append({'unit':unit,'mutation':'encounter uses map canvas','rejected':any('encounter canvas' in e for e in semantic_errors(battle,badroles))})
  badsource=copy.deepcopy(battle);badsource['groups'][0]['frames'][0]['source_sha256']='0'*64
  muts.append({'unit':unit,'mutation':'selected real action source changed','rejected':bool(policy.recipe_errors(PROJECT,badsource))})
  border=[]
  for role in ('attackLeft','attackRight'):
   im=Image.open(PROJECT/recipes[role]['source']).convert('RGBA');alpha=im.getchannel('A');body=alpha.point(lambda a:255 if a>=128 else 0);bbox=body.getbbox()
   border.append({'role':role,'alpha128_bbox':bbox,'opaque_body_touches_edge':not bbox or bbox[0]==0 or bbox[1]==0 or bbox[2]==im.width or bbox[3]==im.height})
  checks.append({'name':'encounter opaque body margins '+unit,'passed':not any(r['opaque_body_touches_edge'] for r in border),'observed':border})
  standing.append((unit,Image.open(PROJECT/groups[2][0]['source']).convert('RGBA')))
  coverage.append({'unit':unit,'status':'authored configuration','recipes':{role:common.descriptor(SOURCE/'recipe-payload'/unit/(role+'.json')) for role in recipes},'genuine_walk_unique_sources':len(set(f['source_sha256'] for f in groups[0])),'groups':{g:len(seq) for g,seq in groups.items()},'corpse22_exact':groups[22][0]['source_sha256']==groups[5][-1]['source_sha256'],'crest_native_review':'pending; source-painted markings are not uniformly legible; old T1 crest proposal not selected','motion_native_execution':False,'visual_approval_granted':False})
 checks.append({'name':'all mutation controls rejected','passed':all(r['rejected'] for r in muts)})
 checks.append({'name':'source/live manifest unchanged','passed':common.sha(manifest_path)==before})
 proposal=copy.deepcopy(manifest);changes=[]
 for row in proposal['assets']:
  path=output_recipes.get(row['output_path'])
  if not path:continue
  recipe=load(path);relative=path.relative_to(SOURCE/'recipe-payload').as_posix()
  target='assets/recipes/creatures/playable-completion-20261028-v1/'+relative if not relative.startswith('projectiles/') else 'assets/recipes/playable-completion-20261028-v1/'+relative
  changes.append({'id':row['id'],'output_path':row['output_path'],'old_source':copy.deepcopy(row.get('source')),'payload':common.descriptor(path),'canonical_recipe_target':target})
  row['source'].update(recipe=target,recipe_path=target,recipe_present=True,recipe_sha256=common.sha(path));row.update(status='built-unreviewed',sha256=outputs[row['output_path']],native_visual_review='pending')
 common.put(REPORT/'manifest-proposal-v1.json',proposal)
 common.put(REPORT/'canonical-integration-packet-v1.json',{'status':'authored configuration','manifest_before_sha256':before,'manifest_proposal':common.descriptor(REPORT/'manifest-proposal-v1.json'),'changes':changes,'retire_colliding_old_producers':True,'coordinator_must_reconcile_full_asset_source_metadata':True,'live_selection_changed':False,'remaining':'Heraldry legibility, Sun Archer anatomical registration/gait, all native movement/projectile/combat observations remain open; not final accepted art.'})
 common.put(REPORT/'coverage-v1.json',coverage)
 board=Image.new('RGBA',(900,4*160),(40,40,40,255));draw=ImageDraw.Draw(board)
 for i,(unit,im) in enumerate(standing):
  x=(i%4)*225;y=(i//4)*160;view=im.crop((105,130,330,285));bg=common.checkbg(view.size);bg.alpha_composite(view);board.paste(bg,(x,y+5));draw.text((x+2,y+2),unit,fill='white')
 common.png(REPORT/'fourteen-painted-native1x.png',board)
 native_files=['client/battle/BattleProjectileController.cpp','client/battle/BattleAnimationClasses.cpp','client/battle/CreatureAnimation.cpp','client/battle/BattleStacksController.cpp','client/mapView/MapRenderer.cpp','lib/CCreatureHandler.cpp']
 authority={n:common.sha(PROJECT.parent/'vcmi-develop/vcmi-develop'/n) for n in native_files if (PROJECT.parent/'vcmi-develop/vcmi-develop'/n).is_file()}
 result={'status':'authored configuration','logical_recipes':len(paths),'physical_outputs':len(outputs),'checks':checks,'passed_checks':sum(r['passed'] for r in checks),'failed_checks':[r for r in checks if not r['passed']],'source_policy_errors':sorted(set(errors)),'mutation_controls':muts,'actual_native_source_authority':authority,'actual_two_shared_compiler_runs':True,'all_outputs':outputs,'runtime_verified':False,'visual_approval_granted':False,'live_manifest_before_after_sha256':before}
 common.put(REPORT/'delivery-verification-v1.json',result)
 print(json.dumps({k:result[k] for k in ('logical_recipes','physical_outputs','passed_checks','failed_checks','source_policy_errors')}))
if __name__=='__main__':main()
