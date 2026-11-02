"""Technical connected-alpha inventory; never draws, deforms or invents art."""
from pathlib import Path
import json
import numpy as np
from PIL import Image

def islands(image, threshold=16):
    a=np.array(image.getchannel('A'))
    parent=[];runs=[];previous=[]
    def find(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]];i=parent[i]
        return i
    def union(a,b):
        a=find(a);b=find(b)
        if a!=b:parent[b]=a
    for y,row in enumerate(a):
        bits=np.r_[False,row>=threshold,False].astype(np.int8)
        bounds=np.flatnonzero(np.diff(bits));current=[]
        for start,end in zip(bounds[::2],bounds[1::2]):
            i=len(parent);parent.append(i);runs.append((y,int(start),int(end),i));current.append((start,end,i))
            for pstart,pend,pid in previous:
                if pend<start:continue
                if pstart>end:break
                union(i,pid)
        previous=current
    grouped={}
    for y,s,e,i in runs:
        key=find(i);grouped.setdefault(key,[]).append((y,s,e))
    result=[]
    for lines in grouped.values():
        count=sum(e-s for y,s,e in lines)
        if count<1000:continue
        box=[min(s for y,s,e in lines),min(y for y,s,e in lines),max(e for y,s,e in lines),max(y for y,s,e in lines)+1]
        result.append({'pixels':count,'box':box,'lines':lines})
    return sorted(result,key=lambda r:(r['box'][1],r['box'][0]))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('--output',type=Path)
    a=p.parse_args();im=Image.open(a.source).convert('RGBA');items=islands(im)
    print(json.dumps({'source':a.source.as_posix(),'dimensions':im.size,'islands':[{k:v for k,v in q.items()if k!='lines'}for q in items]},indent=2))
    if a.output:
        a.output.mkdir(parents=True,exist_ok=True)
        for i,q in enumerate(items):
            mask=np.zeros((im.height,im.width),dtype=np.uint8)
            for y,s,e in q['lines']:mask[y,s:e]=1
            arr=np.array(im);arr[:,:,3]*=mask
            Image.fromarray(arr).crop(q['box']).save(a.output/f'island-{i:02d}.png')
