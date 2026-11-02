"""Metadata-only strict painted-source closure plus two technical Corsair tower crops.

No existing painting/native frame or frozen v5 record is rewritten. Coordinator
alone selects these proposals. Actual unmodified policy and converter execute.
"""
from pathlib import Path
import copy,hashlib,importlib.util,io,json,sys
from PIL import Image
S=Path(__file__).resolve().parent;P=S.parents[3];W=P.parent;OLD=P/'build/reports/painted-creature-completion-20261028-v1/final-packet-v5';R=P/'build/reports/painted-creature-completion-20261028-v1/final-packet-v6';R.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(W/'scripts'));import faction_art_compile,source_export_guard
def sha(b):return hashlib.sha256(b).hexdigest()
def enc(o):return(json.dumps(o,sort_keys=True,indent=2)+'\n').encode()
def load(p):return json.loads(p.read_text())
def rel(p):return p.relative_to(P).as_posix()
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists()and p.read_bytes()!=b:raise RuntimeError('Preserve frozen v6 artifact '+rel(p))
 if not p.exists():p.write_bytes(b)
def record(p,o):put(p,enc(o))
old=load(OLD/'root-integration-packet-v5.json');policy_path=W/'runeterra-targon/scripts/creature_art_policy.py';sp=importlib.util.spec_from_file_location('_actual_unmodified_painted_source_policy',policy_path);policy=importlib.util.module_from_spec(sp);sp.loader.exec_module(policy)
compiler=faction_art_compile.create_compiler('bilgewater');recipes=[];sources=set();bindings={};mutants=[]
# The real58x64 tower consumer gets a centred lossless crop, not stretched art.
large=S/'corsair/native-v5/companions/large.png';small=S/'corsair/native-v5/companions/small.png';tower=S/'siege-tower-portraits-v6/towerLarge58x64.png'
im=Image.open(large).convert('RGBA');assert im.size==(64,64);out=im.crop((3,0,61,64));buf=io.BytesIO();out.save(buf,format='PNG',compress_level=9,optimize=False);put(tower,buf.getvalue());assert Image.open(small).size==(32,32)
for variant in old['variants']:
 unit=variant['unit'];prior=[load(P/row['proposed_recipe'])for row in old['changes']if '/creatures/'+unit+'/'in row['output_path'] or row['output_path'].endswith('/projectiles/'+unit+'.json')];assert len(prior)in[6,7]
 files={}
 for recipe in prior:
  g=recipe['generation'];files.update({a['path']:a['sha256']for a in g['production_inputs']});files[g['provenance']]=sha((P/g['provenance']).read_bytes())
  for group in recipe.get('groups',[]):
   for f in group['frames']:files[f['source']]=sha((P/f['source']).read_bytes())
  if recipe.get('source'):files[recipe['source']]=sha((P/recipe['source']).read_bytes())
 files[rel(Path(__file__))]=sha(Path(__file__).read_bytes())
 if unit=='corsair':files[rel(tower)]=sha(tower.read_bytes());files[rel(large)]=sha(large.read_bytes());files[rel(small)]=sha(small.read_bytes())
 origins=[{'kind':'image-generation','path':n,'sha256':pin,'provider':'OpenAI built-in imagegen','model':'not exposed by built-in tool'}for n,pin in sorted(files.items())if n.endswith('-raw.png')]
 ledger=S/unit/'selected-source-generation-v6.json';record(ledger,{'schema_version':1,'status':'authored configuration','unit':unit,'workflow':'image-based-painted-2d','derived_from_blender':False,'user_rejected':False,'assembly_operations':['fixed-canvas','root-placement','alpha-cleanup','frame-assembly','png-conversion'],'origins':origins,'files_sha256':dict(sorted(files.items())),'actual_assembly_config':variant['config'],'actual_native_pixel_cohort':variant['provenance'],'native_execution':False,'art_acceptance':False,'rights':'unresolved; release prohibited','metadata_only_wrapper':'Adds the actual painted-source consumer schema around unchanged genuine v5 paintings/nativeframes; no provenance origin is removed or relabelled.'})
 unitrecipes=[]
 for recipe in prior:
  g=recipe['generation'];g['workflow']='image-based-painted-2d';g['derived_from_blender']=False;g['source_generation_ledger']=rel(ledger);g['source_generation_ledger_sha256']=sha(ledger.read_bytes());g['production_inputs'].extend([{'path':rel(ledger),'sha256':sha(ledger.read_bytes())},{'path':rel(Path(__file__)),'sha256':sha(Path(__file__).read_bytes())}])
  p=S/'final-proposed-recipes-v6'/unit/(Path(recipe['output_path']).stem+'.json');record(p,recipe);unitrecipes.append(p)
 if unit=='corsair':
  template=copy.deepcopy(prior[0]);g=template['generation'];portraitmaster=S/'corsair/reactions-v1-raw.png';g['painted_master']=rel(portraitmaster);g['painted_master_sha256']=sha(portraitmaster.read_bytes())
  for role,path,size in [('towerLarge',tower,[58,64]),('towerSmall',small,[32,32])]:
   r={k:copy.deepcopy(v)for k,v in template.items()if k not in ['groups','canvas','pivot','generateShadow','generateOverlay','recipe_type','output_path','size','fit','source','source_sha256','source_canvas']};r.update({'recipe_type':'raster','unit':'corsair','output_path':f'Content/Sprites/runeterra/bilgewater/siege/{role}.png','size':size,'fit':'exact','source':rel(path),'source_sha256':sha(path.read_bytes()),'source_canvas':list(Image.open(path).size),'technical_portrait_construction':{'parent':rel(large if role=='towerLarge'else small),'parent_sha256':sha((large if role=='towerLarge'else small).read_bytes()),'crop':[3,0,61,64]if role=='towerLarge'else None,'actual_consumer_dimensions':size,'new_creative_art':False}})
   p=S/'final-proposed-recipes-v6/siege'/f'{role}.json';record(p,r);unitrecipes.append(p)
 for p in unitrecipes:
  r=load(p);errors=policy.recipe_errors(P,r,set())
  if errors:raise RuntimeError('Actual strict painted policy failed '+rel(p)+': '+repr(errors))
  for label,change in [('removed workflow',lambda b:b['generation'].pop('workflow')),('changed ledger pin',lambda b:b['generation'].update(source_generation_ledger_sha256='0'*64)),('unclosed actual source',lambda b:b.update(source='assets/source/missing-unclosed.png')),('forbidden geometry lineage',lambda b:b.update(geometry_source='retired-scene.blend'))]:
   bad=copy.deepcopy(r);change(bad);errs=policy.recipe_errors(P,bad,set());assert errs,label;mutants.append({'recipe':rel(p),'mutation':label,'rejected':True,'errors':errs})
  sources.add(p);recipes.append(p)
 sources.update(P/n for n in files);sources.add(ledger);bindings[unit]={'source_generation_ledger':rel(ledger),'sha256':sha(ledger.read_bytes()),'unchanged_v5_config':variant['config'],'unchanged_v5_pixel_provenance':variant['provenance']}
