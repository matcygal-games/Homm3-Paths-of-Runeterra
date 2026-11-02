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
R=W/'build/reports/ionia-revision20261025-kashuri-v1'
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
