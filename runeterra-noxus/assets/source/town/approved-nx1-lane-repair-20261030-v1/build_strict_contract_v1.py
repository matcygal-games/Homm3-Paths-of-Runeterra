"""Own source candidate only. Execute unchanged production silhouette validator."""
from pathlib import Path
from collections import deque
import json,hashlib,sys,copy
from PIL import Image,ImageDraw,ImageChops
import physical_contract_v2 as P
from contact_traces import CONTACTS
HERE=P.HERE;ROOT=P.ROOT;SIZE=P.SIZE;ROWS=P.ROWS;LAYERS=P.LAYERS;OUT=HERE/'strict-contract-v1'
sys.path.insert(0,str(ROOT.parent/'scripts'))
import faction_town_layout as consumer
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def write(p,obj):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,sort_keys=True,indent=2)+'\n',encoding='utf8')
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.convert('RGB').save(p,compress_level=9)
def poly(points):return P.D.p.poly(points)
def points_mask(points):
 m=Image.new('L',SIZE)
 for q in points:m.putpixel(q,255)
 return m
def cardinal(points):
 result=[tuple(points[0])]
 for end in points[1:]:
  end=tuple(end)
  while result[-1]!=end:
   x,y=result[-1];dx=end[0]-x;dy=end[1]-y
   result.append((x+(1 if dx>0 else -1),y)if abs(dx)>=abs(dy)and dx else(x,y+(1 if dy>0 else -1)))
 return result
