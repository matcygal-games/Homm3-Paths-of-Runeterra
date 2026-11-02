"""Read-only bounded current-source pose clearance for the witnessed Civic barrier."""
from pathlib import Path
from PIL import Image,ImageChops
from collections import deque
import hashlib,json
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];REPORT=ROOT/'build/reports/complete-town-20261027-v2/geometry-final-v2/guild3-route-clearance-search-v1'
def flood_reaches(array,start,goal):
 if not array[start[1],start[0]]:return False
 q=deque([start]);seen={start}
 while q:
  x,y=q.popleft()
  if(x,y)==goal:return True
  for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
   if 0<=xx<800 and 0<=yy<374 and array[yy,xx]and(xx,yy)not in seen:seen.add((xx,yy));q.append((xx,yy))
 return False

def main():
 REPORT.mkdir(parents=True,exist_ok=False)
 c=json.loads((HERE/'town-layout.json').read_text());p=c['silhouette_plan'];target='mageGuild3';walk=np.asarray(Image.open(ROOT/c['source_walkable_plane']['path']).convert('L'))>0;support=Image.open(ROOT/p['support_mask']['path']).convert('L');images={s:Image.open(ROOT[0] if False else ROOT/ref['path']).convert('RGBA')for s,ref in c['frames'].items()};bodies={s:image.getchannel('A').point(lambda value:255 if value>=128 else 0)for s,image in images.items()};doors={s:Image.open(ROOT/row['door_mask']['path']).convert('L')for s,row in p['states'].items()};root=Image.open(ROOT/p['states'][target]['foundation_mask']['path']).convert('L');other_body=np.logical_or.reduce([np.asarray(image)>0 for s,image in bodies.items()if s!=target]);depth={s:site['depth']for site in c['sites']for s in site['states']};bb=images[target].getchannel('A').point(lambda value:255 if value>=8 else 0).getbbox();results=[]
 def move(image,dx,dy):
  output=Image.new(image.mode,image.size);output.paste(image,(dx,dy));return output
 for dx,dy in sorted([(x,y)for x in range(-8,9)for y in range(-8,9)],key=lambda point:(point[0]**2+point[1]**2,abs(point[0])+abs(point[1]),abs(point[0]),point[1],point[0])):
  if not(0<=bb[0]+dx<bb[2]+dx<=800 and 0<=bb[1]+dy<bb[3]+dy<=374):continue
  moved_root=move(root,dx,dy)
  if ImageChops.subtract(moved_root,support).getbbox():continue
  body=move(bodies[target],dx,dy);door=move(doors[target],dx,dy);conflicts=[]
  for state in images:
   if state==target:continue
   if depth[state]<depth[target]:hit=ImageChops.multiply(body,doors[state])
   elif depth[state]>depth[target]:hit=ImageChops.multiply(door,bodies[state])
   else:continue
   if hit.getbbox():conflicts.append(state)
  if conflicts:continue
  reaches=flood_reaches(walk&~(other_body|(np.asarray(body)>0)),(164,163),(384,250))
  if reaches:
   proposal=move(images[target],dx,dy);proposal.save(REPORT/'proposed-mageGuild3-source.png',compress_level=9);moved_root.save(REPORT/'proposed-full-root.png',compress_level=9);results.append({'dx':dx,'dy':dy,'root_pixels':moved_root.histogram()[255],'support_gap_pixels':0,'full_entry_conflicts':[],'civic_to_main_bodyfree_route_exists':True,'new_frame_sha256':hashlib.sha256((REPORT/'proposed-mageGuild3-source.png').read_bytes()).hexdigest()});break
 result={'status':'design proposal','scope':'Minimal whole selected Guild3 translation only; actual full root/entry move together, floor/streets/allotherbodies fixed. Current site depth159 must remain common to in-place Guild replacements.','original_frame':c['frames'][target],'candidates':results,'source_modified':False,'stage_selected':False}
 (REPORT/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
