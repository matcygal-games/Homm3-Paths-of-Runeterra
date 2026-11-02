"""Read-only source-barrier diagnosis; omitted bodies never enter production."""
from pathlib import Path
from PIL import Image
from collections import deque
import numpy as np,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];REPORT=ROOT/'build/reports/complete-town-20261027-v2/geometry-final-v2/access-body-group-diagnosis-v7-002'
def flood(array,start):
 if not array[start[1],start[0]]:return set()
 q=deque([start]);seen={start}
 while q:
  x,y=q.popleft()
  for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
   if 0<=xx<800 and 0<=yy<374 and array[yy,xx]and(xx,yy)not in seen:seen.add((xx,yy));q.append((xx,yy))
 return seen

def main():
 REPORT.mkdir(parents=True,exist_ok=False);c=json.loads((HERE/'town-layout.json').read_text());p=c['silhouette_plan'];walk=np.asarray(Image.open(ROOT/c['source_walkable_plane']['path']).convert('L'))>0;body={s:np.asarray(Image.open(ROOT/ref['path']).getchannel('A'))>=128 for s,ref in c['frames'].items()};sites={site['id']:site['states']for site in c['sites']};state_site={state:sid for sid,states in sites.items()for state in states};allbody=np.logical_or.reduce(list(body.values()));normal=flood(walk&~allbody,(384,250));cache={};rows=[]
 for excluded,states in sites.items():
  union=np.logical_or.reduce([b for s,b in body.items()if s not in states]);cache[excluded]=flood(walk&~union,(384,250))
 for state in ('special1','dwellingLvl3','dwellingUpLvl3','dwellingLvl7'):
  sid=state_site[state];door=np.asarray(Image.open(ROOT/p['states'][state]['door_mask']['path']).convert('L'))>0;treads=np.asarray(Image.open(ROOT/c['source_entry_spans']['own_entry_tread_masks'][state]['path']).convert('L'))>0;anchor=tuple(p['states'][state]['entrance']);base=(walk&~body[state])|(treads&door);removals=[];others=np.logical_or.reduce([b for s,b in body.items()if s not in sites[sid]]);own=flood(base&~others,anchor)
  for excluded,states in sites.items():
   if excluded==sid:continue
   obstacles=np.logical_or.reduce([b for s,b in body.items()if s not in sites[sid]and s not in states]);reachable=flood(base&~obstacles,anchor)
   if reachable&cache[excluded]:removals.append(excluded)
  proxy=flood(walk&~np.logical_or.reduce([b for s,b in body.items()if s==state or s not in sites[sid]]),(384,250))
  rows.append({'state':state,'own_approach_component_pixels':len(own),'own_component_bbox':[min(x for x,y in own),min(y for x,y in own),max(x for x,y in own),max(y for x,y in own)]if own else None,'single_other_site_omission_that_opens_route':removals,'route_opens_if_only_own_alternative_variants_omitted_from_common_global_network':bool(own&proxy)})
 result={'scope':'READONLY barrier identification only, not source selection or permission to omit any actual body/variant. Production still accounts all36.','states':rows};(REPORT/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
