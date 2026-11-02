"""Assemble faithful current-source candidate; failed physical semantics stay failed.
No source art, shared helper, selections, canonical outputs or stages are changed.
"""
from pathlib import Path
from collections import deque
import hashlib,json,importlib.util,argparse
from copy import deepcopy
import numpy as np
from PIL import Image,ImageChops,ImageDraw
HERE=Path(__file__).resolve().parent;TOWN=HERE.parent;ROOT=HERE.parents[4];REPORT=ROOT/'build/reports/complete-town-20261027-v2/geometry-final-v2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf8')
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def blank():return Image.new('L',(800,374))
def alpha(im,t):return im.getchannel('A').point(lambda a:255 if a>=t else 0)
def count(im):return im.histogram()[255]
def flood(allowed,start):
 if not allowed[start[1],start[0]]:return {}
 q=deque([start]);parent={start:None}
 while q:
  x,y=q.popleft()
  for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
   if 0<=xx<800 and 0<=yy<374 and allowed[yy,xx] and (xx,yy) not in parent:parent[xx,yy]=(x,y);q.append((xx,yy))
 return parent
LEVELS={
 ('throneHall','dwellingAxe'):('Upper civic stone landing and apron','Lower west knife-guild work court'),
 ('throneHall','dwellingHound'):('Upper civic stone landing and apron','Lower hound court and foreground roof projection'),
 ('crownBastion','throneHall'):('Rear elevated fortified stone ledge','Nearer upper-left civic landing'),
 ('crownBastion','arcaneAthenaeum'):('Rear elevated fortified stone ledge','Lower college court and frontage'),
 ('crownBastion','dwellingLegion'):('Rear elevated fortified stone ledge','Lower east barracks courtyard'),
 ('crownBastion','dwellingRose'):('Rear elevated fortified stone ledge','Lower menagerie courtyard and gates'),
 ('arcaneAthenaeum','arenaOfValor'):('Upper college entrance court','Lower circular arena terrace'),
 ('dwellingHound','gildedCup'):('Middle west kennel courtyard','Lower foreground inn terrace'),
 ('dwellingAxe','dwellingHound'):('Raised west knife-guild work court','Nearer kennel courtyard frontage'),
 ('arenaOfValor','dwellingCrimson'):('Circular arena terrace outer support','Lower near crimson-hall court'),
 ('dwellingRose','grandMarket'):('Upper menagerie stone court and entry landing','Lower market avenue court and stall frontage'),
 ('grandMarket','crimsonCitadel'):('Raised market plaza paved court','Lower eastern supply-quay stone landing'),
 ('crimsonCitadel','foundry'):('Raised eastern supply-quay loading deck','Lower foreground Foundry court and projecting tower roof')}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--attempt',required=True);ap.add_argument('--candidate',default='candidate-final-v5');ap.add_argument('--entries',default='entry-spans-v3');ap.add_argument('--physical',default='physical-v10');ap.add_argument('--mask-root',default='.');ap.add_argument('--trace-name',default='background-plane-trace-v5.json');ap.add_argument('--state-index');args=ap.parse_args()
 if not args.attempt.replace('-','').isalnum():raise ValueError('Simple attempt name required')
 report=REPORT/args.attempt
 if report.exists():raise ValueError('Preserve historical reports; choose new attempt')
 report.mkdir(parents=True)
 for value in (args.candidate,args.entries,args.physical):
  if '/' in value or '\\' in value or value in ('.','..'):raise ValueError('Direct town source subdirectory required')
 mask_root=(HERE/args.mask_root).resolve()
 if not mask_root.is_relative_to(HERE):raise ValueError('Masks must remain inside owned geometry-final-v2')
 selection=load(TOWN/args.candidate/'selection.json');rows={r['state']:r for r in selection['states']};sites0=selection['sites'];annotation=load(TOWN/args.physical/'annotations.json');annotations={r['state']:r for r in annotation['states']};entries_path=TOWN/args.entries/'entries.json';entries={r['state']:r for r in load(entries_path)['states']};trace_path=mask_root/args.trace_name;trace=load(trace_path)
 root_refs={s:{'path':(TOWN/args.physical/s/'foundation.png').relative_to(ROOT).as_posix(),'sha256':a['foundation_sha256']}for s,a in annotations.items()};semantic_source=ref(TOWN/args.physical/'annotations.json')
 if args.state_index:
  index_path=(TOWN/args.state_index).resolve()
  if not index_path.is_relative_to(TOWN):raise ValueError('State index leaves direct own town sources')
  state_index=load(index_path);indexed={r['state']:r for r in state_index['states']}
  if set(indexed)!=set(rows):raise ValueError('Actual transform index state coverage differs')
  rows=deepcopy(rows);sites0=deepcopy(sites0)
  for state,item in indexed.items():
   rows[state].update(native_layer=item['frame']['path'],native_layer_sha256=item['frame']['sha256'],native_z=item['native_z'])
   annotations[state]={'layer_sha256':item['frame']['sha256'],'foundation_sha256':item['foundation_mask']['sha256']};root_refs[state]=item['foundation_mask'];entries[state]={'source_sha256':item['frame']['sha256'],'mask':item['door_mask'],'own_treads':item['own_treads_mask'],'entrance':item['entrance']}
  for site in sites0:
   depths={rows[state]['native_z']for state in site['states']}
   if len(depths)!=1:raise ValueError('All replacements at a site require one actual native depth')
   site['native_z']=depths.pop()
  entries_path=index_path;semantic_source={'index':ref(index_path),'semantic_ground_zone_masks':{s:item['semantic_zone_mask']for s,item in indexed.items()}}
 if trace.get('source')!={'path':selection['terrain']['native'],'sha256':selection['terrain']['native_sha256']}:raise ValueError('Independent background trace does not bind the current exact selected terrain')
 if set(annotations)!=set(rows)or set(entries)!=set(rows):raise ValueError('Actual physical/entry indices must cover all current states exactly')
 background=Image.open(ROOT/selection['terrain']['native']).convert('RGBA');layers={s:Image.open(ROOT/r['native_layer']).convert('RGBA')for s,r in rows.items()}
 if sha(ROOT/selection['terrain']['native'])!=selection['terrain']['native_sha256']:raise ValueError('Changed terrain')
 support=Image.open(mask_root/'support.png').convert('L');stairs=Image.open(mask_root/'stairs.png').convert('L');water=Image.open(mask_root/'water.png').convert('L');land=Image.open(mask_root/'land.png').convert('L');walkable=Image.open(mask_root/'walkable-plane.png').convert('L');walkarr=np.asarray(walkable)>0
 site_union={};site_body={};allbody=blank();roots={};doors={};own_treads={}
 for site in sites0:
  u=blank();b=blank()
  for state in site['states']:
   if sha(ROOT/rows[state]['native_layer'])!=rows[state]['native_layer_sha256']:raise ValueError('Changed native frame '+state)
   if annotations[state]['layer_sha256']!=rows[state]['native_layer_sha256']or entries[state]['source_sha256']!=rows[state]['native_layer_sha256']:raise ValueError('Physical/entry annotation binds an older source frame '+state)
   if sha(ROOT/root_refs[state]['path'])!=annotations[state]['foundation_sha256']:raise ValueError('Physical root mask differs from its source-owned annotation '+state)
   for role in ('mask','own_treads'):
    if role in entries[state]and sha(ROOT/entries[state][role]['path'])!=entries[state][role]['sha256']:raise ValueError('Entry annotation mask changed '+state+'/'+role)
   u=ImageChops.lighter(u,alpha(layers[state],8));b=ImageChops.lighter(b,alpha(layers[state],128));roots[state]=Image.open(ROOT/root_refs[state]['path']).convert('L');doors[state]=Image.open(ROOT/entries[state]['mask']['path']).convert('L');own_treads[state]=Image.open(ROOT/entries[state]['own_treads']['path']).convert('L')if 'own_treads'in entries[state]else blank()
   if ImageChops.subtract(own_treads[state],ImageChops.multiply(doors[state],alpha(layers[state],8))).getbbox():raise ValueError('Own horizontal treads leave current source alpha8 or full entry '+state)
  site_union[site['id']]=u;site_body[site['id']]=b;allbody=ImageChops.lighter(allbody,b);save(HERE/'sites'/(site['id']+'.png'),u)
 # Cardinal routing is confined to independently traced actual paving/stairs.
 # No RGB cost function; no complement-of-water substitute for the walk plane.
 free=walkarr&~(np.asarray(allbody)>0);start=(384,250);parent=flood(free,start)
 paths=blank();physical={};diagnostics=[]
 for state,row in rows.items():
  sid=row['site'];body=alpha(layers[state],128);door=doors[state];anchor=tuple(entries[state]['entrance']);others=blank()
  for other,m in site_body.items():
   if other!=sid:others=ImageChops.lighter(others,m)
  own_tread_array=np.asarray(own_treads[state])>0
  actual_state_walkplane=walkarr|own_tread_array
  # The full arch is a visibility guard, never a vertical walking surface.
  # Inside the actual solid sprite, only its separately traced horizontal
  # entry treads/apron may carry an approach, even if background paving lies
  # behind that same projected arch pixel.
  apallowed=~(np.asarray(others)>0)&((walkarr&~(np.asarray(body)>0))|(own_tread_array&(np.asarray(door)>0)));q=deque();apparent={};goal=None
  # The public contract requires cardinal contact with the real doorway,
  # not traversal through its single UI/annotation anchor. Seed the verified
  # horizontal stair/apron surface only, ordered nearest the actual anchor.
  # Full vertical arch visibility remains protected separately and unchanged.
  ys,xs=np.nonzero(apallowed&own_tread_array&(np.asarray(door)>0))
  seeds=sorted(zip(map(int,xs),map(int,ys)),key=lambda point:(abs(point[0]-anchor[0])+abs(point[1]-anchor[1]),point[1],point[0]))
  for point in seeds:q.append(point);apparent[point]=None
  while q:
   point=q.popleft()
   if point in parent:goal=point;break
   x,y=point
   for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
    if 0<=xx<800 and 0<=yy<374 and apallowed[yy,xx] and (xx,yy) not in apparent:apparent[(xx,yy)]=point;q.append((xx,yy))
  approach=blank()
  if goal:
   point=goal
   while point is not None:approach.putpixel(point,255);point=apparent[point]
   point=goal
   while point is not None:paths.putpixel(point,255);point=parent[point]
  folder=HERE/'states'/state
  for name,m in [('foundation',roots[state]),('body',body),('door',door),('approach',approach)]:save(folder/(name+'.png'),m)
  record={name+'_mask':ref(folder/(name+'.png'))for name in ('foundation','body','door','approach')};record.update(entrance=list(anchor),access_kind='open-site'if state in ('marketplace','blacksmith','special3','grail')else 'door')
  marine=blank()
  if sid=='coast':
   # Actual bounded selected hull/deck-to-rock anchorage may include its dry
   # side. The public API requires an intersection with external water, not
   # an artificial restriction of every marine pixel to water.
   marine=ImageChops.multiply(ImageChops.lighter(roots[state],own_treads[state]),alpha(layers[state],8));save(folder/'marine.png',marine);record.update(marine_support_mask=ref(folder/'marine.png'),marine_support_kind='moored-hull'if state=='ship'else 'deck-and-pilings',access_kind='moored-vessel')
  physical[state]=record;unsupported=ImageChops.subtract(roots[state],ImageChops.lighter(support,marine));diagnostics.append({'state':state,'entrance':list(anchor),'entry_mask_pixels':count(door),'own_source_horizontal_tread_pixels':count(own_treads[state]),'anchor_on_walkable_background':bool(walkarr[anchor[1],anchor[0]]),'anchor_blocked_by_other_site':bool(others.getpixel(anchor)),'connected_approach':goal is not None,'street_join':list(goal)if goal else None,'approach_pixels':count(approach),'approach_outside_actual_background_or_own_treads':count(ImageChops.subtract(approach,ImageChops.lighter(walkable,own_treads[state]))),'foundation_outside_level_support':count(unsupported),'foundation_unsupported_bbox':unsupported.getbbox(),'foundation_on_stairs':count(ImageChops.multiply(roots[state],stairs)),'foundation_on_external_water':count(ImageChops.multiply(roots[state],water))})
 save(HERE/'paths.png',paths)
 complete=[site['top']for site in sorted(sites0,key=lambda s:s['native_z'])if site['id']not in ('coast','grail')];full=background.copy()
 for state in complete:full.alpha_composite(layers[state])
 save(HERE/'complete-scene.png',full);sites=[];overlaps=[];cases=[]
 for site in sites0:
  bb=site_union[site['id']].getbbox();sites.append({'id':site['id'],'states':site['states'],'depth':site['native_z'],'entrance':physical[site['top']]['entrance'],'box':[bb[0],bb[1],bb[2]-bb[0],bb[3]-bb[1]],'intentional_water':site['id']=='coast','silhouette_mask':ref(HERE/'sites'/(site['id']+'.png'))})
 for i,a in enumerate(sites0):
  for b in sites0[i+1:]:
   rear,front=sorted((a,b),key=lambda s:s['native_z']);sid,fid=rear['id'],front['id'];intersection=ImageChops.multiply(site_union[sid],site_union[fid])
   if intersection.getbbox():
    p=HERE/'overlaps'/(sid+'--'+fid+'.png');save(p,intersection);overlaps.append({'behind':sid,'front':fid,'mask':ref(p),'reason':'Exact current all-state painted silhouette intersection in native depth order; this overlap does not approve ground support or access.'})
   root=blank()
   for state in rear['states']:root=ImageChops.lighter(root,roots[state])
   hidden=ImageChops.multiply(root,site_body[fid])
   if not hidden.getbbox():continue
   rearlevel,frontlevel=LEVELS[sid,fid];folder=HERE/'foundation-projections'/(sid+'--'+fid);save(folder/'intersection.png',hidden);absent=background.copy()
   for state in complete:
    if state not in front['states']:absent.alpha_composite(layers[state])
   overlay=full.copy();color=Image.new('RGBA',(800,374),(0,255,220,0));color.putalpha(hidden);overlay.alpha_composite(color)
   for name,m in [('complete-scene',full),('front-absent-scene',absent),('intersection-overlay',overlay)]:save(folder/(name+'.png'),m)
   reason='Bounded projected lower wall/plinth edge between '+rearlevel.lower()+' and '+frontlevel.lower()+'. Exact non-access intersection only; actual level support and every full doorway and approach remain independently required against the final selected source.'
   write(folder/'source-case.json',{'kind':'supported-terrace-projection','behind':sid,'front':fid,'behind_depth':rear['native_z'],'front_depth':front['native_z'],'rear_level':rearlevel,'front_level':frontlevel,'reason':reason,'hidden_pixels':count(hidden),'hidden_bounds':list(hidden.getbbox()),'mask_sha256':sha(folder/'intersection.png'),'review_status':'Exact source-case candidate; final pinned independent physical truth review required before selection. No door or approach waiver.'});cases.append({'behind':sid,'front':fid,'reason':reason,'mask':ref(folder/'intersection.png'),'source_case':ref(folder/'source-case.json'),'evidence':{name:ref(folder/(name.replace('_','-')+'.png'))for name in ('complete_scene','front_absent_scene','intersection_overlay')}})
 contract={'geometry_mode':'silhouette-v2','canvas':[800,374],'alpha_threshold':8,'ordinary_land_sites':17,'background':ref(ROOT/selection['terrain']['native']),'land_mask':ref(mask_root/'land.png'),'frames':{s:ref(ROOT/r['native_layer'])for s,r in rows.items()},'sites':sites,'silhouette_plan':{'version':2,'support_mask':ref(mask_root/'support.png'),'stairs_mask':ref(mask_root/'stairs.png'),'water_mask':ref(mask_root/'water.png'),'paths_mask':ref(HERE/'paths.png'),'states':physical,'overlaps':overlaps,'foundation_occlusions':cases,'complete_scene':ref(HERE/'complete-scene.png'),'complete_scene_states':complete},'source_semantic_annotations':semantic_source,'source_background_trace':ref(trace_path),'source_walkable_plane':ref(mask_root/'walkable-plane.png'),'source_entry_spans':{'index':ref(entries_path),'own_entry_tread_masks':{s:entry['own_treads']for s,entry in entries.items()if 'own_treads'in entry}}};write(HERE/'town-layout.json',contract)
 result={'status':'authored configuration','ready_for_selection':False,'terrain':contract['background'],'selection_sha256':sha(TOWN/args.candidate/'selection.json'),'entries':ref(entries_path),'script_sha256':sha(Path(__file__)),'states':diagnostics,'source_supported_root_projection_candidates':len(cases),'all_state_overlaps':len(overlaps),'body_free_walkable_component_pixels':len(parent),'global_path_pixels':count(paths),'global_paths_outside_actual_background_walkable':count(ImageChops.subtract(paths,walkable)),'level_support_derived_from_roots':False,'routing_uses_nonwater_complement_or_RGB_cost':False,'limitations':['Conservative current background trace, approximately2nativepixel boundary uncertainty.','Current physical support and actual doorway-foot access gaps require source-pixel review/repair; no ready geometry or art approval.','Empty approaches deliberately expose missing actual route; no invented ground or stairs.','Coastal source deck access is not yet independently traced as horizontal walkplane.']};write(report/'diagnostics.json',result);write(report/'town-layout.json',contract)
 for name,base in [('full',full),('empty',background)]:
  overlay=base.copy()
  for m,c in [(support,(40,255,80)),(stairs,(255,40,40)),(water,(30,70,255)),(paths,(255,245,20))]:tint=Image.new('RGBA',(800,374),(*c,0));tint.putalpha(m.point(lambda a:100 if a else 0));overlay.alpha_composite(tint)
  save(report/(name+'-guard-overlay-v5.png'),overlay)
 print(json.dumps({'contract':ref(HERE/'town-layout.json'),'root_projection_candidates':len(cases),'support_failed_states':len([r for r in diagnostics if r['foundation_outside_level_support']]),'access_failed_states':len([r for r in diagnostics if not r['connected_approach']]),'global_paths_outside_walkable':result['global_paths_outside_actual_background_walkable']}))
if __name__=='__main__':main()
