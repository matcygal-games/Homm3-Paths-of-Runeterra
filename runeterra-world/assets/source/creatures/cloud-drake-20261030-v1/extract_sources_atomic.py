"""Separate complete painted alpha components; never paint/warp body pixels."""
from pathlib import Path
import argparse,hashlib,json,io,os
import numpy as np
from PIL import Image,ImageFilter
BASE=Path(__file__).resolve().parent
PROJECT=next(p for p in BASE.parents if p.name=="runeterra-world")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save_png(p,im):
    temp=PROJECT.parent/'reports/world-cloud-drake-art-20261030-v1/.atomic'/('extract-'+p.name);temp.parent.mkdir(parents=True,exist_ok=True);buffer=io.BytesIO();im.save(buffer,format='PNG',compress_level=9);temp.write_bytes(buffer.getvalue());os.replace(temp,p)
def components(alpha):
    mask=np.asarray(alpha)>=32;h,w=mask.shape
    labels=np.zeros((h,w),np.int32);parents=[0];runs=[];previous=[]
    def find(n):
        while parents[n]!=n:parents[n]=parents[parents[n]];n=parents[n]
        return n
    def union(a,b):
        a,b=find(a),find(b)
        if a!=b:parents[max(a,b)]=min(a,b)
    for y in range(h):
        edge=np.diff(np.r_[False,mask[y],False].astype(np.int8));current=[];j=0
        for x0,x1 in zip(np.flatnonzero(edge==1),np.flatnonzero(edge==-1)):
            label=len(parents);parents.append(label);labels[y,x0:x1]=label;runs.append((label,int(x0),y,int(x1)))
            while j<len(previous) and previous[j][1]<x0-1:j+=1
            for a,b,k in previous[j:]:
                if a>x1:break
                union(label,k)
            current.append((int(x0),int(x1),label))
        previous=current
    stats={};lut=np.asarray([find(k)for k in range(len(parents))],np.int32);labels=lut[labels]
    for label,x0,y,x1 in runs:
        k=int(lut[label]);s=stats.setdefault(k,{"bbox":[w,h,0,0],"area":0,"sx":0.,"sy":0.})
        n=x1-x0;b=s["bbox"];b[0]=min(b[0],x0);b[1]=min(b[1],y);b[2]=max(b[2],x1);b[3]=max(b[3],y+1)
        s["area"]+=n;s["sx"]+=n*(x0+x1-1)/2;s["sy"]+=n*y
    return labels,stats
def process(unit,cohort,filename,expected,columns):
    source=BASE/unit/filename;im=Image.open(source).convert("RGBA");labels,stats=components(im.getchannel("A"))
    major=[k for k,s in stats.items() if s["area"]>=1500]
    if len(major)!=expected:raise ValueError(f"{unit}/{cohort}: expected{expected} separate whole actors; got{len(major)} "+str([stats[k]for k in major]))
    def centroid(k):s=stats[k];return s["sx"]/s["area"],s["sy"]/s["area"]
    ordered=[];by_y=sorted(major,key=lambda k:centroid(k)[1])
    for off in range(0,len(by_y),columns):ordered.extend(sorted(by_y[off:off+columns],key=lambda k:centroid(k)[0]))
    owners={k:k for k in major}
    def distance(k,m):
        x,y=centroid(k);a,b,c,d=stats[m]["bbox"];return max(a-x,0,x-c)**2+max(b-y,0,y-d)**2
    for k,s in stats.items():
        if k not in owners:
            near=min(major,key=lambda m:distance(k,m))
            if distance(k,near)<=64**2:owners[k]=near
            elif s["area"]>=8:raise ValueError("Unassociated visible painted component: "+str(s))
    rows=[];folder=BASE/unit/"isolated";folder.mkdir(exist_ok=True)
    for index,k in enumerate(ordered):
        ids=[a for a,b in owners.items()if b==k];own=np.isin(labels,ids);foreign=np.isin(labels,[a for a,b in owners.items()if b!=k])
        expanded=np.asarray(Image.fromarray(np.where(own,255,0).astype("uint8")).filter(ImageFilter.MaxFilter(7)))>0
        foreign_expanded=np.asarray(Image.fromarray(np.where(foreign,255,0).astype("uint8")).filter(ImageFilter.MaxFilter(7)))>0
        mask=(expanded&~foreign_expanded)|own
        assert not np.any(mask&foreign)
        pixels=np.array(im);pixels[:,:,3]=np.where(mask,pixels[:,:,3],0)
        actor=Image.fromarray(pixels);box=actor.getchannel("A").getbbox();p=folder/f"{cohort}-{index:02d}.png";save_png(p,actor.crop(box))
        assert np.array_equal(pixels[:,:,:3],np.array(im)[:,:,:3])
        rows.append({"index":index,"source":source.relative_to(PROJECT).as_posix(),"source_sha256":sha(source),"source_canvas":list(im.size),"crop":list(box),"principal_bbox":stats[k]["bbox"],"principal_centroid":list(centroid(k)),"image":p.relative_to(PROJECT).as_posix(),"sha256":sha(p),"source_rgb_preserved":True,"source_alpha_core_preserved":True,"principal_touches_source_edge":any((stats[k]["bbox"][0]<=0,stats[k]["bbox"][1]<=0,stats[k]["bbox"][2]>=im.width,stats[k]["bbox"][3]>=im.height))})
    return rows