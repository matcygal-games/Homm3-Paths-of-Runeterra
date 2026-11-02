"""Bounded whole-family source proposal, fixed actual background planes."""
from pathlib import Path
from collections import deque
import argparse,json,numpy as np,hashlib
from PIL import Image,ImageChops
H=Path(__file__).resolve().parent;R=H.parents[4]
def flood(v,seeds):
 seen=np.zeros((374,800),bool);q=deque()
 for x,y in seeds:
  if v[y,x]:seen[y,x]=True;q.append((x,y))
 while q:
  x,y=q.popleft()
  for xx,yy in((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
   if 0<=xx<800 and 0<=yy<374 and v[yy,xx]and not seen[yy,xx]:seen[yy,xx]=True;q.append((xx,yy))
 return seen
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--site',required=True);ap.add_argument('--attempt',required=True);ap.add_argument('--max-x',type=int,default=20);ap.add_argument('--max-y',type=int,default=8);ap.add_argument('--academy-goal',action='store_true');ap.add_argument('--prior-hound',action='store_true');ap.add_argument('--world-goal');args=ap.parse_args();c=json.loads((H/'town-layout.json').read_text());p=c['silhouette_plan'];sites={s['id']:s for s in c['sites']};ss=sites[args.site]['states'];refs=p['states'];frames={s:Image.open(R/r['path']).convert('RGBA')for s,r in c['frames'].items()}
 def arr(ref):return np.asarray(Image.open(R/ref['path']).convert('L'))>0
 b={s:arr(v['body_mask'])for s,v in refs.items()};d={s:arr(v['door_mask'])for s,v in refs.items()};t={s:arr(c['source_entry_spans']['own_entry_tread_masks'][s])&d[s]for s in refs};roots={s:Image.open(R/refs[s]['foundation_mask']['path']).convert('L')for s in ss};support=Image.open(R/p['support_mask']['path']).convert('L');walk=arr(c['source_walkable_plane']);depth={s:site['depth']for site in sites.values()for s in site['states']};state_site={s:sid for sid,site in sites.items()for s in site['states']};targets=['special1','dwellingLvl3','dwellingUpLvl3']+ss
 def move(im,dx,dy):out=Image.new(im.mode,im.size);out.paste(im,(dx,dy));return out
 def ma(v,dx,dy):return np.asarray(move(Image.fromarray(v.astype('uint8')*255),dx,dy))>0
 if args.prior_hound:
  for state in sites['dwellingHound']['states']:
   frames[state]=move(frames[state],-1,-7);b[state]=ma(b[state],-1,-7);d[state]=ma(d[state],-1,-7);t[state]=ma(t[state],-1,-7)
 if args.world_goal and args.world_goal not in targets:targets.append(args.world_goal)
 candidates=[];checks=[]
 for dx,dy in sorted([(x,y)for x in range(-args.max_x,args.max_x+1)for y in range(-args.max_y,args.max_y+1)],key=lambda q:(q[0]*q[0]+q[1]*q[1],abs(q[0])+abs(q[1]),q[1],q[0])):
  bounds=[frames[s].getchannel('A').point(lambda a:255 if a>=8 else 0).getbbox()for s in ss]
  if any(not(0<=bb[0]+dx<bb[2]+dx<=800 and 0<=bb[1]+dy<bb[3]+dy<=374)for bb in bounds):continue
  if any(ImageChops.subtract(move(root,dx,dy),support).getbbox()for root in roots.values()):continue
  bb={s:(ma(v,dx,dy)if s in ss else v)for s,v in b.items()};dd={s:(ma(v,dx,dy)if s in ss else v)for s,v in d.items()};tt={s:(ma(v,dx,dy)if s in ss else v)for s,v in t.items()};conflict=False
  for s in ss:
   for other in refs:
    if other in ss:continue
    if np.any(dd[s]&bb[other])if depth[other]>depth[s]else np.any(dd[other]&bb[s]):conflict=True;break
   if conflict:break
  if conflict:continue
  globalbody=np.logical_or.reduce(list(bb.values()));network=flood(walk&~globalbody,[(384,250)]);success=[]
  for state in targets:
   others=np.logical_or.reduce([v for s,v in bb.items()if state_site[s]!=state_site[state]]);allowed=~others&((walk&~bb[state])|tt[state]);yy,xx=np.where(tt[state]);own=flood(allowed,list(zip(map(int,xx),map(int,yy))))
   if np.any(own&network):success.append(state)
  world_open=False
  if args.world_goal:
   state=args.world_goal;other=np.logical_or.reduce([v for s,v in bb.items()if state_site[s]!=state_site[state]]);permitted=~other&(~bb[state]|tt[state]);component=flood(permitted,[(384,250)]);world_open=bool(np.any(component&tt[state]))
  checks.append({'dx':dx,'dy':dy,'routes':success,'source_forecourt_opens_unknown_terrain_diagnostic':world_open})
  goals=['special1']if args.academy_goal else ['dwellingLvl3','dwellingUpLvl3']
  if world_open if args.world_goal else all(s in success for s in goals):candidates.append(checks[-1]);break
 out=R/'build/reports/complete-town-20261027-v2/geometry-final-v2'/args.attempt;out.mkdir(exist_ok=False)
 if candidates:
  dx,dy=candidates[0]['dx'],candidates[0]['dy'];scene=Image.open(R/c['background']['path']).convert('RGBA')
  for state in ss:
   folder=out/state;folder.mkdir();move(frames[state],dx,dy).save(folder/'frame.png');move(roots[state],dx,dy).save(folder/'foundation.png')
   for role,data in [('door',d[state]),('own-treads',t[state])]:Image.fromarray(ma(data,dx,dy).astype('uint8')*255).save(folder/(role+'.png'))
  for state in p['complete_scene_states']:scene.alpha_composite(move(frames[state],dx,dy)if state in ss else frames[state])
  scene.save(out/'whole-city-proposal.png')
 result={'status':'design proposal','site':args.site,'fixed_background':c['background'],'candidates':candidates,'feasible_support_entry_poses':checks,'canonical_source_modified':False};(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()

