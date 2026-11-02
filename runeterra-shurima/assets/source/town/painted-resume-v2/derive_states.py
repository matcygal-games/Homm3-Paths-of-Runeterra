"""Data-driven technical conversion of painted upgrades at frozen base anchors.

No art synthesis, opaque-bound per-state fitting, global conversion or selection.
Pure registration/surface/recipe helpers can serve later assigned state packets.
"""
from pathlib import Path
import hashlib,io,json,sys
from PIL import Image,ImageChops,ImageFilter
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[3];WORKSPACE=PROJECT.parent
RECIPES=PROJECT/'assets/recipes/town/painted-resume-v2';REPORT=PROJECT/'build/reports/town-painted-resume-20261023-v2'
PREFIX='Content/Sprites/runeterra/shurima/town/structures/'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_bytes())
def encoded(value):return (json.dumps(value,sort_keys=True,indent=2,ensure_ascii=False)+'\n').encode('utf-8')
def png(image):
 stream=io.BytesIO();image.save(stream,format='PNG',compress_level=9,optimize=False);return stream.getvalue()
def put(path,raw):
 path=path.absolute();assert any(path.is_relative_to(root) for root in (HERE,RECIPES,REPORT)),path
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('xb') as stream:stream.write(raw)
def write(path,value):put(path,encoded(value))
def own_source(name):
 path=(PROJECT/name).resolve();assert path.is_relative_to(PROJECT/'assets/source') and path.is_file()
 assert not path.is_symlink() and not getattr(path.stat(),'st_file_attributes',0)&0x400
 return path
def register(image,base):
 """Normalize source canvas at bottom-center, retaining the base's exact crop.

Visible child content outside that crop is rejected, never squeezed or clipped.
This preserves the already-selected base scale/placement rather than enlarging
or shrinking each new state to its own opaque extent.
"""
 assert image.mode=='RGBA' and image.getchannel('A').getbbox()
 width,height=base['source_canvas'];dx=(width-image.width)//2;dy=height-image.height
 child=image.getchannel('A').getbbox();translated=[child[0]+dx,child[1]+dy,child[2]+dx,child[3]+dy];crop=base['source_crop']
 assert crop[0]<=translated[0]<translated[2]<=crop[2] and crop[1]<=translated[1]<translated[3]<=crop[3],'Painted child exceeds frozen base crop; explicit cohort review required'
 aligned=Image.new('RGBA',(width,height),(0,0,0,0));aligned.alpha_composite(image,(dx,dy))
 piece=aligned.crop(crop).resize(tuple(base['resampled_size']),Image.Resampling.LANCZOS)
 frame=Image.new('RGBA',(800,374),(0,0,0,0));frame.alpha_composite(piece,tuple(base['placement']))
 return frame,{'source_canvas_offset':[dx,dy],'translated_nonzero_alpha_bbox':translated,'fixed_base_crop':crop,'fixed_resampled_size':base['resampled_size'],'fixed_placement':base['placement'],'uniform_base_scale':base['uniform_scale']}
