"""Finite original-source restoration and whole lower-form registration.

No new art is painted. All sixteen approved fully built forms stay at their
accepted positions/scales; only exact original step pixels are restored. The
base battery's independently identified public torch/cap becomes permanent
scenery, never a fictitious cannon foot. Lower variants are registered whole,
without anatomy clipping, on the already frozen genuinely painted floors.
"""
from pathlib import Path
from copy import deepcopy
import hashlib,json,math
from PIL import Image,ImageDraw,ImageChops,ImageFilter,ImageOps
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[5]
BASE=HERE.parent
OUT=HERE/'structural-source-finish-v1';OUT.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(PROJECT).as_posix(),'sha256':sha(p)}
def save(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
index_path=HERE/'localized-ground-selection-v3/states.json';index=json.loads(index_path.read_text());candidate=deepcopy(index)
original_path=HERE/'lower-roost-registration-v1/states.json';original=json.loads(original_path.read_text())
findings_path=PROJECT/'build/reports/complete-town-20261028-v1/approved-implementation-v1/physical-refinement-v1/source-entry-study-v1/findings.json';findings=json.loads(findings_path.read_text())
restorations={key:[[x,y]for x,y,old,new in findings['states'][key]['removed_alpha_pixels_in_window']]for key in ('mageGuild1','mageGuild2','capitol')}
restorations['dwellingLvl3']=[[303,y]for y in range(178,182)]
transforms={
 'dwellingLvl1':{'scale':.985,'offset':[-2,0],'pivot':[106.0,251]},
 'dwellingLvl4':{'mirror_axis_twice_x':1300,'offset':[0,10]},
 'dwellingLvl7':{'offset':[0,-1]},
 'mageGuild1':{'offset':[0,-1]},
 'mageGuild2':{'offset':[0,-2]},
 'special1':{'offset':[0,9]},
}
if any(k in index['full_scene_states']for k in transforms):raise ValueError('Approved full form cannot be repositioned/scaled')
actors={key:Image.open(PROJECT/r['frame']).convert('RGBA')for key,r in index['states'].items()}
ground=Image.open(PROJECT/index['background']).convert('RGBA')
genuine=Image.open(BASE/'background-hidden-support-v6.png').convert('RGBA')
restored_details={}
for key,points in restorations.items():
 source=Image.open(PROJECT/original['states'][key]['frame']).convert('RGBA');actor=actors[key]
 for xy in points:
  if source.getpixel(tuple(xy))[3]!=255 or actor.getpixel(tuple(xy))[3]!=0:raise ValueError('Expected exact removed opaque source pixel missing: '+key+str(xy))
  actor.putpixel(tuple(xy),source.getpixel(tuple(xy)))
  # Only restored selected-full anatomy previously baked into the empty source
  # is replaced beneath its now-restored opaque actor by genuine absence RGB.
  if key in index['full_scene_states']:ground.putpixel(tuple(xy),genuine.getpixel(tuple(xy)))
 restored_details[key]={'original':ref(PROJECT/original['states'][key]['frame']),'exact_original_RGBA_pixels':points,'count':len(points)}
# Source-observed public lamp/rail/cap, excluding every cannon/pavilion part.
fixture=Image.new('L',(800,374));draw=ImageDraw.Draw(fixture)
for polygon in [
 [[215,161],[222,160],[227,163],[228,166],[227,170],[224,172],[224,179],[226,181],[228,183],[225,185],[215,185],[212,182],[213,179],[217,177],[217,171],[214,168],[214,164]],
 [[208,174],[212,176],[216,177],[223,177],[228,180],[228,185],[215,186],[208,182]],
]:draw.polygon(list(map(tuple,polygon)),fill=255)
fixture=ImageChops.multiply(fixture,actors['dwellingLvl3'].getchannel('A').point(lambda v:255 if v else 0))
budget=Image.new('L',(800,374))
for key in index['full_scene_states']:budget=ImageChops.lighter(budget,actors[key].getchannel('A').point(lambda v:255 if v==255 else 0))
if ImageChops.subtract(fixture,budget).getbbox():raise ValueError('Public fixture recovery would alter approved full visible pixels')
base_scene=ground.copy();base_scene.alpha_composite(actors['dwellingLvl3'])
ground=Image.composite(base_scene,ground,fixture)
actors['dwellingLvl3'].putalpha(ImageChops.subtract(actors['dwellingLvl3'].getchannel('A'),fixture))
fixture.save(OUT/'base-cannon-public-fixture-ownership.png')
registrations={}
for key,transform in transforms.items():
 source=actors[key];old_alpha=source.getchannel('A');box=old_alpha.getbbox();dx,dy=transform['offset']
 if 'scale'in transform:
  scale=transform['scale'];cx,cy=transform['pivot']
  coefficients=(1/scale,0,cx-(cx+dx)/scale,0,1/scale,cy-(cy+dy)/scale)
  actor=source.transform((800,374),Image.Transform.AFFINE,coefficients,Image.Resampling.BICUBIC)
  clipping=False
  for x,y in ((box[0],box[1]),(box[2]-1,box[1]),(box[0],box[3]-1),(box[2]-1,box[3]-1)):
   xx=cx+(x-cx)*scale+dx;yy=cy+(y-cy)*scale+dy
   if not 0<=xx<800 or not 0<=yy<374:clipping=True
  if clipping:raise ValueError('Uniform lower-form registration clips actual anatomy')
 elif 'mirror_axis_twice_x'in transform:
  actor=Image.new('RGBA',(800,374));actor.paste(ImageOps.mirror(source),(transform['mirror_axis_twice_x']-799+dx,dy))
  if actor.getchannel('A').histogram()!=old_alpha.histogram():raise ValueError('Mirror clips source anatomy')
 else:
  actor=Image.new('RGBA',(800,374));actor.paste(source,(dx,dy))
  if actor.getchannel('A').histogram()!=old_alpha.histogram():raise ValueError('Whole translation clips anatomy')
 actors[key]=actor
 registrations[key]={'transform':transform,'source_bounds':list(box),'new_bounds':list(actor.getchannel('A').getbbox()),'anatomy_crop':False,'whole_source_layer_only':True,'approved_full_form':False,'resampled':bool('scale'in transform),'construction_campaign_sources_unchanged':True}
changed=set(restorations)|set(transforms)
for key in changed:
 folder=OUT/'states'/key;folder.mkdir(parents=True)
 actor=actors[key];alpha=actor.getchannel('A');actor.save(folder/'frame.png',compress_level=9,optimize=False);alpha.save(folder/'alpha_mask.png')
 area=Image.new('RGBA',(800,374),(255,255,255,0));area.putalpha(alpha.point(lambda v:255 if v>=8 else 0));area.save(folder/'area.png',compress_level=9,optimize=False)
 border=ImageChops.subtract(alpha.filter(ImageFilter.MaxFilter(3)),alpha.filter(ImageFilter.MinFilter(3))).point(lambda v:255 if v else 0);area.putalpha(border);area.save(folder/'border.png',compress_level=9,optimize=False)
 for kind in ('frame','alpha_mask','area','border'):
  path=folder/(kind+'.png');candidate['states'][key][kind]=ref(path)['path'];candidate['states'][key][kind+'_sha256']=sha(path)
 candidate['states'][key]['physical_source_refinement']={'ancestry':ref(index_path),'writer':ref(Path(__file__)),'exact_sill_restoration':restored_details.get(key),'whole_lower_registration':registrations.get(key),'public_fixture_ownership':ref(OUT/'base-cannon-public-fixture-ownership.png')if key=='dwellingLvl3'else None}
bg=OUT/'background.png';ground.save(bg,compress_level=9,optimize=False);candidate['background']=ref(bg)['path'];candidate['background_sha256']=sha(bg)
scenes={}
for name,keys in [('empty',[]),('base',index['base_scene_states']),('full',index['full_scene_states'])]:
 scene=ground.copy()
 for key in keys:scene.alpha_composite(actors[key])
 dest=OUT/(name+'-native.png');scene.save(dest,compress_level=9,optimize=False);scenes[name]=ref(dest)
approved=Image.open(BASE/'approved-full-source-v1.png').convert('RGBA');full=Image.open(OUT/'full-native.png').convert('RGBA')
delta=sum(any(v)for v in ImageChops.difference(approved,full).get_flattened_data())
if delta:raise ValueError('Approved fully built BL2 changed: '+str(delta))
save(OUT/'states.json',candidate)
receipt={'status':'authored configuration','ancestor':ref(index_path),'registered_original_source':ref(original_path),'source_entry_findings':ref(findings_path),'exact_restorations':restored_details,'whole_lower_registrations':registrations,'public_fixture':{'state':'dwellingLvl3','source_mask':ref(OUT/'base-cannon-public-fixture-ownership.png'),'pixels':fixture.histogram()[255],'permanent_in_empty_scene':True,'recovered_from_actual_genuine_source_composition':True,'approved_full_visible_pixels_changed':0},'states':ref(OUT/'states.json'),'background':ref(bg),'scenes':scenes,'approved_full_decoded_RGBA_changed_pixels':delta,'all16_approved_full_positions_and_scales_unchanged':True,'strict_whole_physical_passed':False,'current_source_limits':['Actual common routes/visible frontages still require closure; no unseen cliff/stair is invented.','Lower battery additional carriage-bearing interpretation remains source material review, not an automatically certified complete contact mask.']}
save(OUT/'source-refinement-receipt.json',receipt)
print(json.dumps({'states':receipt['states'],'full_delta':delta,'original_pixels_restored':sum(len(v)for v in restorations.values()),'lower_whole_registrations':len(registrations),'public_fixture_pixels':fixture.histogram()[255]}))
