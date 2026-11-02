"""Real source guard, native consumer invariants, mutations and merge packet."""
from pathlib import Path
from PIL import Image,ImageOps,ImageChops
import copy,hashlib,json,sys,importlib.util,shutil
import assemble_packets as common
S=common.SOURCE;P=common.PROJECT;R=common.REPORT/'heraldry-v1'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def module(path,name):
 spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
def check_case(battle,recipes):
 errors=[];groups={r['group']:r['frames'] for r in battle['groups']}
 if groups[22][-1]['source_sha256']!=groups[5][-1]['source_sha256']:errors.append('dead22 is not final death5 corpse')
 for g in (11,12,13):
  seq=groups[g];hit=(len(seq)+1)//2
  if seq[hit]['source_sha256']==groups[2][0]['source_sha256']:errors.append('native HIT is holding instead of contact')
  if len(seq) in (4,6) and seq[hit]['source_sha256']!=seq[hit-1]['source_sha256']:errors.append('native HIT contact not held across its exact boundary')
 for role in ('attackLeft','attackRight'):
  if recipes[role].get('source_canvas')!=[64,64]:errors.append('encounter uses non64 canvas')
 front=Image.open(P/groups[7][-1]['source']).convert('RGBA');right=Image.open(P/groups[8][0]['source']).convert('RGBA')
 expected=Image.new('RGBA',front.size);expected.paste(ImageOps.mirror(front),(2*battle['pivot']['x']-(front.width-1),0))
 if expected.tobytes()!=right.tobytes():errors.append('native TURN flip boundary differs')
 return errors
def outside_guard(base,out,mask):
 if base.getchannel('A').tobytes()!=out.getchannel('A').tobytes():return False
 difference=ImageChops.difference(base.convert('RGB'),out.convert('RGB'))
 physical=mask.point(lambda x:255 if x else 0)
 outside=Image.composite(difference,Image.new('RGB',base.size),ImageChops.invert(physical))
 return outside.getbbox() is None
