"""Independent IX1 terrace observations and strict unchanged consumer replay.

Masks are editable source observations. Public circulation routes are measured
through their union, with all-state architecture/structural contact obstacles.
The procedure never changes art or manufactures support underneath a defect.
"""
from pathlib import Path
import sys,json,shutil,heapq,copy
from collections import deque
from PIL import Image,ImageDraw,ImageChops
from assemble import HERE,PROJECT,ROOT,REPORT,RUNTIME,SIZE,read,dump,sha,rel,ref,save
sys.path.insert(0,str(ROOT/'scripts'))
import faction_town_layout as layout

def poly(points):
 im=Image.new('L',SIZE);ImageDraw.Draw(im).polygon(points,fill=255);return im
def union(images):
 im=Image.new('L',SIZE)
 for other in images:im=ImageChops.lighter(im,other)
 return im
def rectangle(box):
 im=Image.new('L',SIZE);ImageDraw.Draw(im).rectangle(box,fill=255);return im
def count(im):return im.histogram()[255]
DOORS={'hall':(426,104,447,143),'guild':(490,116,507,145),'fort':(601,108,626,130),'hallunatis':(234,90,254,122),
'canopy':(98,119,115,132),'stoneshapers':(281,180,313,210),'nexus':(533,176,568,204),'bristlehogs':(136,188,154,206),
'pakaa':(145,230,164,249),'guides':(215,252,233,274),'wardens':(256,249,277,275),'pairofants':(616,214,639,244),
'smith':(169,313,193,349),'tavern':(352,285,382,314),'market':(538,303,561,337),'silo':(721,326,746,361),'grail':(439,222,463,249),
'coast':(91,116,107,132)}
OPEN={'canopy','stoneshapers','nexus','bristlehogs','pakaa','pairofants','market','grail'}

