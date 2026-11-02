"""Finite town placement plan BEFORE backdrop painting. Never selects active assets."""
from pathlib import Path
from collections import deque
import hashlib,json
from PIL import Image,ImageOps,ImageChops,ImageDraw,ImageFilter

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
REPORT=ROOT/'build/reports/urban-town-community-20261024-v6'
OLD=ROOT/'assets/source/town/urban-community-20261024-v5'
SITES={
 'throneHall':[323,10,145,132],
 'crownBastion':[657,4,135,127],
 'arcaneAthenaeum':[121,78,112,120],
 'dwellingLegion':[1,235,151,133],
 'dwellingHound':[158,233,116,112],
 'dwellingAxe':[460,276,126,94],
 'dwellingRose':[5,147,109,82],
 'dwellingCrimson':[239,122,118,104],
 'dwellingMinotaur':[665,185,127,85],
 'bindingRift':[490,42,133,114],
 'gildedCup':[287,244,145,111],
 'grandMarket':[228,40,93,67],
 'foundry':[639,271,142,99],
 'crimsonCitadel':[596,117,65,80],
 'shipyard':[752,132,48,35],
 'grail':[625,54,29,87],
 'blackRoseAcademy':[4,20,110,119],
 'trifarianHall':[395,159,116,90],
 'arenaOfValor':[516,191,111,83],
}
# Design-only geometry, not painted roads. Continuous organic trunk with branches;
# backed by obstacle-avoiding per-state apron paths in the finite JSON packet.
TRUNK=[(446,373),(446,341),(446,314),(449,292),(472,278),(490,270),(500,253),(510,233),(516,212),(514,191),(493,171),(471,158),(447,149),(426,145),(404,145),(383,151)]
WATER=[[800,151],[792,157],[787,174],[788,195],[800,203]]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def binary(im,t=1):return im.getchannel('A').point(lambda a:255 if a>=t else 0)
def count(im):return sum(im.histogram()[128:])
def fit(im,rect,mirror):
 if mirror:im=ImageOps.mirror(im)
 bb=binary(im,8).getbbox();crop=im.crop(bb)
 size=ImageOps.contain(crop,(rect[2]-4,rect[3]-4),Image.Resampling.LANCZOS)
 xy=[rect[0]+(rect[2]-size.width)//2,rect[1]+rect[3]-2-size.height]
 out=Image.new('RGBA',(800,374));out.alpha_composite(size,xy)
 return out,list(bb),xy,list(size.size)
def main():
 REPORT.mkdir(parents=True,exist_ok=True)
 old=json.loads((OLD/'selection.json').read_text());entrances=json.loads((OLD/'entrance-plan.json').read_text())
 rows=[];layers={};solid_union=Image.new('L',(800,374));foundation_union=Image.new('L',(800,374))
 for prev in old['states']:
  r=dict(prev);state=r['state'];rect=SITES[r['site']];master=ROOT/r['master']
  assert sha(master)==r['master_sha256'],('preserved-master-mismatch',state)
  im,crop,xy,size=fit(Image.open(master).convert('RGBA'),rect,r['mirror_x']);layers[state]=im
  entry=dict(entrances['sites'][r['site']]);entry.update(entrances['state_overrides'].get(state,{}))
  for key in ('door','stair','exit'):
   fx,fy=entry[key]
   if r['mirror_x']:fx=1-fx
   entry[key+'_point']=[xy[0]+round(fx*size[0]),xy[1]+round(fy*size[1])]
  entry.pop('approach',None);entry.pop('approach_polyline',None)
  solid=binary(im,128);allalpha=binary(im,1);bb=solid.getbbox();foundation=allalpha.copy()
  foundation.paste(0,(0,0,800,bb[3]-10));foundation_union=ImageChops.lighter(foundation_union,foundation)
  solid_union=ImageChops.lighter(solid_union,solid)
  row={k:r[k] for k in ('state','site','master','master_sha256','generation_record','generation_record_sha256','mirror_x')}
  row.update(composition_rectangle=rect,native_position=xy,native_size=size,source_crop=crop,native_z=rect[1]+rect[3],full_alpha_bbox=list(allalpha.getbbox()),solid_bbox=list(bb),full_alpha_pixels=count(allalpha),solid_pixels=count(solid),shadow_included=True,foundation={'basis':'Full alpha including contact shadow, lower 10 native pixels','bbox':list(foundation.getbbox()),'pixels':count(foundation)},entrance=entry,depth='near' if rect[1]>210 else 'middle' if rect[1]>120 else 'far')
  rows.append(row)
  folder=HERE/'planned-structures'/state;folder.mkdir(parents=True,exist_ok=True)
  im.save(folder/'layer.png');foundation.save(folder/'foundation.png')
 collisions=[]
 for i,a in enumerate(rows):
  for b in rows[i+1:]:
   if a['site']==b['site']:continue
   for threshold in (1,128):
    n=count(ImageChops.multiply(binary(layers[a['state']],threshold),binary(layers[b['state']],threshold)))
    if n:collisions.append({'states':[a['state'],b['state']],'alpha_threshold':threshold,'pixels':n})
 water=Image.new('L',(800,374));ImageDraw.Draw(water).polygon(WATER,fill=255);water.save(HERE/'planned-water-mask.png')
 # Fixed entry aprons and connecting routes to the central lane. Search only the
 # ground plane: roofs do not falsely block roads behind another structure.
 blocked=foundation_union.filter(ImageFilter.MaxFilter(7))
 blocked=ImageChops.lighter(blocked,water)
 trunkmask=Image.new('L',(800,374));ImageDraw.Draw(trunkmask).line(TRUNK,fill=255,width=7)
 trunk_points={(x,y) for y in range(70,374) for x in range(800) if trunkmask.getpixel((x,y)) and not blocked.getpixel((x,y))}
 def route(start):
  start=(max(1,min(798,start[0])),max(65,min(372,start[1]+4)))
  q=deque([start]);came={start:None};end=None
  while q:
   p=q.popleft()
   if p in trunk_points:end=p;break
   for dx,dy in ((0,1),(1,0),(-1,0),(0,-1)):
    n=(p[0]+dx,p[1]+dy)
    if not(1<=n[0]<799 and 65<=n[1]<373) or n in came:continue
    if blocked.getpixel(n) and abs(n[0]-start[0])+abs(n[1]-start[1])>9:continue
    came[n]=p;q.append(n)
  if end is None:return []
  path=[]
  while end is not None:path.append(list(end));end=came[end]
  path.reverse();corners=[path[0]]
  for i in range(1,len(path)-1):
   if (path[i][0]-path[i-1][0],path[i][1]-path[i-1][1])!=(path[i+1][0]-path[i][0],path[i+1][1]-path[i][1]):corners.append(path[i])
  if len(path)>1:corners.append(path[-1])
  return corners
 for r in rows:
  e=r['entrance'];e['planned_apron']=[e['exit_point'][0]-8,e['exit_point'][1],16,10]
  e['planned_route']=[e['stair_point'],e['exit_point']]+route(e['exit_point'])
  e['scope']='Design support plan BEFORE painting; routes are not evidence that the painted terrain supports entrances or native navigation.'
 foundation_union.save(HERE/'planned-foundation-mask.png')
 roadplan=Image.new('L',(800,374));rd=ImageDraw.Draw(roadplan);rd.line(TRUNK,fill=255,width=14)
 for r in rows:
  if r['site']=='shipyard':continue
  rd.line([tuple(p) for p in r['entrance']['planned_route']],fill=255,width=10)
  x,y,w,h=r['entrance']['planned_apron'];rd.rectangle((x,y,x+w,y+h),fill=255)
 roadplan.save(HERE/'planned-road-and-apron-mask.png')
 plan={'status':'design proposal','canvas':[800,374],'preservation':'All 36 selected painted functional-building masters byte-exact; uniform technical crop/scale/translation and prior whole-family mirror only. No building art regeneration authorized.','site_count':19,'ordinary_land_sites':17,'coast_sites':1,'grail_sites':1,'sites':[{**{k:s[k] for k in ('id','buildings')},'composition_rectangle':SITES[s['id']]} for s in old['sites']],'states':rows,'road_trunk':TRUNK,'water_polygon':WATER,'collision_results':collisions,'painting_requirements':['No repeated horizontal retaining-wall rows; organic interconnected city blocks and winding avenues.','Keep all real estate inside the planned complete alpha/shadow footprints dry and level; never place hut, wall-face, tree or water beneath a building or its entrance apron.','Incidental houses may frame roads outside reserved plots; never bake functional buildings into backdrop.','Low theatrical three-quarter matte perspective, elevated smoky crimson horizon, dark volcanic stone and localized forge fires.','Rear public architecture modestly larger through allocation; near framing retained, no numerical scale ratio art gate.'],'native_verified':False,'visual_approval_granted':False}
 write(HERE/'placement-plan.json',plan)
 board=Image.new('RGBA',(800,374),(66,61,55,255));d=ImageDraw.Draw(board)
 d.polygon(WATER,fill=(43,76,88));d.line(TRUNK,fill=(180,164,133),width=14)
 for r in rows:
  if r['state']!=next(s['buildings'][-1] for s in old['sites'] if s['id']==r['site']):continue
  d.line([tuple(p) for p in r['entrance']['planned_route']],fill=(180,164,133),width=10)
 for r in sorted(rows,key=lambda r:r['native_z']):
  if r['state']!=next(s['buildings'][-1] for s in old['sites'] if s['id']==r['site']):continue
  board.alpha_composite(layers[r['state']])
 board.save(REPORT/'placement-buildings-native.png');d=ImageDraw.Draw(board)
 for r in rows:
  if r['state']!=next(s['buildings'][-1] for s in old['sites'] if s['id']==r['site']):continue
  bb=r['full_alpha_bbox'];d.rectangle(bb,outline=(245,180,90));x,y=r['entrance']['exit_point'];d.ellipse((x-2,y-2,x+2,y+2),fill=(40,255,225))
 board.save(REPORT/'placement-footprints-native.png')
 print(json.dumps({'states':len(rows),'full_alpha_or_solid_collisions':len(collisions),'plan_sha256':sha(HERE/'placement-plan.json')}))
if __name__=='__main__':main()
