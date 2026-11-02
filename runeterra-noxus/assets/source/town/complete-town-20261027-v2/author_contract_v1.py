"""Actual native masks/routes and individual projected-depth source cases.

Technical source annotations only. Complete painted source truth requires the
independent review; this program cannot award architectural or game acceptance.
"""
from pathlib import Path
import hashlib,json,heapq,collections
import numpy as np
from PIL import Image,ImageChops,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
OUT=HERE/'geometry-final-v1';REPORT=ROOT/'build/reports/complete-town-20261027-v2/guards-v1'
X={'villageHall':164,'townHall':175,'cityHall':168,'capitol':174,'fort':437,'citadel':437,'castle':437,'mageGuild1':328,'mageGuild2':335,'mageGuild3':338,'mageGuild4':341,'dwellingLvl1':645,'dwellingUpLvl1':637,'dwellingLvl2':151,'dwellingUpLvl2':172,'dwellingLvl3':66,'dwellingUpLvl3':60,'dwellingLvl4':548,'dwellingUpLvl4':509,'dwellingLvl5':321,'dwellingUpLvl5':319,'dwellingLvl6':523,'dwellingUpLvl6':498,'special4':479,'dwellingLvl7':475,'dwellingUpLvl7':475,'tavern':191,'marketplace':601,'blacksmith':682,'resourceSilo':686,'special1':68,'special2':737,'special3':245,'shipyard':750,'ship':750,'grail':228}
LEVELS={
 ('throneHall','dwellingAxe'):('Upper civic stone landing and apron','Lower west knife-guild work court'),
 ('crownBastion','throneHall'):('Rear elevated fortified stone ledge','Nearer upper-left civic landing'),
 ('crownBastion','arcaneAthenaeum'):('Rear elevated fortified stone ledge','Lower college court and frontage'),
 ('crownBastion','dwellingLegion'):('Rear elevated fortified stone ledge','Lower east barracks courtyard'),
 ('crownBastion','dwellingRose'):('Rear elevated fortified stone ledge','Lower menagerie courtyard and gates'),
 ('arcaneAthenaeum','arenaOfValor'):('Upper college entrance court','Lower circular arena terrace'),
 ('dwellingHound','gildedCup'):('Middle west kennel courtyard','Lower foreground inn terrace'),
 ('dwellingAxe','dwellingHound'):('Raised west knife-guild work court','Nearer kennel courtyard frontage'),
 ('arenaOfValor','dwellingCrimson'):('Circular arena terrace outer support','Lower near crimson-hall court'),
}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf8')
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def blank():return Image.new('L',(800,374))
def alpha(im,t):return im.getchannel('A').point(lambda v:255 if v>=t else 0)
def count(m):return m.histogram()[255]
def main():
 selection=load(HERE/'candidate-final-v2/selection.json');rows={r['state']:r for r in selection['states']};sites0=selection['sites'];annotations={r['state']:r for r in load(HERE/'physical-v10/annotations.json')['states']};layers={s:Image.open(ROOT/r['native_layer']).convert('RGBA') for s,r in rows.items()};background=Image.open(ROOT/selection['terrain']['native']).convert('RGBA')
 water=blank();ImageDraw.Draw(water).polygon([(734,82),(751,104),(751,125),(775,146),(775,157),(766,163),(753,167),(747,175),(749,187),(757,203),(767,221),(772,237),(784,255),(788,270),(799,290),(799,373),(799,82)],fill=255);land=ImageChops.invert(water)
 stairs=blank();d=ImageDraw.Draw(stairs)
 stair_polygons=[[(157,135),(194,135),(194,145),(168,146)],[(20,190),(29,192),(28,195),(20,193)],[(304,196),(320,193),(332,215),(319,221)],[(76,221),(89,221),(103,242),(91,243)],[(408,267),(413,265),(423,274),(419,279),(411,273)],[(645,250),(652,250),(656,259),(649,263),(645,260)],[(48,312),(62,315),(50,322),(32,317)],[(172,340),(190,337),(204,348),(181,356)],[(696,219),(711,219),(730,242),(715,247)]]
 for points in stair_polygons:d.polygon(points,fill=255)
 # Level contact bands are individually annotated native pavement/landing zones,
 # reviewed with actual empty/full painted sources. They are never all dry land.
 support=blank();site_union={};site_body={};allbody=blank();roots={}
 for site in sites0:
  u=blank();b=blank()
  for state in site['states']:
   u=ImageChops.lighter(u,alpha(layers[state],8));b=ImageChops.lighter(b,alpha(layers[state],128));support=ImageChops.lighter(support,Image.open(HERE/'physical-v10'/state/'manual-semantic-ground-zone.png').convert('L'));roots[state]=Image.open(HERE/'physical-v10'/state/'foundation.png').convert('L')
  site_union[site['id']]=u;site_body[site['id']]=b;allbody=ImageChops.lighter(allbody,b);save(OUT/'sites'/(site['id']+'.png'),u)
 support=ImageChops.subtract(ImageChops.multiply(support,land),stairs)
 # Route on actual free projected pixels. Warm visible paving receives lowest
 # cost; dark retaining material/vegetation is expensive and remains reviewable.
 bodyarr=np.asarray(allbody)>0;landarr=np.asarray(land)>0;allowed=landarr&~bodyarr;allowed[:95]=False;rgb=np.asarray(background)[:,:,:3].astype('int16');warm=(rgb[:,:,0]>80)&(rgb[:,:,1]>55)&(rgb[:,:,0]>rgb[:,:,1])&(rgb[:,:,1]>rgb[:,:,2]);cost=np.where(warm,1,65).astype('int32');cost+=np.where(rgb[:,:,0]<45,120,0)
 start=(384,250);distance={start:0};parent={start:None};heap=[(0,*start)]
 while heap:
  dist,x,y=heapq.heappop(heap)
  if distance.get((x,y))!=dist:continue
  for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
   if not(0<=xx<800 and 0<=yy<374 and allowed[yy,xx]):continue
   score=dist+int(cost[yy,xx])
   if score<distance.get((xx,yy),10**12):distance[xx,yy]=score;parent[xx,yy]=(x,y);heapq.heappush(heap,(score,xx,yy))
 paths=blank();physical={};diagnostics=[];state_site={s:site['id'] for site in sites0 for s in site['states']}
 for state,row in rows.items():
  sid=row['site'];body=alpha(layers[state],128);bb=alpha(layers[state],8).getbbox();x=X[state];ys=[y for y in range(bb[1],bb[3]) if body.getpixel((x,y))];y=max(ys)
  if state=='marketplace':y=245
  if state=='dwellingUpLvl4':y=190
  if state in ('shipyard','ship'):y=174
  anchor=(x,y);door=blank();ImageDraw.Draw(door).rectangle((max(bb[0],x-1),max(bb[1],y-2),min(bb[2]-1,x+1),min(bb[3]-1,y+1)),fill=255)
  others=blank()
  for other,mask in site_body.items():
   if other!=sid:others=ImageChops.lighter(others,mask)
  otherarr=np.asarray(others)>0;selfarr=np.asarray(body)>0;doorarr=np.asarray(door)>0;apallowed=~otherarr&(~selfarr|doorarr)
  if sid!='coast':apallowed&=landarr
  else:apallowed&=landarr|(np.asarray(alpha(layers[state],8))>0)
  q=collections.deque([anchor]);apparent={anchor:None};goal=None
  while q:
   point=q.popleft()
   if point in parent:goal=point;break
   xx,yy=point
   for nxt in ((xx-1,yy),(xx+1,yy),(xx,yy-1),(xx,yy+1)):
    a,b=nxt
    if 0<=a<800 and 0<=b<374 and abs(a-x)+abs(b-y)<24 and apallowed[b,a] and nxt not in apparent:apparent[nxt]=point;q.append(nxt)
  if goal is None:raise ValueError('Actual frontage cannot reach unobscured street '+state+str(anchor))
  approach=blank();point=goal
  while point is not None:approach.putpixel(point,255);point=apparent[point]
  point=goal
  while point is not None:paths.putpixel(point,255);point=parent[point]
  folder=OUT/'states'/state
  for name,im in [('foundation',roots[state]),('body',body),('door',door),('approach',approach)]:save(folder/(name+'.png'),im)
  record={name+'_mask':ref(folder/(name+'.png')) for name in ('foundation','body','door','approach')};record.update(entrance=list(anchor),access_kind='open-site' if state in ('marketplace','blacksmith','special3','grail') else 'door')
  if sid=='coast':
   marine=ImageChops.multiply(ImageChops.multiply(ImageChops.lighter(roots[state],ImageChops.lighter(door,approach)),alpha(layers[state],8)),water);save(folder/'marine.png',marine);record.update(marine_support_mask=ref(folder/'marine.png'),marine_support_kind='moored-hull' if state=='ship' else 'deck-and-pilings',access_kind='moored-vessel')
  physical[state]=record;diagnostics.append({'state':state,'actual_frontage':list(anchor),'street_join':list(goal),'foundation_outside_level_support':count(ImageChops.subtract(roots[state],support)),'foundation_on_stairs':count(ImageChops.multiply(roots[state],stairs)),'foundation_on_external_water':count(ImageChops.multiply(roots[state],water)),'route_pixels':count(approach)})
 for name,im in [('land',land),('water',water),('stairs',stairs),('support',support),('paths',paths)]:save(OUT/(name+'.png'),im)
 complete=[site['top'] for site in sorted(sites0,key=lambda s:s['native_z']) if site['id'] not in ('coast','grail')];full=background.copy()
 for state in complete:full.alpha_composite(layers[state])
 save(OUT/'complete-scene.png',full);sites=[];overlaps=[];cases=[]
 for site in sites0:
  bb=site_union[site['id']].getbbox();sites.append({'id':site['id'],'states':site['states'],'depth':site['native_z'],'entrance':physical[site['top']]['entrance'],'box':[bb[0],bb[1],bb[2]-bb[0],bb[3]-bb[1]],'intentional_water':site['id']=='coast','silhouette_mask':ref(OUT/'sites'/(site['id']+'.png'))})
 for i,a in enumerate(sites0):
  for b in sites0[i+1:]:
   rear,front=sorted((a,b),key=lambda s:s['native_z']);sid,fid=rear['id'],front['id'];intersection=ImageChops.multiply(site_union[sid],site_union[fid])
   if intersection.getbbox():p=OUT/'overlaps'/(sid+'--'+fid+'.png');save(p,intersection);overlaps.append({'behind':sid,'front':fid,'mask':ref(p),'reason':'Exact all-state projected silhouette intersection in the reviewed complete city; physical roots and actual frontages are checked separately.'})
   root=blank()
   for state in rear['states']:root=ImageChops.lighter(root,roots[state])
   hidden=ImageChops.multiply(root,site_body[fid])
   if not hidden.getbbox():continue
   if (sid,fid) not in LEVELS:raise ValueError('Unreviewed physical contact relationship '+sid+'/'+fid)
   rearlevel,frontlevel=LEVELS[sid,fid];folder=OUT/'foundation-projections'/(sid+'--'+fid);save(folder/'intersection.png',hidden);absent=background.copy()
   for state in complete:
    if state not in front['states']:absent.alpha_composite(layers[state])
   overlay=full.copy();color=Image.new('RGBA',(800,374),(0,255,220,0));color.putalpha(hidden);overlay.alpha_composite(color)
   for name,im in [('complete-scene',full),('front-absent-scene',absent),('intersection-overlay',overlay)]:save(folder/(name+'.png'),im)
   reason='Bounded projected lower wall/plinth edge between the actual separately supported '+rearlevel.lower()+' and '+frontlevel.lower()+'. Actual door/frontage and approach pixels remain outside this mask in every state.'
   write(folder/'source-case.json',{'kind':'supported-terrace-projection','behind':sid,'front':fid,'behind_depth':rear['native_z'],'front_depth':front['native_z'],'rear_level':rearlevel,'front_level':frontlevel,'reason':reason,'hidden_pixels':count(hidden),'hidden_bounds':list(hidden.getbbox()),'mask_sha256':sha(folder/'intersection.png'),'review_status':'Independent per-pair physical truth review required; no blanket waiver.'});cases.append({'behind':sid,'front':fid,'reason':reason,'mask':ref(folder/'intersection.png'),'source_case':ref(folder/'source-case.json'),'evidence':{name:ref(folder/(name.replace('_','-')+'.png')) for name in ('complete_scene','front_absent_scene','intersection_overlay')}})
 contract={'geometry_mode':'silhouette-v2','canvas':[800,374],'alpha_threshold':8,'ordinary_land_sites':17,'background':ref(ROOT/selection['terrain']['native']),'land_mask':ref(OUT/'land.png'),'frames':{s:ref(ROOT/r['native_layer']) for s,r in rows.items()},'sites':sites,'silhouette_plan':{'version':2,'support_mask':ref(OUT/'support.png'),'stairs_mask':ref(OUT/'stairs.png'),'water_mask':ref(OUT/'water.png'),'paths_mask':ref(OUT/'paths.png'),'states':physical,'overlaps':overlaps,'foundation_occlusions':cases,'complete_scene':ref(OUT/'complete-scene.png'),'complete_scene_states':complete},'source_semantic_annotations':ref(HERE/'physical-v10/annotations.json')};write(OUT/'town-layout.json',contract);write(REPORT/'diagnostics.json',{'status':'authored configuration','states':diagnostics,'stair_polygons':stair_polygons,'cases':len(cases)})
 for name,base in [('full',full),('empty',background)]:
  overlay=base.copy()
  for mask,color in [(support,(40,255,80)),(stairs,(255,40,40)),(water,(30,70,255)),(paths,(255,245,20))]:tint=Image.new('RGBA',(800,374),(*color,0));tint.putalpha(mask.point(lambda v:100 if v else 0));overlay.alpha_composite(tint)
  save(REPORT/(name+'-guard-overlay.png'),overlay)
 print(json.dumps({'contract':ref(OUT/'town-layout.json'),'cases':len(cases),'foundation_stair_diagnostics':[r for r in diagnostics if r['foundation_on_stairs'] or (r['foundation_outside_level_support'] and r['state'] not in ('ship','shipyard'))]}))
if __name__=='__main__':main()
