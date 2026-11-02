"""Deterministic ROI-only assembly from genuine imagegen heraldry edits.

Never synthesizes a pose or emblem. Original RGB/alpha remains exact outside
each explicitly recorded painted plaque rectangle, and fullalpha is retained.
"""
from pathlib import Path
from copy import deepcopy
import hashlib,json
import numpy as np
from PIL import Image,ImageDraw
SELF=Path(__file__).resolve()
W=next(p for p in SELF.parents if (p/'runeterra-noxus/content/factions.json').is_file())
R=W/'build/reports/regional-crests-20261025-v1/noxus-t2-art';P=W/'runeterra-noxus';S=P/'assets/source/regional-crests-20261025-v1/noxus-t2'
PREP=json.loads((S/'preparation-v2-portable.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):return {'path':p.relative_to(P).as_posix(),'sha256':sha(p)}
def save(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists() and p.read_bytes()!=b:raise ValueError('Version immutable candidate: '+str(p))
 p.write_bytes(b)
summary={'status':'authored configuration','candidate_only':True,'units':{}}
producer_path=S/'assemble_candidate_v6.py'
save(producer_path,SELF.read_bytes())
for unit,info in PREP['units'].items():
 rawpath=S/unit/'paint-v1/painted-master-v1.png';raw=Image.open(rawpath).convert('RGBA')
 assert raw.size==(1536,1024)
 rawarr=np.array(raw);entries=[];byconsumer={}
 board=Image.new('RGB',(1152,896),(70,65,60));d=ImageDraw.Draw(board)
 maskboard=Image.new('RGB',(1152,896),(40,40,40));md=ImageDraw.Draw(maskboard)
 for e in info['entries']:
  k=e['index'];origpath=P/e['preserved_native']['path'];orig=Image.open(origpath).convert('RGBA');a=np.array(orig);out=a.copy()
  x0,y0,x1,y1=e['atlas_box'];b=e['visible_bbox'];crop=raw.crop((x0,y0,x1,y1)).resize((b[2]-b[0],b[3]-b[1]),Image.Resampling.LANCZOS);generated=np.array(crop)
  h,w=generated.shape[:2];expected=(round(w*.55),round(h*.84)) if k in (52,53) else (round(w*.76),round(h*.46))
  # A backward/away-facing collapsing pose has no visible frontal collar.
  occluded=(k in (20,21,22,23,24) and unit=='drakeHound') or k==20
  roi=None
  if not occluded:
   rgb=generated[:,:,:3].astype(int)
   bright=(rgb[:,:,0]>170)&(rgb[:,:,1]>145)&(rgb[:,:,2]>105)&(rgb[:,:,0]-rgb[:,:,2]<110)
   yy,xx=np.indices((h,w));eligible=bright&(xx>w*(.20 if k in (52,53) else .4))&(yy>h*(.66 if k in (52,53) else .20))&(yy<h*(.99 if k in (52,53) else .88))
   # Select the real painted ivory mark by locality, not a generated frame.
   pts=np.argwhere(eligible)
   if len(pts):
    distances=(pts[:,1]-expected[0])**2+(pts[:,0]-expected[1])**2
    cy,cx=pts[int(np.argmin(distances))]
    local=eligible&(abs(xx-cx)<=(10 if k in (52,53) else 5))&(abs(yy-cy)<=(12 if k in (52,53) else 7))
    ys,xs=np.nonzero(local)
    lx=max(0,int(xs.min())-2);rx=min(w,int(xs.max())+3);ty=max(0,int(ys.min())-2);by=min(h,int(ys.max())+3)
    # Register the genuinely painted plaque onto the existing collar/strap.
    # The tool placed base hanging tags just outside the unchanged silhouette.
    # Translate only that painted material insert, never the animal or a pose.
    patch=generated[ty:by,lx:rx].copy()
    if k in (52,53):
     limit=(10,12) if k==52 else (6,7)
     scale=min(1,limit[0]/patch.shape[1],limit[1]/patch.shape[0])
     patch=np.array(Image.fromarray(patch).resize((max(1,round(patch.shape[1]*scale)),max(1,round(patch.shape[0]*scale))),Image.Resampling.LANCZOS))
    rgb=patch[:,:,:3].astype(int)
    plaque=((rgb[:,:,0]>55)&(rgb[:,:,0]>rgb[:,:,1]*1.35)&(rgb[:,:,0]>rgb[:,:,2]*1.30))|((rgb[:,:,0]>170)&(rgb[:,:,1]>145)&(rgb[:,:,2]>105))
    white=(rgb[:,:,0]>170)&(rgb[:,:,1]>145)&(rgb[:,:,2]>105)
    tx,tyabs=b[0]+lx+((rx-lx)-patch.shape[1])//2,b[1]+ty+((by-ty)-patch.shape[0])//2
    offsets=[(0,0)]
    if unit=='drakeHound' or k in (52,53):
     offsets=[(dx,dy) for dx in (range(0,11) if k==54 else range(-10,1)) for dy in range(-8,1)]
    scored=[]
    for dx,dy in offsets:
     px,py=tx+dx,tyabs+dy
     if px<0 or py<0 or px+patch.shape[1]>a.shape[1] or py+patch.shape[0]>a.shape[0]:continue
     opaque=a[py:py+patch.shape[0],px:px+patch.shape[1],3]>=224
     missing=int((white&~opaque).sum())
     scored.append((missing*100+abs(dx)+abs(dy),dx,dy))
    _,dx,dy=min(scored)
    tx+=dx;tyabs+=dy
    roi=[tx,tyabs,tx+patch.shape[1],tyabs+patch.shape[0]]
    mask=np.zeros(a.shape[:2],np.uint8)
    mask[roi[1]:roi[3],roi[0]:roi[2]]=plaque&(a[roi[1]:roi[3],roi[0]:roi[2],3]>=224)
    surface=np.zeros_like(a);surface[roi[1]:roi[3],roi[0]:roi[2]]=patch
    out[mask>0,:3]=surface[mask>0,:3]
   else:raise ValueError(f'No painted plaque found; inspect {unit}/{k}')
  else:mask=np.zeros(a.shape[:2],np.uint8)
  assert np.array_equal(out[:,:,3],a[:,:,3])
  assert np.array_equal(out[mask==0],a[mask==0])
  directory=S/unit/'candidate-v6';directory.mkdir(parents=True,exist_ok=True)
  dst=directory/f'pose-{k:03d}.png';Image.fromarray(out).save(dst)
  mp=directory/f'pose-{k:03d}-mask.png';Image.fromarray(mask*255).save(mp)
  record={**e,'candidate':pin(dst),'mask':pin(mp),'painted_roi':roi,'registration_translation':None if occluded else [dx,dy],'occluded':occluded,'changed_rgb_pixels':int(np.any(out!=a,axis=2).sum()),'full_alpha_exact':True,'outside_roi_rgba_exact':True}
  entries.append(record)
  for c in e['consumers']:byconsumer[(c['role'],c['frame'])]=record
  im=Image.fromarray(out).crop(b);m=Image.fromarray(mask*255).crop(b)
  bx=(k%8)*144+(144-im.width)//2;by=(k//8)*128+(128-im.height)//2
  board.paste(im,(bx,by),im);d.text(((k%8)*144+3,(k//8)*128+3),str(k),fill='white')
  maskboard.paste(im,(bx,by),im);overlay=Image.new('RGBA',im.size,(255,0,255,0));overlay.putalpha(m.point(lambda v:120 if v else 0));maskboard.paste(overlay,(bx,by),overlay)
  md.text(((k%8)*144+3,(k//8)*128+3),str(k),fill='white')
 board.save(R/f'{unit}-candidate-native-v6.png');maskboard.save(R/f'{unit}-candidate-masks-v6.png')
 generation={'image_generation_used':True,'provider':'OpenAI builtin imagegen','model':'not exposed by builtin tool',
   'painted_master':rawpath.relative_to(P).as_posix(),'painted_master_sha256':sha(rawpath),
   'prompt':(S/unit/'paint-v1/prompt.txt').read_text(),'prompt_file':(S/unit/'paint-v1/prompt.txt').relative_to(P).as_posix(),
   'route':'Genuine painted2D crest-only edit of selected native pose contact sheet; explicit perpose plaque ROI, original outsideRGBA and fullalpha exact',
   'reference':{'url':'https://dd.b.pvp.net/7_10_0/core/en_us/img/regions/icon-noxus.png','sha256':'2faba5bd37e64f8babfac8006341b9545b45b0914eb25e8f0491c85402d2b392','private_reference_only':True},
   'source_preparation':pin(S/'preparation-v2-portable.json'),'technical_producer':pin(producer_path),
   'raw_receipt_sha256':sha(R/f'{unit}-raw-tool-receipt-v1.json'),'raw_receipt_preserved_privately':True,
   'visual_approval_granted':False,'runtime_verified':False,'release_accepted':False}
 gp=S/unit/'paint-v1/generation-roi-v6.json';gp.write_text(json.dumps(generation,indent=2)+'\n')
 recipes=[]
 for role,pinold in info['recipes'].items():
  rp=P/pinold['path'];assert sha(rp)==pinold['sha256'];rr=json.loads(rp.read_text())
  rr['generation']=generation
  rr['dependencies']=[pin(S/'preparation-v2-portable.json'),pin(rawpath),pin(gp),pin(producer_path)]
  if rr['recipe_type']=='vcmi_animation':
   for group in rr['groups']:
    for i,f in enumerate(group['frames']):
     rec=byconsumer[(role,f'g{group["group"]:02d}-f{i:03d}')]
     f['source']=rec['candidate']['path'];f['sha256']=rec['candidate']['sha256'];f['source_sha256']=rec['candidate']['sha256']
     rr['dependencies'].extend((rec['candidate'],rec['mask'],rec['preserved_native']))
  else:
   rec=byconsumer[(role,'native')];rr['source']=rec['candidate']['path'];rr['source_sha256']=rec['candidate']['sha256']
   rr['source_canvas']=rec['canvas'];rr.pop('crop',None)
   rr['dependencies'].extend((rec['candidate'],rec['mask'],rec['preserved_native']))
  rr['visual_approval_granted']=False;rr['status']='built-unreviewed'
  cr=S/'recipes-v6'/rp.name;cr.parent.mkdir(parents=True,exist_ok=True);cr.write_text(json.dumps(rr,indent=2,sort_keys=True)+'\n');recipes.append(pin(cr))
 summary['units'][unit]={'entries':entries,'generation':pin(gp),'recipes':recipes}
(S/'candidate-selection-v6.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({u:{'unique_poses':len(v['entries']),'changed':sum(e['changed_rgb_pixels'] for e in v['entries']),'occluded':[e['index'] for e in v['entries'] if e['occluded']]} for u,v in summary['units'].items()},indent=2))
