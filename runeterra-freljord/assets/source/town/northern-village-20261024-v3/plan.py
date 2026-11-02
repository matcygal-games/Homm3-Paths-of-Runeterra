"""Prepaint whole-master Freljord village plan; no active selection or staging."""
from pathlib import Path
import hashlib,importlib.util,json,itertools
from PIL import Image,ImageOps,ImageChops,ImageDraw,ImageFilter
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
REPORT=ROOT/'build/reports/northern-village-20261024-v3'
spec=importlib.util.spec_from_file_location('freljord_town_helper',ROOT/'scripts/prepare_town_art.py');art=importlib.util.module_from_spec(spec);spec.loader.exec_module(art)
RECTS={
 'dwelling-tier-7':[3,93,119,94],
 'civic-hall':[224,40,201,137],
 'fortifications':[578,43,215,130],
 'mage-guild':[430,48,141,132],
 'thunder-temple':[134,94,84,78],
 'true-ice-quarry':[569,213,166,56],
 'optional-coast':[693,180,104,48],
 'dwelling-tier-3':[3,194,118,85],
 'anivia-shrine':[134,174,91,74],
 'dwelling-tier-5':[267,193,122,89],
 'dwelling-tier-4':[398,190,132,79],
 'forge':[528,183,83,65],
 'dwelling-tier-1':[3,289,110,72],
 'tavern-hall':[119,256,156,102],
 'market':[320,280,111,73],
 'dwelling-tier-6':[451,279,153,79],
 'dwelling-tier-2':[627,269,169,89],
}
ROAD=[(418,373),(426,349),(435,321),(434,297),(423,280),(405,270),(381,264),(368,248),(367,228),(378,209),(397,194),(422,186),(444,185),(480,189),(521,189),(554,184),(586,181),(626,180),(663,182),(683,184)]
WATER=[[777,190],[800,190],[800,246],[775,242],[762,225],[768,208]]
# Actual front doors/steps, normalized in unmirrored full-alpha crop; altar,
# natural roost landing and pen gate are explicit alternatives to a human door.
ENTRY={
 'dwelling-tier-7':(.47,.70,.47,.98,'natural landing ledge and ridge approach'),
 'civic-hall':(.48,.78,.48,.99,'communal hall doorway and front steps'),
 'fortifications':(.46,.78,.46,.99,'palisade gate and whole angled timber bases'),
 'mage-guild':(.50,.80,.50,.99,'planned northern ritual hall doorway; new family pending'),
 'thunder-temple':(.47,.80,.47,.99,'Frostguard vigil entry'),
 'true-ice-quarry':(.44,.84,.44,.99,'working crane yard entrance and stone loading base'),
 'optional-coast':(.18,.76,.16,.99,'landward pier/quay approach; boat intentionally overwater'),
 'dwelling-tier-3':(.46,.75,.46,.99,'troll cave mouth and packed-earth apron'),
 'anivia-shrine':(.49,.85,.49,.99,'offering altar ground approach'),
 'dwelling-tier-5':(.43,.80,.43,.99,'winter diviner hall doorway'),
 'dwelling-tier-4':(.48,.80,.48,.99,'Frostguard/Draklorn house entry'),
 'forge':(.44,.79,.44,.99,'working forge and supply entrance'),
 'dwelling-tier-1':(.32,.80,.32,.99,'poro shelter yard gate'),
 'tavern-hall':(.48,.80,.48,.99,'hearth hall/tavern front steps'),
 'market':(.49,.83,.49,.99,'communal market frontage'),
 'dwelling-tier-6':(.49,.84,.49,.99,'druvask stockade gate'),
 'dwelling-tier-2':(.29,.78,.29,.99,'hunter lodge front doorway'),
}
OVERRIDES={'villageHall':(.50,.81,.50,.99),'townHall':(.42,.78,.42,.99),'cityHall':(.39,.80,.39,.99),'capitol':(.42,.80,.42,.99),'dwellingUpLvl1':(.34,.80,.34,.99),'dwellingLvl2':(.30,.80,.30,.99),'special1':(.40,.80,.40,.99)}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def mask(im,t=128):return im.getchannel('A').point(lambda a:255 if a>=t else 0)
def count(im):return sum(im.histogram()[128:])
def main():
 REPORT.mkdir(parents=True,exist_ok=True)
 old=art.read(ROOT/'design/building-layout.json');selector=art.read(ROOT/'assets/production/town/community-selection-v2.json');rows=[];layers={};sites=[]
 mirrors=set()
 for site in old['sites']:
  s=dict(site);s['rect']=RECTS[site['id']];s['z']=s['rect'][1]+s['rect'][3]
  s['state_rects']={}
  if s['id']=='civic-hall':
   x,y,w,h=s['rect'];bottom=y+h
   for state,width,height in [('villageHall',124,84),('townHall',150,103),('cityHall',178,121)]:s['state_rects'][state]=[x+(w-width)//2,bottom-height,width,height]
   s['state_rects']['grail']=[405,126,19,51]
  if s['id']=='dwelling-tier-7':s['state_rects']['dwellingLvl7']=[18,110,89,77]
  s.update(ground_contact_rect=[s['rect'][0],s['rect'][1]+s['rect'][3]-10,s['rect'][2],10],state_geometry_note='Complete genuine painted master uniform contain, no camera/perspective warp; much larger rear institutions allocated before backdrop painting.',physical_role='large rear village institution' if s['id'] in ('civic-hall','fortifications','mage-guild') else 'domestic/service/ritual village site')
  sites.append(s)
  for state in s['states']:
   selected=selector['states'][state];master=ROOT/selected['master']['path'];assert sha(master)==selected['master']['sha256']
   im=art.load_rgba(master)
   if s['id'] in mirrors:im=ImageOps.mirror(im)
   rect=s['state_rects'].get(state,s['rect']);native,conv=art.place(im,rect);layers[state]=native
   full=mask(native,1);solid=mask(native);a,b,c,d,kind=ENTRY[s['id']]
   if state in OVERRIDES:a,b,c,d=OVERRIDES[state]
   if s['id'] in mirrors:a,c=1-a,1-c
   ox,oy=conv['placed_origin'];pw,ph=conv['placed_size'];door=[ox+round(a*pw),oy+round(b*ph)];exit=[ox+round(c*pw),oy+round(d*ph)]
   if state=='grail':door=exit=[ox+pw//2,oy+ph-1];kind='Grail is simultaneous civic ornament, not a hall replacement; no separate doorway'
   footprint=full.copy();bb=solid.getbbox();footprint.paste(0,(0,0,800,max(0,bb[3]-10)))
   folder=HERE/'planned'/state;folder.mkdir(parents=True,exist_ok=True);native.save(folder/'layer.png');footprint.save(folder/'foundation.png')
   row={'state':state,'site':s['id'],'land':s['land'],'master':rel(master),'master_sha256':sha(master),'generation_record':rel(master.parent/'generation.json'),'generation_record_sha256':sha(master.parent/'generation.json'),'conversion':conv,'rect':rect,'z':s['z']+(1 if state=='grail' else 0),'mirror_x':s['id'] in mirrors,'full_alpha_bbox':list(full.getbbox()),'solid_bbox':list(bb),'alpha1_pixels':count(full),'solid_pixels':count(solid),'native_layer':rel(folder/'layer.png'),'native_layer_sha256':sha(folder/'layer.png'),'entrance':{'door_point':door,'front_exit_point':exit,'front_apron':[exit[0]-8,exit[1],16,10],'facing':[0,1],'kind':kind,'scope':'Proposed painted source contact and apron; actual road support pending genuine backdrop and pixel review, not native navigation.'},'pending_master_change':'Replace mismatching pagoda with genuine painted northern ritual-guild family inside this entire reserved rectangle' if state.startswith('mageGuild') else 'Coordinator crest-only communal hall edit, complete architecture preserved' if state in ('villageHall','townHall','cityHall','capitol') else None}
   rows.append(row)
 overlaps=[]
 for a,b in itertools.combinations(rows,2):
  if a['site']==b['site']:continue
  for t in (1,128):
   n=count(ImageChops.multiply(mask(layers[a['state']],t),mask(layers[b['state']],t)))
   if n:overlaps.append({'states':[a['state'],b['state']],'threshold':t,'pixels':n})
 apron_hits=[]
 for a in rows:
  if a['state']=='grail' or not a['land']:continue
  x,y,w,h=a['entrance']['front_apron'];apron=Image.new('L',(800,374));ImageDraw.Draw(apron).rectangle((x,y,x+w-1,y+h-1),fill=255)
  for b in rows:
   if a['site']==b['site']:continue
   n=count(ImageChops.multiply(apron,mask(layers[b['state']],128)))
   if n:apron_hits.append({'entrance':a['state'],'obstruction':b['state'],'pixels':n})
 water=Image.new('L',(800,374));ImageDraw.Draw(water).polygon(WATER,fill=255);water.save(HERE/'planned-water.png')
 document={'status':'design proposal','canvas':[800,374],'site_count':17,'ordinary_land_sites':16,'optional_coast_sites':1,'sites':sites,'states':rows,'water_polygon':WATER,'road_spine':ROAD,'collision_results':overlaps,'entrance_apron_obstructions':apron_hits,'same_site_semantics':{'civic-hall':'Grail additive ornament; test every hall+Grail combination. Hall chain replaces itself.','forge':'special1 upgrades blacksmith','tavern-hall':'special4 upgrades tavern','optional-coast':'ship replaces shipyard and contains both dock and boat'},'identity':'Inhabited small northern Freljord timber/snow village at pale winterbluehour with visible aurora, warm hearths, practical snowpacked paths and occupied incidental cottages. No brightdaylight/nightblack mismatch, uniformdisplaypads, isometricgrid or continuousparallelterracebands.','master_policy':'Existing painted master bytes preserved except explicitly approved northern guild replacement and genuine crest-only communal-hall edits; former inputs retained as history.','native_verified':False,'visual_approval_granted':False}
 write(HERE/'placement-plan.json',document)
 bg=Image.new('RGBA',(800,374),(64,69,76,255));draw=ImageDraw.Draw(bg);draw.polygon(WATER,fill=(39,74,97));draw.line(ROAD,fill=(170,156,128),width=13)
 chosen=[]
 for s in sites:
  if not s['land']:continue
  opts=[x for x in s['states'] if x!='grail'];state=opts[-1];chosen.append(state)
  e=next(r for r in rows if r['state']==state)['entrance']['front_exit_point'];target=min(ROAD,key=lambda p:(p[0]-e[0])**2+(p[1]-e[1])**2);draw.line([tuple(e),target],fill=(170,156,128),width=9)
 for state in sorted(chosen,key=lambda st:next(r['z'] for r in rows if r['state']==st)):bg.alpha_composite(layers[state])
 bg.save(REPORT/'placement-buildings-native.png');draw=ImageDraw.Draw(bg)
 for state in chosen:
  r=next(r for r in rows if r['state']==state);draw.rectangle(r['full_alpha_bbox'],outline=(240,185,85));x,y=r['entrance']['front_exit_point'];draw.ellipse((x-2,y-2,x+2,y+2),fill=(60,245,225))
 bg.save(REPORT/'placement-footprints-native.png')
 print(json.dumps({'states':len(rows),'sites':len(sites),'collisions':len(overlaps),'plan_sha256':sha(HERE/'placement-plan.json')}))
if __name__=='__main__':main()
