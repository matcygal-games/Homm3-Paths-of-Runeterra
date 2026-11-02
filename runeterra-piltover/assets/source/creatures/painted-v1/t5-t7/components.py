"""Technical connected-component inventory of genuinely painted transparent pixels."""
from collections import deque
import numpy as np

def components(alpha, threshold=8):
    work=np.asarray(alpha,dtype=np.uint8).copy()>=threshold
    h,w=work.shape
    remaining=set(map(int,np.flatnonzero(work)))
    result=[]
    while remaining:
        first=remaining.pop(); pending=deque([first]); area=0
        x0=x1=first%w; y0=y1=first//w; pixels=[]
        while pending:
            pos=pending.popleft(); y,x=divmod(pos,w);area+=1;pixels.append(pos)
            x0=min(x0,x);x1=max(x1,x);y0=min(y0,y);y1=max(y1,y)
            neighbors=[]
            if x:neighbors.append(pos-1)
            if x+1<w:neighbors.append(pos+1)
            if y:neighbors.append(pos-w)
            if y+1<h:neighbors.append(pos+w)
            for other in neighbors:
                if other in remaining:remaining.remove(other);pending.append(other)
        result.append({'area':area,'box':[x0,y0,x1+1,y1+1],'pixels':pixels})
    return sorted(result,key=lambda x:x['area'],reverse=True)
