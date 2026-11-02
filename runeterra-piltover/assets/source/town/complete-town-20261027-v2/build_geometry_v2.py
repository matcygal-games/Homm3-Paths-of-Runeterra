"""Build explicit physical-mask candidates and execute real V2 consumer checks.

Masks are editable technical annotations. They do not grant architectural/art
approval; every route/root is reviewed against the approved whole painting.
"""
from pathlib import Path
from collections import deque
from copy import deepcopy
import hashlib
import importlib.util
import json
import shutil
import sys
import numpy as np
from PIL import Image,ImageDraw,ImageChops,ImageFilter

S=Path(__file__).resolve().parent
P=S.parents[3]
W=P.parent
R=P/'build/reports/complete-town-20261027-v2/derivation-v1'
sys.path.insert(0,str(W/'scripts'))
import faction_town_layout

SIZE=(800,374)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def rel(path):return path.relative_to(P).as_posix()
def ref(path):return {'path':rel(path),'sha256':sha(path)}
def dump(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def mask_array(image,threshold=128):return np.asarray(image.getchannel('A') if image.mode=='RGBA'else image)>=threshold
def image_mask(array):return Image.fromarray(np.asarray(array,dtype=np.uint8)*255,'L')
def save(name,array):
 path=S/'physical-masks-v2'/name
 path.parent.mkdir(parents=True,exist_ok=True)
 image_mask(array).save(path)
 return ref(path)
def polygon(points):
 image=Image.new('L',SIZE)
 ImageDraw.Draw(image).polygon([tuple(p)for p in points],fill=255)
 return np.asarray(image)>0
def drawlines(lines,width):
 image=Image.new('L',SIZE)
 d=ImageDraw.Draw(image)
 for points in lines:d.line([tuple(p)for p in points],fill=255,width=width)
 return np.asarray(image)>0
def dilate(array,width):return np.asarray(image_mask(array).filter(ImageFilter.MaxFilter(width)))>0
def route(allowed,start,goal):
 sx,sy=start
 if not (0<=sx<800 and 0<=sy<374 and allowed[sy,sx]):return None
 previous={start:None};q=deque([start]);end=None
 while q:
  point=q.popleft();x,y=point
  if goal[y,x]:end=point;break
  for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
   if 0<=nx<800 and 0<=ny<374 and allowed[ny,nx] and (nx,ny)not in previous:
    previous[nx,ny]=point;q.append((nx,ny))
 if end is None:return None
 points=[]
 while end is not None:points.append(end);end=previous[end]
 return points[::-1]

def build():
 registration=json.loads((S/'frame-registration-v1.json').read_text())['states']
 traces=json.loads((S/'silhouette-traces-v1.json').read_text())['sites']
 program=json.loads((S/'functional-program-v2.json').read_text())['sites']
 content={'factions':json.loads((P/'content/factions.json').read_text())}
 town=content['factions']['piltover']['town']
 images={state:Image.open(S/'frames'/r['site']/(state+'.png')).convert('RGBA')for state,r in registration.items()}
 bodies={state:mask_array(image)for state,image in images.items()}
 fulls={state:mask_array(image,8)for state,image in images.items()}
 water=polygon([[799,223],[774,235],[772,258],[768,280],[767,306],[751,317],[735,324],[733,341],[716,348],[703,354],[682,356],[669,364],[644,368],[634,373],[799,373]])
 land=polygon([[0,65],[40,81],[89,97],[154,103],[193,100],[229,99],[280,105],[347,111],[400,106],[438,93],[476,100],[536,108],[599,112],[651,99],[702,106],[750,95],[799,102],[799,373],[0,373]])&~water
 foundations={};doors={};entrances={};physical={};issues=[]
 for state,r in registration.items():
  body=bodies[state];site_trace=traces[r['site']];xroot,yroot=site_trace.get('state_doors',{}).get(state,site_trace['door']);foundation=np.zeros((374,800),bool)
  for x in range(800):
   ys=np.flatnonzero(body[:,x])
   # Never discard a lower front/side plinth merely because it extends more
   # than ten pixels below the door. High roof-only side columns remain above
   # the observed frontage band and are reviewed separately as exclusions.
   if len(ys) and yroot-12<=ys[-1]:
    y=int(ys[-1]);foundation[max(0,y-2):y+1,x]=body[max(0,y-2):y+1,x]
  if not foundation.any():raise ValueError('No annotated real contact profile '+state)
  # One observed frontal entrance/visitor frontage, not a free whole-body ignore.
  nearby=[]
  for dy in range(-5,7):
   for dx in range(-5,6):
    x,y=xroot+dx,yroot+dy
    if 0<=x<800 and 0<=y<374 and body[y,x]:nearby.append((abs(dx)+abs(dy),x,y))
  if not nearby:raise ValueError('No actual entrance pixels near authored frontage '+state)
  _,x,y=min(nearby)
  ys=np.flatnonzero(body[:,x]);bottom=int(ys[-1])
  door=np.zeros((374,800),bool)
  box=image_mask(fulls[state]).getbbox()
  door[max(box[1],y-3):min(box[3],bottom+1),max(box[0],x-2):min(box[2],x+3)]=True
  entrances[state]=[x,y];doors[state]=door;foundations[state]=foundation
  if r['site']=='coast' and state=='ship':
   hull=polygon(traces['coast']['marine_polygon'])&fulls[state]
   hull_contact=hull&water
   # Full actual hull/water contact band, not a whole-water exemption.
   for xx in range(800):
    ys2=np.flatnonzero(hull_contact[:,xx])
    if len(ys2):yy=int(ys2[-1]);foundation[max(0,yy-2):yy+1,xx]|=hull[max(0,yy-2):yy+1,xx]
  physical[state]={'bottom':bottom,'door_start':[x,y]}
 # These are the observed public stair flights between level landings. Private
 # short entry steps remain part of each authored doorway, not terrain stairs.
 stairs=np.zeros((374,800),bool)
 for poly in ([[118,131],[128,131],[146,149],[136,151]],[[154,157],[169,153],[177,170],[162,181]],[[370,165],[383,165],[402,180],[389,185]],[[315,231],[324,230],[337,249],[326,251]],[[279,348],[292,344],[311,368],[299,373]]):stairs|=polygon(poly)
 support=np.zeros((374,800),bool)
 for state,foundation in foundations.items():
  if registration[state]['site']!='coast':support|=dilate(foundation,9)
  else:support|=dilate(foundation&land,7)
 support&=land&~stairs&~water
 for state,foundation in foundations.items():
  if registration[state]['site']!='coast' and np.any(foundation&~support):issues.append({'kind':'foundation_support','state':state,'pixels':int((foundation&~support).sum()),'coordinates':np.argwhere(foundation&~support)[:,::-1].tolist()})
 # Painted street corridors are authored as a visible connected town network.
 # The actual all-state bodies then bound a safe centerline inside those lanes.
 lines=[[[3,338],[730,338]],[[3,140],[3,338]],[[229,338],[229,312],[231,282],[223,255],[220,236],[212,221],[201,207],[181,197],[171,186],[165,181]],[[124,130],[150,139],[163,151],[171,165],[165,181]],[[36,218],[19,222],[3,222]],[[128,177],[145,180],[164,181]],[[135,232],[151,238],[177,240],[215,236]],[[222,124],[209,115],[199,117],[190,132],[150,139]],[[259,194],[252,201],[232,214],[212,221]],[[268,252],[254,259],[241,268],[231,282]],[[394,163],[422,171],[450,182],[458,209],[489,232],[489,277],[475,298],[475,338]],[[393,213],[365,218],[343,228],[319,235],[310,247],[292,255],[254,259]],[[431,277],[456,281],[475,298]],[[506,225],[482,229],[489,247],[489,277]],[[646,234],[626,234],[607,235],[581,231],[551,229],[506,225]],[[718,159],[709,168],[694,172],[668,179],[645,180],[624,172],[606,172],[575,169],[553,170],[545,189],[551,218],[551,229]],[[526,155],[545,159],[553,170]],[[122,333],[122,338]],[[327,332],[327,338]],[[624,335],[624,338]],[[723,334],[716,338]]]
 # Observed front gallery of the depot continues east to the quay stair;
 # the Orrery landing connects east behind the shield workshop.
 lines.extend([[[646,241],[742,241],[752,253],[750,280],[735,310],[719,331]],[[738,241],[743,220],[725,206],[718,164]],[[393,216],[448,216],[458,209]],[[128,184],[145,187],[165,184],[181,197]]])
 corridor=drawlines(lines,19)&land
 blocked=np.zeros((374,800),bool)
 all_body=np.zeros((374,800),bool)
 for state,body in bodies.items():blocked|=body&~doors[state];all_body|=body
 safe=corridor&~blocked
 seed=(475,338)
 # A doorway can itself be a tiny clear island. Route to the actual connected
 # public street component, never stop at the first isolated clear door pixel.
 reached=np.zeros((374,800),bool);queue=deque([seed]);reached[seed[1],seed[0]]=True
 while queue:
  xx,yy=queue.popleft()
  for nx,ny in ((xx-1,yy),(xx+1,yy),(xx,yy-1),(xx,yy+1)):
   if 0<=nx<800 and 0<=ny<374 and safe[ny,nx] and not reached[ny,nx]:
    reached[ny,nx]=True;queue.append((nx,ny))
 safe&=reached
 tree=np.zeros((374,800),bool);tree[seed[1],seed[0]]=True
 # Grow the same connected street tree to all states using actual clear lanes.
 approach_masks={};failures=[];route_details={}
 for state,r in registration.items():
  x,y=entrances[state];bottom=physical[state]['bottom'];start=(x,min(373,bottom+1))
  other=np.zeros((374,800),bool)
  for other_state,other_body in bodies.items():
   if registration[other_state]['site']!=r['site']:other|=other_body
  permitted=(corridor|dilate(doors[state],25))&land&~other&~(bodies[state]&~doors[state])
  # Connect the actual door/frontage through its own short apron to the clear
  # global corridor; no other roof/body can be used as an invisible bridge.
  goal=safe
  first=route(permitted,(x,y),goal)
  if first is None:
   failures.append({'state':state,'kind':'door_to_corridor','entrance':[x,y],'bottom':bottom});continue
  join=first[-1]
  second=route(safe,join,tree)
  if second is None:
   failures.append({'state':state,'kind':'disconnected_street','join':join});continue
  for xx,yy in second:tree[yy,xx]=True
  route_details[state]={'apron':first,'street':second}
  approach=np.zeros((374,800),bool)
  # A short actual apron including the doorway pixel gives cardinal contact.
  for xx,yy in first:approach[yy,xx]=True
  approach_masks[state]=approach
  # The network includes the approved apron only when it is free of every
  # selected body's solid pixels outside their separately recorded frontages.
  for xx,yy in first:
   if not blocked[yy,xx]:tree[yy,xx]=True
  if not np.any(approach&tree):
   for xx,yy in second[:1]:approach[yy,xx]=True
 dump(R/'physical-plan-findings-v1.json',{'status':'authored configuration','support_findings':issues,'access_findings':failures,'source_annotation_review':'pending','scope':'Actual current source pixels, not synthetic pass claims'})
 dump(R/'route-details-v1.json',route_details)
 overlay=Image.open(S/'complete-town-native-v2.png').convert('RGBA')
 overlay.alpha_composite(Image.fromarray(np.dstack([np.zeros((374,800),np.uint8),np.full((374,800),255,np.uint8),np.zeros((374,800),np.uint8),tree.astype(np.uint8)*190]),'RGBA'))
 overlay.save(R/'path-centerlines-v1.png')
 # Preserve native source diagnostics even when admission fails.
 debug=R/'physical-diagnostics';debug.mkdir(exist_ok=True)
 image_mask(blocked).save(debug/'all-state-solid.png')
 image_mask(corridor).save(debug/'authored-streets.png')
 image_mask(safe).save(debug/'clear-streets.png')
 for state in {f['state'] for f in failures+issues}:
  site=registration[state]['site'];box=image_mask(fulls[state]).getbbox()
  crop=(max(0,box[0]-18),max(0,box[1]-12),min(800,box[2]+28),min(374,box[3]+30))
  view=Image.open(S/'complete-town-native-v2.png').convert('RGBA')
  for array,color in [(blocked,(255,0,0)),(safe,(0,255,0)),(doors[state],(0,200,255)),(foundations[state],(255,255,0))]:
   view.alpha_composite(Image.fromarray(np.dstack([np.full((374,800),c,np.uint8)for c in color]+[array.astype(np.uint8)*155]),'RGBA'))
  d=ImageDraw.Draw(view);x,y=entrances[state];d.ellipse((x-2,y-2,x+2,y+2),outline='white')
  view.crop(crop).resize(((crop[2]-crop[0])*4,(crop[3]-crop[1])*4),Image.Resampling.NEAREST).save(debug/(state+'.png'))
 if issues or failures:
  print(json.dumps({'ok':False,'support_findings':issues,'access_findings':failures}));return None
 sites=[];frames={};plans={};unions={}
 for site in program:
  identifier=site['id'];states=site['states'];union=np.zeros((374,800),bool)
  for state in states:union|=fulls[state]
  unions[identifier]=union;b=image_mask(union).getbbox();site_ref=save('sites/'+identifier+'-silhouette.png',union)
  sites.append({'id':identifier,'states':states,'box':[b[0],b[1],b[2]-b[0],b[3]-b[1]],'entrance':entrances[traces[identifier]['master_state']],'depth':traces[identifier]['depth'],'intentional_water':identifier=='coast','silhouette_mask':site_ref})
  for state in states:
   path=S/'frames'/identifier/(state+'.png');frames[state]=ref(path)
   foundation=foundations[state]
   plans[state]={'access_kind':'moored-vessel'if state=='ship'else'open-site'if identifier in ('market','smith','rifles','freight','rotors','apex','coast')else'door','entrance':entrances[state],'foundation_mask':save('states/'+state+'-foundation.png',foundation),'body_mask':save('states/'+state+'-body.png',bodies[state]),'door_mask':save('states/'+state+'-door.png',doors[state]),'approach_mask':save('states/'+state+'-approach.png',approach_masks[state])}
   marine=foundation&water
   if marine.any():
    if identifier!='coast':raise ValueError('Ordinary root crosses external water '+state)
    plans[state]['marine_support_mask']=save('states/'+state+'-marine.png',marine)
    plans[state]['marine_support_kind']='moored-hull'if state=='ship'else'deck-and-pilings'
   town['structures'][state]['z']=traces[identifier]['depth']
 overlaps=[]
 for i,a in enumerate(sites):
  for b in sites[i+1:]:
   overlap=unions[a['id']]&unions[b['id']]
   if overlap.any():
    behind,front=(a,b)if a['depth']<b['depth']else(b,a)
    overlaps.append({'behind':behind['id'],'front':front['id'],'mask':save('overlaps/'+behind['id']+'--'+front['id']+'.png',overlap),'reason':'Bounded projected roof/side-wall depth in the reviewed complete city; every actual foundation, public frontage and approach remains exposed and supported.'})
 ordered=[traces[s['id']]['master_state']for s in sorted(program,key=lambda p:traces[p['id']]['depth'])]
 complete=Image.open(S/'background-native-v1.png').convert('RGBA')
 for state in ordered:complete.alpha_composite(images[state])
 complete.save(S/'complete-reassembled-v1.png')
 contract={'status':'authored configuration','geometry_mode':'silhouette-v2','ordinary_land_sites':16,'canvas':[800,374],'alpha_threshold':8,'background':ref(S/'background-native-v1.png'),'land_mask':save('land.png',land),'sites':sites,'frames':frames,'silhouette_plan':{'version':2,'support_mask':save('level-support.png',support),'stairs_mask':save('public-stairs.png',stairs),'water_mask':save('external-water.png',water),'paths_mask':save('connected-paths.png',tree),'states':plans,'overlaps':overlaps,'complete_scene':ref(S/'complete-reassembled-v1.png'),'complete_scene_states':ordered},'native_observed':False,'visual_approval_granted':False}
 contract_path=S/'layout-acceptance-contract-v2.json';dump(contract_path,contract)
 design=deepcopy(json.loads((P/'design/town-visuals.json').read_text()))
 design.update({'layout_geometry_mode':'silhouette-v2','layout_contract':ref(contract_path),'background':rel(S/'background-native-v1.png'),'sites':{s['id']:{'box':s['box'],'keys':s['states'],'z':s['depth'],'door':s['entrance']}for s in sites},'review':'Complete-city-first master derivation. Exact approved visible master pixels, genuine predecessor/hidden paintings; V2 masks are technical source annotations pending native/human review.'})
 # Earlier selected layout metadata is history, not this complete-city plan.
 design.pop('frozen_plan',None)
 design.update({'identity':'Piltover connected innovation quarter on an irregular civic headland; urban cobbled streets, right-edge eastern quay, brass-blue civic utility network and mercantile workshops.','complete_city_program':ref(S/'functional-program-v2.json'),'complete_city_master':ref(S/'complete-town-native-v2.png'),'plate_rules':[
  'Sixteen ordinary land sites and exactly seven troop-tier sites; all 35 states use independent full 800x374 frames',
  'Complete all-state silhouettes determine envelopes; bounded projected overlaps carry exact all-state masks',
  'Foreground forge, market and cargo architecture frames irregular middle and rear institutions in the reviewed complete city',
  'Actual foundation profiles meet level dry support; public stairs connect landings and doors have connected approaches',
  'Optional right-edge quay and moored ship share one coastal site with traced bounded hull support and dry access',
  'Optional Progress Orrery occupies its own central civic landing',
  'Painted absence terrain contains no completed functional architecture; early and developed views remain separate reviews',
  'Physical Piltover heraldry and blue/brass infrastructure follow the complete-city source'
 ],'special_sites':{identifier:{**design['sites'][identifier],'subject':next(site['identity']for site in program if site['id']==identifier)}for identifier in ('coast','grail')}})
 dump(S/'town-visuals.candidate-v2.json',design);dump(S/'town-structures.candidate-v2.json',town['structures'])
 dump(S/'native-content-geometry.candidate-v2.json',content)
 print(json.dumps({'ok':True,'states':len(frames),'sites':len(sites),'overlap_pairs':len(overlaps),'contract_sha256':sha(contract_path)}))
 return contract,content,design

if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--report-name',default='derivation-v1');args=parser.parse_args()
 if Path(args.report_name).name!=args.report_name:parser.error('report name must be one directory name')
 R=P/'build/reports/complete-town-20261027-v2'/args.report_name
 R.mkdir(parents=True,exist_ok=True)
 build()
