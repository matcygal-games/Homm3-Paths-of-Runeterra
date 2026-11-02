"""Coordinator-authorized bounded source integration; no stages or profiles."""
from pathlib import Path
import copy,hashlib,importlib.util,io,json,sys
from PIL import Image,ImageChops

HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[3];ROOT=PROJECT.parent
CANDIDATE=HERE/'candidate-v4';STATE=HERE/'states-v3';SEALED=HERE/'selected-v1'
REPORT=ROOT/'reports/bandle-bulwark-site-integration-20261030-v1'
PREVIEW=ROOT/'reports/bandle-bulwark-site-repair-20261030-v1'
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
rel=lambda p:Path(p).relative_to(PROJECT).as_posix()
def data(value):return (json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
def dump(p,value):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data(value))
def preserve(p,raw):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists() and p.read_bytes()!=raw:raise ValueError('Preserved selection changed: '+str(p))
 if not p.exists():p.write_bytes(raw)
def png(image):
 out=io.BytesIO();image.save(out,format='PNG');return out.getvalue()

def main():
 if (REPORT/'integration.json').exists():raise ValueError('Integration already executed; audit receipt instead of replay')
 plan=read(CANDIDATE/'integration-plan.json');design=read(PROJECT/'design/town-visuals.json')
 faction=read(PROJECT/'content/factions.json');prior_design=copy.deepcopy(design)
 prior_selection=read(PROJECT/design['selected_sources']['path']);prior_revision=(PROJECT/design['selected_sources']['path']).parent
 def prior_resource(suffix):
  direct=prior_revision/suffix
  if direct.is_file():return direct
  matches=[PROJECT/p for p in prior_selection['files'] if p.endswith('/'+suffix)]
  if len(matches)!=1:raise ValueError('Ambiguous prior selected resource: '+suffix)
  return matches[0]
 names={r['canonical']:r for r in plan['recipes']}
 for name,row in names.items():
  if sha(PROJECT/name)!=row['before_sha256'] or sha(PROJECT/row['candidate'])!=row['candidate_sha256']:
   raise ValueError('Rebase required: recipe changed '+name)
  preserve(REPORT/'before'/name,(PROJECT/name).read_bytes())
 for name in ('content/factions.json','design/town-visuals.json','assets/manifest.json'):
  preserve(REPORT/'before'/name,(PROJECT/name).read_bytes())
 generated_before={p.relative_to(PROJECT/'assets/generated').as_posix():sha(p) for p in (PROJECT/'assets/generated').rglob('*') if p.is_file()}
 dump(REPORT/'generated-before.json',generated_before)
 # Exact reviewed provenance is made a permanent own source dependency.
 for name in ('imagegen-exact-requests-v1.json','threshold-contact-v1.json','original-reference-check.json'):
  preserve(HERE/name,(PREVIEW/name).read_bytes())
 bindings=[];files={PROJECT/p for p in prior_selection['files']}
 files.update([Path(__file__),HERE/'generation-ledger-v3.json',HERE/'derive-v3.py',HERE/'background-provider-v1.png',HERE/'castle-provider-v1.png'])
 files.update(HERE/name for name in ('imagegen-exact-requests-v1.json','threshold-contact-v1.json','original-reference-check.json'))
 for binding in prior_selection['recipe_bindings']:
  active=binding['active'];row=names.get(active)
  chosen=PROJECT/row['candidate'] if row else PROJECT/active
  # Seal every current native recipe so previously repaired dwelling cards stay selected.
  target=SEALED/'recipes'/Path(active).relative_to('assets/recipes/town')
  preserve(target,chosen.read_bytes());files.add(target)
  bindings.append({'active':active,'candidate':rel(target),'sha256':sha(target)})
  recipe=read(target)
  def closure(value):
   if isinstance(value,dict):
    for key,child in value.items():
     if key in ('source','painted_master','technical_producer','source_generation_ledger') and isinstance(child,str) and (PROJECT/child).is_file():files.add(PROJECT/child)
     closure(child)
   elif isinstance(value,list):
    for child in value:closure(child)
  closure(recipe)
 site=next(s for s in design['sites'] if s['id']=='fortification')
 replacements=copy.deepcopy(plan['design_site_replacement_fields']);replacements.pop('site_id')
 site.update(replacements);site['layer_origin']=[0,0];site.pop('native_state_z',None)
 for state,row in site['selected_state_art'].items():
  row['footing_water_pixels']=0
  site['source'][state]=row['master'];site['sha256'][state]=row['master_sha256']
  faction['bandlecity']['town']['structures'][state]['z']=80
  files.update((STATE/state).glob('*.png'))
 terrain=copy.deepcopy(design['terrain'])
 terrain.update(master=rel(HERE/'background-provider-v1.png'),master_sha256=sha(HERE/'background-provider-v1.png'),
   native=rel(SEALED/'background/native.png'),native_sha256=sha(STATE/'background.png'),
   annotation=terrain['annotation']+' Local Library/Bulwark masonry bridgehead repaired at x212..306,y54..118; unchanged outside that bounded region.')
 preserve(SEALED/'background/native.png',(STATE/'background.png').read_bytes())
 oldwater=PROJECT/Path(design['terrain']['native']).parent/'water-annotation.png'
 preserve(SEALED/'background/water-annotation.png',oldwater.read_bytes())
 files.update([SEALED/'background/native.png',SEALED/'background/water-annotation.png'])
 design.update(terrain=terrain,recipe_paths=[b['candidate'] for b in bindings],status='authored configuration',
   layout_note='BC1 community preserved except user-requested Library/Bulwark bridgehead and three fortification states; exact original master retained as history. Sixteen land sites, seven dwelling pairs and optional coast preserved. Fortification uses one exterior floor guide with separately measured visible thresholds.',
   visual_approval_granted=False)
 # Full selected composition derives from pinned source layers, independently of outputs.
 layers={s:Image.open(PROJECT/r['native_layer']).convert('RGBA') for st in design['sites'] for s,r in st['selected_state_art'].items()}
 allbuilt={s for st in design['sites'] if st['id'] not in ('coast','grailOrnament') for s in st['states']}
 town=faction['bandlecity']['town']
 visible={s for s in allbuilt if not any(town['buildings'][o].get('upgrades')==s for o in allbuilt)}
 full=Image.open(STATE/'background.png').convert('RGBA')
 for s in sorted(visible,key=lambda s:town['structures'][s]['z']):full.alpha_composite(layers[s])
 preserve(SEALED/'complete-design/native.png',png(full));files.add(SEALED/'complete-design/native.png')
 preserve(SEALED/'complete-design/previous-approved-native.png',prior_resource('complete-design/native.png').read_bytes())
 files.add(SEALED/'complete-design/previous-approved-native.png')
 saveplan=read(prior_resource('placement-plan.json'))
 saveplan['sites']['fortification'].update(ground_approach=[270,75],actual_full_silhouette_box=[239,11,58,67],
   visible_thresholds={'fort':[270,73],'citadel':[270,72],'castle':[270,75]})
 dump(SEALED/'placement-plan.json',saveplan);files.add(SEALED/'placement-plan.json')
 preserve(SEALED/'support_annotations.py',prior_resource('support_annotations.py').read_bytes())
 spec=importlib.util.spec_from_file_location('integrated_bc1_support',SEALED/'support_annotations.py');support=importlib.util.module_from_spec(spec);spec.loader.exec_module(support)
 checks,support_files=support.prepare(design,layers);files.update(support_files)
 if not checks['ok']:raise ValueError('Native support annotations rejected candidate')
 selection={'schema_version':1,'revision':'BC1-library-bulwark-repair-20261030-v1','status':'authored configuration',
   'visual_approval_granted':False,'sites':design['sites'],'terrain':terrain,'recipe_bindings':bindings,
   'files':{rel(p):sha(p) for p in sorted(files)},'preparation_policy':'Reviewed scoped source integration only. Native art/gameplay and rights/release acceptance remain pending.',
   'previous_selection':prior_design['selected_sources'],'local_revision':{'roi':[212,54,307,119],
   'reason':'User rejected Library/Bulwark ground and base fort placement; independent source reviewer GO, coordinator authorized integration.',
   'fully_built_gate_changed':True,'unrelated_art_preserved':True}}
 dump(SEALED/'selection.json',selection)
 design['selected_sources']={'path':rel(SEALED/'selection.json'),'sha256':sha(SEALED/'selection.json'),
   'terrain_master':terrain['master'],'terrain_master_sha256':terrain['master_sha256'],
   'terrain_native':terrain['native'],'terrain_native_sha256':terrain['native_sha256']}
 spec=importlib.util.spec_from_file_location('selected_bandle_preflight',PROJECT/'scripts/bandle_town_art.py');preflight=importlib.util.module_from_spec(spec);spec.loader.exec_module(preflight)
 preflight.preflight_selected(design,verify_active=False)
 # All selected dependencies validated before any canonical recipe/content/design write.
 for row in names.values():(PROJECT/row['canonical']).write_bytes((PROJECT/row['candidate']).read_bytes())
 dump(PROJECT/'content/factions.json',faction);dump(PROJECT/'design/town-visuals.json',design)
 preflight.preflight_selected(design)
 dump(REPORT/'integration.json',{'status':'authored configuration','canonical_source_integrated':True,
   'selected_revision':design['selected_sources'],'recipe_count_changed':14,'content_structure_changes':['fort.z','citadel.z','castle.z'],
   'selected_recipe_bindings':len(bindings),'selected_dependency_count':len(files),'support_checked_states':len(checks['states']),
   'generated_outputs_written':False,'stage_or_profile_modified':False,'native_testing':False})
 print(json.dumps(read(REPORT/'integration.json'),indent=2))

if __name__=='__main__':main()
