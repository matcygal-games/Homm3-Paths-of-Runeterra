"""Actual all-state source-paving connectivity, with no inferred cliff roads.

This is a diagnostic, not physical admission. Retained architecture from ALL35
states is a hard obstacle to the common street. Each own approach may enter its
real observed doorway only; other-site buildings remain entirely blocked.
"""
from pathlib import Path
from collections import deque
import json,hashlib
import numpy as np
from PIL import Image,ImageChops
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[5]
OUT=HERE/'public-routes-study-v1'
OUT.mkdir(exist_ok=False)
def ref(p):return {'path':p.relative_to(PROJECT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def arr(p):return np.asarray(Image.open(p).convert('L'))>0
index_path=HERE/'ownership-separation-v3/states.json';index=json.loads(index_path.read_text())
anno_path=HERE/'ownership-contact-roles-v1/annotations.json';anno=json.loads(anno_path.read_text())
support=arr(HERE/'public-source-ground-v1/support.png');stairs=arr(HERE/'public-source-ground-v1/stairs.png');walk=support|stairs
body={k:np.asarray(Image.open(PROJECT/r['frame']).getchannel('A'))>=128 for k,r in index['states'].items()}
closed=np.logical_or.reduce(list(body.values()))
common=walk&~closed
h,w=common.shape
def neighbors(x,y):
 for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
  nx,ny=x+dx,y+dy
  if 0<=nx<w and 0<=ny<h:yield nx,ny
labels=np.full((h,w),-1,dtype=np.int32);components=[]
for y,x in zip(*np.nonzero(common)):
 if labels[y,x]>=0:continue
 cid=len(components);q=deque([(int(x),int(y))]);labels[y,x]=cid;pts=[]
 while q:
  xx,yy=q.popleft();pts.append((xx,yy))
  for nx,ny in neighbors(xx,yy):
   if common[ny,nx] and labels[ny,nx]<0:labels[ny,nx]=cid;q.append((nx,ny))
 components.append(pts)
main_id=int(labels[260,420]);main=labels==main_id
records={};paths=np.zeros_like(main);route_union=np.zeros_like(main)
def mask_definition(d):
 from PIL import ImageDraw
 im=Image.new('L',(800,374));draw=ImageDraw.Draw(im)
 for p in d.get('polygons',[]):draw.polygon(list(map(tuple,p)),fill=255)
 for p in d.get('lines',[]):draw.line(list(map(tuple,p['points'])),fill=255,width=p['width'])
 for x,y in d.get('pixels',[]):draw.point((x,y),fill=255)
 return np.asarray(im)>0
for key,r in anno['states'].items():
 door=mask_definition(r['door']);site=index['states'][key]['site']
 other=np.logical_or.reduce([b for k,b in body.items() if index['states'][k]['site']!=site])
 domain=(walk|door)&~other&~(body[key]&~door)
 starts=list(zip(*np.nonzero(door&domain)))
 q=deque();prev={}
 for y,x in starts:q.append((int(x),int(y)));prev[(int(x),int(y))]=None
 target=None
 while q:
  pt=q.popleft();x,y=pt
  if main[y,x]:target=pt;break
  for nx,ny in neighbors(x,y):
   if domain[ny,nx] and (nx,ny)not in prev:prev[(nx,ny)]=pt;q.append((nx,ny))
 path=[]
 if target is not None:
  pt=target
  while pt is not None:path.append(list(pt));pt=prev[pt]
  path.reverse()
  for x,y in path:route_union[y,x]=True
  records[key]={'main_public_component_reached':True,'approach_pixels':path,'length':len(path)}
 else:
  reached=sorted({int(labels[y,x])for x,y in prev if labels[y,x]>=0})
  records[key]={'main_public_component_reached':False,'door_reachable_components':reached,'door_reachable_pixels':len(prev)}
rgb=np.asarray(Image.open(HERE/'ownership-separation-v3/empty-native.png').convert('RGB')).copy()
colours=[(50+(i*71)%200,45+(i*113)%205,55+(i*173)%195)for i in range(len(components))]
for i,pts in enumerate(components):
 for x,y in pts:rgb[y,x]=(np.array(rgb[y,x],dtype=np.int16)+np.array(colours[i]))//2
rgb[route_union]=[255,20,180]
Image.fromarray(rgb).save(OUT/'native-component-overlay.png')
Image.fromarray(np.uint8(main)*255).save(OUT/'main-component.png')
report={'status':'design proposal','source_index':ref(index_path),'source_annotation':ref(anno_path),'main_component':main_id,'main_pixels':int(main.sum()),'component_count':len(components),'components':[{'id':i,'pixels':len(p),'bounds':[min(x for x,y in p),min(y for x,y in p),max(x for x,y in p)+1,max(y for x,y in p)+1]}for i,p in enumerate(components)],'states':records,'actual_public_consumer_executed':False,'source_walkable_only':True,'all35_bodies_hard_obstacles':True}
(OUT/'study.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps({'main_pixels':report['main_pixels'],'components':len(components),'reached':[k for k,v in records.items()if v['main_public_component_reached']],'unreached':{k:v for k,v in records.items()if not v['main_public_component_reached']}}))