passes=[];conversion=[]
for replay in[1,2]:
 products={}
 for p in recipes:
  outputs,receipt=compiler.plan(P,p)
  assert not(set(products)&set(outputs));products.update(outputs);conversion.append({'pass':replay,'recipe':rel(p),'receipt':receipt})
 hashes={n:sha(b)for n,b in products.items()};passes.append(hashes)
 if replay==1:
  for name,raw in products.items():put(R/'compiled'/name,raw)
assert passes[0]==passes[1]
oldoutputs=load(OLD/'physical-output-hashes-v5.json');assert all(passes[0][n]==pin for n,pin in oldoutputs.items())
privacy=source_export_guard.check(P,files={P.name+'/'+rel(p):p.read_bytes()for p in sources});record(R/'actual-source-export-admission-v6.json',privacy);assert privacy['source_export_eligible'],privacy['errors']
manifest=P/'assets/manifest.json';entries=load(manifest)['assets'];changes=[]
for p in recipes:
 r=load(p);e=next(a for a in entries if a['output_path']==r['output_path']);changes.append({'output_path':r['output_path'],'expected_manifest_entry_sha256':sha(enc(e)),'expected_manifest_entry':e,'proposed_recipe':rel(p),'proposed_recipe_sha256':sha(p.read_bytes()),'compiled_sha256':passes[0][r['output_path']],'dimensions':r.get('canvas',r.get('size')),'group_frame_counts':{str(a['group']):len(a['frames'])for a in r.get('groups',[])}})
record(R/'actual-converter-replays-v6.json',{'status':'authored configuration','logical_recipes':len(recipes),'physical_outputs':len(passes[0]),'two_pass_identical':True,'all948_prior_creature_pixels_unchanged':True,'all_output_sha256':passes[0],'conversion_receipts':conversion,'native_execution':False,'art_acceptance':False})
record(R/'actual-strict-policy-mutations-v6.json',{'status':'authored configuration','actual_policy_path':policy_path.relative_to(W).as_posix(),'actual_policy_sha256':sha(policy_path.read_bytes()),'admitted_recipes':len(recipes),'mutants_rejected':len(mutants),'mutants':mutants,'rights_or_art_acceptance':False})
packet={'status':'authored configuration','selected':False,'apply_automatically':False,'supersedes_only_recipe_metadata_of':rel(OLD/'root-integration-packet-v5.json'),'prior_packet_sha256':sha((OLD/'root-integration-packet-v5.json').read_bytes()),'expected_manifest_sha256':sha(manifest.read_bytes()),'variant_count':10,'creature_logical_recipes':64,'additional_tower_portraits':2,'logical_recipes':len(recipes),'physical_outputs_per_compile_pass':len(passes[0]),'all948_prior_creature_output_hashes_unchanged':True,'changes':changes,'variants':old['variants'],'source_bindings':bindings,'graphics_offset_proposals':old['graphics_offset_proposals'],'muzzle_consumer_note':rel(OLD/'native-muzzle-consumer-note-v1.txt'),'actual_strict_policy_admitted':True,'source_closure_files':len(sources),'actual_source_export_errors':0,'evidence':{rel(p):sha(p.read_bytes())for p in[R/'actual-source-export-admission-v6.json',R/'actual-converter-replays-v6.json',R/'actual-strict-policy-mutations-v6.json',OLD/'executed-tests-v5.json',OLD/'selected-source-body-and-stock-crop-v5.json']},'limitations':old['limitations']+['New tower portrait large uses a lossless centred58x64crop of actual genuine baseCorsair64x64portrait; small uses actual32x32portrait. Former old prepared-v2 sources preserved, never selected by these proposals.']}
record(R/'root-integration-packet-v6.json',packet);record(R/'selected-source-inventory-v6.json',{'files_sha256':{rel(p):sha(p.read_bytes())for p in sorted(sources)},'source_export_eligible':True})
print(json.dumps({'recipes':len(recipes),'outputs':len(passes[0]),'prior_creature_outputs_unchanged':len(oldoutputs),'actual_policy_mutants_rejected':len(mutants),'source_closure_files':len(sources),'source_export_errors':0,'packet':rel(R/'root-integration-packet-v6.json'),'packet_sha256':sha((R/'root-integration-packet-v6.json').read_bytes())}))
