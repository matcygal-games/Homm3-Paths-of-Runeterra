"""Execute unchanged public geometry and source collector on exact town candidates.

This is a bounded first physical baseline, not semantic/art acceptance. Inherited
provisional contact observations are explicitly identified, never promoted by a
successful PNG compile. The approved scene is immutable throughout.
"""
from pathlib import Path
from collections import deque
import heapq
from io import BytesIO
import hashlib,json,sys,shutil,copy
from PIL import Image,ImageDraw,ImageChops
from assemble import HERE,BASE,PROJECT,SIZE,read,dump,ref,rel,sha,image,union
WORKSPACE=PROJECT.parent
sys.path.insert(0,str(WORKSPACE/'scripts'))
import faction_town_layout as consumer
import faction_pipeline as fp
import faction_production as production
REPORT=PROJECT/'build/reports/complete-town-20261028-v1/approved-implementation-v2'
def polygon(points):
 a=Image.new('L',SIZE);ImageDraw.Draw(a).polygon([tuple(p)for p in points],fill=255);return a
def lines(parts,width=3):
 a=Image.new('L',SIZE);d=ImageDraw.Draw(a)
 for part in parts:d.line([tuple(p)for p in part],fill=255,width=width)
 return a
def count(a):return a.histogram()[255]
def lower_contact(alpha,window):
 """Complete lower contact of an independently annotated actual foot/step part."""
 selected=ImageChops.multiply(alpha,window);box=selected.getbbox();result=Image.new('L',SIZE)
 if box:
  for x in range(box[0],box[2]):
   ys=[y for y in range(box[1],box[3])if selected.getpixel((x,y))]
   if ys:result.putpixel((x,max(ys)),255)
 return result
