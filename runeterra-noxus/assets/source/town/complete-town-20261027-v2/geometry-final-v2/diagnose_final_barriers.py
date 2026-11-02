"""Omitted source bodies are diagnostic only, never an acceptance fixture."""
from pathlib import Path
from collections import deque
import json,numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;R=H.parents[4];c=json.loads((H/'town-layout.json').read_text());p=c['silhouette_plan']
def a(ref):return np.asarray(Image.open(R/ref['path']).convert('L'))>0
def flood(allowed,seeds):
 seen=np.zeros((374,800),dtype=bool);q=deque()
 for x,y in seeds:
  if allowed[y,x]:seen[y,x]=True;q.append((x,y))
 while q:
  x,y=q.popleft()
  for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
   if 0<=xx<800 and 0<=yy<374 and allowed[yy,xx]and not seen[yy,xx]:seen[yy,xx]=True;q.append((xx,yy))
 return seen
walk=a(c['source_walkable_plane']);b={s:a(v['body_mask'])for s,v in p['states'].items()};sites={t['id']:t['states']for t in c['sites']};sb={sid:np.logical_or.reduce([b[s]for s in states])for sid,states in sites.items()};cache={}
for omitted in [None]+list(sites):
 solid=np.logical_or.reduce([im for sid,im in sb.items()if sid!=omitted]);cache[omitted]=flood(walk&~solid,[(384,250)])
rows=[]
for state in ('special1','dwellingLvl3','dwellingUpLvl3','dwellingLvl1','dwellingUpLvl1','dwellingLvl4','dwellingUpLvl4','marketplace','resourceSilo','special2','shipyard'):
 sid=next(sid for sid,ss in sites.items()if state in ss);tread=a(c['source_entry_spans']['own_entry_tread_masks'][state])&a(p['states'][state]['door_mask']);yy,xx=np.where(tread);seeds=list(zip(map(int,xx),map(int,yy)));find=[]
 for omitted in [None]+[t for t in sites if t!=sid]:
  solid=np.logical_or.reduce([im for other,im in sb.items()if other not in(sid,omitted)]);allowed=~solid&((walk&~b[state])|tread);own=flood(allowed,seeds)
  if np.any(own&cache[omitted]):find.append(omitted)
 rows.append({'state':state,'single_other_site_body_omission_opening_actual_floor_route':find,'diagnostic_only':True})
out=R/'build/reports/complete-town-20261027-v2/geometry-final-v2/barriers-final-v12-001';out.mkdir(exist_ok=False);(out/'receipt.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows))
