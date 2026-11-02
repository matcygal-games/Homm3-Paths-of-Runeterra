"""Diagnose a real approach component; shortest gaps never authorize paths."""
from pathlib import Path
from PIL import Image
from collections import deque
import argparse,json
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
def flood(array,start):
 if not array[start[1],start[0]]:return set()
 queue=deque([start]);seen={start}
 while queue:
  x,y=queue.popleft()
  for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
   if 0<=xx<800 and 0<=yy<374 and array[yy,xx]and (xx,yy)not in seen:seen.add((xx,yy));queue.append((xx,yy))
 return seen

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--state',default='villageHall');parser.add_argument('--attempt',required=True);args=parser.parse_args();report=ROOT/'build/reports/complete-town-20261027-v2/geometry-final-v2'/args.attempt;report.mkdir(parents=True,exist_ok=False)
 c=json.loads((HERE/'town-layout.json').read_text());plan=c['silhouette_plan'];state=args.state;site=next(site for site in c['sites']if state in site['states']);walk=np.asarray(Image.open(ROOT/c['source_walkable_plane']['path']).convert('L'))>0;body={s:np.asarray(Image.open(ROOT/ref['path']).convert('RGBA').getchannel('A'))>=128 for s,ref in c['frames'].items()};allbody=np.logical_or.reduce(list(body.values()));others=np.logical_or.reduce([value for s,value in body.items()if s not in site['states']]);tref=c['source_entry_spans']['own_entry_tread_masks'][state];treads=np.asarray(Image.open(ROOT/tref['path']).convert('L'))>0;door=np.asarray(Image.open(ROOT/plan['states'][state]['door_mask']['path']).convert('L'))>0;allowed=~others&((walk&~body[state])|(treads&door));anchor=tuple(plan['states'][state]['entrance']);own=flood(allowed,anchor);main=flood(walk&~allbody,(384,250));background=flood(walk,anchor);distance=np.full((374,800),-1,dtype='int32');prev={};queue=deque()
 for point in main:distance[point[1],point[0]]=0;queue.append(point)
 goal=None
 while queue:
  point=queue.popleft()
  if point in own:goal=point;break
  x,y=point
  for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
   if 0<=xx<800 and 0<=yy<374 and distance[yy,xx]<0:distance[yy,xx]=distance[y,x]+1;prev[(xx,yy)]=point;queue.append((xx,yy))
 gap=[];point=goal
 while point in prev:gap.append({'xy':point,'walkable':bool(walk[point[1],point[0]]),'body_blockers':[s for s,value in body.items()if value[point[1],point[0]]]});point=prev[point]
 result={'state':state,'anchor':anchor,'actual_own_component_pixels':len(own),'background_only_component_pixels':len(background),'background_only_reaches_main_seed':(384,250)in background,'actual_global_component_pixels':len(main),'closest_canvas_gap_length':int(distance[goal[1],goal[0]])if goal else None,'gap_is_diagnostic_not_authorization':gap};(report/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');image=Image.open(ROOT/c['background']['path']).convert('RGBA');overlay=Image.new('RGBA',image.size)
 for x,y in own:overlay.putpixel((x,y),(0,255,255,110))
 for x,y in main:overlay.putpixel((x,y),(255,255,0,70))
 image.alpha_composite(overlay);image.save(report/'components.png');print(json.dumps({key:value for key,value in result.items()if key!='gap_is_diagnostic_not_authorization'}));print(json.dumps({'gap_first20':gap[:20],'gap_last10':gap[-10:]}))
if __name__=='__main__':main()
