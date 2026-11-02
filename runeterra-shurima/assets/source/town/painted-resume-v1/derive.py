"""Only crop/resample/alpha/mask/assembly from existing painted Shurima masters.

Writes only the assigned new derived-source leaf, recipe leaf and report leaf.
Strict configured compiler.plan produces actual bytes, stored only in report.
Missing states and original masters are never generated or changed.
"""
from pathlib import Path
from collections import Counter
import hashlib,io,json,sys
from PIL import Image,ImageChops,ImageFilter
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[3];WORKSPACE=PROJECT.parent
RECIPES=PROJECT/'assets/recipes/town/painted-resume-v1'
REPORT=PROJECT/'build/reports/town-painted-resume-20261023-v1'
COMPILED=REPORT/'compiled';PREFIX='Content/Sprites/runeterra/shurima/town/structures/'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def read(path):return json.loads(path.read_bytes())
def relative(path):return path.relative_to(PROJECT).as_posix()
def put(path,raw):
 path=path.absolute();assert any(path.is_relative_to(root) for root in (HERE,RECIPES,REPORT)),path
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('xb') as stream:stream.write(raw)
def encoded(value):return (json.dumps(value,sort_keys=True,indent=2,ensure_ascii=False)+'\n').encode('utf-8')
def write(path,value):put(path,encoded(value))
def png(image):
 stream=io.BytesIO();image.save(stream,format='PNG',compress_level=9,optimize=False);return stream.getvalue()
def producers():
 result={}
 for path in sorted((PROJECT/'assets/recipes').rglob('*.json')):
  recipe=read(path)
  if 'recipe_type' not in recipe:continue
  for output in [recipe.get('output_path'),*recipe.get('output_paths',[])]:
   if output:result.setdefault(output.casefold(),[]).append(relative(path))
 return result
