"""Read-only shortest unclassified-gap witnesses; never route authorizations."""
from pathlib import Path
from collections import deque
import json,numpy as np,argparse
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;R=H.parents[4]
c=json.loads((H/'town-layout.json').read_text());p=c['silhouette_plan']
def a(ref):return np.asarray(Image.open(R/ref['path']).convert('L'))>0
ap=argparse.ArgumentParser();ap.add_argument('--approved-poses',action='store_true');ap.add_argument('--attempt',required=True);args=ap.parse_args()
walk=a(c['source_walkable_plane']);b={s:a(v['body_mask'])for s,v in p['states'].items()}
if args.approved_poses:
 for s,dx,dy in [('dwellingLvl2',-1,-7),('dwellingUpLvl2',-1,-7),('marketplace',3,0)]:
  im=Image.fromarray(b[s].astype('uint8')*255);m=Image.new('L',im.size);m.paste(im,(dx,dy));b[s]=np.asarray(m)>0
allb=np.logical_or.reduce(list(b.values()));globalpath=np.zeros_like(walk);q=deque([(384,250)]);globalpath[250,384]=True
while q:
 x,y=q.popleft()
 for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
  if 0<=xx<800 and 0<=yy<374 and walk[yy,xx]and not allb[yy,xx]and not globalpath[yy,xx]:globalpath[yy,xx]=True;q.append((xx,yy))
out=R/'build/reports/complete-town-20261027-v2/geometry-final-v2'/args.attempt;out.mkdir(exist_ok=False)
rows=[]
for state in ('special1','dwellingLvl3','dwellingUpLvl3','dwellingLvl1','dwellingLvl4','marketplace','resourceSilo','special2','dwellingLvl7','shipyard'):
 site=next(t for t in c['sites']if state in t['states']);other=np.logical_or.reduce([v for s,v in b.items()if s not in site['states']]);tread=a(c['source_entry_spans']['own_entry_tread_masks'][state])&a(p['states'][state]['door_mask']);allowed=~other&((walk&~b[state])|tread);permitted=~other&(~b[state]|tread)
 dist=np.full((374,800),999999,dtype=np.int32);prev={};q=deque();
 for yy,xx in zip(*np.where(globalpath&permitted)):dist[yy,xx]=0;q.append((int(xx),int(yy)))
 target=None
 while q:
  x,y=q.popleft()
  if tread[y,x]and permitted[y,x]:target=(x,y);break
  for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
   if 0<=xx<800 and 0<=yy<374 and permitted[yy,xx]:
    cost=0 if allowed[yy,xx] else 1;d=dist[y,x]+cost
    if d<dist[yy,xx]:dist[yy,xx]=d;prev[(xx,yy)]=(x,y);q.appendleft((xx,yy))if cost==0 else q.append((xx,yy))
 path=[];pt=target
 while pt in prev:path.append(pt);pt=prev[pt]
 unknown=[pt for pt in path if not walk[pt[1],pt[0]]and not tread[pt[1],pt[0]]]
 row={'state':state,'canvas_route_exists_with_unknown_terrain_permitted':target is not None,'unknown_pixel_count':len(unknown)if target is not None else None,'unknown_pixels':unknown,'diagnostic_only_not_authorization':True};rows.append(row)
 im=Image.open(R/c['background']['path']).convert('RGB');d=ImageDraw.Draw(im)
 for pt in path:d.point(pt,fill='yellow')
 for pt in unknown:d.point(pt,fill='red')
 im.save(out/(state+'-background-gap.png'))
print(json.dumps(rows));(out/'receipt.json').write_text(json.dumps(rows,indent=2)+'\n')
