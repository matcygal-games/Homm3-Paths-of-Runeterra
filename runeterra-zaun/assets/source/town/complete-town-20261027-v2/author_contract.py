"""Source-only physical annotation and existing production converter candidate.

Masks are technical annotations; no architecture is drawn by this program.
Review the native overlay against the complete painted city before sealing.
"""
from pathlib import Path
import copy,hashlib,json,sys,shutil,collections,importlib.util
import numpy as np
from PIL import Image,ImageChops,ImageDraw,ImageFilter
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];REPORT=ROOT/'build/reports/complete-town-20261027-v2';PREFIX='Content/Sprites/runeterra/zaun/'
sys.path.insert(0,str(ROOT.parent/'scripts'));sys.path.insert(0,str(ROOT/'scripts'))
import faction_artifacts as compiler
import faction_town_layout as admission
sp=importlib.util.spec_from_file_location('contours',HERE/'visible_contours.py');ct=importlib.util.module_from_spec(sp);sp.loader.exec_module(ct)
sp=importlib.util.spec_from_file_location('contact_traces',HERE/'contact_traces.py');traces=importlib.util.module_from_spec(sp);sp.loader.exec_module(traces)
read=lambda p:json.loads(p.read_text(encoding='utf-8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);v.save(p,compress_level=9)
def ref(p):return {'path':rel(p),'sha256':sha(p)}
def mask():return Image.new('L',(800,374))
def binary(im,t=8):return im.getchannel('A').point(lambda v:255 if v>=t else 0)
def poly(points):m=mask();ImageDraw.Draw(m).polygon(points,fill=255);return m
def count(m):return m.histogram()[255]
DOOR_X={'foundryHall':217,'sumpRampart':470,'shimmerInstitute':634,'dwellingThug':212,'dwellingRavager':606,'dwellingConstruct':345,'dwellingEnforcer':62,'dwellingAgent':732,'dwellingVeteran':728,'dwellingPredator':366,'grog':347,'scrapExchange':548,'ammoFoundry':107,'shimmerFactory':165,'augmentationWorkshop':246,'augmentationClinic':377,'theSump':68,'fightingPit':489,'shipyard':708,'codeOfProgress':428}
REASON='Zaun preserves eighteen independently visible land institutions: seven tier dwellings, hall, fort, guild, tavern, market, forge, boiler silo, augmentation workshop, clinic, bounded Sump utility and fighting pit. Combining them would hide functional services and destroy the reviewed whole-city architecture; coast and Grail remain two optional sites.'
def make():
 plan=read(HERE/'derived-state-plan.json');families=read(HERE/'family-specs.json')['families'];rows=plan['states'];layers={r['state']:Image.open(ROOT/r['native_layer']).convert('RGBA') for r in rows};state_site={r['state']:r['site'] for r in rows}
 md=HERE/'physical';md.mkdir(exist_ok=True)
 water=poly([(571,373),(799,373),(799,273),(787,280),(753,293),(712,308),(683,319),(649,331),(614,342),(571,357)])
 land=ImageChops.invert(water)
 stairs=mask();ds=ImageDraw.Draw(stairs)
 for p in [[(486,142),(498,136),(509,150),(495,163)],[(559,226),(571,224),(583,244),(574,253)],[(535,288),(545,288),(558,309),(551,315)],[(123,181),(134,179),(148,195),(139,203)],[(484,169),(494,168),(477,191),(466,191)]]:ds.polygon(p,fill=255)
 allbody=mask();site_union={};site_body={}
 for f in families:
  u=mask();b=mask()
  for state in f['states']:u=ImageChops.lighter(u,binary(layers[state]));b=ImageChops.lighter(b,binary(layers[state],128));allbody=ImageChops.lighter(allbody,binary(layers[state],128))
  site_union[f['id']]=u;site_body[f['id']]=b;save(md/'sites'/(f['id']+'.png'),u)
 bodyarr=np.asarray(allbody)>0;landarr=np.asarray(land)>0
 support=mask();d=ImageDraw.Draw(support)
 # Traced level contact bands around actual painted foundation profiles. Stair
 # flights between courts and the external canal remain excluded explicitly.
 for f in families:
  name=f['id'];points=ct.GROUND_LIMITS.get(name)
  if points:d.polygon([(x,y-10) for x,y in points]+[(x,y+9) for x,y in reversed(points)],fill=255)
  elif name=='scrapExchange':d.polygon([(465,207),(493,212),(551,215),(604,211),(635,206),(635,230),(604,237),(551,239),(493,235),(465,230)],fill=255)
 # The smaller Chem-Jack loading hall has a rearward west return. Its actual
 # upper-yard floor is above the developed hall's front-edge band at that X.
 # This separately traced upper court preserves the complete wall contact.
 d.polygon([(560,181),(581,184),(599,190),(600,203),(560,202)],fill=255)
 # Dry stone quay and landward boarding beam; only the part on actual land
 # contributes level support. External water remains excluded below.
 d.polygon([(684,302),(734,291),(784,276),(791,286),(740,306),(689,319)],fill=255)
 support=ImageChops.subtract(ImageChops.multiply(support,land),stairs)
 physical={};diagnostics=[];doors=mask();root_by={}
 for row in rows:
  state=row['state'];sid=row['site'];im=layers[state];full=binary(im);bb=full.getbbox();points,entrance,apron=traces.TRACES[state]
  # Explicit independently editable source-pixel contact traces, not a percentage
  # of alpha bounds. Band includes wall/base thickness and is clipped to actual
  # source alpha; no source image/root is erased to obtain physical admission.
  foot=mask();ImageDraw.Draw(foot).line(points,fill=255,width=5);foot=ImageChops.multiply(foot,full)
  x,y=apron;direction=-1 if sid=='shipyard' else 1
  door=mask();ImageDraw.Draw(door).line([entrance,apron],fill=255,width=3);door=ImageChops.multiply(door,poly([(bb[0],bb[1]),(bb[2]-1,bb[1]),(bb[2]-1,bb[3]-1),(bb[0],bb[3]-1)]));doors=ImageChops.lighter(doors,door)
  root_by[state]=(x,y);physical[state]={'foundation':foot,'door':door,'entrance':list(entrance),'apron':[x,y],'direction':direction}
  diagnostics.append({'state':state,'site':sid,'entrance':list(entrance),'apron':[x,y],'ground_contact_polyline':points,'foundation_pixels':count(foot),'foundation_outside_level_support':count(ImageChops.subtract(foot,support)),'trace_source':ref(HERE/'contact_traces.py')})
 # Painted civic street corridors provide a bounded routing guide. BFS avoids
 # every actual body in every state; it cannot tunnel through another building.
 corridors=mask();dd=ImageDraw.Draw(corridors)
 routes=[[(2,82),(137,92),(145,118),(290,128),(440,143),(500,148),(570,138),(684,139)],[(140,120),(141,164),(145,190),(210,222),(330,214),(442,210),(503,226),(608,225),(682,222),(736,227)],[(497,148),(479,180),(444,205)],[(572,227),(582,251),(575,274),(557,298),(578,327),(571,345)],[(130,195),(154,222),(190,242),(208,272),(220,315),(245,336),(386,340),(489,349),(573,346),(664,312),(720,302),(791,281)],[(3,329),(108,331),(242,338)],[(3,84),(4,180),(140,189)]]
 for points in routes:dd.line(points,fill=255,width=15)
 # Each actual level court joins its local frontage to the pictured street.
 for f in families:
  name=f['id'];bb=site_union[name].getbbox();dd.rectangle((max(0,bb[0]-7),max(0,bb[3]-14),min(799,bb[2]+7),min(373,bb[3]+16)),fill=255)
 allowed=(np.asarray(corridors)>0)&landarr&~bodyarr
 # Doors do not make the global network pass through a facade: the street starts
 # in the first physically free pixel immediately in front of each actual root.
 targets=[(x,y+physical[state]['direction']) for state,(x,y) in root_by.items()]
 start=(446,214)
 if not allowed[start[1],start[0]]:
  points=np.argwhere(allowed);y,x=min(points,key=lambda p:abs(int(p[0])-214)+abs(int(p[1])-446));start=(int(x),int(y))
 q=collections.deque([start]);parent={start:None}
 while q:
  x,y=q.popleft()
  for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
   if 0<=xx<800 and 0<=yy<374 and allowed[yy,xx] and (xx,yy)not in parent:parent[(xx,yy)]=(x,y);q.append((xx,yy))
 paths=mask();dp=ImageDraw.Draw(paths);unreachable=[]
 for state,target in zip(root_by,targets):
  if target not in parent:unreachable.append({'state':state,'target':target});continue
  p=target
  while p is not None:paths.putpixel(p,255);p=parent[p]
  approach=mask();approach.putpixel(target,255);physical[state]['approach']=approach
 if unreachable:
  write(REPORT/'physical-routing-failures.json',{'unreachable':unreachable,'root_annotations':diagnostics});save(REPORT/'routing-allowed.png',Image.fromarray(allowed.astype('uint8')*255));raise ValueError('Unreachable actual level-court doors: '+str(unreachable))
 for key,value in [('land',land),('support',support),('stairs',stairs),('water',water),('paths',paths)]:save(md/(key+'.png'),value)
 states={}
 for row in rows:
  state=row['state'];p=physical[state];folder=md/'states'/state
  for key in ('foundation','door','approach'):save(folder/(key+'.png'),p[key])
  save(folder/'body.png',binary(layers[state],128));record={key+'_mask':ref(folder/(key+'.png')) for key in ('foundation','door','approach','body')};record.update({'entrance':p['entrance'],'access_kind':'open-site' if row['site']in('theSump','fightingPit','scrapExchange','codeOfProgress') else 'door'})
  if row['site']=='shipyard':
   contact=ImageChops.lighter(p['foundation'],ImageChops.lighter(p['door'],p['approach']));marine=ImageChops.multiply(ImageChops.multiply(contact,binary(layers[state])),water);save(folder/'marine.png',marine);record.update({'marine_support_mask':ref(folder/'marine.png'),'marine_support_kind':'moored-hull' if state=='ship' else 'deck-and-pilings','access_kind':'moored-vessel'})
  states[state]=record
 sites=[];overlaps=[]
 for f in families:
  sid=f['id'];bb=site_union[sid].getbbox();sites.append({'id':'coast' if sid=='shipyard' else 'grail' if sid=='codeOfProgress' else sid,'box':[bb[0],bb[1],bb[2]-bb[0],bb[3]-bb[1]],'depth':ct.DEPTHS[sid],'states':f['states'],'entrance':root_by[f['states'][-1]],'intentional_water':sid=='shipyard','silhouette_mask':ref(md/'sites'/(sid+'.png'))})
 for i,a in enumerate(families):
  for b in families[i+1:]:
   aa,bb=sorted((a['id'],b['id']),key=lambda k:ct.DEPTHS[k]);intersection=ImageChops.multiply(site_union[aa],site_union[bb])
   if intersection.getbbox():
    p=md/'overlaps'/(aa+'--'+bb+'.png');save(p,intersection);overlaps.append({'behind':'coast' if aa=='shipyard' else 'grail' if aa=='codeOfProgress' else aa,'front':'coast' if bb=='shipyard' else 'grail' if bb=='codeOfProgress' else bb,'mask':ref(p),'reason':'Actual bounded projected architectural overlap in the reviewed whole-city painting; separate supported courts and all actual doors/frontages remain exposed.'})
 brief=HERE/'SITE_BUDGET.txt';brief.write_text(REASON+'\n',encoding='utf-8')
 full=Image.open(ROOT/plan['background']).convert('RGBA');order=[]
 for f in sorted(families,key=lambda f:ct.DEPTHS[f['id']]):order.append(f['states'][-1]);full.alpha_composite(layers[order[-1]])
 save(HERE/'complete-reassembly.png',full)
 # Exact all-state projected roots are retained, never erased to pass a test.
 # These source cases require coordinator pixel review of the separate courts.
 levels={
  ('dwellingRavager','scrapExchange'):('Chem-Jack upper loading court behind the market','Market stall court below the eastern loading frontage'),
  ('dwellingConstruct','augmentationClinic'):('Pressure-cell court at the west edge of the clinic block','Clinic lower frontage and east return wall'),
  ('dwellingPredator','foundryHall'):('Pressure augmentation rear foundry terrace','Civic clock-hall front terrace and east return'),
  ('dwellingPredator','sumpRampart'):('Pressure augmentation rear foundry terrace','Defended gate front terrace and west return'),
  ('augmentationWorkshop','dwellingConstruct'):('Workshop upper west return and loading threshold','Pressure-cell lower frontage and west return'),
  ('augmentationWorkshop','ammoFoundry'):('Workshop upper west return and loading threshold','Forge lower west workyard and eastern return'),
  ('augmentationClinic','fightingPit'):('Clinic raised west frontage and east return','Fighting-pit lower gathering court and western return')}
 foundation_cases=[]
 for (behind,front),(rear_level,front_level) in levels.items():
  rear=mask();frontbody=mask()
  for state in next(f['states'] for f in families if f['id']==behind):rear=ImageChops.lighter(rear,physical[state]['foundation'])
  for state in next(f['states'] for f in families if f['id']==front):frontbody=ImageChops.lighter(frontbody,binary(layers[state],128))
  hidden=ImageChops.multiply(rear,frontbody)
  if not hidden.getbbox():continue
  folder=md/'foundation-projections'/(behind+'--'+front);save(folder/'intersection.png',hidden)
  absent=Image.open(ROOT/plan['background']).convert('RGBA')
  for f in sorted(families,key=lambda f:ct.DEPTHS[f['id']]):
   if f['id']!=front:absent.alpha_composite(layers[f['states'][-1]])
  save(folder/'complete-native.png',full);save(folder/'front-absent-native.png',absent)
  overlay=full.copy();tint=Image.new('RGBA',full.size,(255,0,255,0));tint.putalpha(hidden);overlay.alpha_composite(tint);save(folder/'intersection-overlay.png',overlay)
  reason='Bounded non-access projected root edge between separately supported city courts: '+behind+' behind '+front+'. Doors and their dry approaches remain fully exposed in every state; source-pixel review remains required.'
  case={'kind':'supported-terrace-projection','behind':behind,'front':front,'behind_depth':ct.DEPTHS[behind],'front_depth':ct.DEPTHS[front],'rear_level':rear_level,'front_level':front_level,'reason':reason,'hidden_pixels':count(hidden),'hidden_bounds':list(hidden.getbbox()),'mask_sha256':sha(folder/'intersection.png'),'coordinator_visual_review':'pending'}
  write(folder/'source-case.json',case)
  foundation_cases.append({'behind':behind,'front':front,'reason':reason,'mask':ref(folder/'intersection.png'),'source_case':ref(folder/'source-case.json'),'evidence':{'complete_scene':ref(folder/'complete-native.png'),'front_absent_scene':ref(folder/'front-absent-native.png'),'intersection_overlay':ref(folder/'intersection-overlay.png')}})
 contract={'geometry_mode':'silhouette-v2','canvas':[800,374],'alpha_threshold':8,'ordinary_land_sites':18,'site_budget_exception':REASON,'site_budget_brief':ref(brief),'background':ref(ROOT/plan['background']),'land_mask':ref(md/'land.png'),'frames':{r['state']:ref(ROOT/r['native_layer']) for r in rows},'sites':sites,'silhouette_plan':{'version':2,'support_mask':ref(md/'support.png'),'stairs_mask':ref(md/'stairs.png'),'water_mask':ref(md/'water.png'),'paths_mask':ref(md/'paths.png'),'states':states,'overlaps':overlaps,'complete_scene':ref(HERE/'complete-reassembly.png'),'complete_scene_states':order}}
 contract['silhouette_plan']['foundation_occlusions']=foundation_cases
 contract['physical_trace_source']=ref(HERE/'contact_traces.py')
 write(HERE/'town-layout.json',contract);write(REPORT/'physical-annotation-diagnostics.json',diagnostics)
 overlay=full.copy()
 for annotation,color in [(water,(30,80,255)),(support,(0,255,80)),(stairs,(255,0,0)),(paths,(255,255,0))]:t=Image.new('RGBA',full.size,(*color,0));t.putalpha(annotation.point(lambda v:120 if v else 0));overlay.alpha_composite(t)
 for state,p in physical.items():ImageDraw.Draw(overlay).ellipse((p['entrance'][0]-2,p['entrance'][1]-2,p['entrance'][0]+2,p['entrance'][1]+2),fill='white')
 save(REPORT/'physical-annotation-overlay.png',overlay)
 print('Authored candidate physical contract; source pixel review and actual inspection still required.',flush=True)
if __name__=='__main__':make()
