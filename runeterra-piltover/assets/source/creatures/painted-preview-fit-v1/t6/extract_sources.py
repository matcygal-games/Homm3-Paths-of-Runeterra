"""Technical whole-actor separation of genuine painted animation sheets.

No drawing, per-pose resize, limb warping, borrowed pixels or invented actions.
Source-alpha components are retained in their original positions and density.
"""
from pathlib import Path
import argparse, json, hashlib, re
import numpy as np
from PIL import Image, ImageFilter
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if p.name=='runeterra-piltover')
UNIT_IDS=('hextechRotorwing','hextechStormwing')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
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
 stats={}
 lut=np.asarray([find(k) for k in range(len(parents))],np.int32);labels=lut[labels]
 for label,x0,y,x1 in runs:
  k=int(lut[label]);s=stats.setdefault(k,{'bbox':[w,h,0,0],'area':0,'sx':0.,'sy':0.})
  n=x1-x0;b=s['bbox'];b[0]=min(b[0],x0);b[1]=min(b[1],y);b[2]=max(b[2],x1);b[3]=max(b[3],y+1)
  s['area']+=n;s['sx']+=n*(x0+x1-1)/2;s['sy']+=n*y
 return labels,stats
def process(unit,kind):
 if unit not in UNIT_IDS or kind not in ('movement','combat','flight'):raise ValueError('Unknown owned source unit/cohort')
 selection_path=HERE/'selected-cohorts-v1.json'
 selection=json.loads(selection_path.read_text(encoding='utf-8')) if selection_path.is_file() else {}
 filename=selection.get(unit,{}).get(kind,kind+'-v1.png')
 if not re.fullmatch(re.escape(kind)+r'-v[1-9][0-9]*\.png',filename):raise ValueError('Selected cohort must be an exact safe local versioned PNG filename')
 source=HERE/unit/filename;im=Image.open(source).convert('RGBA')
 alpha_policy=None
 labels,stats=components(im.getchannel('A'))
 majors=[k for k,s in stats.items() if s['area']>=2000]
 expected=8 if kind=='flight' else 16
 if len(majors)!=expected:raise ValueError(f'{unit}/{kind}: expected{expected} whole actors, got{len(majors)}; inspect before extraction')
 def centroid(k):s=stats[k];return s['sx']/s['area'],s['sy']/s['area']
 columns=4
 ordered=[]
 by_y=sorted(majors,key=lambda k:centroid(k)[1])
 for off in range(0,len(by_y),columns):ordered.extend(sorted(by_y[off:off+columns],key=lambda k:centroid(k)[0]))
 owners={k:k for k in majors}
 def distance(k,m):
  x,y=centroid(k);a,b,c,d=stats[m]['bbox'];return max(a-x,0,x-c)**2+max(b-y,0,y-d)**2
 for k,s in stats.items():
  if k in owners:continue
  near=min(majors,key=lambda m:distance(k,m))
  if distance(k,near)<=64**2:owners[k]=near
  elif s['area']>=8:raise ValueError(f'Unassociated painted part {unit}/{kind}: {s}')
 out=HERE/unit/'isolated';out.mkdir(parents=True,exist_ok=True);rows=[]
 for index,k in enumerate(ordered):
  ids=[a for a,b in owners.items() if b==k]
  own_core=np.isin(labels,ids)
  foreign_core=np.isin(labels,[a for a,b in owners.items() if b!=k])
  own_expanded=np.asarray(Image.fromarray(np.where(own_core,255,0).astype('uint8')).filter(ImageFilter.MaxFilter(7)))>0
  foreign_expanded=np.asarray(Image.fromarray(np.where(foreign_core,255,0).astype('uint8')).filter(ImageFilter.MaxFilter(7)))>0
  # Preserve every owned alpha>=32 pixel. Ambiguous soft alpha between close,
  # separate silhouettes is excluded rather than stealing a neighbour's edge.
  mask=Image.fromarray(np.where((own_expanded & ~foreign_expanded)|own_core,255,0).astype('uint8'))
  if np.any((np.asarray(mask)>0)&foreign_core):raise ValueError(f'Cross-actor contamination at{unit}/{kind}/{index}')
  actor=im.copy();actor.putalpha(Image.fromarray(np.where(np.asarray(mask)>0,np.asarray(im.getchannel('A')),0).astype('uint8')))
  bbox=actor.getchannel('A').getbbox();p=out/f'{kind}-{index:02d}.png';actor.crop(bbox).save(p)
  rows.append({'index':index,'source':source.relative_to(PROJECT).as_posix(),'source_sha256':sha(source),'source_canvas':list(im.size),'crop':list(bbox),'principal_bbox':stats[k]['bbox'],'principal_centroid':list(centroid(k)),'image':p.relative_to(PROJECT).as_posix(),'sha256':sha(p),'alpha_treatment':alpha_policy,'anatomical_root':'pending explicit projected-root annotation; never inferred from alpha bounds'})
 return rows
def main():
 p=argparse.ArgumentParser();p.add_argument('--unit',nargs='+',choices=UNIT_IDS,required=True);args=p.parse_args()
 for unit in args.unit:
  selection_path=HERE/'selected-cohorts-v1.json'
  selection=json.loads(selection_path.read_text(encoding='utf-8')) if selection_path.is_file() else {}
  rows={kind:process(unit,kind) for kind in ('movement','combat','flight') if (HERE/unit/selection.get(unit,{}).get(kind,kind+'-v1.png')).is_file()}
  target=HERE/unit/'isolated-source-map-v1.json';target.write_text(json.dumps({'status':'authored configuration','method':'Whole painted actor separation only; no root fitting or per-pose scaling','cohorts':rows},indent=2)+'\n',encoding='utf-8')
  print(unit,{k:len(v) for k,v in rows.items()})
if __name__=='__main__':main()
