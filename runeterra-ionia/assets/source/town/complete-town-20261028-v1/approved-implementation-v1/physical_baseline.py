"""Execute unchanged public geometry and source collector on exact town candidates.

This is a bounded first physical baseline, not semantic/art acceptance. Inherited
provisional contact observations are explicitly identified, never promoted by a
successful PNG compile. The approved scene is immutable throughout.
"""
from pathlib import Path
from io import BytesIO
import hashlib,json,sys,shutil,copy
from PIL import Image,ImageDraw,ImageChops
from assemble import HERE,BASE,PROJECT,SIZE,read,dump,ref,rel,sha,image,union
WORKSPACE=PROJECT.parent
sys.path.insert(0,str(WORKSPACE/'scripts'))
import faction_town_layout as consumer
import faction_pipeline as fp
import faction_production as production
REPORT=PROJECT/'build/reports/complete-town-20261028-v1/approved-implementation-v1'
def polygon(points):
 a=Image.new('L',SIZE);ImageDraw.Draw(a).polygon([tuple(p)for p in points],fill=255);return a
def lines(parts,width=3):
 a=Image.new('L',SIZE);d=ImageDraw.Draw(a)
 for part in parts:d.line([tuple(p)for p in part],fill=255,width=width)
 return a
def count(a):return a.histogram()[255]
def main():
 idx=read(HERE/'frame-index.json');old=BASE/'physical-contract-v1';terrain=read(old/'terrain-observation-draft-v1.json');contacts=read(old/'contact-observation-draft-v1.json')
 root=HERE/'physical-baseline';root.mkdir(exist_ok=True);fixture=root/'fixture';fixture.mkdir(exist_ok=True)
 folders=root/'masks';folders.mkdir(exist_ok=True)
 def save(name,im):
  p=folders/name;p.parent.mkdir(parents=True,exist_ok=True);im.convert('RGBA').save(p,compress_level=9);return ref(p)
 canonical=PROJECT/'content/factions.json';factions=read(canonical);town=factions['ionia']['town'];before=sha(canonical)
 for s,r in idx['frames'].items():town['structures'][s].update(x=0,y=0,z=r['depth'])
 dump(HERE/'factions-candidate.json',factions)
 water=union(polygon(p)for p in terrain['water_polygons']);land=ImageChops.subtract(polygon(terrain['land_boundary']),water)
 stairs=union(polygon(x['polygon'])for x in terrain['public_stair_observations'])
 support=ImageChops.subtract(union(polygon(p)for p in terrain['level_regions'].values()),union([water,stairs]))
 # Previously genuine-painted western Cloud connector replaces the rejected
 # eastern roof-crossing trace. Ground semantics still need independent review.
 cloud_path=read(BASE/'cloud-crop-transform-v2.json')['path']
 contacts['sites']['cloudDragon']['approach']=[[187,103],*cloud_path,[128,197]]
 contacts['sites']['cloudDragon'].pop('rejected_approach_observation',None)
 # Three demonstrated base-state pixels at y104 are the actual own entrance
 # stair/frontage continuation, not a side wall. Keep them in the doorway role;
 # do not delete actual contact pixels or manufacture extra support beneath them.
 contacts['sites']['cloudDragon']['state_overrides']={'dwellingLvl7':{'door_polygon':[[180,90],[197,90],[198,105],[180,105]]}}
 contacts['sites']['coast']={'contact_lines':[[[0,218],[8,226],[29,232],[48,234]],[[52,231],[52,237]],[[77,232],[77,240]],[[94,231],[94,239]],[[110,230],[111,239]]],'entrance':[110,237],'door_polygon':[[105,230],[115,230],[115,241],[105,241]],'approach':[[113,237],[122,237],[132,236],[135,228],[129,217]],'access_kind':'moored-vessel','marine_support_kind':'moored-hull','state_overrides':{'shipyard':{'marine_support_kind':'deck-and-pilings','contact_lines':[[[32,227],[34,235]],[[55,230],[55,237]],[[78,229],[78,237]],[[99,228],[99,237]],[[111,230],[113,239]]]}}}
 # These lines are authored observations for a first baseline, not pathfinding
 # through body masks or generation of terrain/support fitted to building feet.
 trunk=[[[268,369],[268,350],[258,331],[253,316],[254,296],[252,279],[255,260],[261,242],[280,224],[289,201],[292,186]],[[268,369],[554,370],[595,359],[610,343],[615,318],[625,300],[631,276],[635,249],[626,235]],[[261,242],[300,241],[340,237],[395,235],[430,239],[439,262],[437,284],[425,304],[451,321],[521,326],[554,350],[554,370]],[[430,239],[476,239],[521,238],[580,237],[626,235]],[[292,186],[331,181],[380,183],[439,183],[481,183],[531,183],[580,183],[622,181]],[[626,235],[626,207],[622,181]],[[268,369],[223,371],[176,364]],[[554,370],[601,366],[632,372],[679,370]]]
 # Global trunk is a single observed public street network. Individual inherited
 # approaches remain independent and must actually touch it; do not connect them
 # synthetically across intervening roofs just to satisfy the public consumer.
 paths=lines(trunk)
 records=[];states={};footing_results={};frame_images={s:image(PROJECT/r['path'])for s,r in idx['frames'].items()}
 for site,siteinfo in idx['sites'].items():
  keys=siteinfo['states'];sil=union(frame_images[s].getchannel('A').point(lambda v:255 if v>=8 else 0)for s in keys);box=sil.getbbox();ob=contacts['sites'][site]
  records.append({'id':site,'states':keys,'depth':idx['frames'][keys[0]]['depth'],'entrance':ob['entrance'],'box':[box[0],box[1],box[2]-box[0],box[3]-box[1]],'intentional_water':site=='coast','silhouette_mask':save('sites/'+site+'.png',sil)})
  for s in keys:
   spec={**ob,**ob.get('state_overrides',{}).get(s,{})};a=frame_images[s].getchannel('A').point(lambda v:255 if v>=8 else 0);body=frame_images[s].getchannel('A').point(lambda v:255 if v>=128 else 0)
   contact=ImageChops.multiply(lines(spec['contact_lines']),a);own=Image.new('L',SIZE)
   if 'own_entry_region'in spec:
    x0,y0,x1,y1=spec['own_entry_region'];ImageDraw.Draw(own).rectangle((x0,y0,x1-1,y1-1),fill=255);own=ImageChops.multiply(own,contact)
   foundation=ImageChops.subtract(contact,own);door=polygon(spec['door_polygon']);bounds=a.getbbox();envelope=Image.new('L',SIZE);ImageDraw.Draw(envelope).rectangle((bounds[0],bounds[1],bounds[2]-1,bounds[3]-1),fill=255);door=ImageChops.multiply(door,envelope);approach=lines([spec['approach']]);d={'access_kind':spec.get('access_kind','door'),'entrance':spec['entrance'],'body_mask':save(s+'/body.png',body),'foundation_mask':save(s+'/foundation.png',foundation),'door_mask':save(s+'/door.png',door),'approach_mask':save(s+'/approach.png',approach)}
   marine=Image.new('L',SIZE)
   if site=='coast':
    marine=ImageChops.multiply(water,ImageChops.multiply(a,union([foundation,door,approach])));d.update(marine_support_kind=spec['marine_support_kind'],marine_support_mask=save(s+'/marine.png',marine))
   states[s]=d;unsupported=ImageChops.subtract(foundation,union([support,marine]));footing_results[s]={'foundation_pixels':count(foundation),'unsupported_pixels':count(unsupported),'unsupported_bounds':unsupported.getbbox(),'on_actual_draft_stairs':count(ImageChops.multiply(foundation,stairs)),'own_approach_body_intersection':count(ImageChops.multiply(approach,ImageChops.subtract(body,door))),'public_path_body_intersection':count(ImageChops.multiply(paths,ImageChops.subtract(body,door))),'complete_contact_pixels':count(contact),'own_entry_contact_pixels':count(own)}
 contract={'status':'design proposal','geometry_mode':'silhouette-v2','canvas':list(SIZE),'alpha_threshold':8,'ordinary_land_sites':16,'background':idx['background'],'land_mask':save('terrain/land.png',land),'frames':{s:{'path':r['path'],'sha256':r['sha256']}for s,r in idx['frames'].items()},'sites':records,'silhouette_plan':{'version':2,'support_mask':save('terrain/support.png',support),'stairs_mask':save('terrain/stairs.png',stairs),'water_mask':save('terrain/water.png',water),'paths_mask':save('terrain/paths.png',paths),'states':states,'overlaps':[],'foundation_occlusions':[],'complete_scene':idx['complete_scene'],'complete_scene_states':idx['complete_scene_states']},'authoring_sources':[ref(old/'terrain-observation-draft-v1.json'),ref(old/'contact-observation-draft-v1.json'),ref(HERE/'physical_baseline.py')],'semantic_limits':'First bounded public-consumer baseline using inherited provisional contact/support observations. Not selected canonical geometry. Source-art ownership, all contact extents, all-state routes and bounded overlaps require correction/review if rejected. No terrain or support fitted to feet.'}
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
