"""Uniform whole-source Academy fit proposal; owner must retrace actual feet."""
from pathlib import Path
import json,numpy as np
from PIL import Image,ImageChops,ImageFilter
from search_final_access_pose import flood
H=Path(__file__).resolve().parent;R=H.parents[4];c=json.loads((H/'town-layout.json').read_text());p=c['silhouette_plan'];state='special1';site=next(s for s in c['sites']if state in s['states'])
def a(ref):return Image.open(R/ref['path']).convert('L')
frames={s:Image.open(R/r['path']).convert('RGBA')for s,r in c['frames'].items()};door={s:a(r['door_mask'])for s,r in p['states'].items()};tread={s:a(c['source_entry_spans']['own_entry_tread_masks'][s])for s in frames};root=a(p['states'][state]['foundation_mask']);support=a(p['support_mask']);walk=np.asarray(a(c['source_walkable_plane']))>0;depth={s:site['depth']for site in c['sites']for s in site['states']}
def move(im,dx,dy):v=Image.new(im.mode,im.size);v.paste(im,(dx,dy));return v
for s in ('dwellingLvl2','dwellingUpLvl2'):
 frames[s]=move(frames[s],-1,-7);door[s]=move(door[s],-1,-7);tread[s]=move(tread[s],-1,-7)
frames['marketplace']=move(frames['marketplace'],3,0);door['marketplace']=move(door['marketplace'],3,0);tread['marketplace']=move(tread['marketplace'],3,0)
body={s:im.getchannel('A').point(lambda v:255 if v>=128 else 0)for s,im in frames.items()};other=np.logical_or.reduce([np.asarray(v)>0 for s,v in body.items()if s!=state]);records=[];selected=None
index=json.loads((H.parent/'native-transforms-v12/states.json').read_text());source_row=next(r for r in index['states']if r['state']==state);zone=a(source_row['semantic_zone_mask'])
for percent in range(99,84,-1):
 scale=percent/100;pivot=(42,130);inv=1/scale;matrix=(inv,0,pivot[0]*(1-inv),0,inv,pivot[1]*(1-inv))
 for dx,dy in sorted([(x,y)for x in range(-4,5)for y in range(-3,4)],key=lambda q:(q[0]**2+q[1]**2,q[1],q[0])):
  frame=move(frames[state].transform((800,374),Image.Transform.AFFINE,matrix,Image.Resampling.BICUBIC),dx,dy);full=frame.getchannel('A').point(lambda v:255 if v>=8 else 0);bb=frame.getchannel('A').point(lambda v:255 if v>=128 else 0)
  dd=ImageChops.multiply(move(door[state].transform((800,374),Image.Transform.AFFINE,matrix,Image.Resampling.NEAREST),dx,dy),full);tt=ImageChops.multiply(move(tread[state].transform((800,374),Image.Transform.AFFINE,matrix,Image.Resampling.NEAREST),dx,dy),dd)
  zz=move(zone.transform((800,374),Image.Transform.AFFINE,matrix,Image.Resampling.NEAREST),dx,dy);ba=np.asarray(bb)>0;za=np.asarray(zz)>0;ra=np.zeros_like(ba);classified=True
  for x in range(800):
   ys=np.flatnonzero(ba[:,x])
   if not len(ys):continue
   bottom=int(ys[-1])
   if not za[bottom,x]:classified=False;break
   for y in range(bottom,bottom-4,-1):
    if not ba[y,x]or not za[y,x]:break
    ra[y,x]=True
  if not classified:continue
  rr=Image.fromarray(ra.astype('uint8')*255)
  if ImageChops.subtract(rr,support).getbbox():continue
  if any(ImageChops.multiply(dd,body[s]).getbbox()if depth[s]>depth[state]else ImageChops.multiply(door[s],bb).getbbox()for s in frames if s!=state):continue
  network=flood(walk&~(other|(np.asarray(bb)>0)),[(384,250)]);ta=np.asarray(tt)>0;allowed=~other&((walk&~(np.asarray(bb)>0))|ta);ys,xs=np.where(ta);own=flood(allowed,list(zip(map(int,xs),map(int,ys))));connected=bool(np.any(network&own));record={'uniform_scale_percent':percent,'dx':dx,'dy':dy,'pivot':list(pivot),'full_entry_conflicts':0,'actual_source_four_pixel_root_outside_support':0,'actual_source_root_pixels':int(ra.sum()),'academy_route_connects':connected};records.append(record)
  if connected:selected=(record,frame,rr,dd,tt);break
 if selected:break
out=R/'build/reports/complete-town-20261027-v2/geometry-final-v2/academy-uniform-fit-v12-002';out.mkdir(exist_ok=False)
if selected:
 record,frame,rr,dd,tt=selected
 for name,im in [('frame',frame),('foundation-PROXY-REQUIRES-ACTUAL-RETRACE',rr),('door-PROXY',dd),('own-treads-PROXY',tt)]:im.save(out/(name+'.png'))
 scene=Image.open(R/c['background']['path']).convert('RGBA')
 for s in p['complete_scene_states']:scene.alpha_composite(frame if s==state else frames[s])
 scene.save(out/'whole-city-proposal.png')
result={'status':'design proposal','selected':selected[0]if selected else None,'source_root_retrace_required_before_adoption':True,'checked_support_entry_poses':records,'fixed_background':c['background'],'prior_approved_hound':[-1,-7],'prior_approved_market':[3,0],'source_modified':False};(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='checked_support_entry_poses'}))
