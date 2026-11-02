"""Authorized two-state authored2D retained-landmark registration correction.

Historical v4 bytes are snapshotted; other11 states and ship cleanup stay exact.
The picked architectural points are authored2D evidence, not camera recovery.
"""
from pathlib import Path
import copy,hashlib,importlib.util,json,shutil,sys
from PIL import Image,ImageChops,ImageDraw
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[3];WORKSPACE=PROJECT.parent
REPORT=PROJECT/'build/reports/town-painted-resume-20261023-v4';RECIPES=PROJECT/'assets/recipes/town/painted-resume-v4';HISTORY=REPORT/'history/registration-v1'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_bytes())
def write(path,payload,*,replace=False):
 assert any(path.resolve().is_relative_to(root) for root in (HERE,RECIPES,REPORT))
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('wb' if replace else 'xb') as stream:stream.write(payload)
def dump(path,value):write(path,(json.dumps(value,sort_keys=True,indent=2,ensure_ascii=False)+'\n').encode())
def main():
 snapshot=read(HISTORY/'snapshot-manifest.json')
 for name,row in snapshot['files'].items():assert sha(HISTORY/name)==row['sha256']
 spec=importlib.util.spec_from_file_location('base_remaining_producer',HERE/'derive_remaining.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base);helper=base.load_helper()
 conversion=read(REPORT/'conversion.json');original=copy.deepcopy(conversion);registration=read(HERE/'registration.json');jobs={row['key']:row for row in registration['states']}
 picked={
  'capitol':{'parent_key':'cityHall','parent_frame':'assets/source/town/painted-resume-v3/cityHall/frame.png','feature':'Outer corners of paired retained front-court masonry plinth span; manually picked native view','parent_points':[[398,110],[486,110]],'child_points':[[398,114],[480,114]],'native_pick_uncertainty_pixels':2},
  'mageGuild3':{'parent_key':'mageGuild2','parent_frame':'assets/source/town/painted-resume-v3/mageGuild2/frame.png','feature':'Left/right edge of retained ground-floor doorway at mid panel; manually picked native view','parent_points':[[517,158],[532,158]],'child_points':[[526,164],[538,164]],'native_pick_uncertainty_pixels':2}}
 sys.path.insert(0,str(WORKSPACE/'scripts'));import faction_art_compile
 compiler=faction_art_compile.create_compiler('shurima');compiled_root=REPORT/'compiled-v2';assert not compiled_root.exists()
 for name,row in original['compiled_outputs'].items():
  source=REPORT/'compiled'/name;assert sha(source)==row['sha256'];dest=compiled_root/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
 revisions=[]
 for key,points in picked.items():
  job=jobs[key];parent=PROJECT/points['parent_frame'];assert sha(parent)==job['parent_contact_sha256']
  target_span=points['parent_points'][1][0]-points['parent_points'][0][0];old_span=points['child_points'][1][0]-points['child_points'][0][0];factor=target_span/old_span
  with Image.open(PROJECT/job['source']) as image:
   assert sha(PROJECT/job['source'])==job['source_sha256'];raw=image.crop(job['raw_crop']);original_image=image.copy()
  size=[round(raw.width*job['uniform_chain_scale']*factor),round(raw.height*job['uniform_chain_scale']*factor)];piece=raw.resize(tuple(size),Image.Resampling.LANCZOS)
  actual_x_ratio=size[0]/job['resampled_size'][0];child_mid=sum(point[0] for point in points['child_points'])/2-job['placement'][0];parent_mid=sum(point[0] for point in points['parent_points'])/2
  placement=[round(parent_mid-child_mid*actual_x_ratio),job['foundation_alpha32_contact']-base.contact(piece)]
  assert not base.overflow_pixels(piece,placement),'New architecture would leave native viewport'
  frame=Image.new('RGBA',(800,374));frame.alpha_composite(piece,tuple(placement));images=helper.surfaces(frame,original_image)
  row=next(state for state in conversion['states'] if state['job']['key']==key);prior_sources=copy.deepcopy(row['derived_sources'])
  revision={'key':key,'picked_landmarks':points,'parent_frame_sha256':sha(parent),'preliminary_child_frame_sha256':prior_sources['frame']['sha256'],'normalization_factor':factor,'source_to_native_scale':job['uniform_chain_scale']*factor,'resampled_size':size,'placement':placement,'foundation_contact':job['foundation_alpha32_contact'],'native_nonzero_alpha_bbox':frame.getchannel('A').getbbox(),'native_body_alpha128_bbox':images['area'].getchannel('A').getbbox(),'method':'Uniform camera normalization from picked retained architectural point span and midpoint; foundation-contact translation. Never fit whole opaque bounds. Pixel rounding and manual2D tolerance remain explicit.','physical_camera_recovered':False}
  for role,image in images.items():
   path=HERE/key/(role+'.png');assert sha(path)==prior_sources[role]['sha256'];write(path,helper.png(image),replace=True);row['derived_sources'][role]['sha256']=sha(path)
  for path in sorted(RECIPES.glob(key+'-*.json')):
   recipe=read(path);role=path.stem[len(key)+1:]
   if role=='animation':
    descriptor=recipe['groups'][0]['frames'][0];descriptor['sha256']=descriptor['source_sha256']=row['derived_sources']['frame']['sha256']
   else:recipe['source_sha256']=row['derived_sources'][role]['sha256']
   recipe['authored_registration_revision']={'ledger':'assets/source/town/painted-resume-v4/registration-v2.json','scope':'Manual retained-foundation landmark correction; no art approval'}
   write(path,helper.encoded(recipe),replace=True);outputs,receipt=compiler.plan(PROJECT,path)
   for name,payload in outputs.items():
    write(compiled_root/name,payload,replace=True);conversion['compiled_outputs'][name]={'sha256':hashlib.sha256(payload).hexdigest(),'bytes':len(payload),'recipe_path':path.relative_to(PROJECT).as_posix(),'recipe_sha256':sha(path)}
   item=next(item for item in row['required_output_mapping'] if item['output_path']==recipe['output_path']);item['sha256']=conversion['compiled_outputs'][item['output_path']]['sha256'];item['recipe_sha256']=sha(path)
  row['authored_registration_v2']=revision;row['native_body_bbox']=images['area'].getchannel('A').getbbox();row['native_alpha_bbox']=frame.getchannel('A').getbbox();conversion['all35_frame_sources'][key]['sha256']=row['derived_sources']['frame']['sha256'];revisions.append(revision)
  # Comparison includes actual parent, prior candidate, corrected candidate.
  frames=[]
  for source in (parent,HISTORY/('assets/source/town/painted-resume-v4/'+key+'/frame.png'),HERE/key/'frame.png'):
   with Image.open(source) as image:frames.append(image.convert('RGBA'))
  boxes=[frame.getchannel('A').getbbox() for frame in frames];bbox=[max(0,min(b[0] for b in boxes)-2),max(0,min(b[1] for b in boxes)-2),min(800,max(b[2] for b in boxes)+2),min(374,max(b[3] for b in boxes)+2)];w=bbox[2]-bbox[0];h=bbox[3]-bbox[1]
  board=Image.new('RGBA',(w*3,h+22),(45,45,45,255));draw=ImageDraw.Draw(board)
  for index,(image,label) in enumerate(zip(frames,['parent','v4 preliminary','landmark corrected'])):board.alpha_composite(image.crop(bbox),(w*index,22));draw.text((w*index+3,4),label,fill='white')
  write(REPORT/(key+'-landmark-correction-native.png'),helper.png(board))
 dump(HERE/'registration-v2.json',{'preliminary_registration_sha256':sha(HERE/'registration.json'),'snapshot_manifest_sha256':sha(HISTORY/'snapshot-manifest.json'),'revision_scope':['capitol','mageGuild3'],'unchanged_other_states':11,'revisions':revisions,'native_execution':False,'visual_approval_granted':False})
 faction=read(PROJECT/'content/factions.json')['shurima']['town'];lookup={key:PROJECT/item['source'] for key,item in conversion['all35_frame_sources'].items()}
 with Image.open(PROJECT/'assets/source/town/landscape-v1/native-rgba.png') as image:terrain=image.convert('RGBA')
 exposure={}
 for name,keys in conversion['variants'].items():
  scene=terrain.copy();covered=Image.new('L',(800,374),0);rows={}
  for key in sorted(keys,key=lambda k:faction['structures'][k]['z']):
   with Image.open(lookup[key]) as image:scene.alpha_composite(image)
  for key in sorted(keys,key=lambda k:faction['structures'][k]['z'],reverse=True):
   with Image.open(lookup[key]) as image:mask=image.getchannel('A').point(lambda a:255 if a>=128 else 0)
   visible=ImageChops.subtract(mask,covered);rows[key]={'click_pixels':mask.histogram()[255],'uncovered_click_pixels':visible.histogram()[255]};covered=ImageChops.lighter(covered,mask)
  exposure[name]=rows;write(REPORT/('registration-v2-'+name+'-800x374.png'),helper.png(scene))
 conversion['exposure']=exposure;conversion['all_visible_masks_exposed']=all(row['uncovered_click_pixels']>0 for scene in exposure.values() for row in scene.values());assert conversion['all_visible_masks_exposed']
 conversion['compiled_root']='compiled-v2';conversion['registration_v2_sha256']=sha(HERE/'registration-v2.json');conversion['historical_conversion_sha256']=sha(REPORT/'conversion.json');conversion['source_of_truth']='Latest authored2D correction, other11 unchanged; native/visual acceptance pending'
 for row in conversion['states']:
  key=row['job']['key']
  if key not in picked:
   prior=next(r for r in original['states'] if r['job']['key']==key);assert row==prior
   for role,item in row['derived_sources'].items():assert sha(PROJECT/item['path'])==item['sha256']
 for name,row in snapshot['files'].items():assert sha(HISTORY/name)==row['sha256']
 dump(HERE/'provenance-v2.json',{'producer':Path(__file__).relative_to(PROJECT).as_posix(),'producer_sha256':sha(Path(__file__)),'registration_v2_sha256':sha(HERE/'registration-v2.json'),'states':conversion['states'],'native_execution':False,'visual_approval_granted':False})
 dump(REPORT/'conversion-v2.json',conversion)
 print(json.dumps({'revised_states':list(picked),'other11_unchanged':True,'compiled_resources':len(conversion['compiled_outputs']),'all_exposed':conversion['all_visible_masks_exposed'],'registration_sha256':sha(HERE/'registration-v2.json'),'native_execution':False}))
if __name__=='__main__':main()