def main():
 policy=module(P/'scripts/art_policy.py','heraldry_policy');privacy=module(P/'scripts/source_export_guard.py','heraldry_privacy')
 payload=S/'recipe-payload-heraldry-v1';projectile_target=payload/'projectiles';projectile_target.mkdir(exist_ok=True)
 for p in sorted((S/'recipe-payload/projectiles').glob('*.json')):shutil.copyfile(p,projectile_target/p.name)
 recipes=sorted(payload.rglob('*.json'));checks=[];mutations=[];errors=[];entries={};sourcepins={};outputpins={}
 sys.path.insert(0,str(P.parent/'scripts'));import faction_art_compile
 compiler=faction_art_compile.create_compiler('shurima')
 for path in recipes:
  recipe=load(path);failures=policy.recipe_errors(P,recipe);checks.append({'name':'actual regional art policy '+common.rel(path),'passed':not failures,'errors':failures});errors.extend(failures)
  local=list(privacy.fields(recipe));checks.append({'name':'actual source privacy field scanner '+common.rel(path),'passed':not local,'errors':local})
  for row in recipe.get('production_inputs',[]):
   p=P/row['path'];ok=p.is_file() and common.sha(p)==row['sha256'];checks.append({'name':'actual declared producer input '+row['path'],'passed':ok})
   if ok:sourcepins[row['path']]=row['sha256']
  pair=[]
  for n in (1,2):
   outputs,receipt=compiler.plan(P,path);pair.append({name:hashlib.sha256(data).hexdigest() for name,data in outputs.items()})
   if n==1:
    for name,data in outputs.items():
     target=R/'compiled'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
  checks.append({'name':'actual strict compiler two runs '+common.rel(path),'passed':pair[0]==pair[1]})
  if set(outputpins)&set(pair[0]):errors.append('colliding own output')
  outputpins.update(pair[0]);entries[recipe['output_path']]=path
 units=sorted(load(P/'content/creatures.json'));coverage=[]
 for unit in units:
  rr={p.stem:load(p) for p in (payload/unit).glob('*.json')};battle=rr['battle'];groups={row['group']:row['frames'] for row in battle['groups']};failures=check_case(battle,rr)
  checks.append({'name':'native source consumer semantics '+unit,'passed':not failures,'errors':failures})
  bad=copy.deepcopy(battle);next(g for g in bad['groups'] if g['group']==22)['frames']=[groups[2][0]]
  mutations.append({'unit':unit,'mutation':'replace actual terminal corpse with holding','rejected':'dead22 is not final death5 corpse' in check_case(bad,rr)})
  bad=copy.deepcopy(battle);next(g for g in bad['groups'] if g['group']==8)['frames'][0]=groups[2][0]
  mutations.append({'unit':unit,'mutation':'replace actual turn boundary with holding','rejected':'native TURN flip boundary differs' in check_case(bad,rr)})
  bad=copy.deepcopy(battle);next(g for g in bad['groups'] if g['group']==12)['frames'][(len(groups[12])+1)//2]=groups[2][0]
  mutations.append({'unit':unit,'mutation':'replace native HIT frame with holding','rejected':'native HIT is holding instead of contact' in check_case(bad,rr)})
  badroles=copy.deepcopy(rr);badroles['attackRight']['source_canvas']=[96,64]
  mutations.append({'unit':unit,'mutation':'regress real encounter canvas to map96','rejected':'encounter uses non64 canvas' in check_case(battle,badroles)})
  for role in ('attackLeft','attackRight'):
   im=Image.open(P/rr[role]['source']).convert('RGBA');a=im.getchannel('A').point(lambda x:255 if x>=128 else 0);box=a.getbbox()
   checks.append({'name':'whole opaque encounter silhouette inside64 '+unit+' '+role,'passed':bool(box) and 0<box[0] and 0<box[1] and box[2]<64 and box[3]<64,'observed':box})
  for frame in rr['map']['groups'][0]['frames']:
   im=Image.open(P/frame['source']).convert('RGBA');opaque=im.getchannel('A').point(lambda x:255 if x>=128 else 0)
   checks.append({'name':'actual two-column mapMask body coverage '+unit+' '+Path(frame['source']).name,'passed':opaque.crop((0,0,32,64)).getbbox() is None,'mapMask':load(P/'content/creatures.json')[unit]['graphics']['mapMask']})
  # Keep exactly actual inherited flight start/end pictures; material composition may
  # alter only explicit attachment surfaces, never replace takeoff by holding.
  if unit in ('sandstoneChimera','gildedChimera'):checks.append({'name':'genuine flight/takeoff/landing cohort retained '+unit,'passed':len(groups[0])==6 and len(groups[20])==3 and len(groups[21])==3})
  coverage.append({'unit':unit,'status':'authored configuration','body_and_material':'genuine painted2D; T1 prior physical-plane source retained, other12 explicitly annotated attachment planes','battle':common.descriptor(payload/unit/'battle.json'),'ordinary_source_view':common.descriptor(R/unit/'right-all-actions-native1x.png'),'both_facing_motion':common.rel(R/unit/'g00-native-left-samehex.gif'),'native_recruitment_portrait':common.descriptor(R/'compiled'/rr['large']['output_path']),'groups':{g:len(seq) for g,seq in groups.items()},'runtime_verified':False,'external_art_acceptance':False})
 annotations=load(R/'physical-annotations-v1.json')
 for row in annotations:
  base=Image.open(P/row['input']['source']).convert('RGBA');shifted=Image.new('RGBA',base.size);shifted.paste(base,(row['native_translation_x'],0));out=Image.open(P/row['output']['source']).convert('RGBA');mask=Image.open(P/row['mask']['source']).convert('L')
  ok=outside_guard(shifted,out,mask);checks.append({'name':'actual alpha/outside-plane invariance '+row['unit']+' '+Path(row['output']['source']).stem,'passed':ok})
  mutant=out.copy();r,g,b,a=mutant.getpixel((0,0));mutant.putpixel((0,0),(r^1,g,b,a))
  mutations.append({'unit':row['unit'],'mutation':'one RGB bit outside actual material plane','source':row['output']['source'],'rejected':not outside_guard(shifted,mutant,mask)})
 checks.append({'name':'all real mutation controls rejected','passed':all(row['rejected'] for row in mutations)})
 # Produce a selective merge packet: never overwrite the coordinator's town or heroes.
 manifest=load(P/'assets/manifest.json');changes=[]
 for entry in manifest['assets']:
  path=entries.get(entry['output_path'])
  if path is None:continue
  new=copy.deepcopy(entry);relative=path.relative_to(payload).as_posix();target='assets/recipes/creatures/playable-completion-20261028-v1/'+relative
  new['source'].update(recipe=target,recipe_path=target,recipe_present=True,recipe_sha256=common.sha(path));new.update(status='built-unreviewed',sha256=outputpins[entry['output_path']],native_visual_review='pending native; source physical-plane review executed separately')
  changes.append({'id':entry['id'],'before_entry_sha256':hashlib.sha256(json.dumps(entry,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'before_entry':entry,'after_entry':new,'recipe_payload':common.descriptor(path),'canonical_recipe_target':target})
 retire=[]
 for old in sorted((P/'assets/recipes').rglob('*.json')):
  value=load(old)
  if value.get('output_path') in entries:retire.append(common.descriptor(old))
 checks.append({'name':'all requested creature and missile logical entries covered','passed':len(changes)==88})
 packet={'status':'authored configuration','scope':'14 creature variants84roles plus4 physical missile resources; no town, hero or mechanics balance changes','baseline_manifest_sha256':common.sha(P/'assets/manifest.json'),'content_creatures_guard_sha256':common.sha(P/'content/creatures.json'),'merge_only_these_entries_by_id':changes,'retire_colliding_live_recipes_preserve_history':retire,'shared_compiler':common.descriptor(P.parent/'scripts/faction_art_compile.py') if False else {'workspace_path':'scripts/faction_art_compile.py','sha256':common.sha(P.parent/'scripts/faction_art_compile.py')},'compiled_output_root':common.rel(R/'compiled'),'compiled_outputs':outputpins,'source_dependency_pins':sourcepins,'all_current_pngs_built':True,'runtime_verified':False,'release_accepted':False,'native_actions_for_coordinator':['standing/gaits and correct visible regional crests, both faces','recruitment/adventure appearance and both direction encounter reactions','physical shot launch/climax4 up/front/down both facings','fly takeoff/hover/land and melee contact4 or6 exact HIT frames','actual terminal corpse after death/save/battle result'],'external_approval':'Final independent native art/motion and rights acceptance remain separate; no fabricated automated approval'}
 common.put(R/'canonical-integration-packet-v3.json',packet);common.put(R/'coverage-v3.json',coverage)
 result={'status':'authored configuration','recipes':len(recipes),'physical_outputs':len(outputpins),'checks':checks,'passed':sum(row['passed'] for row in checks),'failed':[row for row in checks if not row['passed']],'actual_regional_source_policy_errors':errors,'mutations':mutations,'mutation_count':len(mutations),'all_mutants_rejected':all(row['rejected'] for row in mutations),'native_execution':False,'visual_approval_granted':False,'compiled_outputs':outputpins,'integration_packet':common.descriptor(R/'canonical-integration-packet-v3.json')}
 common.put(R/'consumer-and-source-checks-v3.json',result)
 print(json.dumps({k:result[k] for k in ('recipes','physical_outputs','passed','failed','actual_regional_source_policy_errors','mutation_count','all_mutants_rejected')}))
if __name__=='__main__':main()