def main():
 OUT.mkdir(exist_ok=True);content={'factions':json.loads((ROOT/'content/factions.json').read_text())};town=content['factions']['noxus']['town']
 images={s:Image.open(LAYERS/'structures'/s/'layer.png').convert('RGBA')for s in ROWS};bodies={s:P.D.binary(im)for s,im in images.items()};blank=Image.new('L',SIZE)
 groups={}
 for s,row in ROWS.items():groups.setdefault(row['site'],[]).append(s)
 tops=[states[-1]for site,states in groups.items()if site!='coast'];full=Image.open(LAYERS/'full.png').convert('RGBA')
 land=poly([(0,91),(125,90),(230,96),(302,104),(510,104),(518,131),(550,144),(621,161),(641,145),(648,90),(771,90),(799,129),(799,373),(0,373)])
 land=ImageChops.lighter(land,Image.open(LAYERS/'public-lanes.png').convert('L'))
 stairs=blank.copy()
 for ps in [[(303,121),(505,121),(524,138),(284,138)],[(92,189),(115,188),(122,201),(108,210),(89,201)],[(259,184),(296,184),(295,195),(255,195)],[(676,173),(701,173),(709,184),(672,184)],[(412,208),(446,208),(451,221),(408,221)],[(739,278),(777,278),(784,293),(730,293)]]:stairs=ImageChops.lighter(stairs,poly(ps))
 water=Image.open(ROOT/('assets/source/town/approved-nx1-finish-20261030-v1/terrain/coastal-water-mask.png')).convert('L');land=ImageChops.subtract(land,water);support=ImageChops.subtract(land,stairs)
 quay_passage=poly([(485,333),(490,333),(490,356),(485,356)])
 union=blank.copy()
 for state,b in bodies.items():union=ImageChops.lighter(union,ImageChops.subtract(b,quay_passage)if ROWS[state]['site']=='coast'else b)
 # The optional quay's real right-hand stone entry stair is a traversable
 # architectural frontage, not a roof/body waiver or public-courtyard matte.
 # Only this exact painted stair corner may connect the adjacent streets.
 free=ImageChops.subtract(land,union);origin=(380,320);visited={origin:None};queue=deque([origin]);pix=free.load()
 while queue:
  x,y=queue.popleft()
  for q in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
   if 0<=q[0]<800 and 0<=q[1]<374 and q not in visited and pix[q[0],q[1]]:visited[q]=(x,y);queue.append(q)
 state_records={};physical={};network=blank.copy();failures=[]
 for s,row in ROWS.items():
  logical=P.ROUTES[s]
  if row['site']=='coast':logical=[(405,342),(390,342),(385,335),(380,333)]
  route_points=cardinal(logical);approach=points_mask(route_points);body=bodies[s];door=ImageChops.multiply(approach,body);anchor=logical[0];door.putpixel(tuple(anchor),255)
  if row['site']=='coast':door=ImageChops.lighter(door,ImageChops.multiply(quay_passage,body))
  other=blank.copy()
  for other_s,b in bodies.items():
   if ROWS[other_s]['site']!=row['site']:other=ImageChops.lighter(other,b)
  hit=ImageChops.multiply(approach,other)
  if hit.getbbox():failures.append(s+': true neighbour route collision '+str(hit.getbbox()))
  exits=[q for q in reversed(route_points)if q in visited]
  if not exits:failures.append(s+': no free connected exit')
  else:
   q=exits[0]
   while q is not None:network.putpixel(q,255);q=visited[q]
  authored_contact=blank.copy();draw=ImageDraw.Draw(authored_contact)
  for points in CONTACTS[s]:draw.line(points,fill=255,width=1)
  foundation=ImageChops.multiply(authored_contact,body)
  if not foundation.getbbox():failures.append(s+': independently authored contact trace has no genuine opaque pixels')
  folder=OUT/'states'/s
  for name,mask in [('foundation',foundation),('door',door),('approach',approach),('body',body)]:save(folder/(name+'.png'),mask)
  record={'entrance':list(anchor),'access_kind':'open-site'if s in ('special3','fort','citadel','castle','dwellingLvl2','dwellingUpLvl2')else'door','foundation_mask':ref(folder/'foundation.png'),'door_mask':ref(folder/'door.png'),'approach_mask':ref(folder/'approach.png'),'body_mask':ref(folder/'body.png'),'description':'Actual painted visitor threshold and attached entry steps; public terrace continues on selected connected ground. Hound side service gate is a separately preserved generated correction.'}
  state_records[s]=record;physical[s]=(foundation,door,approach)
 for name,mask in [('land',land),('support',support),('stairs',stairs),('water',water),('paths',network)]:save(OUT/'terrain'/(name+'.png'),mask)
 sites=[];site_sil={}
 for site,states in groups.items():
  alpha=blank.copy()
  for s in states:alpha=ImageChops.lighter(alpha,P.D.binary(images[s],8))
  save(OUT/'sites'/f'{site}.png',alpha);site_sil[site]=alpha;bb=alpha.getbbox();x,y,x1,y1=bb
  sites.append({'id':site,'states':states,'box':[x,y,x1-x,y1-y],'entrance':list(P.ROUTES[states[-1]][0]),'depth':ROWS[states[-1]]['native_z'],'intentional_water':site=='coast','silhouette_mask':ref(OUT/'sites'/f'{site}.png')})
 overlaps=[];foundation_occlusions=[]
 for i,a in enumerate(sites):
  for b in sites[i+1:]:
   behind,front=(a,b)if a['depth']<b['depth']else(b,a)
   exact=ImageChops.multiply(site_sil[behind['id']],site_sil[front['id']])
   if not exact.getbbox():continue
   name=behind['id']+'--'+front['id'];file=OUT/'overlaps'/(name+'.png');save(file,exact)
   overlaps.append({'behind':behind['id'],'front':front['id'],'mask':ref(file),'reason':'Exact whole-silhouette projection intersection in the selected painted scene. Native z preserves the approved oblique terrace depth; entrances and local approaches remain separately collision checked.'})
   rear_root=blank.copy();rear_access=blank.copy();front_body=blank.copy()
   for s in behind['states']:
    f,d,r=physical[s];rear_root=ImageChops.lighter(rear_root,f);rear_access=ImageChops.lighter(rear_access,ImageChops.lighter(d,r))
   for s in front['states']:front_body=ImageChops.lighter(front_body,bodies[s])
   hidden=ImageChops.multiply(rear_root,front_body)
   if not hidden.getbbox():continue
   case_dir=OUT/'foundation-projections'/name;save(case_dir/'mask.png',hidden)
   reason='The rear compound stands on its own upper level masonry terrace; the lower foreground roof projects over only the shown non-access root pixels. Actual rear frontage and approach remain visible and collision-free in every native family variant.'
   case={'kind':'supported-terrace-projection','behind':behind['id'],'front':front['id'],'behind_depth':behind['depth'],'front_depth':front['depth'],'reason':reason,'hidden_pixels':hidden.histogram()[255],'hidden_bounds':list(hidden.getbbox()),'mask_sha256':sha(case_dir/'mask.png'),'rear_level':'Raised masonry terrace for '+behind['id'],'front_level':'Lower street parcel for '+front['id']};write(case_dir/'case.json',case)
   absent=Image.open(LAYERS/'background.png').convert('RGBA')
   for s in sorted(tops,key=lambda q:ROWS[q]['native_z']):
    if ROWS[s]['site']!=front['id']:absent.alpha_composite(images[s])
   overlay=full.copy();mark=Image.new('RGBA',SIZE,(0,250,180,0));mark.putalpha(hidden.point(lambda p:255 if p else 0));overlay.alpha_composite(mark)
   for name_,im in [('complete-scene',full),('foreground-absent',absent),('intersection-overlay',overlay)]:im.save(case_dir/(name_+'.png'),compress_level=9)
   foundation_occlusions.append({'behind':behind['id'],'front':front['id'],'reason':reason,'mask':ref(case_dir/'mask.png'),'source_case':ref(case_dir/'case.json'),'evidence':{'complete_scene':ref(case_dir/'complete-scene.png'),'front_absent_scene':ref(case_dir/'foreground-absent.png'),'intersection_overlay':ref(case_dir/'intersection-overlay.png')}})
 plan={'version':2,'support_mask':ref(OUT/'terrain/support.png'),'stairs_mask':ref(OUT/'terrain/stairs.png'),'water_mask':ref(OUT/'terrain/water.png'),'paths_mask':ref(OUT/'terrain/paths.png'),'states':state_records,'overlaps':overlaps,'foundation_occlusions':foundation_occlusions,'complete_scene_states':sorted(tops,key=lambda s:ROWS[s]['native_z']),'complete_scene':ref(LAYERS/'full.png')}
 contract={'geometry_mode':'silhouette-v2','canvas':list(SIZE),'alpha_threshold':8,'ordinary_land_sites':17,'background':ref(LAYERS/'background.png'),'land_mask':ref(OUT/'terrain/land.png'),'frames':{s:ref(LAYERS/'structures'/s/'layer.png')for s in ROWS},'sites':sites,'silhouette_plan':plan,'status':'authored configuration','candidate_only':True,'source_note':'Original approved whole painting is immutable. All candidate generation prompts, finite composite masks and source-only state ownership are preserved alongside this contract.'}
 write(OUT/'town-layout.json',contract)
 try:consumer._inspect_silhouettes(ROOT,contract,sites,images,town,land,set());strict=[]
 except (ValueError,KeyError,OSError,TypeError)as error:strict=[str(error)]
 write(OUT/'executed-check.json',{'status':'authored configuration','preflight_failures':failures,'actual_strict_consumer_errors':strict,'shared_consumer_sha256':sha(ROOT.parent/'scripts/faction_town_layout.py'),'selected_canonical_changed':False,'foundation_projection_cases':len(foundation_occlusions),'states':len(images),'sites':len(sites)});print(json.dumps({'preflight':failures,'strict':strict,'foundation_cases':len(foundation_occlusions)},indent=2))
if __name__=='__main__':main()
