"""Isolated sparse behind-roof proof. No shared consumer/canonical writes."""
from pathlib import Path
from collections import deque
import heapq,hashlib,json,sys
from PIL import Image,ImageChops,ImageDraw
import prototype_roofs as P
HERE=P.HERE;ROOT=P.ROOT;ROWS=P.ROWS;SIZE=P.SIZE
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
def poly(points):return P.poly(points)
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n',encoding='utf8')
def binary(im,t=128):return im.getchannel('A').point(lambda p:255 if p>=t else 0)
def neighbours(p):return ((p[0]-1,p[1]),(p[0]+1,p[1]),(p[0],p[1]-1),(p[0],p[1]+1))
def within(p):return 0<=p[0]<800 and 0<=p[1]<374
def line_points(points):
 out=[]
 for a,b in zip(points,points[1:]):
  # Cardinal line rasterization; intermediate corners stay on painted frontage.
  x,y=a;dx=b[0]-x;dy=b[1]-y;steps=abs(dx)+abs(dy);done=0
  if not out:out.append((x,y))
  while (x,y)!=tuple(b):
   target_x=a[0]+dx*(done+1)/steps;target_y=a[1]+dy*(done+1)/steps
   options=[]
   if x!=b[0]:options.append((abs(x+(1 if dx>0 else -1)-target_x)+abs(y-target_y),0,(x+(1 if dx>0 else -1),y)))
   if y!=b[1]:options.append((abs(x-target_x)+abs(y+(1 if dy>0 else -1)-target_y),1,(x,y+(1 if dy>0 else -1))))
   _,_,(x,y)=min(options);out.append((x,y));done+=1
 return out
def mask_points(points):
 m=Image.new('L',SIZE)
 for p in points:m.putpixel(p,255)
 return m