def main():
 idx=read(HERE/'frame-index.json');old=BASE/'physical-contract-v1';terrain=read(old/'terrain-observation-draft-v1.json');contacts=read(old/'contact-observation-draft-v1.json')
 separation=read(HERE/'source-separation.json')
 for site,spec in separation['sites'].items():
  contacts['sites'][site]['contact_lines']=spec['contacts'];contacts['sites'][site]['own_entry_region']=spec['entry_box']
 for state,parts in separation['state_additional_contacts'].items():
  site=idx['frames'][state]['site'];contacts['sites'][site].setdefault('state_overrides',{})[state]={'contact_lines':contacts['sites'][site]['contact_lines']+parts}
 root=HERE/'physical-baseline';root.mkdir(exist_ok=True);fixture=root/'fixture';fixture.mkdir(exist_ok=True)
 folders=root/'masks';folders.mkdir(exist_ok=True)
 def save(name,im):
  p=folders/name;p.parent.mkdir(parents=True,exist_ok=True);im.convert('RGBA').save(p,compress_level=9);return ref(p)
 canonical=PROJECT/'content/factions.json';factions=read(canonical);town=factions['ionia']['town'];before=sha(canonical)
 for s,r in idx['frames'].items():town['structures'][s].update(x=0,y=0,z=r['depth'])
 dump(HERE/'factions-candidate.json',factions)
 terrain['level_regions']=read(HERE/'terrain-plan.json')['level_regions']
 # Trace the selected short-pier shore: vertical stone retaining masonry is
 # land, not river. The inherited draft incorrectly painted water across the
 # clearly visible bank stair and west-monastery public lane around128,215.
 terrain['water_polygons'][0]=[[0,179],[88,181],[89,218],[96,228],[110,231],[116,240],[139,242],[152,246],[170,249],[190,253],[213,259],[225,265],[217,275],[0,277]]
 water=union(polygon(p)for p in terrain['water_polygons']);land=ImageChops.subtract(polygon(terrain['land_boundary']),water)
 stairs=union(polygon(x['polygon'])for x in terrain['public_stair_observations'])
 hidden=read(HERE/'hidden-bed-incorporation.json');bed_masks=[]
 for name,row in hidden['repairs'].items():bed_masks.append(Image.open(PROJECT/row['incorporation_mask']['path']).convert('L'))
 beds=union(bed_masks);stairs=ImageChops.subtract(stairs,beds)
 support=ImageChops.subtract(union([*[polygon(p)for p in terrain['level_regions'].values()],beds]),union([water,stairs]))
 # Previously genuine-painted western Cloud connector replaces the rejected
 # eastern roof-crossing trace. Ground semantics still need independent review.
 cloud_path=read(BASE/'cloud-crop-transform-v2.json')['path']
 contacts['sites']['cloudDragon']['approach']=[[187,103],*cloud_path,[128,197]]
 contacts['sites']['cloudDragon'].pop('rejected_approach_observation',None)
 # Three demonstrated base-state pixels at y104 are the actual own entrance
 # stair/frontage continuation, not a side wall. Keep them in the doorway role;
 # do not delete actual contact pixels or manufacture extra support beneath them.
 contacts['sites']['cloudDragon']['state_overrides']={'dwellingLvl7':{'door_polygon':[[180,90],[197,90],[198,105],[180,105]]}}
 # The Kinkou institution is an open monastic compound. The visible veranda
 # floor and its eastern gate provide real access around the foreground roof;
 # it is not a straight path through the roof or a fictional second entrance.
 contacts['sites']['kinkou'].update(access_kind='open-site',entrance=[261,213],door_polygon=[[155,207],[230,207],[237,211],[244,215],[257,215],[257,206],[270,206],[272,220],[255,224],[242,221],[232,215],[155,215]],approach=[[261,216],[261,222],[273,225],[289,214],[289,201]])
 for site in ('grove','market','harmony','gateway'):contacts['sites'][site]['access_kind']='open-site'
 access=read(HERE/'access-plan.json')
 for site,values in access['sites'].items():contacts['sites'][site].update(values)
 # Preserve actual complete marine soles, not the old lines along upright
 # shafts. The full visible piles and braces remain unchanged in the actor.
 contacts['sites']['coast']={'contact_lines':[[[0,218],[8,226],[29,232],[48,234]],[[52,231],[52,237]],[[77,232],[77,240]],[[94,231],[94,239]],[[110,230],[111,239]]],'entrance':[110,237],'door_polygon':[[105,230],[115,230],[115,241],[105,241]],'approach':[[113,237],[122,237],[132,236],[135,228],[129,217]],'access_kind':'moored-vessel','marine_support_kind':'moored-hull','state_overrides':{'shipyard':{'marine_support_kind':'deck-and-pilings','contact_lines':[[[32,227],[34,235]],[[55,230],[55,237]],[[78,229],[78,237]],[[99,228],[99,237]],[[111,230],[113,239]]]}}}
 contacts['sites']['coast']['contact_lines']=[[[0,222],[8,227],[29,231],[48,234]],[[51,237],[54,237]],[[76,240],[78,240]],[[93,239],[95,239]],[[110,239],[114,239]]]
 contacts['sites']['coast']['state_overrides']['shipyard']['contact_lines']=[[[33,235],[35,235]],[[54,237],[57,237]],[[77,237],[79,237]],[[98,237],[100,237]],[[111,239],[114,239]]]
 contacts['sites']['coast'].update(access['sites']['coast'])
 for state,values in access.get('state_overrides',{}).items():contacts['sites'][idx['frames'][state]['site']].setdefault('state_overrides',{}).setdefault(state,{}).update(values)
 # These lines are authored observations for a first baseline, not pathfinding
 # through body masks or generation of terrain/support fitted to building feet.
 trunk=[[[268,369],[268,350],[258,331],[253,316],[254,296],[252,279],[255,260],[261,242],[280,224],[289,201],[292,186]],[[268,369],[554,370],[595,359],[610,343],[615,318],[625,300],[631,276],[635,249],[626,235]],[[261,242],[300,241],[340,237],[395,235],[430,239],[439,262],[437,284],[425,304],[451,321],[521,326],[554,350],[554,370]],[[430,239],[476,239],[521,238],[580,237],[626,235]],[[292,186],[331,181],[380,183],[439,183],[481,183],[531,183],[580,183],[622,181]],[[626,235],[626,207],[622,181]],[[268,369],[223,371],[176,364]],[[554,370],[601,366],[632,372],[679,370]]]
 # Global trunk is a single observed public street network. Individual inherited
 # approaches remain independent and must actually touch it; do not connect them
 # synthetically across intervening roofs just to satisfy the public consumer.
 west_portico=[[289,201],[289,214],[273,225],[254,223],[242,220],[233,213],[228,211],[162,211],[158,215],[155,220],[142,221],[128,215],[128,197]]
 paths=union([lines(trunk),lines([west_portico],3)])
 records=[];states={};footing_results={};frame_images={s:image(PROJECT/r['path'])for s,r in idx['frames'].items()}
 for site,siteinfo in idx['sites'].items():
  keys=siteinfo['states'];sil=union(frame_images[s].getchannel('A').point(lambda v:255 if v>=8 else 0)for s in keys);box=sil.getbbox();ob=contacts['sites'][site]
  records.append({'id':site,'states':keys,'depth':idx['frames'][keys[0]]['depth'],'entrance':ob['entrance'],'box':[box[0],box[1],box[2]-box[0],box[3]-box[1]],'intentional_water':site=='coast','silhouette_mask':save('sites/'+site+'.png',sil)})
  for s in keys:
   spec={**ob,**ob.get('state_overrides',{}).get(s,{})};a=frame_images[s].getchannel('A').point(lambda v:255 if v>=8 else 0);body=frame_images[s].getchannel('A').point(lambda v:255 if v>=128 else 0)
   # One native pixel traces the actual contact seam. The inherited three-pixel
   # brush included column shafts above the seam and public paving below it.
   structural=ImageChops.multiply(lines(spec['contact_lines'],1),a)
   for island in spec.get('contact_islands',[]):structural=union([structural,lower_contact(a,polygon(island))])
   own=Image.new('L',SIZE)
   if 'own_entry_region'in spec:
    x0,y0,x1,y1=spec['own_entry_region'];region=Image.new('L',SIZE);ImageDraw.Draw(region).rectangle((x0,y0,x1-1,y1-1),fill=255);own=ImageChops.subtract(lower_contact(a,region),structural)
   contact=union([structural,own]);foundation=structural;door=polygon(spec['door_polygon']);bounds=a.getbbox();envelope=Image.new('L',SIZE);ImageDraw.Draw(envelope).rectangle((bounds[0],bounds[1],bounds[2]-1,bounds[3]-1),fill=255);door=ImageChops.multiply(door,envelope);approach=lines([spec['approach']]);d={'access_kind':spec.get('access_kind','door'),'entrance':spec['entrance'],'body_mask':save(s+'/body.png',body),'foundation_mask':save(s+'/foundation.png',foundation),'door_mask':save(s+'/door.png',door),'approach_mask':save(s+'/approach.png',approach)}
   if spec.get('door_silhouette_clip'):
    door=ImageChops.multiply(door,a);d['door_mask']=save(s+'/door.png',door)
   save(s+'/complete-contact.png',contact);save(s+'/own-entry-contact.png',own)
   marine=Image.new('L',SIZE)
   if site=='coast':
    marine=ImageChops.multiply(water,ImageChops.multiply(a,union([foundation,door,approach])));d.update(marine_support_kind=spec['marine_support_kind'],marine_support_mask=save(s+'/marine.png',marine))
   states[s]=d;unsupported=ImageChops.subtract(foundation,union([support,marine]));footing_results[s]={'foundation_pixels':count(foundation),'unsupported_pixels':count(unsupported),'unsupported_bounds':unsupported.getbbox(),'on_actual_draft_stairs':count(ImageChops.multiply(foundation,stairs)),'own_approach_body_intersection':count(ImageChops.multiply(approach,ImageChops.subtract(body,door))),'public_path_body_intersection':count(ImageChops.multiply(paths,ImageChops.subtract(body,door))),'complete_contact_pixels':count(contact),'own_entry_contact_pixels':count(own)}
 # Route actual visible public circulation independently of building support.
 # Search inside hand-observed court/street/stair regions; closed architecture
 # and complete structural feet are hard obstacles in EVERY construction state.
 # Door/frontage exceptions are exact real open porticoes/entrance stairs above.
 allowed=ImageChops.multiply(union([*[polygon(p)for p in access['public_circulation_regions']],lines([cloud_path],3)]),land)
 blocked=Image.new('L',SIZE)
 for s,record in states.items():
  body=Image.open(PROJECT/record['body_mask']['path']).convert('L');door=Image.open(PROJECT/record['door_mask']['path']).convert('L');foundation=Image.open(PROJECT/record['foundation_mask']['path']).convert('L')
  blocked=union([blocked,ImageChops.subtract(body,door),foundation])
 free=ImageChops.subtract(allowed,blocked);network=Image.new('L',SIZE);network.putpixel((554,370),255);whole=image(HERE/'approved-full.png');route_records=[];route_failures=[]
 def search(start):
  if not free.getpixel(start):return None
  targets={(x,y)for y in range(374)for x in range(800)if network.getpixel((x,y))};bounds=(min(x for x,y in targets),min(y for x,y in targets),max(x for x,y in targets),max(y for x,y in targets));q=[(0,0,start)];distance={start:0};previous={start:None};found=None
  while q:
   _,cost,node=heapq.heappop(q)
   if cost!=distance[node]:continue
   if node in targets:found=node;break
   for point in ((node[0]+1,node[1]),(node[0]-1,node[1]),(node[0],node[1]+1),(node[0],node[1]-1)):
    x,y=point
    if not(0<=x<800 and 0<=y<374 and free.getpixel(point)):continue
    r,g,b,_=whole.getpixel(point);step=1
    if not(r>105 and g>90 and b>70 and r>=g*.9):step+=12
    if r>g*1.23 and b>g*1.08:step+=70
    if not(support.getpixel(point)or stairs.getpixel(point)):step+=3
    new=cost+step
    if new<distance.get(point,10**12):
     distance[point]=new;previous[point]=node;dx=max(bounds[0]-x,0,x-bounds[2]);dy=max(bounds[1]-y,0,y-bounds[3]);heapq.heappush(q,(new+dx+dy,new,point))
  if found is None:return None
  path=[]
  while found is not None:path.append(found);found=previous[found]
  return list(reversed(path))
 for site in ('market','inn','grail','workshop','resistance','disciple','vastayan','kashuri','gateway','kinkou','guild','harmony','civic','defenses','protector','grove','coast','cloudDragon'):
  endpoint=tuple(contacts['sites'][site]['approach'][-1]);route=search(endpoint)
  if route is None:route_failures.append({'site':site,'endpoint':list(endpoint),'endpoint_free':bool(free.getpixel(endpoint))});continue
  for point in route:network.putpixel(point,255)
  route_records.append({'site':site,'endpoint':list(endpoint),'pixels':len(route),'path':[list(p)for p in route]})
 paths=network
 dump(root/'public-routing.json',{'status':'authored configuration','method':'Cardinal centerlines on actual hand-observed circulation regions, full all-state architecture/complete-foot hard obstacles, exact real open-frontage masks. No terrain/support/source art changed by route search.','routes':route_records,'failures':route_failures,'allowed_region':save('terrain/observed-circulation.png',allowed),'actual_all_state_hard_obstacles':save('terrain/all-state-circulation-obstacles.png',blocked)})
 overlay=Image.new('RGBA',SIZE);overlay.paste((255,0,210,255),(0,0),paths);Image.alpha_composite(whole,overlay).save(root/'public-path-native-overlay.png')
 for s,record in states.items():
  body=Image.open(PROJECT/record['body_mask']['path']).convert('L');door=Image.open(PROJECT/record['door_mask']['path']).convert('L');footing_results[s]['public_path_body_intersection']=count(ImageChops.multiply(paths,ImageChops.subtract(body,door)))
 cases=read(HERE/'projection-cases.json')['cases'];overlaps=[];occlusions=[]
 def render(selected):
  scene=image(PROJECT/idx['background']['path'])
  for name in sorted(selected,key=lambda s:idx['frames'][s]['depth']):scene.alpha_composite(frame_images[name])
  return scene
 for i,a in enumerate(records):
  for b in records[i+1:]:
   back,front=(a,b)if a['depth']<b['depth']else(b,a);rear=Image.open(PROJECT/back['silhouette_mask']['path']).convert('L');near=Image.open(PROJECT/front['silhouette_mask']['path']).convert('L');intersection=ImageChops.multiply(rear,near)
   if not intersection.getbbox():continue
   pair=back['id']+'/'+front['id']
   if pair not in cases:raise ValueError('New actual source overlap needs a bounded independent disposition: '+pair)
   spec=cases[pair];intersection_ref=save('overlaps/'+pair.replace('/','--')+'.png',intersection);overlaps.append({'behind':back['id'],'front':front['id'],'reason':spec['reason'],'mask':intersection_ref})
   hidden=Image.new('L',SIZE);variants=[]
   for rear_state in back['states']:
    f=Image.open(PROJECT/states[rear_state]['foundation_mask']['path']).convert('L')
    for front_state in front['states']:
     bb=frame_images[front_state].getchannel('A').point(lambda a:255 if a>=128 else 0);hit=ImageChops.multiply(f,bb);hidden=union([hidden,hit])
     if hit.getbbox():variants.append({'behind_state':rear_state,'front_state':front_state,'pixels':count(hit),'bounds':list(hit.getbbox())})
   if not hidden.getbbox():continue
   if back['id']=='coast':raise ValueError('Coastal contacts may never be hidden: '+pair)
   rear_access=union(union([Image.open(PROJECT/states[s]['door_mask']['path']).convert('L'),Image.open(PROJECT/states[s]['approach_mask']['path']).convert('L')])for s in back['states'])
   if ImageChops.multiply(hidden,rear_access).getbbox():raise ValueError('An actual doorway/approach is occluded; no projection waiver is permitted: '+pair)
   mask_ref=save('foundation-cases/'+pair.replace('/','--')+'-intersection.png',hidden);folder=root/'foundation-cases'/pair.replace('/','--');folder.mkdir(parents=True,exist_ok=True);worst=max(variants,key=lambda v:v['pixels']);selected=[s for s in idx['complete_scene_states']if s not in back['states']and s not in front['states']]+[worst['behind_state'],worst['front_state']];complete=render(selected);absent=render([s for s in selected if s not in front['states']]);overlay=Image.new('RGBA',SIZE);overlay.paste((255,30,20,230),(0,0),hidden)
   complete.save(folder/'complete.png');absent.save(folder/'foreground-absent.png');Image.alpha_composite(complete,overlay).save(folder/'intersection-overlay.png')
   case={'kind':'supported-terrace-projection','behind':back['id'],'front':front['id'],'behind_depth':back['depth'],'front_depth':front['depth'],'reason':spec['reason'],'rear_level':spec['rear_level'],'front_level':spec['front_level'],'hidden_pixels':count(hidden),'hidden_bounds':list(hidden.getbbox()),'mask_sha256':mask_ref['sha256'],'variant_intersections':variants,'evidence_state_pair':worst,'native_execution':False,'semantic_review':'Authored source projection case; independent review and runtime remain separate.'};dump(folder/'source-case.json',case)
   occlusions.append({'behind':back['id'],'front':front['id'],'reason':spec['reason'],'mask':mask_ref,'source_case':ref(folder/'source-case.json'),'evidence':{'complete_scene':ref(folder/'complete.png'),'front_absent_scene':ref(folder/'foreground-absent.png'),'intersection_overlay':ref(folder/'intersection-overlay.png')}})
 contract={'status':'authored configuration','geometry_mode':'silhouette-v2','canvas':list(SIZE),'alpha_threshold':8,'ordinary_land_sites':16,'background':idx['background'],'land_mask':save('terrain/land.png',land),'frames':{s:{'path':r['path'],'sha256':r['sha256']}for s,r in idx['frames'].items()},'sites':records,'silhouette_plan':{'version':2,'support_mask':save('terrain/support.png',support),'stairs_mask':save('terrain/stairs.png',stairs),'water_mask':save('terrain/water.png',water),'paths_mask':save('terrain/paths.png',paths),'states':states,'overlaps':overlaps,'foundation_occlusions':occlusions,'complete_scene':idx['complete_scene'],'complete_scene_states':idx['complete_scene_states']},'authoring_sources':[ref(old/'terrain-observation-draft-v1.json'),ref(old/'contact-observation-draft-v1.json'),ref(HERE/'source-separation.json'),ref(HERE/'physical_baseline.py')],'semantic_limits':'Actual independent architectural/public-terrace separation and complete-contact source annotations. Actual public consumer must pass unchanged; external art/runtime acceptance remains separate. No support fitted to feet.'}
 cp=root/'town-layout-proposal.json';dump(cp,contract);design={'layout_geometry_mode':'silhouette-v2','layout_contract':ref(cp)}
 # Exact owned fixture contains all helper-declared refs and compiler products.
 refs=set()
 def visit(v):
  if isinstance(v,dict):
   if isinstance(v.get('path'),str)and isinstance(v.get('sha256'),str):refs.add(v['path'])
   for x in v.values():visit(x)
  elif isinstance(v,list):
   for x in v:visit(x)
 visit(contract);refs.add(rel(cp))
 for name in refs:
  q=fixture/name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(PROJECT/name,q)
 dump(fixture/'design/town-visuals.json',design);dump(fixture/'content/factions.json',factions)
 compiled=REPORT/'compiled'
 for p in compiled.rglob('*'):
  if p.is_file():q=fixture/'assets/generated'/p.relative_to(compiled);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
 errors,deps=consumer.inspect(fixture,{'factions':factions},'ionia')
 try:
  pipeline=fp.Pipeline(fixture,'runeterra-ionia','ionia');export=production._current_town_layout_source_entries(pipeline,{});declared=consumer.dependency_paths(fixture);missing=[str(p.relative_to(fixture))for p in declared if export.get('runeterra-ionia/'+p.relative_to(fixture).as_posix())!=p.read_bytes()];collector={'executed':True,'declared_dependencies':len(declared),'exported_members':len(export),'byte_mismatches':missing,'exact':not missing}
 except Exception as e:collector={'executed':True,'error':str(e),'exact':False}
 # A hash/linkage negative is meaningful independently of the failing physical
 # baseline; record it explicitly as such, never as a passed physical mutation.
 chosen=next(iter(contract['frames']));source=fixture/contract['frames'][chosen]['path'];original=source.read_bytes();source.write_bytes(original+b'not-a-selected-frame');negative,_=consumer.inspect(fixture,{'factions':factions},'ionia');source.write_bytes(original)
 result={'status':'authored configuration','actual_unchanged_consumer':{'path':'scripts/faction_town_layout.py','sha256':sha(WORKSPACE/'scripts/faction_town_layout.py')},'contract':ref(cp),'before_canonical_factions_sha256':before,'after_canonical_factions_sha256':sha(canonical),'canonical_unchanged':before==sha(canonical),'physical_baseline_errors':errors,'physical_pass':not errors,'all35_draft_contact_measurements':footing_results,'actual_public_source_collector':collector,'source_drift_negative_errors':negative,'source_drift_negative_rejected':bool(negative)and negative!=errors,'physical_placement_negatives_executed':False,'physical_placement_negative_limit':'A valid physical baseline is required first; source drift rejection is not a stair/water placement pass.','approved_full':ref(HERE/'approved-full.png'),'native_execution':False,'release_accepted':False}
 dump(REPORT/'physical-baseline-receipt.json',result)
 print(json.dumps({'physical_errors':errors,'collector':collector,'source_drift_negative_rejected':result['source_drift_negative_rejected'],'states_measured':len(footing_results),'canonical_unchanged':result['canonical_unchanged']}))
if __name__=='__main__':main()