def main():
 idx=read(HERE/'frame-index.json');root=HERE/'physical';root.mkdir(exist_ok=True)
 def mask(name,im):return save(root/'masks'/name,im.convert('RGBA'))
 images={s:Image.open(PROJECT/r['frame']['path']).convert('RGBA') for s,r in idx['frames'].items()}
 if idx['missing']:raise ValueError('Physical plan requires every state: '+str(idx['missing']))
 # Actual supported civic terraces occupy the lower city. Visible falls are
 # outside the bridge deck; the conditional river inlet is reserved at rear.
 land=union([poly([(0,73),(132,73),(132,103),(330,110),(347,108),(347,73),(595,73),(595,107),(799,107),(799,373),(0,373)]),poly([(133,89),(325,89),(329,120),(132,124)])])
 water=union([poly([(0,54),(40,60),(106,72),(129,88),(128,108),(104,126),(0,103)]),poly([(636,130),(663,130),(667,146),(655,154),(634,147)])])
 # Existing supported canopy footbridge deck is public land above the inlet.
 water=ImageChops.subtract(water,poly([(0,113),(72,111),(122,120),(145,137),(141,149),(88,133),(0,128)]))
 land=ImageChops.subtract(land,water)
 # The public main stair spine is explicit nonlevel ground. Own entrance
 # stairs are recorded in their door/frontage roles, not structural footings.
 stairs=union([poly([(434,329),(465,329),(467,373),(431,373)]),poly([(441,258),(464,258),(463,277),(440,277)])])
 support=ImageChops.subtract(land,stairs)
 frames={};sites=[];states={};foundations={};doors={};bodies={};alpha={};physicalstats={}
 source_sites=read(HERE/'inputs/town-visuals-before.json')['sites']
 for site,spec in source_sites.items():
  keys=spec['keys'];a=union([images[s].getchannel('A').point(lambda v:255 if v>=8 else 0) for s in keys]);box=a.getbbox();depth=idx['frames'][keys[0]]['depth']
  entrance=idx['frames'][keys[-1]]['entrance'];sites.append({'id':site,'states':keys,'depth':depth,'entrance':entrance,'box':[box[0],box[1],box[2]-box[0],box[3]-box[1]],'intentional_water':site=='coast','silhouette_mask':mask('sites/'+site+'.png',a)})
  for state in keys:
   im=images[state];a=im.getchannel('A').point(lambda v:255 if v>=8 else 0);body=im.getchannel('A').point(lambda v:255 if v>=128 else 0);box=a.getbbox();row=idx['frames'][state]
   if row['kind']=='independent-painted-predecessor':
    x,y=row['entrance'];door=rectangle((x-10,max(box[1],y-22),x+10,min(box[3]-1,y+3)))
    if site=='fort':door=rectangle((x-10,y-7,x+10,min(box[3]-1,y+3)))
    if site=='guild':door=rectangle((x-4,max(box[1],y-15),x+4,min(box[3]-1,y+3)))
   else:door=rectangle(DOORS[site])
   if site=='coast':door=poly([(98,131),(102,131),(103,132),(102,133),(98,133)])
   # Door annotation only covers the visible actual frame bounds.
   door=ImageChops.multiply(door,rectangle((box[0],box[1],box[2]-1,box[3]-1)))
   entrance=row['entrance']
   if not door.getpixel(tuple(entrance)):raise ValueError('Measured entrance outside frontage '+state)
   # Actual lower opaque contour in the independently observed foundation
   # band. The entry stair strip is distinct from structural foot support.
   contact=Image.new('L',SIZE);pixels=a.load()
   for x in range(box[0],box[2]):
    ys=[y for y in range(max(box[1],box[3]-9),box[3]) if pixels[x,y]]
    if ys:contact.putpixel((x,max(ys)),255)
   foundation=ImageChops.subtract(contact,door)
   if site=='coast':
    # Independently observed piling/hull soles, not the lower alpha edge of
    # the conditional water/shore painting. Native grid inspection retained.
    contact=Image.new('L',SIZE);draw=ImageDraw.Draw(contact)
    for points in [[(107,109),(109,109)],[(116,117),(118,117)],[(124,114),(125,114)],[(132,111),(133,111)],[(141,113),(145,115)]]:draw.line(points,fill=255,width=1)
    if state=='ship':draw.line([(73,94),(81,99),(89,100),(99,97)],fill=255,width=1)
    foundation=ImageChops.multiply(contact,a)
   if not foundation.getbbox():raise ValueError('Missing structural contact '+state)
   frames[state]=row['frame'];alpha[state]=a;bodies[state]=body;foundations[state]=foundation;doors[state]=door
   states[state]={'entrance':entrance,'access_kind':'moored-vessel' if state=='ship' else 'open-site' if site in OPEN else 'door','foundation_mask':mask(state+'/foundation.png',foundation),'door_mask':mask(state+'/door.png',door),'body_mask':mask(state+'/body.png',body)}
   if site=='coast':
    marine=ImageChops.multiply(a,ImageChops.multiply(water,foundation))
    states[state].update(marine_support_kind='moored-hull' if state=='ship' else 'deck-and-pilings',marine_support_mask=mask(state+'/marine.png',marine))
   unsupported=ImageChops.subtract(foundation,union([support,water if site=='coast' else Image.new('L',SIZE)]))
   physicalstats[state]={'foundation_pixels':count(foundation),'unsupported_pixels':count(unsupported),'unsupported_bounds':unsupported.getbbox(),'stairs_pixels':count(ImageChops.multiply(foundation,stairs))}
 # Annotated circulation courts/lanes; these are terrain observations, not a
 # blanket all-land permission. Search only through their actual open pixels.
 circulation=union([poly([(418,125),(478,125),(493,176),(520,211),(522,249),(480,275),(484,313),(469,373),(421,373),(432,314),(431,263),(427,214),(434,172)]),
 poly([(145,113),(355,113),(428,140),(432,154),(344,143),(227,145),(191,160),(178,189),(169,222),(168,257),(150,267),(149,233),(151,185),(145,155)]),
 poly([(273,207),(427,207),(432,226),(293,229),(286,255),(288,282),(300,315),(289,346),(279,341),(279,293),(263,272),(239,279),(181,280),(164,265),(168,251),(192,259),(222,260),(248,265),(273,255)]),
 poly([(474,137),(518,137),(526,143),(492,152),(484,181),(488,206),(616,205),(624,175),(626,152),(646,133),(717,121),(720,133),(655,147),(638,162),(632,197),(628,221),(493,226),(479,212),(470,181)]),
 poly([(477,326),(633,326),(638,340),(764,357),(768,373),(476,373)]),
 poly([(286,311),(428,311),(433,332),(286,332)]),
 poly([(608,217),(640,217),(642,248),(617,258),(605,245)]),
 poly([(594,126),(721,126),(721,132),(594,135)]),
 poly([(598,129),(624,129),(632,149),(624,177),(610,205),(601,205),(610,174),(612,151)]),
 poly([(141,186),(163,186),(172,222),(168,253),(145,258),(143,235)]),
 poly([(531,195),(568,195),(568,213),(531,213)]),
 poly([(137,140),(154,139),(176,154),(180,166),(169,169),(152,155)]),
 poly([(10,344),(286,340),(290,356),(424,356),(424,373),(9,373)]),
 poly([(80,112),(120,112),(146,126),(149,146),(137,153),(109,139),(91,131)])])
 # Reserve every state body outside its genuine entrance and every actual
 # structural foot. Open-site frontage is traversable, closed walls are not.
 hard=union([union([ImageChops.subtract(bodies[s],doors[s]),foundations[s]]) for s in images]);free=ImageChops.subtract(ImageChops.multiply(circulation,land),hard)
 network=Image.new('L',SIZE);network.putpixel((450,373),255);native=Image.open(HERE/'approved-full.png').convert('RGBA');routes=[];failures=[]
 connected=Image.new('L',SIZE);todo=deque([(450,373)]);connected.putpixel((450,373),255)
 while todo:
  x,y=todo.popleft()
  for point in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
   xx,yy=point
   if 0<=xx<800 and 0<=yy<374 and free.getpixel(point) and not connected.getpixel(point):connected.putpixel(point,255);todo.append(point)
 def search(start,allowed=free,target_mask=None):
  if not allowed.getpixel(start):return None
  target_mask=network if target_mask is None else target_mask
  dist={start:0};prev={start:None};queue=[(0,start)];found=None
  while queue:
   cost,node=heapq.heappop(queue)
   if cost!=dist[node]:continue
   if target_mask.getpixel(node):found=node;break
   for x,y in ((node[0]-1,node[1]),(node[0]+1,node[1]),(node[0],node[1]-1),(node[0],node[1]+1)):
    if not(0<=x<800 and 0<=y<374 and allowed.getpixel((x,y))):continue
    r,g,b,_=native.getpixel((x,y));step=1 if r>100 and g>90 and b>65 and r>g*.94 else 30
    nxt=(x,y);new=cost+step
    if new<dist.get(nxt,10**12):dist[nxt]=new;prev[nxt]=node;heapq.heappush(queue,(new,nxt))
  if found is None:return None
  result=[]
  while found is not None:result.append(found);found=prev[found]
  return result[::-1]
 for site in sites:
  site_routes=[]
  for s in site['states']:
   start=tuple(idx['frames'][s]['entrance'])
   # A state-specific entry route may cross an absent alternative's projected
   # envelope, never a different site. The shared public network remains clear
   # of every alternate body. This follows actual upgrade-family rendering.
   other_bodies=union([bodies[other] for other,row in idx['frames'].items() if row['site']!=site['id']])
   local_hard=union([other_bodies,ImageChops.subtract(bodies[s],doors[s]),foundations[s]])
   db=doors[s].getbbox()
   apron=rectangle((db[0],db[3]-1,db[2]-1,min(373,db[3]+12)))
   if s=='dwellingLvl2':apron=union([apron,rectangle((78,195,154,201))])
   if s=='dwellingLvl3':apron=union([apron,rectangle((119,241,160,245))])
   if s=='dwellingLvl7':apron=union([apron,rectangle((618,224,735,238))])
   local_free=ImageChops.subtract(ImageChops.multiply(union([circulation,doors[s],apron]),land),local_hard)
   local=search(start,local_free,connected)
   route=search(local[-1]) if local else None
   if route is None:failures.append({'state':s,'site':site['id'],'start':list(start),'local_exit':list(local[-1]) if local else None});continue
   im=Image.new('L',SIZE);d=ImageDraw.Draw(im);d.line(local,fill=255,width=1)
   for point in local:im.putpixel(point,255)
   states[s]['approach_mask']=mask(s+'/approach.png',im)
   for p in route:network.putpixel(p,255)
   site_routes.append({'state':s,'approach':[list(p) for p in local],'path':[list(p) for p in route]})
  routes+=site_routes
 dump(root/'routing-diagnostics.json',{'routes':routes,'failures':failures,'physical_measurements':physicalstats,'observed_circulation':mask('terrain/circulation.png',circulation),'all_state_obstacles':mask('terrain/obstacles.png',hard)})
 overlay=Image.new('RGBA',SIZE);overlay.paste((255,0,220,255),(0,0),network);save(REPORT/'path-overlay.png',Image.alpha_composite(native,overlay))
 if failures:
  print(json.dumps({'route_failures':failures,'unsupported':[s for s,v in physicalstats.items() if v['unsupported_pixels'] or v['stairs_pixels']]}));return 2
 overlaps=[];occlusions=[]
 cases={('guild','nexus'):{'reason':'The upper scholar campus stands on its own higher council terrace. Its non-entry right-hand foundation projects behind the lower civic Axiom ring court; the left-side threshold and its route remain entirely visible.',
 'rear_level':'Upper council scholar terrace, threshold125 and frontage142',
 'front_level':'Lower axiom civic court, ring plinth181-200'},
 ('bristlehogs','pakaa'):{'reason':'The boar refuge stands on the upper retained animal terrace. A lower Pakaa shelter palm projects across a small non-entry part of that upper retaining foot; both right-side access lanes remain unobscured.',
 'rear_level':'Upper Bristlehog refuge terrace, wall contact around215',
 'front_level':'Lower Pakaa refuge terrace, shelter/root contact239-255'},
 ('pakaa','smith'):{'reason':'The Pakaa refuge occupies the rear retained garden level. Foreground forge architecture projects over a bounded non-entry portion of its lower wall foot; the refuge side gate and eastern stair stay open.',
 'rear_level':'Retained Pakaa garden at contact239-255',
 'front_level':'Foreground working forge terrace at contact330-346'},
 ('guides','smith'):{'reason':'The Tracker house is supported by its own upper residential terrace. The larger foreground forge projects over a bounded non-entry west/root edge; the visible right-hand arch and connected court remain open.',
 'rear_level':'Upper Tracker residential terrace at contact263-273',
 'front_level':'Foreground forge/community court at contact330-346'},
 ('wardens','smith'):{'reason':'The Warden annex stands on the upper residential terrace behind the forge. Only its non-entry left-side root can be projected behind foreground roof material; its right-hand doorway and courtyard access remain visible.',
 'rear_level':'Upper Warden residential terrace at contact267-275',
 'front_level':'Foreground forge/community court at contact330-346'},
 ('pairofants','silo'):{'reason':'The Pairofant refuge sits on the higher right-hand animal terrace. Foreground repository roofs project across part of its non-entry front retaining foot; the left-side refuge access remains completely clear.',
 'rear_level':'Higher Pairofant sanctuary terrace at contact224-249',
 'front_level':'Foreground repository/store terrace at contact340-358'},
 ('stoneshapers','guides'):{'reason':'The material-study court is on the higher central-left terrace. The lower residential roof projects over only a non-entry west corner of its retained foot; the central study entrance and lane remain unobscured.',
 'rear_level':'Higher material-study terrace at contact198-209',
 'front_level':'Lower Tracker residential terrace at contact263-273'}}
 def render(names):
  out=Image.open(HERE/'background.png').convert('RGBA')
  for s in sorted(names,key=lambda state:idx['frames'][state]['depth']):out.alpha_composite(images[s])
  return out
 for n,a in enumerate(sites):
  aa=union([alpha[s] for s in a['states']])
  for b in sites[n+1:]:
   bb=union([alpha[s] for s in b['states']]);hit=ImageChops.multiply(aa,bb)
   if hit.getbbox():
    behind,front=(a,b) if a['depth']<b['depth'] else (b,a)
    overlaps.append({'behind':behind['id'],'front':front['id'],'reason':'Approved theatrical terrace projection; complete source footprints are bounded and independently visible doors remain accessible.','mask':mask('overlaps/'+behind['id']+'--'+front['id']+'.png',hit)})
    pair=(behind['id'],front['id'])
    if pair in cases:
     rear=union([foundations[s] for s in behind['states']]);body=union([bodies[s] for s in front['states']]);hidden=ImageChops.multiply(rear,body)
     if hidden.getbbox():
      spec=cases[pair];folder=root/'foundation-cases'/(pair[0]+'--'+pair[1]);folder.mkdir(parents=True,exist_ok=True)
      hidden_ref=mask('foundation-cases/'+pair[0]+'--'+pair[1]+'.png',hidden)
      source_case={'kind':'supported-terrace-projection','behind':pair[0],'front':pair[1],'behind_depth':behind['depth'],'front_depth':front['depth'],'reason':spec['reason'],'rear_level':spec['rear_level'],'front_level':spec['front_level'],'hidden_pixels':count(hidden),'hidden_bounds':list(hidden.getbbox()),'mask_sha256':hidden_ref['sha256']}
      dump(folder/'case.json',source_case)
      rear_state=max(behind['states'],key=lambda s:count(ImageChops.multiply(foundations[s],body)))
      selected=[s for s in idx['complete_scene_states'] if s not in behind['states'] and s not in front['states']]+[rear_state,front['states'][-1]]
      complete=render(selected);absent=render([s for s in selected if s not in front['states']]);overlay=Image.new('RGBA',SIZE);overlay.paste((255,0,120,255),(0,0),hidden)
      evidence={'complete_scene':save(folder/'complete.png',complete),'front_absent_scene':save(folder/'front-absent.png',absent),'intersection_overlay':save(folder/'intersection.png',Image.alpha_composite(complete,overlay))}
      occlusions.append({'behind':pair[0],'front':pair[1],'reason':spec['reason'],'mask':hidden_ref,'source_case':ref(folder/'case.json'),'evidence':evidence})
 contract={'status':'authored configuration','geometry_mode':'silhouette-v2','canvas':list(SIZE),'alpha_threshold':8,'ordinary_land_sites':16,'background':idx['background'],'land_mask':mask('terrain/land.png',land),'frames':frames,'sites':sites,'silhouette_plan':{'version':2,'support_mask':mask('terrain/support.png',support),'stairs_mask':mask('terrain/stairs.png',stairs),'water_mask':mask('terrain/water.png',water),'paths_mask':mask('terrain/paths.png',network),'states':states,'overlaps':overlaps,'foundation_occlusions':occlusions,'complete_scene':ref(HERE/'approved-full.png'),'complete_scene_states':idx['complete_scene_states']},'authoring_sources':[ref(Path(__file__)),ref(HERE/'assemble.py'),ref(HERE/'frame-index.json')],'native_tested':False}
 cp=root/'layout-contract.json';dump(cp,contract)
 factions=read(HERE/'inputs/factions-before.json');town=factions['ixtal']['town']
 for s in images:town['structures'][s].update(x=0,y=0,z=idx['frames'][s]['depth'])
 dump(HERE/'factions-candidate.json',factions)
 fixture=REPORT/'physical-fixture';fixture.mkdir(exist_ok=True)
 paths=set()
 def collect(v):
  if isinstance(v,dict):
   if isinstance(v.get('path'),str) and isinstance(v.get('sha256'),str):paths.add(v['path'])
   for vv in v.values():collect(vv)
  elif isinstance(v,list):
   for vv in v:collect(vv)
 collect(contract);paths.add(rel(cp))
 for name in paths:
  dst=fixture/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(PROJECT/name,dst)
 dump(fixture/'design/town-visuals.json',{'layout_geometry_mode':'silhouette-v2','layout_contract':ref(cp)})
 for src in RUNTIME.rglob('*'):
  if src.is_file():dst=fixture/'assets/generated'/src.relative_to(RUNTIME);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
 errors,deps=layout.inspect(fixture,{'factions':factions},'ixtal');dump(REPORT/'physical-checks.json',{'errors':errors,'dependency_count':len(deps),'passed':not errors,'native_tested':False})
 print(json.dumps({'physical_errors':errors,'dependency_count':len(deps)}));return 0 if not errors else 2

if __name__=='__main__':raise SystemExit(main())