def parts(mask):return P.components(mask)
def main():
 out=HERE/'passage-proof-v1';out.mkdir(exist_ok=True)
 layers={s:Image.open(HERE/'structures'/s/'layer.png').convert('RGBA') for s in ROWS}
 bodies={s:binary(im) for s,im in layers.items()};union=Image.new('L',SIZE);roots=Image.new('L',SIZE);roofs={};blocked=Image.new('L',SIZE)
 for state,row in ROWS.items():
  b=bodies[state];union=ImageChops.lighter(union,b)
  root=Image.open(P.SOURCE/'structures'/state/'foundation.png').convert('L');root=ImageChops.multiply(root,b)
  if not root.getbbox():
   bb=b.getbbox();root=Image.new('L',SIZE)
   if bb:root.paste(b.crop((bb[0],max(bb[1],bb[3]-2),bb[2],bb[3])),(bb[0],max(bb[1],bb[3]-2)))
  roots=ImageChops.lighter(roots,root);save(out/'states'/state/'root.png',root)
  r=Image.open(HERE/'roof-traces'/f'{state}.png').convert('L') if row['site']!='coast' else Image.new('L',SIZE)
  roofs[state]=ImageChops.multiply(r,b);blocked=ImageChops.lighter(blocked,ImageChops.subtract(b,roofs[state]))
 land=poly([(0,97),(20,97),(34,93),(125,92),(230,103),(302,109),(510,108),(518,131),(550,144),(621,161),(641,145),(650,111),(768,111),(799,129),(799,373),(0,373)])
 water=Image.open(P.SOURCE/'terrain/coastal-water-mask.png').convert('L');land=ImageChops.subtract(land,water)
 visible=ImageChops.subtract(land,union);potential=ImageChops.subtract(land,ImageChops.lighter(blocked,roots))
 access=Image.new('L',SIZE);accesses={};failures=[]
 for state,row in ROWS.items():
  points=row.get('route_points') or [tuple(row['entrance']),(390,342),(385,335),(380,333)]
  if state=='resourceSilo':points=[(570,166),(615,170),(626,173)]
  raw=line_points(points);inside=[i for i,p in enumerate(raw) if bodies[state].getpixel(p)]
  if row['site']=='coast':anchor=(489,334);tail=[anchor,(489,333)]
  elif not inside and row.get('entry_kind')=='open_arch':anchor=raw[0];tail=raw
  elif not inside:failures.append(state+': no physical frontage point');continue
  else:anchor=raw[max(inside)];tail=raw[max(inside):]
  if len(tail)>1:
   dx=tail[-1][0]-tail[-2][0];dy=tail[-1][1]-tail[-2][1]
   while within(tail[-1]) and not visible.getpixel(tail[-1]) and len(tail)<100:
    p=(tail[-1][0]+dx,tail[-1][1]+dy)
    if not within(p):break
    tail.append(p)
  if len(tail)<2:failures.append(state+': no external access');continue
  approach=mask_points(tail);door=Image.new('L',SIZE);draw=ImageDraw.Draw(door);draw.rectangle((anchor[0]-1,anchor[1]-1,anchor[0]+1,anchor[1]+1),fill=255)
  if row['site']=='coast':draw.line([(489,334),(489,351)],fill=255,width=1)
  other=Image.new('L',SIZE)
  for s in ROWS:
   if ROWS[s]['site']!=row['site']:other=ImageChops.lighter(other,bodies[s])
  if ImageChops.multiply(approach,other).getbbox():failures.append(state+': local access still intersects another body')
  if ImageChops.subtract(ImageChops.multiply(approach,bodies[state]),door).getbbox():failures.append(state+': local access traverses own body outside threshold')
  # A visible threshold cannot be exempted by a roof record.
  if ImageChops.multiply(door,other).getbbox():
   door=ImageChops.subtract(door,other)
   if not door.getpixel(anchor):failures.append(state+': anchor hidden by another body')
  endpoint=tail[-1]
  if not visible.getpixel(endpoint):failures.append(state+': exit not on true visible ground '+str(endpoint))
  access=ImageChops.lighter(access,ImageChops.lighter(door,approach));save(out/'states'/state/'door.png',door);save(out/'states'/state/'approach.png',approach)
  accesses[state]={'anchor':list(anchor),'endpoint':endpoint,'door':ref(out/'states'/state/'door.png'),'approach':ref(out/'states'/state/'approach.png'),'kind':'open-site','description':'Visible visitor threshold at the actual outer forecourt, fenced-yard gate or entry-stair landing; inner building portals are not relabeled as public roads.'}
 # Only hidden pixels are excluded from local accesses; visible centreline joins remain legal.
 protected=ImageChops.lighter(roots,access);hidden_allowed={}
 for s,r in roofs.items():hidden_allowed[s]=ImageChops.subtract(r,protected)
 blocked=Image.new('L',SIZE)
 for s,b in bodies.items():
  allowed=ImageChops.lighter(hidden_allowed[s],Image.open(ROOT/accesses[s]['door']['path']).convert('L')) if s in accesses else hidden_allowed[s]
  blocked=ImageChops.lighter(blocked,ImageChops.subtract(b,allowed))
 potential=ImageChops.subtract(land,blocked)
 path_visible=visible.copy()
 for s,item in accesses.items():path_visible=ImageChops.lighter(path_visible,ImageChops.multiply(land,Image.open(ROOT/item['door']['path']).convert('L')))
 origin=(380,320)
 if not visible.getpixel(origin):failures.append('Origin is not visible public ground')
 tree={origin};paths=[];hidden_records=[]
 for state,item in accesses.items():
  start=tuple(item['endpoint'])
  if not potential.getpixel(start):failures.append(state+': endpoint not in proven navigation domain');continue
  distances={start:0};prev={};heap=[(0,start)];target=None
  while heap:
   cost,p=heapq.heappop(heap)
   if cost!=distances.get(p):continue
   if p in tree and path_visible.getpixel(p):target=p;break
   for q in neighbours(p):
    if not within(q) or not potential.getpixel(q):continue
    score=cost+(1 if path_visible.getpixel(q) else 16)
    if score<distances.get(q,10**12):distances[q]=score;prev[q]=p;heapq.heappush(heap,(score,q))
  if target is None:failures.append(state+': no root/access-safe projected path');continue
  path=[target]
  while path[-1]!=start:path.append(prev[path[-1]])
  path.reverse();paths.extend(path);tree.update(path)
  # Record each consecutive hidden interval with its genuine visible endpoints.
  i=0
  while i<len(path):
   if path_visible.getpixel(path[i]):i+=1;continue
   first=i
   while i<len(path) and not path_visible.getpixel(path[i]):i+=1
   if first==0 or i==len(path):failures.append(state+': hidden segment lacks two visible ends');continue
   seg=path[first-1:i+1];hidden=mask_points(path[first:i]);case_id=f'passage-{len(hidden_records):02}'
   occluders=[s for s,b in bodies.items() if ImageChops.multiply(hidden,b).getbbox()]
   sites=sorted({ROWS[s]['site'] for s in occluders})
   if len(sites)!=1:failures.append(case_id+': adjacent projected roofs need separate visible break: '+str(sites))
   record={'id':case_id,'requested_by':state,'path':seg,'visible_endpoints':[list(seg[0]),list(seg[-1])],'occluding_site':sites,'occluding_states':occluders,'hidden_pixels':hidden.histogram()[255],'hidden_bbox':list(hidden.getbbox()),'not_selected':True}
   save(out/'passages'/case_id/'path.png',mask_points(seg));save(out/'passages'/case_id/'hidden.png',hidden)
   record['path_mask']=ref(out/'passages'/case_id/'path.png');record['hidden_mask']=ref(out/'passages'/case_id/'hidden.png');hidden_records.append(record)
 network=mask_points(paths or [origin]);save(out/'global-path-centrelines.png',network);save(out/'land.png',land);save(out/'roots-protected.png',roots);save(out/'local-access-protected.png',access);save(out/'navigation-domain.png',potential)
 full=Image.open(HERE/'full.png').convert('RGBA');overlay=Image.new('RGBA',SIZE,(80,240,170,0));overlay.putalpha(network.point(lambda p:220 if p else 0));full.alpha_composite(overlay);full.save(out/'network-overlay.png')
 write(out/'proof.json',{'status':'authored configuration','prototype_only':True,'canonical_or_shared_files_modified':False,'accesses':accesses,'passages':hidden_records,'failures':failures,'all_required_exits_connected':not failures,'contract':'No roof can exempt a local doorway/approach, any real ground root, or a true masonry/non-roof body pixel. Each hidden run needs two visible ground ends and exactly one projected foreground roof site.'})
 print(json.dumps({'states':len(accesses),'hidden_runs':len(hidden_records),'failures':failures,'network_pixels':network.histogram()[255]},indent=2))
if __name__=='__main__':main()