def surfaces(frame,image):
 alpha=frame.getchannel('A').point(lambda value:255 if value>=128 else 0)
 area=Image.new('RGBA',frame.size,(255,255,255,0));area.putalpha(alpha)
 border=Image.new('RGBA',frame.size,(255,255,0,0));border.putalpha(ImageChops.subtract(alpha.filter(ImageFilter.MaxFilter(5)),alpha))
 piece=image.crop(image.getchannel('A').getbbox());piece.thumbnail((54,60),Image.Resampling.LANCZOS)
 campaign=Image.new('RGBA',(58,64),(0,0,0,0));campaign.alpha_composite(piece,((58-piece.width)//2,62-piece.height))
 return {'frame':frame,'area':area,'border':border,'campaign':campaign}
def recipe_set(key,sources,common,base):
 def descriptor(role,canvas):return {'source':sources[role]['path'],'source_sha256':sources[role]['sha256'],'source_canvas':canvas}
 x,y,w,h=base['native_site_box']
 result={'animation':{**common,'recipe_type':'vcmi_animation','output_path':PREFIX+key+'.json','canvas':[800,374],'pivot':{'x':x+w//2,'y':min(373,y+h-1)},'generateShadow':0,'generateOverlay':0,'groups':[{'group':0,'frames':[{'frame':0,**descriptor('frame',[800,374]),'sha256':sources['frame']['sha256']}]}]}}
 for role,canvas in (('area',[800,374]),('border',[800,374]),('campaign',[58,64])):
  result[role]={**common,'recipe_type':'raster','output_path':PREFIX+key+'_'+role+'.png','canvas':canvas,'size':canvas,'fit':'exact','require_alpha':True,**descriptor(role,canvas)}
  if role in ('area','border'):result[role]['production_status']='derived-technical-mask-complete'
 return result
def main():
 jobs=read(HERE/'jobs.json');ledger=PROJECT/jobs['registration_ledger'];assert sha(ledger)==jobs['registration_ledger_sha256']
 old={row['key']:row for row in read(ledger)['states']};comparison=PROJECT/jobs['comparison_assembly'];assert sha(comparison)==jobs['comparison_assembly_sha256']
 faction=read(PROJECT/'content/factions.json')['shurima']['town'];required={row['output_path'] for row in read(PROJECT/'assets/manifest.json')['assets']}
 initial_pins={name:sha(PROJECT/name) for name in ('content/factions.json','design/town-visuals.json','assets/manifest.json')}
 protected={str(path):sha(path) for root in (PROJECT/'assets/source/town/buildings-v1',PROJECT/'assets/source/town/painted-resume-v1',PROJECT/'assets/recipes/town/painted-resume-v1') for path in root.rglob('*') if path.is_file()}
 producers={}
 for path in (PROJECT/'assets/recipes').rglob('*.json'):
  value=read(path)
  if 'recipe_type' in value:
   for output in [value.get('output_path'),*value.get('output_paths',[])]:
    if output:producers.setdefault(output.casefold(),[]).append(str(path.relative_to(PROJECT)))
 targets=[PREFIX+job['key']+suffix for job in jobs['states'] for suffix in ('.json','_area.png','_border.png','_campaign.png')]
 collisions={name:producers[name.casefold()] for name in targets if name.casefold() in producers}
 assert set(targets)<=required and len(targets)==len(set(name.casefold() for name in targets))
 write(REPORT/'prewrite-check.json',{'collisions':collisions,'target_outputs':targets,'input_pins':initial_pins,'preserved_old_source_recipe_pins':protected});assert not collisions,'Existing output producer collision'
 sys.path.insert(0,str(WORKSPACE/'scripts'));import faction_art_compile
 compiler=faction_art_compile.create_compiler('shurima');records=[];compiled={};results=[]
 for job in jobs['states']:
  key=job['key'];base=old[job['registration_base']];master=own_source(job['master']);metadata_path=own_source(job['generation']);prompt=own_source(job['prompt'])
  assert sha(master)==job['master_sha256'] and sha(metadata_path)==job['generation_sha256'] and sha(prompt)==job['prompt_sha256']
  meta=read(metadata_path);assert meta['master']==job['master'] and meta['master_sha256']==job['master_sha256'] and meta['prompt_sha256']==job['prompt_sha256'] and meta['image_generation_used'] is True
  assert meta['parent']==base['master'] and meta['parent_sha256']==base['master_sha256']
  assert sha(PROJECT/base['master'])==base['master_sha256']
  structure=faction['structures'][key];assert all(structure[axis]==base['native_structure'][axis] for axis in ('x','y','z'))
  with Image.open(master) as image:image.load();original=image.copy()
  frame,registration=register(original,base);images=surfaces(frame,original);sources={}
  for role,image in images.items():
   path=HERE/key/(role+'.png');put(path,png(image));sources[role]={'path':path.relative_to(PROJECT).as_posix(),'sha256':sha(path)}
  common={'status':'painted-candidate','production_status':'painted-master-complete-unapproved','visual_approval_granted':False,'generation':{'image_generation_used':True,'provider':meta['provider'],'model':meta['model'],'painted_master':job['master'],'painted_master_sha256':job['master_sha256'],'prompt':prompt.read_text(encoding='utf-8'),'prompt_file':job['prompt']},'credits':{'author':'Project-directed builtin image generation; deterministic technical conversion','license':None,'redistribution':'unresolved; no release approval'}}
  recipes=recipe_set(key,sources,common,base);mapping=[]
  for role,recipe in recipes.items():
   path=RECIPES/(key+'-'+role+'.json');write(path,recipe);outputs,result=compiler.plan(PROJECT,path);results.append(result)
   for name,payload in outputs.items():
    assert name not in compiled;put(REPORT/'compiled'/name,payload);compiled[name]={'bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest(),'recipe_path':path.relative_to(PROJECT).as_posix(),'recipe_sha256':sha(path)}
   mapping.append({'output_path':recipe['output_path'],'recipe_path':path.relative_to(PROJECT).as_posix(),'recipe_sha256':sha(path),'dimensions':recipe['canvas'],'sha256':compiled[recipe['output_path']]['sha256']})
  keys=[row['key'] for row in read(comparison)['states'] if row['key'] not in ('shipyard','grail')];assert job['registration_base'] in keys
  with Image.open(PROJECT/'assets/source/town/landscape-v1/native-rgba.png') as image:terrain=image.convert('RGBA')
  before=terrain.copy();after=terrain.copy()
  for oldkey in sorted(keys,key=lambda value:faction['structures'][value]['z']):
   with Image.open(PROJECT/old[oldkey]['derived_sources']['frame']['path']) as image:
    before.alpha_composite(image);after.alpha_composite(frame if oldkey==job['registration_base'] else image)
  put(REPORT/(key+'-before-800x374.png'),png(before));put(REPORT/(key+'-after-800x374.png'),png(after))
  pair=Image.new('RGBA',(1600,374));pair.alpha_composite(before);pair.alpha_composite(after,(800,0));put(REPORT/(key+'-native-before-after.png'),png(pair))
  x,y,w,h=base['native_site_box'];crop=(x,y,x+w,y+h);pair=Image.new('RGBA',(w*2,h));pair.alpha_composite(before.crop(crop));pair.alpha_composite(after.crop(crop),(w,0));put(REPORT/(key+'-civic-native-crops.png'),png(pair))
  records.append({'job':job,'registration':registration,'base_registration':base,'derived_sources':sources,'required_output_mapping':mapping,'native_click_pixels':images['area'].getchannel('A').histogram()[255],'native_alpha_bbox':frame.getchannel('A').getbbox(),'native_structure':structure})
 assert all(sha(Path(path))==pin for path,pin in protected.items())
 assert all(sha(PROJECT/name)==pin for name,pin in initial_pins.items())
 write(HERE/'provenance.json',{'producer':str(Path(__file__).relative_to(PROJECT)),'producer_sha256':sha(Path(__file__)),'jobs_sha256':sha(HERE/'jobs.json'),'registration_ledger_sha256':sha(ledger),'states':records,'native_execution':False,'visual_approval_granted':False,'old_sources_unchanged':True})
 write(REPORT/'conversion.json',{'actual_converter':str(WORKSPACE/'scripts/faction_art_compile.py'),'converter_sha256':sha(WORKSPACE/'scripts/faction_art_compile.py'),'method':'Actual configured compiler.plan returns bytes written to ownreport only','states':records,'results':results,'compiled_outputs':compiled,'global_generated_written':False,'manifest_modified':False,'native_execution':False,'visual_approval_granted':False})
 print(json.dumps({'states':len(records),'recipes':len(results),'compiled_resources':len(compiled),'old_sources_unchanged':True,'manifest_modified':False,'native_execution':False}))
if __name__=='__main__':main()
