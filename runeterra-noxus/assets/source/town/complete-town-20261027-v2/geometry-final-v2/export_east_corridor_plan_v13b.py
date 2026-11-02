"""Actual source obstacle corridor for painter; unknown terrain is not admitted."""
from pathlib import Path
from collections import deque
import json,numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;R=H.parents[4];T=H.parent;ix=json.loads((T/'native-transforms-v13/states.json').read_text());rows={r['state']:r for r in ix['states']};proposal=R/'build/reports/complete-town-20261027-v2/geometry-final-v2/silo-local-egress-fit-v13b-001';frames={s:Image.open(R/r['frame']['path']).convert('RGBA')for s,r in rows.items()};frames['resourceSilo']=Image.open(proposal/'frame.png').convert('RGBA');b={s:np.asarray(im.getchannel('A'))>=128 for s,im in frames.items()};walk=np.asarray(Image.open(H/'final-v13b-trace-v1/walkable-plane.png'))>0;result=[];out=H/'east-corridor-plan-v13b';out.mkdir(exist_ok=False)
for state in ('dwellingLvl1','dwellingUpLvl1','special2','shipyard'):
 ownsite=rows[state]['site'];other=np.logical_or.reduce([v for s,v in b.items()if rows[s]['site']!=ownsite]);tread=np.asarray(Image.open(R/rows[state]['own_treads_mask']['path']))>0;door=np.asarray(Image.open(R/rows[state]['door_mask']['path']))>0;tread&=door;permitted=~other&(~b[state]|tread);allowed=~other&((walk&~b[state])|tread);permitted[:150]=False;permitted[247:]=False;permitted[:,:430]=False;permitted[:,748:]=False
 if state=='shipyard':permitted[:,748:]=~other[:,748:]&(~b[state][:,748:]|tread[:,748:])
 dist=np.full((374,800),999999,np.int32);dist[180,441]=0;q=deque([(441,180)]);prev={};target=None
 while q:
  x,y=q.popleft()
  if tread[y,x]and permitted[y,x]:target=(x,y);break
  for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
   if 0<=xx<800 and 0<=yy<374 and permitted[yy,xx]:
    cost=0 if allowed[yy,xx]else 1;d=dist[y,x]+cost
    if d<dist[yy,xx]:dist[yy,xx]=d;prev[(xx,yy)]=(x,y);q.appendleft((xx,yy))if cost==0 else q.append((xx,yy))
 path=[];pt=target
 while pt in prev:path.append(pt);pt=prev[pt]
 unknown=[pt for pt in path if not walk[pt[1],pt[0]]and not tread[pt[1],pt[0]]];result.append({'state':state,'bodyfree_local_egress_exists':target is not None,'unknown_terrain_pixels_NOT_approved':unknown,'unknown_count':len(unknown)if target else None,'actual_source_path':path})
scene=Image.open(T/'terrain/final-native-v13b-proposal.png').convert('RGBA')
for s in sorted(frames,key=lambda s:rows[s]['native_z']):
 if s not in('fort','citadel','mageGuild1','mageGuild2','mageGuild3','dwellingLvl1','dwellingLvl2','dwellingLvl3','dwellingLvl4','dwellingLvl5','dwellingLvl6','dwellingLvl7','special4','villageHall','townHall','cityHall','shipyard','ship','grail'):scene.alpha_composite(frames[s])
for row in result:
 im=scene.copy()
 for x,y in row['actual_source_path']:im.putpixel((x,y),(255,255,0,255))
 for x,y in row['unknown_terrain_pixels_NOT_approved']:im.putpixel((x,y),(255,0,0,255))
 im.crop((580,145,780,245)).resize((1000,500)).save(out/(row['state']+'-SOURCE-CLEAR-UNKNOWN-TERRAIN-PLAN.png'))
(out/'index.json').write_text(json.dumps({'status':'design proposal','source_silo_proposal':str(proposal),'unknown_pixels_are_NOT_support_or_route_masks':True,'states':result},indent=2)+'\n');print(json.dumps([{k:v for k,v in row.items()if k!='actual_source_path'}for row in result]))
