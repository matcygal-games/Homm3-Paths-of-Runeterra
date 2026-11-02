"""Use the pinned v2 pure helpers with explicit v3 complete-source registration."""
from pathlib import Path
import hashlib,importlib.util,json,sys
from PIL import Image,ImageChops
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[3];WORKSPACE=PROJECT.parent
RECIPES=PROJECT/'assets/recipes/town/painted-resume-v3';REPORT=PROJECT/'build/reports/town-painted-resume-20261023-v3'
PREFIX='Content/Sprites/runeterra/shurima/town/structures/'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_bytes())
def put(path,payload):
 assert any(path.resolve().is_relative_to(root) for root in (HERE,RECIPES,REPORT));path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('xb') as stream:stream.write(payload)
def write(path,value):put(path,(json.dumps(value,sort_keys=True,indent=2,ensure_ascii=False)+'\n').encode())
def main():
 jobs=read(HERE/'registration.json');helper_path=PROJECT/jobs['helper'];assert sha(helper_path)==jobs['helper_sha256']
 spec=importlib.util.spec_from_file_location('reviewed_painted_v2_helpers',helper_path);helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
 inspection={row['key']:row for row in read(REPORT/'source-inspection.json')['states']}
 old={row['key']:row for row in read(PROJECT/'assets/source/town/painted-resume-v1/provenance.json')['states']}
 faction=read(PROJECT/'content/factions.json')['shurima']['town'];visual=read(PROJECT/'design/town-visuals.json')
 sites={key:value for value in {**visual['sites'],**visual['special_sites']}.values() for key in value['keys']}
 required={row['output_path'] for row in read(PROJECT/'assets/manifest.json')['assets']}
 preserved={str(path):sha(path) for root in [PROJECT/'assets/source/town'/name for name in ('buildings-v1','painted-resume-v1','painted-resume-v2')]+[PROJECT/'assets/recipes/town'/name for name in ('painted-resume-v1','painted-resume-v2')] for path in root.rglob('*') if path.is_file()}
 pins={name:sha(PROJECT/name) for name in ('content/factions.json','design/town-visuals.json','assets/manifest.json')}
 producers={}
 for path in (PROJECT/'assets/recipes').rglob('*.json'):
  recipe=read(path)
  if 'recipe_type' in recipe:
   for name in [recipe.get('output_path'),*recipe.get('output_paths',[])]:
    if name:producers.setdefault(name.casefold(),[]).append(str(path.relative_to(PROJECT)))
 targets=[PREFIX+job['key']+suffix for job in jobs['states'] for suffix in ('.json','_area.png','_border.png','_campaign.png')]
 collisions={name:producers[name.casefold()] for name in targets if name.casefold() in producers}
 write(REPORT/'prewrite-check.json',{'collisions':collisions,'target_outputs':targets,'preserved_old_sources':preserved,'input_pins':pins});assert not collisions and set(targets)<=required
 sys.path.insert(0,str(WORKSPACE/'scripts'));import faction_art_compile
 compiler=faction_art_compile.create_compiler('shurima');compiled={};results=[];records=[];new_frames={}
 baseline_keys=[key for key in old if key not in ('shipyard','grail')]
 with Image.open(PROJECT/'assets/source/town/landscape-v1/native-rgba.png') as image:terrain=image.convert('RGBA')
 def scene(replacements):
  result=terrain.copy()
  for basekey in sorted(baseline_keys,key=lambda key:faction['structures'][key]['z']):
   source=replacements.get(basekey,PROJECT/old[basekey]['derived_sources']['frame']['path'])
   if isinstance(source,Image.Image):result.alpha_composite(source)
   else:
    with Image.open(source) as image:result.alpha_composite(image)
  return result
 for job in jobs['states']:
  key=job['key'];entry=inspection[key];folder=PROJECT/'assets/source/town/buildings-v2'/key;master=folder/'master.png';metadata_path=folder/'master-generation.json';meta=read(metadata_path);prompt=folder/'prompt.txt'
  assert sha(master)==entry['master_sha256']==meta['master_sha256'] and sha(metadata_path)==entry['metadata_sha256'] and sha(prompt)==entry['prompt_sha256']==meta['prompt_sha256']
  assert sha(PROJECT/meta['parent'])==entry['parent_sha256']==meta['parent_sha256'] and meta['image_generation_used'] is True
  assert faction['buildings'][key]['upgrades']==job['replacement']
  registration=job['registration'];assert registration['native_site_box']==sites[key]['box'] and faction['structures'][key]['x']==faction['structures'][key]['y']==0
  assert faction['structures'][key]['z']==sites[key]['z']
  with Image.open(master) as image:image.load();original=image.copy()
  frame,observed=helper.register(original,registration);images=helper.surfaces(frame,original);sources={}
  for role,image in images.items():
   path=HERE/key/(role+'.png');put(path,helper.png(image));sources[role]={'path':path.relative_to(PROJECT).as_posix(),'sha256':sha(path)}
  common={'status':'painted-candidate','production_status':'painted-master-complete-unapproved','visual_approval_granted':False,'generation':{'image_generation_used':True,'provider':meta['provider'],'model':meta['model'],'painted_master':master.relative_to(PROJECT).as_posix(),'painted_master_sha256':sha(master),'prompt':prompt.read_text(encoding='utf-8'),'prompt_file':prompt.relative_to(PROJECT).as_posix()},'credits':{'author':'Project-directed builtin image generation; deterministic technical conversion','license':None,'redistribution':'pending; no release approval'}}
  mapping=[]
  for role,recipe in helper.recipe_set(key,sources,common,registration).items():
   path=RECIPES/(key+'-'+role+'.json');write(path,recipe);outputs,receipt=compiler.plan(PROJECT,path);results.append(receipt)
   for name,payload in outputs.items():
    assert name not in compiled;put(REPORT/'compiled'/name,payload);compiled[name]={'sha256':hashlib.sha256(payload).hexdigest(),'bytes':len(payload),'recipe_path':path.relative_to(PROJECT).as_posix(),'recipe_sha256':sha(path)}
   mapping.append({'output_path':recipe['output_path'],'recipe_path':path.relative_to(PROJECT).as_posix(),'recipe_sha256':sha(path),'sha256':compiled[recipe['output_path']]['sha256'],'dimensions':recipe['canvas']})
  parent_frame=PROJECT/job['comparison_parent_frame'];before=scene({job['base_site']:parent_frame});after=scene({job['base_site']:frame})
  put(REPORT/(key+'-before-800x374.png'),helper.png(before));put(REPORT/(key+'-after-800x374.png'),helper.png(after))
  pair=Image.new('RGBA',(1600,374));pair.alpha_composite(before);pair.alpha_composite(after,(800,0));put(REPORT/(key+'-native-before-after.png'),helper.png(pair))
  x,y,w,h=registration['native_site_box'];pair=Image.new('RGBA',(w*2,h));pair.alpha_composite(before.crop((x,y,x+w,y+h)));pair.alpha_composite(after.crop((x,y,x+w,y+h)),(w,0));put(REPORT/(key+'-native-site-crops.png'),helper.png(pair))
  new_frames[job['base_site']]=frame
  records.append({'job':job,'source_inspection':entry,'observed_registration':observed,'derived_sources':sources,'required_output_mapping':mapping,'parent_frame_sha256':sha(parent_frame),'native_click_pixels':images['area'].getchannel('A').histogram()[255],'native_body_alpha_bbox':images['area'].getchannel('A').getbbox()})
 combined=scene(new_frames);put(REPORT/'all-three-upgrades-800x374.png',helper.png(combined))
 ordered=[]
 for key in baseline_keys:
  if key in new_frames:
   frame=new_frames[key];realkey=next(job['key'] for job in jobs['states'] if job['base_site']==key)
  else:frame=Image.open(PROJECT/old[key]['derived_sources']['frame']['path']).convert('RGBA');realkey=key
  ordered.append((faction['structures'][realkey]['z'],realkey,frame))
 covered=Image.new('L',(800,374),0);exposure={}
 for _,key,frame in sorted(ordered,reverse=True,key=lambda item:item[0]):
  mask=frame.getchannel('A').point(lambda v:255 if v>=128 else 0);exposed=ImageChops.subtract(mask,covered)
  exposure[key]={'click_pixels':mask.histogram()[255],'uncovered_click_pixels':exposed.histogram()[255]};covered=ImageChops.lighter(covered,mask)
 assert all(row['uncovered_click_pixels']>0 for row in exposure.values())
 assert sha(helper_path)==jobs['helper_sha256'] and all(sha(Path(name))==pin for name,pin in preserved.items()) and all(sha(PROJECT/name)==pin for name,pin in pins.items())
 write(HERE/'provenance.json',{'producer':Path(__file__).relative_to(PROJECT).as_posix(),'producer_sha256':sha(Path(__file__)),'registration_sha256':sha(HERE/'registration.json'),'helper_sha256':sha(helper_path),'states':records,'old_sources_unchanged':True,'native_execution':False,'visual_approval_granted':False})
 write(REPORT/'conversion.json',{'states':records,'results':results,'compiled_outputs':compiled,'click_exposure':exposure,'actual_converter_sha256':sha(WORKSPACE/'scripts/faction_art_compile.py'),'native_execution':False,'global_generated_written':False,'manifest_modified':False,'visual_approval_granted':False})
 print(json.dumps({'states':len(records),'recipes':len(results),'compiled_resources':len(compiled),'native_execution':False,'manifest_modified':False}))
if __name__=='__main__':main()
