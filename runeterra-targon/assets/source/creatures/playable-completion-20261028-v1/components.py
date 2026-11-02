"""Technical alpha-island inventory; never draws or modifies artistic content."""
from __future__ import annotations
import numpy as np

def components(image, threshold=64, minimum=300):
    alpha=np.asarray(image.getchannel('A'))>threshold
    parents=[]; runs=[]; previous=[]
    def root(i):
        while parents[i]!=i:
            parents[i]=parents[parents[i]]; i=parents[i]
        return i
    for y,row in enumerate(alpha):
        delta=np.diff(np.r_[False,row,False].astype('i1'))
        starts=np.flatnonzero(delta==1); ends=np.flatnonzero(delta==-1); current=[]
        for x0,x1 in zip(starts,ends):
            i=len(parents);parents.append(i);runs.append((y,int(x0),int(x1)));current.append((x0,x1,i))
            for p0,p1,j in previous:
                if p0>x1: break
                if p1>=x0: parents[root(j)]=root(i)
        previous=current
    found={}
    for i,(y,x0,x1) in enumerate(runs):
        j=root(i)
        if j not in found:found[j]={'bbox':[x0,y,x1,y+1],'area':0,'runs':[]}
        c=found[j];b=c['bbox'];b[0]=min(b[0],x0);b[1]=min(b[1],y);b[2]=max(b[2],x1);b[3]=max(b[3],y+1);c['area']+=x1-x0;c['runs'].append((y,x0,x1))
    return [v for v in found.values() if v['area']>=minimum]