def source_descriptor(path,canvas):return {'source':relative(path),'source_sha256':sha(path),'source_canvas':canvas}
def main():
 inventory=read(REPORT/'input-inventory.json');assert inventory['master_count']==18
 assert not RECIPES.exists(),'Do not overwrite a previous producer run'
 for name in ('content/factions.json','design/town-visuals.json','assets/manifest.json'):
  assert sha(PROJECT/name)==inventory['input_pins'][name],name
 manifest=read(PROJECT/'assets/manifest.json');required={x['output_path'] for x in manifest['assets']}
 collision=producers();targets=[PREFIX+row['key']+tail for row in inventory['masters'] for tail in ('.json','_area.png','_border.png','_campaign.png')]
 assert set(targets)<=required,'Unexpected output outside current required manifest'
 found={name:collision[name.casefold()] for name in targets if name.casefold() in collision}
 write(REPORT/'prewrite-producer-check.json',{'target_count':len(targets),'collisions':found,'existing_producers':collision,'native_execution':False})
 assert not found,'Existing producer collision: '+repr(found)
 faction=read(PROJECT/'content/factions.json')['shurima']['town'];visual=read(PROJECT/'design/town-visuals.json')
 sites={key:(name,site) for name,site in {**visual['sites'],**visual['special_sites']}.items() for key in site['keys']}
 records=[];all_recipes=[];layers={};areas={}
 for entry in inventory['masters']:
  key=entry['key'];master=PROJECT/entry['master'];assert sha(master)==entry['sha256']
  generation=read(PROJECT/entry['generation']);prompt=master.with_name('prompt.txt')
  assert sha(prompt)==entry['prompt_sha256'] and sha(PROJECT/entry['generation'])==entry['generation_sha256']
  site,layout=sites[key];x,y,w,h=layout['box'];structure=faction['structures'][key]
  assert structure['x']==structure['y']==0 and structure['z']==layout['z']
  with Image.open(master) as opened:
   opened.load();assert opened.mode=='RGBA';original=opened.copy()
  crop=original.getchannel('A').getbbox();assert crop and list(crop)==entry['alpha_bbox']
  # Preserve every source pixel with nonzero alpha. Uniform size and one bottom
  # anchor per available site; no per-state upgrade fitting is inferred.
  piece=original.crop(crop);scale=min((w-4)/piece.width,(h-3)/piece.height)
  native_size=(max(1,round(piece.width*scale)),max(1,round(piece.height*scale)))
  piece=piece.resize(native_size,Image.Resampling.LANCZOS)
  placement=(x+(w-piece.width)//2,y+h-piece.height)
  frame=Image.new('RGBA',(800,374),(0,0,0,0));frame.alpha_composite(piece,placement)
  # SDLImage::isTransparent uses alpha<128 or pure cyan. White binary alpha
  # makes click area exact and excludes resampling fringe/weak source shadow.
  solid=frame.getchannel('A').point(lambda value:255 if value>=128 else 0)
  area=Image.new('RGBA',frame.size,(255,255,255,0));area.putalpha(solid)
  outline=ImageChops.subtract(solid.filter(ImageFilter.MaxFilter(5)),solid)
  border=Image.new('RGBA',frame.size,(255,255,0,0));border.putalpha(outline)
  iconpiece=original.crop(crop);iconpiece.thumbnail((54,60),Image.Resampling.LANCZOS)
  campaign=Image.new('RGBA',(58,64),(0,0,0,0));campaign.alpha_composite(iconpiece,((58-iconpiece.width)//2,64-2-iconpiece.height))
  folder=HERE/key
  sources={}
  for role,image in (('frame',frame),('area',area),('border',border),('campaign',campaign)):
   path=folder/(role+'.png');put(path,png(image));sources[role]=path
  provenance={'image_generation_used':True,'provider':generation['tool'],'model':generation['model'],'prompt':prompt.read_text(encoding='utf-8'),'painted_master':entry['master'],'painted_master_sha256':entry['sha256'],'prompt_file':relative(prompt)}
  common={'status':'painted-candidate','production_status':'painted-master-complete-unapproved','visual_approval_granted':False,'generation':provenance,'credits':{'author':'Project-directed builtin image generation; deterministic technical conversion','license':None,'redistribution':'unresolved; no release approval'}}
  recipe={**common,'recipe_type':'vcmi_animation','output_path':PREFIX+key+'.json','canvas':[800,374],'pivot':{'x':x+w//2,'y':min(373,y+h-1)},'generateShadow':0,'generateOverlay':0,'groups':[{'group':0,'frames':[{'frame':0,**source_descriptor(sources['frame'],[800,374]),'sha256':sha(sources['frame'])}]}]}
  path=RECIPES/(key+'-animation.json');write(path,recipe);all_recipes.append(path)
  for role,canvas in (('area',[800,374]),('border',[800,374]),('campaign',[58,64])):
   recipe={**common,'recipe_type':'raster','output_path':PREFIX+key+'_'+role+'.png','canvas':canvas,'size':canvas,'fit':'exact','require_alpha':True,**source_descriptor(sources[role],canvas)}
   if role in ('area','border'):recipe['production_status']='derived-technical-mask-complete'
   path=RECIPES/(key+'-'+role+'.json');write(path,recipe);all_recipes.append(path)
  visible=solid.histogram()[255];border_count=outline.histogram()[255]
  assert visible>0 and border_count>0
  records.append({'key':key,'site':site,'master':entry['master'],'master_sha256':entry['sha256'],'generation_sha256':entry['generation_sha256'],'prompt_sha256':entry['prompt_sha256'],'source_crop':list(crop),'source_canvas':list(original.size),'uniform_scale':scale,'resampled_size':list(native_size),'placement':list(placement),'native_site_box':layout['box'],'native_structure':structure,'native_alpha_bbox':list(frame.getchannel('A').getbbox()),'native_click_bbox':list(solid.getbbox()),'click_pixels':visible,'highlight_pixels':border_count,'source_alpha_touches_canvas_edge':crop[0]==0 or crop[1]==0 or crop[2]==original.width or crop[3]==original.height,'derived_sources':{role:{'path':relative(path),'sha256':sha(path)} for role,path in sources.items()},'future_upgrade_policy':'Missing upgrade masters remain missing. These transforms establish current base anchors only; review the complete same-site cohort before future upgrade selection.'})
  layers[key]=frame;areas[key]=solid
 # Call the actual configured compiler planner on real project sources. This
 # returns all native JSON/PNG bytes; its normal global output writer is not run.
 sys.path.insert(0,str(WORKSPACE/'scripts'))
 import faction_art_compile
 compiler=faction_art_compile.create_compiler('shurima')
 receipt={'actual_converter':str(WORKSPACE/'scripts/faction_art_compile.py'),'converter_sha256':sha(WORKSPACE/'scripts/faction_art_compile.py'),'method':'create_compiler(shurima).plan(actual_project, actual_recipe); returned bytes written exclusively to owned report compiled folder','native_execution':False,'manifest_modified':False,'global_generated_written':False,'results':[],'outputs':{}}
 for path in all_recipes:
  outputs,result=compiler.plan(PROJECT,path)
  for name,raw in outputs.items():
   assert name not in receipt['outputs'],'Duplicate expanded output producer'
   put(COMPILED/name,raw);receipt['outputs'][name]={'sha256':digest(raw),'bytes':len(raw),'recipe':relative(path)}
  receipt['results'].append(result)
 assert len(receipt['results'])==72 and len(receipt['outputs'])==90
 write(REPORT/'conversion.json',receipt)
 with Image.open(PROJECT/'assets/source/town/landscape-v1/native-rgba.png') as image:terrain=image.convert('RGBA')
 assert terrain.size==(800,374)
 variants={'ordinary-base':[key for key in layers if key not in ('shipyard','grail')],'all-available':list(layers),'early':['villageHall','tavern','dwellingLvl1']}
 exposed={}
 for variant,keys in variants.items():
  scene=terrain.copy();ordered=sorted(keys,key=lambda key:faction['structures'][key]['z'])
  for key in ordered:scene.alpha_composite(layers[key])
  put(REPORT/(variant+'-800x374.png'),png(scene))
  # Read-only silhouette exposure diagnostic; no acceptance threshold invented.
  cover=Image.new('L',(800,374),0);exposure={}
  for key in reversed(ordered):
   click=areas[key];remaining=ImageChops.subtract(click,cover)
   exposure[key]={'mask_pixels':click.histogram()[255],'uncovered_click_pixels':remaining.histogram()[255]}
   cover=ImageChops.lighter(cover,layers[key].getchannel('A').point(lambda v:255 if v>=128 else 0))
  exposed[variant]=exposure
 # Keep private reference pixels in report only, never recipes or generated mod.
 castle_path=PROJECT/'assets/references/native/castle/selected-original-scene.png'
 with Image.open(castle_path) as image:castle=image.convert('RGBA')
 assert castle.size==(800,374)
 with Image.open(REPORT/'all-available-800x374.png') as image:partial=image.convert('RGBA')
 comparison=Image.new('RGBA',(800,748));comparison.alpha_composite(castle,(0,0));comparison.alpha_composite(partial,(0,374));put(REPORT/'castle-and-partial-native.png',png(comparison))
 write(HERE/'provenance.json',{'producer':relative(Path(__file__)),'producer_sha256':sha(Path(__file__)),'technical_operations':['exact-alpha bounding crop','uniform LANCZOS resample','declared bottom-centered site placement in full800x374 canvas','binary alpha128 click silhouette','2pixel external silhouette dilation highlight','58x64 campaign crop/contain','native composition by actual structure z'],'states':records,'masters_unchanged':True,'missing_states':inventory['missing_states'],'native_execution':False,'visual_approval_granted':False,'release_accepted':False})
 write(REPORT/'assembly.json',{'status':'authored configuration','states':records,'available_states':len(records),'missing_states':inventory['missing_states'],'recipes':{relative(path):sha(path) for path in all_recipes},'required_outputs_covered':targets,'remaining_building_state_outputs':[name for name in required if name.startswith(PREFIX) and name not in targets],'partial_compositions':{variant:relative(REPORT/(variant+'-800x374.png')) for variant in variants},'click_exposure_diagnostics':exposed,'native_castle_comparison':{'path':relative(castle_path),'sha256':sha(castle_path)},'manifest_unchanged':sha(PROJECT/'assets/manifest.json')==inventory['input_pins']['assets/manifest.json'],'visual_approval_granted':False,'native_execution':False})
 for entry in inventory['masters']:assert sha(PROJECT/entry['master'])==entry['sha256']
 after=producers();assert all(len(values)==1 for values in after.values()),'Output producer collision after write'
 assert all(name.casefold() in after for name in targets)
 write(REPORT/'postwrite-producer-check.json',{'target_count':len(targets),'all_targets_single_producer':True,'manifest_unchanged':sha(PROJECT/'assets/manifest.json')==inventory['input_pins']['assets/manifest.json'],'actual_recipe_output_index':after})
 print(json.dumps({'available_states':len(records),'missing_states':len(inventory['missing_states']),'recipes':len(all_recipes),'compiled_resources':len(receipt['outputs']),'manifest_modified':False,'global_generated_written':False,'native_execution':False}))
if __name__=='__main__':main()
