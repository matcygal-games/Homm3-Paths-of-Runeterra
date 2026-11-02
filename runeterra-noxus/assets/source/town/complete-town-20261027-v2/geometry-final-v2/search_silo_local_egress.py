"""Actual-source Silo fit for an eastern egress corridor; no terrain admission."""
from pathlib import Path
from collections import deque
import json,numpy as np,hashlib
from PIL import Image,ImageChops
from search_final_access_pose import flood
H=Path(__file__).resolve().parent;R=H.parents[4];T=H.parent;index=json.loads((T/'native-transforms-v13/states.json').read_text());rows={r['state']:r for r in index['states']};state='resourceSilo';maskroot=H/'final-v13-trace-v1';walk=np.asarray(Image.open(maskroot/'walkable-plane.png'))>0;support=Image.open(maskroot/'support.png').convert('L');frames={s:Image.open(R/r['frame']['path']).convert('RGBA')for s,r in rows.items()};body={s:im.getchannel('A').point(lambda a:255 if a>=128 else 0)for s,im in frames.items()};door={s:Image.open(R/r['door_mask']['path']).convert('L')for s,r in rows.items()};tread={s:Image.open(R/r['own_treads_mask']['path']).convert('L')for s,r in rows.items()};zone=Image.open(R/rows[state]['semantic_zone_mask']['path']).convert('L');others=np.logical_or.reduce([np.asarray(im)>0 for s,im in body.items()if s!=state]);records=[];selected=None;foot_reference=Image.open(R/rows[state]['foundation_mask']['path']).convert('L')
def move(im,dx,dy):out=Image.new(im.mode,im.size);out.paste(im,(dx,dy));return out
def root4(bb,zz):
 b=np.asarray(bb)>0;z=np.asarray(zz)>0;out=np.zeros_like(b)
 for x in np.flatnonzero(b.any(axis=0)):
  bottom=int(np.flatnonzero(b[:,x])[-1])
  if not z[bottom,x]:return None
  for y in range(bottom,bottom-4,-1):
   if not b[y,x]or not z[y,x]:break
   out[y,x]=True
 return Image.fromarray(out.astype('uint8')*255)
assert root4(body[state],zone).tobytes()==foot_reference.tobytes(),'Original411 fullprofile reconstruction must beexact'
local=np.zeros((374,800),bool);local[150:247,430:748]=True
for percent in range(100,89,-1):
 scale=percent/100;pivot=(717,258);inv=1/scale;matrix=(inv,0,pivot[0]*(1-inv),0,inv,pivot[1]*(1-inv));frame0=frames[state].copy()if percent==100 else frames[state].transform((800,374),Image.Transform.AFFINE,matrix,Image.Resampling.BICUBIC);full0=frame0.getchannel('A').point(lambda a:255 if a>=8 else 0);body0=frame0.getchannel('A').point(lambda a:255 if a>=128 else 0);zone0=zone.transform((800,374),Image.Transform.AFFINE,matrix,Image.Resampling.NEAREST);root0=root4(body0,zone0)
 if root0 is None:continue
 door0=ImageChops.multiply(door[state].transform((800,374),Image.Transform.AFFINE,matrix,Image.Resampling.NEAREST),full0);tread0=ImageChops.multiply(tread[state].transform((800,374),Image.Transform.AFFINE,matrix,Image.Resampling.NEAREST),door0)
 for dx,dy in sorted([(x,y)for x in range(-4,14)for y in range(-4,7)],key=lambda v:(v[0]*v[0]+v[1]*v[1],v[1],v[0])):
  root=move(root0,dx,dy)
  if ImageChops.subtract(root,support).getbbox():continue
  bb=move(body0,dx,dy);dd=move(door0,dx,dy);tt=move(tread0,dx,dy);conflicts=[]
  for s in rows:
   if s==state:continue
   if ImageChops.multiply(dd,body[s]).getbbox()if rows[s]['native_z']>rows[state]['native_z']else ImageChops.multiply(door[s],bb).getbbox():conflicts.append(s)
  if conflicts:continue
  # Other architecture remains exact. Unknown local terrain is allowed ONLY
  # for body-corridor diagnosis; it is never written as support or a route.
  solids=others|(np.asarray(bb)>0);allowed=local&~solids;target='dwellingLvl1';td=np.asarray(tread[target])>0;permit=local&~np.logical_or.reduce([np.asarray(v)>0 for s,v in body.items()if s not in('dwellingLvl1','dwellingUpLvl1',state)])&~(np.asarray(bb)>0)&(~(np.asarray(body[target])>0)|td);ys,xs=np.where(td&permit);component=flood(permit,list(zip(map(int,xs),map(int,ys))));opens=bool(component[180,441]);rec={'scale_percent':percent,'pivot':list(pivot),'dx':dx,'dy':dy,'full_structural_root_pixels':root.histogram()[255],'actual_root_outside_fixed_floor':0,'full_opaque_entry_conflicts':[],'upper_barracks_to_menacourt_local_bodyfree_corridor':opens,'terrain_connection_NOT_yet_verified':True};records.append(rec)
  if opens:selected=(rec,move(frame0,dx,dy),root,dd,tt,move(zone0,dx,dy));break
 if selected:break
out=R/'build/reports/complete-town-20261027-v2/geometry-final-v2/silo-local-egress-fit-v13-001';out.mkdir(exist_ok=False)
if selected:
 rec,frame,root,dd,tt,zz=selected
 for name,im in [('frame',frame),('foundation-actual-full-four-pixel-profile',root),('full-entry',dd),('own-treads',tt),('semantic-zone',zz)]:im.save(out/(name+'.png'))
 c=json.loads((H/'town-layout.json').read_text());scene=Image.open(T/'terrain/final-native-v13-proposal.png').convert('RGBA')
 for s in c['silhouette_plan']['complete_scene_states']:scene.alpha_composite(frame if s==state else frames[s])
 scene.save(out/'whole-city-proposal.png')
result={'status':'design proposal','selected':selected[0]if selected else None,'scope':'Whole actual source, faithful zone, actual resampled alpha128 bottom4px per column; full entry/own treads transform together. Original411 reconstruction exact. Fixed actualV13floor and currentcoastboundary. Local unknownterrain allowedONLYforbodycorridorplanning, no physicalroute pass.','state_index_sha256':hashlib.sha256((T/'native-transforms-v13/states.json').read_bytes()).hexdigest(),'checked_supported_entry_clear_poses':records,'source_modified':False};(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='checked_supported_entry_clear_poses'}))
