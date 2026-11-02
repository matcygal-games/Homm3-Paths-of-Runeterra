"""Run-length connected-component isolation; no artwork synthesis. Reused unchanged extraction algorithm from prior painted2D candidate tooling."""
from pathlib import Path
import numpy as np,json
from PIL import Image
def components(mask):
 parent=[];stats=[];runs=[];previous=[]
 def root(k):
  while parent[k]!=k:parent[k]=parent[parent[k]];k=parent[k]
  return k
 for y,row in enumerate(mask):
  v=np.pad(row.astype('int8'),(1,1));edges=np.diff(v);starts=np.nonzero(edges==1)[0];ends=np.nonzero(edges==-1)[0];current=[];j=0
  for x0,x1 in zip(starts,ends):
   k=len(parent);parent.append(k);stats.append([int(x0),y,int(x1),y+1,int(x1-x0)]);current.append((x0,x1,k));runs.append((y,int(x0),int(x1),k))
   while j<len(previous)and previous[j][1]<x0:j+=1
   z=j
   while z<len(previous)and previous[z][0]<=x1:
    a=root(k);b=root(previous[z][2]);parent[b]=a;z+=1
  previous=current
 groups={}
 for y,x0,x1,k in runs:
  k=root(k)
  if k not in groups:groups[k]={'box':[x0,y,x1,y+1],'area':0,'runs':[]}
  g=groups[k];b=g['box'];g['box']=[min(b[0],x0),min(b[1],y),max(b[2],x1),max(b[3],y+1)];g['area']+=x1-x0;g['runs'].append([y,x0,x1])
 return list(groups.values())
