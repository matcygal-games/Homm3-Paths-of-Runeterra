"""Current-cohort physical DIAGNOSTIC, preserving explicit source access HOLDs.

This binds all35 actual states and exact original restorations to the strict
consumer. It does not manufacture a missing door, dry stair, cliff crossing or
complete physical admission from an inherited annotation or passing subset.
"""
from pathlib import Path
from collections import deque
import json,hashlib,importlib.util
import numpy as np
from PIL import Image,ImageDraw,ImageChops
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[5]
OUT=HERE/'source-finish-physical-v1';OUT.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(PROJECT).as_posix(),'sha256':sha(p)}
def read(p):return json.loads(p.read_text())
def save(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
spec=importlib.util.spec_from_file_location('binder',HERE/'bind_contract.py');binder=importlib.util.module_from_spec(spec);spec.loader.exec_module(binder)
index_path=HERE/'structural-source-finish-v1/states.json';index=read(index_path)
receipt=read(HERE/'structural-source-finish-v1/source-refinement-receipt.json')
prior_path=HERE/'source-contact-roles-final-v2/annotations.json';annotation=read(prior_path)
prior_roles=read(HERE/'source-contact-roles-final-v2/role-receipt.json')['states']
fixture=Image.open(HERE/'structural-source-finish-v1/base-cannon-public-fixture-ownership.png').convert('L')
def points(im):
 b=im.getbbox();return [[x,y]for y in range(b[1],b[3])for x in range(b[0],b[2])if im.getpixel((x,y))]if b else[]
def mask(ps):
 im=Image.new('L',(800,374));d=ImageDraw.Draw(im)
 for xy in ps:d.point(tuple(xy),fill=255)
 return im
def transform(key,ps):
 t=receipt['whole_lower_registrations'].get(key,{}).get('transform',{});dx,dy=t.get('offset',[0,0]);out=[]
 for x,y in ps:
  if 'scale'in t:
   cx,cy=t['pivot'];s=t['scale'];x=round(cx+(x-cx)*s+dx);y=round(cy+(y-cy)*s+dy)
  elif 'mirror_axis_twice_x'in t:x=t['mirror_axis_twice_x']-x+dx;y=y+dy
  else:x+=dx;y+=dy
  out.append([x,y])
 return sorted({tuple(p)for p in out})
roles={};support_results={}
support=Image.open(HERE/'fixed-floor-registration-study-v2/fixed-source-support.png').convert('L');stairs=Image.open(HERE/'fixed-floor-registration-study-v2/fixed-source-stairs.png').convert('L')
# Exactly three independently source-confirmed boundary omissions, not dilation.
for xy in ((456,118),(457,118)):support.putpixel(xy,255)
stairs.putpixel((447,234),255);stairs=ImageChops.subtract(stairs,support)
land=Image.open(HERE/'public-source-ground-v2/land.png').convert('L');land=ImageChops.lighter(land,ImageChops.lighter(support,stairs));water=Image.open(HERE/'public-source-ground-v2/water.png').convert('L')
if ImageChops.multiply(land,water).getbbox():raise ValueError('Actual water/land conflict remains')
for k,im in [('support',support),('stairs',stairs),('land',land),('water',water)]:im.save(OUT/(k+'.png'))
body={}
for key,row in index['states'].items():
 frame=Image.open(PROJECT/row['frame']).convert('RGBA');alpha=frame.getchannel('A').point(lambda v:255 if v>=8 else 0);body[key]=frame.getchannel('A').point(lambda v:255 if v>=128 else 0)
 structural=annotation['states'][key]['foundation']['pixels']
 entry=points(Image.open(PROJECT/prior_roles[key]['own_entry_contact']['path']).convert('L'))
 if key=='dwellingLvl3':
  structural=[xy for xy in structural if not fixture.getpixel(tuple(xy))and xy not in ([313,177],[314,175])]
  structural.append([303,181])
  annotation['states'][key]['source_bearing_limit']='Public street lamp/cap is permanent source scenery, not an artillery sole. Actual retained pavilion/post contacts are bound; additional gun wheel/cradle lower material is separately observed and remains exhaustive-role adjudication, never silently certified.'
 if key=='capitol':entry += [[x,y]for x,y in receipt['exact_restorations'][key]['exact_original_RGBA_pixels']if y>=129]
 if key=='mageGuild1':entry += [[494,130]]
 if key=='mageGuild2':entry += [[x,y]for x,y in receipt['exact_restorations'][key]['exact_original_RGBA_pixels']if y==131]
 structural=mask(transform(key,structural));entry=ImageChops.subtract(mask(transform(key,entry)),structural)
 if ImageChops.subtract(structural,alpha).getbbox():raise ValueError('Real mapped material foot left actual source alpha8: '+key)
 complete=ImageChops.lighter(structural,entry)
 if ImageChops.subtract(entry,alpha).getbbox():raise ValueError('Actual mapped entry sole left selected source material: '+key)
 folder=OUT/key;folder.mkdir()
 for name,im in [('structural-foundation',structural),('own-entry-contact',entry),('complete-contact',complete)]:im.save(folder/(name+'.png'))
 annotation['states'][key]['foundation']={'pixels':points(structural)}
 # Source observation transport, not a frontage admission. Keep its explicit
 # unresolved-source finding below rather than fabricate a painted opening.
 for name in ('door','approach'):
  observed=mask(transform(key,points(binder.trace(annotation['states'][key][name]))))
  if name=='door':
   b=alpha.getbbox();inside=Image.new('L',(800,374));ImageDraw.Draw(inside).rectangle((b[0],b[1],b[2]-1,b[3]-1),fill=255);observed=ImageChops.multiply(observed,inside)
  annotation['states'][key][name]={'pixels':points(observed)}
 annotation['states'][key]['entrance']=list(transform(key,[annotation['states'][key]['entrance']])[0])
 if key in ('ship','shipyard'):
  annotation['states'][key]['marine_support']={'pixels':points(structural)}
  annotation['states'][key]['marine_support_kind']='moored-hull'if key=='ship'else'deck-and-pilings'
  effective=ImageChops.lighter(support,structural)
 else:effective=support
 outside=ImageChops.subtract(structural,effective);onstairs=ImageChops.multiply(structural,stairs)
 support_results[key]={'declared_actual_material_contact_pixels':len(points(structural)),'outside_effective_actual_support_pixels':len(points(outside)),'structural_contact_on_stairs_pixels':len(points(onstairs)),'complete_contact_role_partition_exact':not ImageChops.multiply(structural,entry).getbbox(),'source_contact_semantic_admission':False if key=='dwellingLvl3'else'bounded reviewed material candidate; not whole-town admission'}
 roles[key]={'structural_foundation':ref(folder/'structural-foundation.png'),'own_entry_contact':ref(folder/'own-entry-contact.png'),'complete_contact':ref(folder/'complete-contact.png'),'structural_contact_pixels':len(points(structural)),'own_entry_contact_pixels':len(points(entry)),'complete_contact_pixels':len(points(complete))}
annotation['contact_role_partition']=roles
annotation['state_index_sha256']=sha(index_path);annotation['background']={'path':index['background'],'sha256':index['background_sha256']};annotation['complete_scene_states']=index['full_scene_states']
annotation['terrain']={k:ref(OUT/(k+'.png'))for k in ('support','stairs','land','water')}
# A finite common-road diagnostic uses ONLY the reviewed Market fabric ribbon.
# No facade, vegetation, guessed stair or retaining-face shortcut is added.
projection=Image.open(HERE/'market-projection-proposal-v1/occluded-floor.png').convert('L')
blockers={k:im.copy()for k,im in body.items()};blockers['marketplace']=ImageChops.subtract(blockers['marketplace'],projection)
closed=Image.new('L',(800,374))
for im in blockers.values():closed=ImageChops.lighter(closed,im)
walk=np.asarray(ImageChops.lighter(support,stairs))>0;blocked=np.asarray(closed)>0;free=walk&~blocked
q=deque([(420,260)]);seen={(420,260)}
while q:
 x,y=q.popleft()
 for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
  if 0<=nx<800 and 0<=ny<374 and free[ny,nx]and(nx,ny)not in seen:seen.add((nx,ny));q.append((nx,ny))
paths=mask(seen);paths.save(OUT/'paths.png');annotation['terrain']['paths']=ref(OUT/'paths.png')
# Bind actual all-state silhouettes and retire only empty old scenery pairs.
sil={};depth={}
for key,row in index['states'].items():
 a=Image.open(PROJECT/row['frame']).getchannel('A').point(lambda v:255 if v>=8 else 0);site=row['site'];sil[site]=ImageChops.lighter(sil.get(site,Image.new('L',(800,374))),a);depth[site]=row['z']
old={(r['behind'],r['front']):r for r in annotation['overlaps']};overlaps=[];sites=list(sil)
for i,a in enumerate(sites):
 for b in sites[i+1:]:
  if ImageChops.multiply(sil[a],sil[b]).getbbox():
   behind,front=(a,b)if depth[a]<depth[b]else(b,a)
   overlaps.append(old.get((behind,front),{'behind':behind,'front':front,'reason':'Exact actual whole-state source silhouette intersection at current native depth; this declaration grants no door, material-root, source-floor or circulation exemption.'}))
annotation['overlaps']=overlaps;annotation['foundation_occlusions']=[]
findings=read(PROJECT/'build/reports/complete-town-20261028-v1/approved-implementation-v1/physical-refinement-v1/source-entry-study-v2/contours.json')
annotation['current_literal_entry_observations']=findings
annotation['physical_admission']='HOLD: source-visible circulation/frontage constraints remain. Inherited transported door/approach masks above are a rejected diagnostic prototype, not a source-entry certification.'
annotation['review_limits']='Exact original pixels, genuine fixed floors, whole lower registrations and all35 actual configured compiler frames are bound. No actual positive complete physical baseline is asserted; no failed baseline is a negative-control pass. Explicit missing/uncertain entry/stair/shore links must be resolved from source evidence or a separate visible alternative under the user full-image lock.'
refs={}
def add(p):
 p=p.resolve()
 if p.is_relative_to(PROJECT.resolve())and p.is_file():refs[p.relative_to(PROJECT.resolve()).as_posix()]=sha(p)
def refwalk(v):
 if isinstance(v,dict):
  if isinstance(v.get('path'),str)and isinstance(v.get('sha256'),str):add(PROJECT/v['path'])
  for key,pin in v.items():
   if key.endswith('_sha256')and isinstance(pin,str)and isinstance(v.get(key[:-7]),str)and v[key[:-7]].startswith(('assets/','build/reports/','content/','design/')):add(PROJECT/v[key[:-7]])
  for x in v.values():refwalk(x)
 elif isinstance(v,list):
  for x in v:refwalk(x)
for name in ['hidden-support-source-closure-v4.json']:
 refwalk(read(BASE/name))
for p in [index_path,HERE/'structural-source-finish-v1/source-refinement-receipt.json',HERE/'localized-ground-selection-v3/selection-receipt.json',HERE/'ownership-separation-v5/plan.json',HERE/'ownership-separation-v5/separation-receipt.json',prior_path,HERE/'source-contact-roles-final-v2/role-receipt.json',HERE/'public-source-ground-v2/terrain-plan.json',HERE/'fixed-floor-registration-study-v2/study.json',Path(__file__),HERE/'finish_structural_sources_v1.py',HERE/'compile_source_finish_v1.py',HERE/'select_localized_ground_v3.py',HERE/'ground_projection_proposal_v1.py']:
 add(p)
 if p.suffix=='.json':refwalk(read(p))
refwalk(index);refwalk(receipt);refwalk(annotation)
for p in OUT.rglob('*.png'):add(p)
annotation['selected_editable_sources']=[{'path':p,'sha256':pin}for p,pin in sorted(refs.items())]
save(OUT/'annotations.json',annotation)
save(OUT/'support-and-source-roles.json',{'status':'authored configuration','source_index':ref(index_path),'annotations':ref(OUT/'annotations.json'),'states':support_results,'state_count':len(support_results),'main_source_road_component_pixels':len(seen),'source_route_model':'Reviewed Market-only projection plus three exact independently observed junction points. No Tavern facade permission.','all35_geometry_admission_claimed':False,'unproven_source_entries':findings})
print(json.dumps({'annotations':ref(OUT/'annotations.json'),'states':len(support_results),'unsupported_declared_contacts':{k:v for k,v in support_results.items()if v['outside_effective_actual_support_pixels']or v['structural_contact_on_stairs_pixels']},'main_source_component_pixels':len(seen),'flat_authoring_refs':len(refs),'complete_baseline_passed':False}))
