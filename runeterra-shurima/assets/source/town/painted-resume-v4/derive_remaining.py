"""Finish source-bound technical town layers, using pinned v2 pure primitives.

Only documented transparent padding is removed. Each chain uses its existing
source-pixel scale, fixed source center and explicit parent foundation contact.
No automatic per-state opaque fit, native execution or production publication.
"""
from pathlib import Path
import hashlib,importlib.util,json,sys
from PIL import Image,ImageChops,ImageDraw
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[3];WORKSPACE=PROJECT.parent
RECIPES=PROJECT/'assets/recipes/town/painted-resume-v4';REPORT=PROJECT/'build/reports/town-painted-resume-20261023-v4'
PREFIX='Content/Sprites/runeterra/shurima/town/structures/'
HELPER=PROJECT/'assets/source/town/painted-resume-v2/derive_states.py';HELPER_SHA='9244b8e0109d40de74eab4b9716d43ac7cb170f6aaebdda3daa96b045d4eb56f'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_bytes())
def put(path,payload):
 assert any(path.resolve().is_relative_to(root) for root in (HERE,RECIPES,REPORT));path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('xb') as stream:stream.write(payload)
def write(path,value):put(path,(json.dumps(value,sort_keys=True,indent=2,ensure_ascii=False)+'\n').encode())
def load_helper():
 assert sha(HELPER)==HELPER_SHA;spec=importlib.util.spec_from_file_location('pinned_painted_v2_primitives',HELPER);helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper);return helper
def contact(image):return image.getchannel('A').point(lambda v:255 if v>=32 else 0).getbbox()[3]
def render_piece(image,job):
 # Declared raw crop removes only previously attested transparent padding,
 # never the per-state opaque bbox or newly painted upper architecture.
 return image.crop(job['raw_crop']).resize(tuple(job['resampled_size']),Image.Resampling.LANCZOS)
