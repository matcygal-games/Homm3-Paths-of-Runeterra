"""Isolate intact poses from controlled genuine painted2D production atlases.

This is technical ownership/alpha assembly, not figure drawing. A selected
object keeps its original RGBA inside its owned support. No adjacent figure,
clipped source body, reconstructed limb, 3D guide or per-frame scaling is used.
"""
from pathlib import Path
import hashlib,io,json
import numpy as np
from PIL import Image
S=Path(__file__).resolve().parent;P=S.parents[3];W=P.parent
R=W/'build/reports/regional-crests-20261025-v1/zaun-clean-t1-newactions'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def enc(v):return (json.dumps(v,indent=2,sort_keys=True)+'\n').encode()
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists() and p.read_bytes()!=b:raise ValueError('Frozen pose input differs; make a new version: '+str(p))
 p.write_bytes(b)
def png(p,im):
 b=io.BytesIO();im.save(b,format='PNG',compress_level=9,optimize=False);put(p,b.getvalue())
def rel(p):return p.relative_to(P).as_posix()
def objects(im):
 a=np.array(im.getchannel('A'));active=a>=16;h,w=active.shape;labels=np.zeros(active.shape,np.int32);ys,xs=np.nonzero(active);rows=[];counter=0
 for yy,xx in zip(ys,xs):
  if labels[yy,xx]:continue
  counter+=1;todo=[(int(yy),int(xx))];labels[yy,xx]=counter;count=0;left=right=int(xx);top=bottom=int(yy)
  while todo:
   y,x=todo.pop();count+=1;left=min(left,x);right=max(right,x);top=min(top,y);bottom=max(bottom,y)
   for dy in (-1,0,1):
    for dx in (-1,0,1):
     cy=y+dy;cx=x+dx
     if 0<=cy<h and 0<=cx<w and active[cy,cx] and not labels[cy,cx]:labels[cy,cx]=counter;todo.append((cy,cx))
  if count>=1500:rows.append({'label':counter,'area':count,'bounds':[left,top,right+1,bottom+1],'edge_clipped':left==0 or top==0 or right==w-1 or bottom==h-1})
 return labels,rows
def run():
 inventory_path=S/'source-inventory-v1.json';inventory=json.loads(inventory_path.read_text());allrecords=[]
 for source in inventory['sources']:
  path=P/source['path'];assert sha(path)==source['sha256'];im=Image.open(path).convert('RGBA');a=np.array(im);labels,rows=objects(im);cols=source['columns'];ordering=source['ordering']
  rows.sort(key=lambda r:(r['bounds'][0]+r['bounds'][2])/2 if ordering=='one-row' else (r['bounds'][1]+r['bounds'][3])/2)
  if ordering!='one-row':rows=[r for start in range(0,len(rows),cols) for r in sorted(rows[start:start+cols],key=lambda r:(r['bounds'][0]+r['bounds'][2])/2)]
  assert len(rows)==source['expected_objects'],(source['unit'],source['cohort'],len(rows));selected=set(source['selected_objects'])
  for index,row in enumerate(rows):
   if index not in selected:continue
   assert not row['edge_clipped'],('Clipped source cannot be final',source['unit'],source['cohort'],index)
   l,t,r,b=row['bounds'];box=[max(0,l-3),max(0,t-3),min(im.width,r+3),min(im.height,b+3)];core=labels[box[1]:box[3],box[0]:box[2]]==row['label'];ownership=core.copy()
   # Retain only this body's antialias fringe. Adjacent component pixels are
   # never copied merely because two rectangular pose bounds intersect.
   for dy in range(-2,3):
    for dx in range(-2,3):
     y0=max(0,dy);y1=min(core.shape[0],core.shape[0]+dy);x0=max(0,dx);x1=min(core.shape[1],core.shape[1]+dx)
     ownership[y0:y1,x0:x1]|=core[y0-dy:y1-dy,x0-dx:x1-dx]
   ownlabels=labels[box[1]:box[3],box[0]:box[2]];ownership&=(ownlabels==row['label'])|(ownlabels==0);crop=a[box[1]:box[3],box[0]:box[2]].copy();crop[~ownership]=0
   assert not np.any((ownlabels!=0)&(ownlabels!=row['label'])&(crop[:,:,3]>0));out=S/source['unit']/'isolated-v1'/f"{source['cohort']}-o{index:02d}.png";mask=S/source['unit']/'isolated-v1'/f"{source['cohort']}-o{index:02d}-ownership.png";png(out,Image.fromarray(crop));png(mask,Image.fromarray(ownership.astype(np.uint8)*255));allrecords.append({'unit':source['unit'],'cohort':source['cohort'],'object_index':index,'master':source['path'],'master_sha256':source['sha256'],'source_window':box,'original_body_bounds':row['bounds'],'isolated':rel(out),'isolated_sha256':sha(out),'ownership_mask':rel(mask),'ownership_mask_sha256':sha(mask),'adjacent_components_excluded':True,'source_body_RGBA_inside_owner_exact':True,'whole_source_object_not_clipped':True})
  print(source['unit'],source['cohort'],'selected',len(selected),flush=True)
 receipt={'status':'authored configuration','source_inventory':rel(inventory_path),'source_inventory_sha256':sha(inventory_path),'producer':rel(Path(__file__)),'producer_sha256':sha(Path(__file__)),'records':allrecords,'no_body_warp_or_pose_synthesis':True,'selected_or_staged':False,'runtime_verified':False,'release_accepted':False};put(S/'isolated-source-receipt-v1.json',enc(receipt));print('Selected intact source poses:',len(allrecords))
if __name__=='__main__':run()
