"""Separate whole genuine painted actors; never generate or warp body pixels."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image,ImageFilter
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if p.name=='runeterra-ixtal')
UNITS=('auroraHallunatis','crownedHallunatis','pairofant','elderPairofant')
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
 stats={};lut=np.asarray([find(k) for k in range(len(parents))],np.int32);labels=lut[labels]
 for label,x0,y,x1 in runs:
  k=int(lut[label]);s=stats.setdefault(k,{'bbox':[w,h,0,0],'area':0,'sx':0.,'sy':0.})
  n=x1-x0;b=s['bbox'];b[0]=min(b[0],x0);b[1]=min(b[1],y);b[2]=max(b[2],x1);b[3]=max(b[3],y+1)
  s['area']+=n;s['sx']+=n*(x0+x1-1)/2;s['sy']+=n*y
 return labels,stats
def process(unit,kind):
 name=('holding-v3.png' if unit=='elderPairofant' else 'holding-v2.png')if kind=='holding'else kind+'-v1.png'
 source=HERE/unit/name;im=Image.open(source).convert('RGBA')
 # The base combat sheet's three touching corpses remain historical; a new
 # independent four-pose death sheet supplies that action without body cuts.
 if unit=='pairofant' and kind=='combat':im=im.crop((0,0,im.width,770))
 labels,stats=components(im.getchannel('A'))
 expected=4 if kind in ('death','holding') else 8 if kind=='flight' else 12 if unit=='pairofant' and kind=='combat' else 16
 majors=[k for k,s in stats.items() if s['area']>=2000]
 if len(majors)!=expected:raise ValueError(f'{unit}/{kind}: expected {expected} complete actors; got {len(majors)}: '+str([stats[k]for k in majors]))
 def centroid(k):s=stats[k];return s['sx']/s['area'],s['sy']/s['area']
 ordered=[];by_y=sorted(majors,key=lambda k:centroid(k)[1])
 columns=2 if kind in ('death','holding') else 4
 for off in range(0,len(by_y),columns):ordered.extend(sorted(by_y[off:off+columns],key=lambda k:centroid(k)[0]))
 owners={k:k for k in majors}
 def distance(k,m):
  x,y=centroid(k);a,b,c,d=stats[m]['bbox'];return max(a-x,0,x-c)**2+max(b-y,0,y-d)**2
 for k,s in stats.items():
  if k not in owners:
   near=min(majors,key=lambda m:distance(k,m))
   if distance(k,near)<=64**2:owners[k]=near
   elif s['area']>=8:raise ValueError('Unassociated visible painted component: '+str(s))
 out=HERE/unit/'isolated';out.mkdir(exist_ok=True);rows=[]
 for index,k in enumerate(ordered):
  ids=[a for a,b in owners.items()if b==k];own=np.isin(labels,ids);foreign=np.isin(labels,[a for a,b in owners.items()if b!=k])
  expanded=np.asarray(Image.fromarray(np.where(own,255,0).astype('uint8')).filter(ImageFilter.MaxFilter(7)))>0
  foreign_expanded=np.asarray(Image.fromarray(np.where(foreign,255,0).astype('uint8')).filter(ImageFilter.MaxFilter(7)))>0
  mask=(expanded&~foreign_expanded)|own
  assert not np.any(mask&foreign)
  pixels=np.array(im);pixels[:,:,3]=np.where(mask,pixels[:,:,3],0)
  actor=Image.fromarray(pixels);bbox=actor.getchannel('A').getbbox();p=out/f'{kind}-{index:02d}.png';actor.crop(bbox).save(p,compress_level=9)
  assert np.array_equal(pixels[:,:,:3],np.array(im)[:,:,:3])
  rows.append({'index':index,'source':source.relative_to(PROJECT).as_posix(),'source_sha256':sha(source),'source_canvas':list(im.size),'crop':list(bbox),'principal_bbox':stats[k]['bbox'],'principal_centroid':list(centroid(k)),'image':p.relative_to(PROJECT).as_posix(),'sha256':sha(p),'source_rgb_preserved':True,'source_alpha_core_preserved':True,'native_root':'pending manual annotation'})
 return rows
if __name__=='__main__':
 for unit in UNITS:
  cohorts={kind:process(unit,kind)for kind in ('movement','combat','flight','death')if(HERE/unit/(kind+'-v1.png')).is_file()}
  cohorts['holding']=process(unit,'holding')
  (HERE/unit/'isolated-source-map-v1.json').write_text(json.dumps({'status':'authored configuration','method':'whole-alpha-component separation; original RGBA retained within mask; no code-drawn body or per-pose fitting','cohorts':cohorts},indent=2)+'\n')
  print(unit,{k:len(v)for k,v in cohorts.items()})
