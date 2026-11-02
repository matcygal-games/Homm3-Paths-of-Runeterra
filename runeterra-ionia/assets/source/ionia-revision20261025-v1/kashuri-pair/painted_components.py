"""Deterministic connected ownership for actual painted 2D atlas cutouts.

This extracts whole, untouched source pixels. It creates no artwork and never
changes anatomy, clothing, limb ownership or individual pose proportions.
"""
import numpy as np
from PIL import Image, ImageFilter

def components(image, threshold=16):
    active=np.asarray(image.getchannel('A'))>=threshold
    parent=[0]; runs=[]; previous=[]
    def find(a):
        while parent[a]!=a:
            parent[a]=parent[parent[a]]; a=parent[a]
        return a
    for y,row in enumerate(active):
        edges=np.diff(np.pad(row.astype(np.int8),(1,1)))
        starts=np.where(edges==1)[0]; ends=np.where(edges==-1)[0]
        current=[]; j=0
        for left,right in zip(starts,ends):
            label=len(parent); parent.append(label)
            while j<len(previous) and previous[j][1]<left: j+=1
            k=j
            while k<len(previous) and previous[k][0]<=right:
                parent[find(label)]=find(previous[k][2]); k+=1
            current.append((int(left),int(right),label))
            runs.append((y,int(left),int(right),label))
        previous=current
    labels=np.zeros(active.shape,np.int32); rows={}
    for y,left,right,label in runs:
        root=find(label); labels[y,left:right]=root
        if root not in rows: rows[root]={'label':root,'area':0,'bounds':[left,y,right,y+1]}
        r=rows[root]; r['area']+=right-left
        b=r['bounds']; b[:]=[min(b[0],left),min(b[1],y),max(b[2],right),max(b[3],y+1)]
    for r in rows.values():
        l,t,rr,b=r['bounds'];r['edge_clipped']=l==0 or t==0 or rr==image.width or b==image.height
    return labels,[r for r in rows.values() if r['area']>=1500]

def ordered(rows,columns):
    rows=sorted(rows,key=lambda r:(r['bounds'][1]+r['bounds'][3])/2)
    return [r for start in range(0,len(rows),columns)
            for r in sorted(rows[start:start+columns],key=lambda r:r['bounds'][0])]

def isolate(image,labels,row,padding=3):
    l,t,r,b=row['bounds']; box=[max(0,l-padding),max(0,t-padding),min(image.width,r+padding),min(image.height,b+padding)]
    a=np.array(image.crop(tuple(box)).convert('RGBA'))
    sub=labels[box[1]:box[3],box[0]:box[2]]
    support=Image.fromarray(np.uint8(sub==row['label'])*255).filter(ImageFilter.MaxFilter(7))
    own=np.array(support)>0
    own[(sub!=0)&(sub!=row['label'])]=False
    a[~own]=0
    return Image.fromarray(a),Image.fromarray(np.uint8(own)*255),box
