"""Finite source candidate and real existing converters in isolated report roots.

Never runs canonical CLI, stage, launcher, publication or a native game.
"""
from pathlib import Path
import copy,hashlib,json,sys,shutil
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];REPORT=ROOT/'build/reports/complete-town-20261027-v2';PREFIX='Content/Sprites/runeterra/zaun/'
sys.path.insert(0,str(ROOT.parent/'scripts'));import faction_artifacts as compiler;import faction_town_layout as geometry
read=lambda p:json.loads(p.read_text(encoding='utf-8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def ref(p):return {'path':rel(p),'sha256':sha(p)}
def prepare():
 plan=read(HERE/'derived-state-plan.json');contract=read(HERE/'town-layout.json');bindings=[];recipes=[];values={r['state']:r['native_z'] for r in plan['states']};sites={s['id']:s for s in contract['sites']}
 for row in plan['states']:
  state=row['state'];sid='coast' if row['site']=='shipyard' else 'grail' if row['site']=='codeOfProgress' else row['site'];folder=HERE/'structures'/state
  generation={'status':'authored configuration','provider':'OpenAI built-in imagegen','model':None,'model_disclosed':False,'image_generation_used':True,'new_image_generation_used':True,'workflow':'complete whole-town painting reviewed before slicing; genuine hidden-face and lower-state family paintings','route':row['route'],'master':row['whole_master'],'master_sha256':row['whole_master_sha256'],'source_native_layer':row['native_layer'],'source_native_layer_sha256':row['native_layer_sha256'],'derived_from_blender':False,'runtime_verified':False,'release_accepted':False,'visual_approval_granted':False}
  provenance=HERE/'provenance'/(state+'.json');write(provenance,{**generation,'technical_state':row,'deriver':ref(HERE/'derive_sources.py'),'families':ref(HERE/'family-specs.json')})
  deps=[ref(provenance),ref(HERE/'derived-state-plan.json'),ref(HERE/'town-layout.json'),ref(HERE/'complete-design/native-v2.png'),ref(HERE/'complete-design/provider-master-v2.png'),ref(HERE/'complete-design/prompt-v2.txt'),ref(HERE/'complete-design/review-checkpoint.json'),ref(HERE/'visible_contours.py'),ref(HERE/'derive_sources.py'),ref(HERE/'author_contract.py'),ref(HERE/'prepare_candidate.py'),ref(HERE/'family-specs.json')]
  for record in row['provider_inputs']:
   for key in ('source','raw_atlas'):
    if (ROOT/record[key]).is_file():deps.append(ref(ROOT/record[key]))
  deps.append(ref(HERE/'contact_traces.py'))
  fam=HERE/'families'/row['site']
  for name in ('prompt.txt','generation-v1.json','whole-master-context.png','context.json'):
   if (fam/name).is_file():deps.append(ref(fam/name))
  for kind in ('animation','area','border','construction'):
   active=f'assets/recipes/town/construction/{state}.json' if kind=='construction' else f'assets/recipes/town/structures/{state}-{kind}.json';r=read(ROOT/active);surface=folder/('layer.png' if kind=='animation' else kind+'.png')
   r.update({'source_sha256':sha(surface),'generation':generation,'dependencies':deps,'identity_review':rel(REPORT/'SOURCE_REVIEW.json'),'native_visual_review':'pending','visual_approval_granted':False});r.pop('technical_assembly',None);r.pop('depends_on',None)
   if kind=='animation':r['groups'][0]['frames']=[{'source':rel(surface),'sha256':sha(surface)}];r['building_contract']['full_canvas_placement']={'x':0,'y':0,'z':row['native_z']};r['building_contract']['native_ground_contact']=sites[sid]['box']
   else:r['source']=rel(surface)
   p=HERE/'recipes'/Path(active).relative_to('assets/recipes');write(p,r);recipes.append((active,p));bindings.append({'active':active,'candidate':rel(p),'sha256':sha(p)})
 bg=ROOT/plan['background'];r=read(ROOT/'assets/recipes/town/background.json');r.update({'source':rel(bg),'source_sha256':sha(bg),'generation':read(HERE/'background/generation-v2.json'),'dependencies':[ref(HERE/'background/generation-v2.json'),ref(HERE/'background/provider-empty-v1.png'),ref(HERE/'background/provider-pit-cleanup-v2.png'),ref(HERE/'background/prompt-v1.txt'),ref(HERE/'background/pit-removal-prompt.txt'),ref(HERE/'town-layout.json')],'identity_review':rel(REPORT/'SOURCE_REVIEW.json'),'native_visual_review':'pending','visual_approval_granted':False});p=HERE/'recipes/town/background.json';write(p,r);recipes.append(('assets/recipes/town/background.json',p));bindings.append({'active':'assets/recipes/town/background.json','candidate':rel(p),'sha256':sha(p)})
 design=read(ROOT/'design/town-visuals.json');oldsites={s['id']:s for s in design['sites']};newsites=[]
 for site in contract['sites']:
  sid='shipyard' if site['id']=='coast' else 'codeOfProgress' if site['id']=='grail' else site['id'];old=copy.deepcopy(oldsites[sid]);states={r['state']:r for r in plan['states'] if r['site']==sid};old.update({'composition_rectangle':site['box'],'native_z':site['depth'],'source_states':states});newsites.append(old)
 design.update({'layout_geometry_mode':'silhouette-v2','layout_contract':ref(HERE/'town-layout.json'),'sites':newsites,'selected_sources':{'kind':'complete-town-first-painted2D','revision':HERE.name,'selection':rel(HERE/'selection.json'),'background':rel(bg)},'derivation':'Reviewed complete city first; actual visible master cuts, genuine painted hidden-face reconstruction/lower-state cohorts, matching painted empty plate. Exact all-state alpha silhouettes, foundation and public frontage masks replace rectangle-only placement.'});design['layoutPolicy'].update({'selectedSourcePlan':rel(HERE/'derived-state-plan.json'),'selectedSourcePlanSha256':sha(HERE/'derived-state-plan.json'),'nativeComposition':rel(REPORT/'upgraded-native.png'),'geometryEvidence':rel(REPORT/'geometry-checks.json'),'nativeReview':'pending new fresh native stage','functionalBoundary':'Eighteen ordinary visible institutions plus optional coast and Grail; all36 states preserved. '+contract['site_budget_exception']});design['canvas']['currentState']='Reviewed complete town first; derived source candidate, native verification pending.';write(HERE/'town-visuals.candidate.json',design);write(HERE/'content-z-patch.json',{'values':values,'scope':'Only zaun town structure z changes; preserve every other authored dictionary field.'})
 inventories=[];admissions=[]
 for run in (1,2):
  scratch=REPORT/f'conversion-{run}';shutil.copytree(HERE,scratch/rel(HERE),dirs_exist_ok=True,ignore=shutil.ignore_patterns('recipes','selection.json'));construction={};receipts=[]
  for active,p in recipes:
   target=scratch/active;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target);r=read(p);receipt=compiler.CONVERTERS[r['recipe_type']](scratch,r,PREFIX,False,{},check=False);receipts.append({'recipe':rel(p),'receipt':receipt})
   if p.parent.name=='construction':construction[r['building']]=receipt['sha256']
  index=read(ROOT/'assets/recipes/town/buildingIcons.json')
  for frame in index['frames']:frame['sha256']=construction[frame['building']];frame['producer_sha256']=sha(HERE/'recipes/town/construction'/(frame['building']+'.json'))
  index.update({'dependencies':[ref(HERE/'town-layout.json')],'generation':{'image_generation_used':True,'new_image_generation_used':False,'provider':'OpenAI built-in imagegen','model':None,'model_disclosed':False,'route':'Native indexed assembly of36 own matching construction icons from actual selected whole-city states','visual_approval_granted':False}});write(HERE/'recipes/town/buildingIcons.json',index);write(scratch/'assets/recipes/town/buildingIcons.json',index);compiler.convert_indexed(scratch,index,PREFIX,False,{},check=False)
  write(scratch/'design/town-visuals.json',design);factions=read(ROOT/'content/factions.json')
  for state,z in values.items():factions['zaun']['town']['structures'][state]['z']=z
  content={'factions':factions};errors,deps=geometry.inspect(scratch,content,'zaun');admissions.append({'errors':errors,'dependency_count':len(deps)});print('Actual physical admission run'+str(run)+': '+str(errors),flush=True)
  inventory={p.relative_to(scratch/'assets/generated').as_posix():sha(p) for p in sorted((scratch/'assets/generated').rglob('*')) if p.is_file()};inventories.append(inventory);write(REPORT/f'conversion-{run}-receipts.json',receipts)
 if inventories[0]!=inventories[1]:raise ValueError('Nondeterministic real converter outputs')
 bindings.append({'active':'assets/recipes/town/buildingIcons.json','candidate':rel(HERE/'recipes/town/buildingIcons.json'),'sha256':sha(HERE/'recipes/town/buildingIcons.json')})
 result={'status':'authored configuration','ok':not any(a['errors'] for a in admissions),'actual_physical_admission':admissions,'converter_runs':2,'identical_outputs':True,'recipe_count':len(bindings),'output_count':len(inventories[0]),'native_verified':False,'release_accepted':False};write(REPORT/'geometry-checks.json',result)
 write(HERE/'selection.json',{'status':'authored configuration','recipe_bindings':bindings,'layout':rel(HERE/'town-visuals.candidate.json'),'layout_sha256':sha(HERE/'town-visuals.candidate.json'),'source_plan':rel(HERE/'derived-state-plan.json'),'source_plan_sha256':sha(HERE/'derived-state-plan.json'),'physical_contract':ref(HERE/'town-layout.json'),'background':rel(bg),'background_sha256':sha(bg),'physical_outputs':inventories[0],'converter_runs':2,'output_determinism':True,'active_integration':False,'native_verified':False,'release_accepted':False})
 print(json.dumps(result),flush=True)
if __name__=='__main__':prepare()