def overflow_pixels(piece,placement):
 x,y=placement
 return [[i%piece.width,i//piece.width,rgba[3]] for i,rgba in enumerate(piece.get_flattened_data()) if rgba[3] and not (0<=x+i%piece.width<800 and 0<=y+i//piece.width<374)]
def clean_reviewed_ship(piece,job,helper):
 before=helper.png(piece);pixels=overflow_pixels(piece,job['placement']);authorization=job['ship_cleanup']
 assert hashlib.sha256(before).hexdigest()==authorization['before_resampled_png_sha256']
 assert pixels==authorization['exact_pixels'] and len(pixels)==33 and max(row[2] for row in pixels)==4
 assert job['placement']==[446,287] and piece.size==(126,98)
 changed=piece.copy()
 for x,y,a in pixels:
  r,g,b,old=changed.getpixel((x,y));assert old==a<=4 and job['placement'][1]+y>=374;changed.putpixel((x,y),(r,g,b,0))
 assert not overflow_pixels(changed,job['placement'])
 return changed,{'operation':'Clear ONLY the33 reviewed outside-viewport alpha<=4 fringe pixels; RGB,all inbounds RGBA,hull/rope/body unchanged','count':33,'max_alpha':4,'pixels':pixels,'before_resampled_png_sha256':hashlib.sha256(before).hexdigest(),'after_resampled_png_sha256':hashlib.sha256(helper.png(changed)).hexdigest(),'source_sha256':job['source_sha256'],'placement':job['placement'],'native_execution':False,'art_acceptance_granted':False}
def main():
 helper=load_helper();inspection=read(REPORT/'source-inspection.json');entries=inspection['states']
 old={row['key']:row for row in read(PROJECT/'assets/source/town/painted-resume-v1/provenance.json')['states']}
 lookup={key:PROJECT/row['derived_sources']['frame']['path'] for key,row in old.items()}
 for version in ('v2','v3'):
  for row in read(PROJECT/f'assets/source/town/painted-resume-{version}/provenance.json')['states']:
   key=row.get('job',{}).get('key',row.get('key'));lookup[key]=PROJECT/row['derived_sources']['frame']['path']
 faction=read(PROJECT/'content/factions.json')['shurima']['town'];visuals=read(PROJECT/'design/town-visuals.json');sites={key:(name,site) for name,site in {**visuals['sites'],**visuals['special_sites']}.items() for key in site['keys']}
 base_for={**{f'dwellingUpLvl{i}':f'dwellingLvl{i}' for i in range(1,8)},'capitol':'villageHall','castle':'fort','mageGuild3':'mageGuild1','special2':'dwellingLvl3','special4':'dwellingLvl7','ship':'shipyard'}
 jobs=[]
 for entry in entries:
  key=entry['key'];base=old[base_for[key]];crop=entry['raw_crop'];size=[round((crop[2]-crop[0])*base['uniform_scale']),round((crop[3]-crop[1])*base['uniform_scale'])]
  # Native ship replacement is inherited from the verified building library;
  # the faction's special vessel state intentionally does not repeat it.
  parentkey=faction['buildings'][key].get('upgrades')
  if parentkey is None:
   assert key=='ship'
   native_text=(WORKSPACE/'vcmi-develop/vcmi-develop/config/buildingsLibrary.json').read_text(encoding='utf-8')
   import re
   match=re.search(r'"ship"\s*:\s*\{[^}]*"upgrades"\s*:\s*"([^"]+)"',native_text)
   assert match and match[1]=='shipyard';parentkey=match[1]
  reference=lookup.get(parentkey,lookup[base_for[key]])
  with Image.open(reference) as image:ground=contact(image)
  with Image.open(PROJECT/entry['source']) as image:
   piece=image.crop(crop).resize(tuple(size),Image.Resampling.LANCZOS);top=ground-contact(piece)
  placement=[base['placement'][0]+(base['resampled_size'][0]-size[0])//2,top]
  job={**entry,'base_site':base_for[key],'native_parent':parentkey,'parent_contact_reference':reference.relative_to(PROJECT).as_posix(),'parent_contact_sha256':sha(reference),'uniform_chain_scale':base['uniform_scale'],'resampled_size':size,'placement':placement,'foundation_alpha32_contact':ground,'native_site_box':sites[key][1]['box'],'layout_anchor':[sites[key][1]['box'][0]+sites[key][1]['box'][2]//2,sum(sites[key][1]['box'][1::2])],'decision':'Retain existing chain source-pixel scale and source center; translate only to current parent foundation contact. Raw source crop is full generation canvas after known transparent padding removal. No whole-body bbox fit or global shrink.'}
  if key=='ship':
   pixels=overflow_pixels(piece,placement);assert len(pixels)==33 and max(row[2] for row in pixels)==4 and placement==[446,287]
   job['ship_cleanup']={'authorization':'Coordinator explicit33outsideviewport alpha<=4pixels only; no inboundsRGBA change','exact_pixels':pixels,'before_resampled_png_sha256':hashlib.sha256(helper.png(piece)).hexdigest(),'overflow_report_sha256':sha(REPORT/'ship-overflow.json')}
  else:assert not overflow_pixels(piece,placement),(key,'Native viewport clipping prohibited')
  jobs.append(job)
 write(HERE/'registration.json',{'states':jobs,'helper_sha256':HELPER_SHA,'scope':'Explicit full-source registration and foundation-contact translation; actual painted camera/foundation shape continuity still requires native-size review.','native_execution':False,'visual_approval_granted':False})
 preserved={str(path):sha(path) for folder in [PROJECT/'assets/source/town'/name for name in ('buildings-v1','painted-resume-v1','painted-resume-v2','painted-resume-v3')]+[PROJECT/'assets/recipes/town'/name for name in ('painted-resume-v1','painted-resume-v2','painted-resume-v3')] for path in folder.rglob('*') if path.is_file()}
 pins={name:sha(PROJECT/name) for name in ('assets/manifest.json','content/factions.json','design/town-visuals.json')}
 producers={}
 for path in (PROJECT/'assets/recipes').rglob('*.json'):
  recipe=read(path)
  if 'recipe_type' in recipe:
   for name in [recipe.get('output_path'),*recipe.get('output_paths',[])]:
    if name:producers.setdefault(name.casefold(),[]).append(path.relative_to(PROJECT).as_posix())
 targets=[PREFIX+job['key']+suffix for job in jobs for suffix in ('.json','_area.png','_border.png','_campaign.png')]
 required={row['output_path'] for row in read(PROJECT/'assets/manifest.json')['assets']};collisions={name:producers[name.casefold()] for name in targets if name.casefold() in producers}
 write(REPORT/'prewrite-check.json',{'collisions':collisions,'target_outputs':targets,'preserved_old_sources':preserved,'input_pins':pins});assert not collisions and set(targets)<=required
 sys.path.insert(0,str(WORKSPACE/'scripts'));import faction_art_compile
 compiler=faction_art_compile.create_compiler('shurima');compiled={};results=[];records=[]
 for job in jobs:
  key=job['key'];source=PROJECT/job['source'];assert sha(source)==job['source_sha256'] and sha(PROJECT/job['metadata'])==job['metadata_sha256'] and sha(PROJECT/job['prompt'])==job['prompt_sha256'] and sha(PROJECT/job['parent'])==job['parent_sha256']
  with Image.open(source) as image:image.load();original=image.copy()
  piece=render_piece(original,job);cleanup=None
  if key=='ship':
   put(REPORT/'ship-before-cleanup-resample.png',helper.png(piece));piece,cleanup=clean_reviewed_ship(piece,job,helper);write(REPORT/'ship-exact-alpha-cleanup.json',cleanup)
  assert not overflow_pixels(piece,job['placement'])
  frame=Image.new('RGBA',(800,374),(0,0,0,0));frame.alpha_composite(piece,tuple(job['placement']));images=helper.surfaces(frame,original);sources={}
  for role,image in images.items():
   path=HERE/key/(role+'.png');put(path,helper.png(image));sources[role]={'path':path.relative_to(PROJECT).as_posix(),'sha256':sha(path)}
  meta=read(PROJECT/job['metadata']);provider=meta.get('provider',meta.get('tool'));model=meta.get('model','not exposed by built-in tool')
  common={'status':'painted-candidate','production_status':'painted-master-complete-unapproved','visual_approval_granted':False,'generation':{'image_generation_used':True,'provider':provider,'model':model,'painted_master':job['source'],'painted_master_sha256':job['source_sha256'],'prompt':(PROJECT/job['prompt']).read_text(encoding='utf-8'),'prompt_file':job['prompt']},'credits':{'author':'Project-directed builtin image generation; deterministic technical conversion','license':None,'redistribution':'pending; no release approval'}}
  if cleanup:common['technical_alpha_cleanup']={**cleanup,'receipt':(REPORT/'ship-exact-alpha-cleanup.json').relative_to(PROJECT).as_posix(),'receipt_sha256':sha(REPORT/'ship-exact-alpha-cleanup.json')}
  mapping=[]
  for role,recipe in helper.recipe_set(key,sources,common,{'native_site_box':job['native_site_box']}).items():
   path=RECIPES/(key+'-'+role+'.json');write(path,recipe);outputs,receipt=compiler.plan(PROJECT,path);results.append(receipt)
   for name,payload in outputs.items():
    assert name not in compiled;put(REPORT/'compiled'/name,payload);compiled[name]={'sha256':hashlib.sha256(payload).hexdigest(),'bytes':len(payload),'recipe_path':path.relative_to(PROJECT).as_posix(),'recipe_sha256':sha(path)}
   mapping.append({'output_path':recipe['output_path'],'recipe_path':path.relative_to(PROJECT).as_posix(),'recipe_sha256':sha(path),'sha256':compiled[recipe['output_path']]['sha256'],'dimensions':recipe['canvas']})
  lookup[key]=HERE/key/'frame.png';records.append({'job':job,'derived_sources':sources,'required_output_mapping':mapping,'native_body_bbox':images['area'].getchannel('A').getbbox(),'native_alpha_bbox':frame.getchannel('A').getbbox(),'cleanup':cleanup})
 assert len(lookup)==35 and set(lookup)==set(faction['buildings'])
 with Image.open(PROJECT/'assets/source/town/landscape-v1/native-rgba.png') as image:terrain=image.convert('RGBA')
 def scene(keys):
  image=terrain.copy()
  for key in sorted(keys,key=lambda k:faction['structures'][k]['z']):
   with Image.open(lookup[key]) as frame:image.alpha_composite(frame)
  return image
 groups={**visuals['sites'],**visuals['special_sites']};base_keys=[site['keys'][0] for site in visuals['sites'].values()];upgrade_keys=[site['keys'][-1] for site in visuals['sites'].values()]
 partial=[{'civic':'cityHall','defenses':'citadel','guild':'mageGuild2','rockbears':'special2','colossus':'special4'}.get(name,site['keys'][-1] if name in ('nomads','archers','priests') else site['keys'][0]) for name,site in visuals['sites'].items()]
 variants={'all-base':base_keys,'all-upgraded':upgrade_keys,'partial':partial,'coast-shipyard':upgrade_keys+['shipyard'],'coast-ship':upgrade_keys+['ship'],'grail-coast':upgrade_keys+['ship','grail']};exposures={}
 for name,keys in variants.items():
  put(REPORT/(name+'-800x374.png'),helper.png(scene(keys)));covered=Image.new('L',(800,374),0);rows={}
  for key in sorted(keys,key=lambda k:faction['structures'][k]['z'],reverse=True):
   with Image.open(lookup[key]) as image:mask=image.getchannel('A').point(lambda v:255 if v>=128 else 0)
   exposed=ImageChops.subtract(mask,covered);rows[key]={'click_pixels':mask.histogram()[255],'uncovered_click_pixels':exposed.histogram()[255]};covered=ImageChops.lighter(covered,mask)
  exposures[name]=rows
 # Every state is shown once in the chain atlas, using union crops so new
 # architecture outside a historical site's box is never hidden by the board.
 rows=[]
 for name,site in groups.items():
  bounds=[]
  for key in site['keys']:
   with Image.open(lookup[key]) as im:bounds.append(im.getchannel('A').getbbox())
  bbox=[max(0,min(b[0] for b in bounds)-2),max(0,min(b[1] for b in bounds)-2),min(800,max(b[2] for b in bounds)+2),min(374,max(b[3] for b in bounds)+2)];w=bbox[2]-bbox[0];h=bbox[3]-bbox[1]
  row=Image.new('RGBA',(max(800,w*len(site['keys'])),h+22),(45,45,45,255));draw=ImageDraw.Draw(row)
  for index,key in enumerate(site['keys']):row.alpha_composite(scene([key]).crop(bbox),(index*w,22));draw.text((index*w+3,4),key,fill='white')
  rows.append(row);put(REPORT/(name+'-cohort-native.png'),helper.png(row))
 atlas=Image.new('RGBA',(max(row.width for row in rows),sum(row.height for row in rows)),(45,45,45,255));y=0
 for row in rows:atlas.alpha_composite(row,(0,y));y+=row.height
 put(REPORT/'all35-cohort-native.png',helper.png(atlas))
 assert all(sha(Path(name))==pin for name,pin in preserved.items()) and all(sha(PROJECT/name)==pin for name,pin in pins.items()) and sha(HELPER)==HELPER_SHA
 for job in jobs:assert sha(PROJECT/job['source'])==job['source_sha256'] and sha(PROJECT/job['metadata'])==job['metadata_sha256']
 write(HERE/'provenance.json',{'producer':Path(__file__).relative_to(PROJECT).as_posix(),'producer_sha256':sha(Path(__file__)),'registration_sha256':sha(HERE/'registration.json'),'helper_sha256':HELPER_SHA,'states':records,'native_execution':False,'visual_approval_granted':False})
 write(REPORT/'conversion.json',{'states':records,'results':results,'compiled_outputs':compiled,'all35_frame_sources':{key:{'source':path.relative_to(PROJECT).as_posix(),'sha256':sha(path)} for key,path in lookup.items()},'variants':variants,'exposure':exposures,'all_visible_masks_exposed':all(row['uncovered_click_pixels']>0 for variant in exposures.values() for row in variant.values()),'actual_converter_sha256':sha(WORKSPACE/'scripts/faction_art_compile.py'),'native_execution':False,'global_generated_written':False,'manifest_modified':False,'visual_approval_granted':False})
 print(json.dumps({'states':len(records),'recipes':len(results),'compiled_resources':len(compiled),'all35_states':len(lookup),'all_exposed':all(row['uncovered_click_pixels']>0 for variant in exposures.values() for row in variant.values()),'native_execution':False}))
if __name__=='__main__':main()
