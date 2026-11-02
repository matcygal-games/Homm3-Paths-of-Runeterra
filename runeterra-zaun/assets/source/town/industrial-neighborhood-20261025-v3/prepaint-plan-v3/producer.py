"""Technical whole-master prepaint plan. Diagram strokes are guides, never game art."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageOps,ImageChops,ImageDraw
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
REPORT=ROOT/'build/reports/industrial-neighborhood-20261025-v3'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
RECTS={
 'foundryHall':[195,7,170,133],'sumpRampart':[5,19,155,133],
 'shimmerInstitute':[420,30,113,146],'dwellingPredator':[615,9,174,141],
 'shimmerFactory':[537,79,79,84], 'codeOfProgress':[366,112,45,61],
 'dwellingEnforcer':[8,158,117,91],'augmentationWorkshop':[143,142,111,91],
 'augmentationClinic':[273,156,82,64], 'theSump':[452,177,100,88],
 'dwellingVeteran':[564,180,105,92],'dwellingAgent':[669,154,126,92],
 'scrapExchange':[347,198,100,65],
 'dwellingThug':[4,249,148,104],'dwellingRavager':[161,247,132,85],
 'grog':[300,282,130,78],'fightingPit':[435,271,100,77],
 'dwellingConstruct':[543,291,110,69],'ammoFoundry':[668,251,95,65],
 'shipyard':[706,318,89,42]}
# Relative measured front threshold/stair-foot X in the WHOLE cropped master;
# the visible contact Y is measured from each final native alpha silhouette.
ENTRY_X={'villageHall':.37,'townHall':.29,'cityHall':.38,'capitol':.39,
 'fort':.51,'citadel':.50,'castle':.50,'mageGuild1':.51,'mageGuild2':.54,
 'mageGuild3':.51,'mageGuild4':.51,'dwellingLvl1':.40,'dwellingUpLvl1':.43,
 'dwellingLvl2':.53,'dwellingUpLvl2':.48,'dwellingLvl3':.47,'dwellingUpLvl3':.51,
 'dwellingLvl4':.47,'dwellingUpLvl4':.47,'dwellingLvl5':.46,'dwellingUpLvl5':.45,
 'dwellingLvl6':.59,'dwellingUpLvl6':.58,'dwellingLvl7':.43,'dwellingUpLvl7':.43,
 'tavern':.48,'marketplace':.63,'blacksmith':.55,'resourceSilo':.62,
 'grail':.53,'special1':.53,'special2':.66,'special3':.95,'special4':.48,
 'shipyard':.16,'ship':.16}
ENTRY_Y={'villageHall':.94,'townHall':.96,'cityHall':.97,'capitol':.97,
 'fort':.94,'citadel':.95,'castle':.96,'mageGuild1':.95,'mageGuild2':.96,
 'mageGuild3':.96,'mageGuild4':.97,'dwellingLvl1':.91,'dwellingUpLvl1':.91,
 'dwellingLvl2':.95,'dwellingUpLvl2':.94,'dwellingLvl3':.94,'dwellingUpLvl3':.94,
 'dwellingLvl4':.93,'dwellingUpLvl4':.93,'dwellingLvl5':.96,'dwellingUpLvl5':.96,
 'dwellingLvl6':.97,'dwellingUpLvl6':.97,'dwellingLvl7':.97,'dwellingUpLvl7':.97,
 'tavern':.95,'marketplace':.94,'blacksmith':.96,'resourceSilo':.95,
 'grail':.97,'special1':.94,'special2':.95,'special3':.73,'special4':.96,
 'shipyard':.37,'ship':.37}
MIRROR=set()
BOAT_RECT=[745,337,51,30]
NATIVE_Z={'dwellingConstruct':359,'shipyard':361}
def write(p,data):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def fit(im,rect):
 x,y,w,h=rect;small=ImageOps.contain(im,(w-4,h-4),Image.Resampling.LANCZOS)
 xy=(x+(w-small.width)//2,y+h-2-small.height)
 layer=Image.new('RGBA',(800,374));layer.alpha_composite(small,xy)
 return layer,small.size,xy
def main():
 old=read(ROOT/'assets/source/town/painted-community-20261024-v1/coordinator-handoff.json')
 layout=read(ROOT/'design/town-visuals.json');by={r['state']:r for r in old['states']}
 rows=[];layers={};siteof={};sites=[]
 for site in layout['sites']:
  sid=site['id'];rect=RECTS[sid];sr=[]
  for state in site['buildings']:
   orig=by[state];p=ROOT/orig['master'];assert sha(p)==orig['master_sha256']
   im=Image.open(p).convert('RGBA').crop(orig['source_crop'])
   if sid in MIRROR:im=ImageOps.mirror(im)
   layer,size,xy=fit(im,rect)
   if state=='ship':
    boat,_,_=fit(im,BOAT_RECT);layer=layers['shipyard'].copy();layer.alpha_composite(boat)
   alpha=layer.getchannel('A');box=alpha.getbbox();solid=alpha.point(lambda a:255 if a>=128 else 0).getbbox()
   dx=ENTRY_X[state];dx=1-dx if sid in MIRROR else dx
   ex=round(xy[0]+size[0]*dx)
   ey=round(xy[1]+size[1]*ENTRY_Y[state])
   if state=='ship':
    dock=next(r for r in sr if r['state']=='shipyard');ex,ey=dock['front_exit']
   apron=[ex-9,ey,ex+9,ey+11]
   footing=alpha.copy();keep=Image.new('L',(800,374));ImageDraw.Draw(keep).rectangle([box[0],round(box[1]+(box[3]-box[1])*.72),box[2],box[3]],fill=255);footing=ImageChops.multiply(footing,keep)
   row={**orig,'site':sid,'composition_rectangle':rect,'native_z':NATIVE_Z.get(sid,rect[1]+rect[3]),
    'whole_master_sha256':sha(p),'mirror_x':sid in MIRROR,'native_size':list(size),'native_offset':list(xy),
    'full_alpha_bbox':list(box),'solid_bbox':list(solid),'front_exit':[ex,ey],
    'door_facing':'front/southwest' if sid not in MIRROR else 'front/southeast',
    'visible_front_apron':apron,'contact_measurement':'Measured native threshold or front stair foot; source-relative fractions explicit, not plot bottom surrogate.',
    'foundation_rule':'All visible lower-body foundation pixels plus contact shadows require supported floor; Sump interior basin and coastal dock piles are intentional liquid structures.',
    'native_layer':f'{HERE.relative_to(ROOT).as_posix()}/layers/{state}.png'}
   out=ROOT/row['native_layer'];out.parent.mkdir(parents=True,exist_ok=True);layer.save(out,compress_level=9)
   footing.save(out.with_name(state+'-foundation.png'),compress_level=9)
   row['foundation_mask']=out.with_name(state+'-foundation.png').relative_to(ROOT).as_posix();row['foundation_mask_sha256']=sha(ROOT/row['foundation_mask'])
   row['click_bbox']=list(solid);row['click_pixels']=alpha.point(lambda a:255 if a>=128 else 0).histogram()[255]
   row['footing_water_pixels']=None;row['footing_outside_buildable_floor_pixels']=None
   row['terrain_support_status']='unassessed: new background is not painted; declared plot/door guides only'
   row['native_layer_sha256']=sha(out);rows.append(row);sr.append(row);layers[state]=layer;siteof[state]=sid
  sites.append({'id':sid,'states':site['buildings'],'composition_rectangle':rect,'native_z':NATIVE_Z.get(sid,rect[1]+rect[3]),
   'full_replacement_envelope':list(ImageChops.lighter(*[layers[s].getchannel('A') for s in site['buildings'][:2]]).getbbox()) if len(site['buildings'])==2 else [min(r['full_alpha_bbox'][0] for r in sr),min(r['full_alpha_bbox'][1] for r in sr),max(r['full_alpha_bbox'][2] for r in sr),max(r['full_alpha_bbox'][3] for r in sr)]})
 collisions=[];names=list(layers)
 for i,a in enumerate(names):
  for b in names[i+1:]:
   if siteof[a]==siteof[b]:continue
   for threshold in [1,128]:
    aa=layers[a].getchannel('A').point(lambda v:255 if v>=threshold else 0);bb=layers[b].getchannel('A').point(lambda v:255 if v>=threshold else 0)
    hit=ImageChops.multiply(aa,bb);n=hit.histogram()[255]
    if n:collisions.append({'states':[a,b],'alpha_threshold':threshold,'pixels':n})
 apronbad=[r['state'] for r in rows if r['visible_front_apron'][0]<0 or r['visible_front_apron'][2]>800 or r['visible_front_apron'][3]>374]
 apronhits=[]
 for row in rows:
  m=Image.new('L',(800,374));ImageDraw.Draw(m).rectangle(row['visible_front_apron'],fill=255)
  for other in rows:
   if row['site']==other['site']:continue
   hit=ImageChops.multiply(m,layers[other['state']].getchannel('A').point(lambda a:255 if a>=128 else 0));n=hit.histogram()[255]
   if n:apronhits.append({'entrance':row['state'],'obstruction':other['state'],'pixels':n})
 plan={'status':'design proposal','canvas':[800,374],'siteCount':20,'stateCount':36,
  'masters_preserved':True,'sites':sites,'states':rows,'source_layout_sha256':sha(ROOT/'design/town-visuals.json'),
  'collision_findings':collisions,'offcanvas_aprons':apronbad,'apron_solid_obstructions':apronhits,'boat_rectangle':BOAT_RECT,
  'coast_semantics':old['coast_semantics'],'grail_semantics':'Independent grounded ornament site; additive, never a Hall replacement.',
  'route_guidance':'Organic tapered industrial street spine and diagonal small shared courts; painter must create true level paved support under every visible threshold and all replacement footprints. No straight terrace bands or rectangular fenced lots.',
  'water_plan':'Narrow deliberate lower-right dock inlet only under moored hull; all other full foundations/approaches dry. Sump intrinsic green containment basin remains its own authored building pixels.',
  'planned_inlet_polygon':[[744,340],[752,332],[799,325],[799,373],[714,373],[719,355],[743,348]],
  'native_z_overrides':NATIVE_Z,
  'background_painted':False,'native_verified':False,'release_accepted':False}
 write(HERE/'placement-plan.json',plan)
 for variant in ['base','upgraded','grail','moored']:
  canvas=Image.new('RGBA',(800,374),(48,44,44,255))
  for site in sorted(sites,key=lambda s:s['native_z']):
   sid=site['id'];ss=site['states']
   state=ss[0 if variant=='base' else -1]
   if sid=='codeOfProgress' and variant!='grail':continue
   if sid=='shipyard' and variant not in ['moored','grail']:continue
   canvas.alpha_composite(layers[state])
  canvas.convert('RGB').save(REPORT/f'placement-{variant}-native.png')
  if variant=='upgraded':
   guide=canvas.copy();d=ImageDraw.Draw(guide)
   for s in sites:
    r=next(r for r in rows if r['state']==s['states'][-1]);d.rectangle(r['full_alpha_bbox'],outline=(225,110,90));d.rectangle(r['visible_front_apron'],outline=(60,220,210));d.text((r['full_alpha_bbox'][0],r['full_alpha_bbox'][1]),s['id'],fill='white')
   guide.save(REPORT/'placement-guide-native.png')
  if variant=='moored':
   shore=canvas.copy();dd=ImageDraw.Draw(shore);dd.line(plan['planned_inlet_polygon']+[plan['planned_inlet_polygon'][0]],fill=(60,220,255),width=1)
   for r in rows:
    if r['site']=='shipyard':dd.rectangle(r['visible_front_apron'],outline=(240,190,70))
   shore.save(REPORT/'placement-coast-guide-native.png')
 print(json.dumps({'plan_sha256':sha(HERE/'placement-plan.json'),'collisions':collisions,'offcanvas_aprons':apronbad,'apron_solid_obstructions':apronhits,'states':len(rows),'sites':len(sites)}))
if __name__=='__main__':main()
