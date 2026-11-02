"""NX1 physical ownership prototype: immutable prior sources; own new cohort."""
from pathlib import Path
import hashlib,json,sys
from collections import deque
from PIL import Image,ImageChops,ImageDraw,ImageFilter
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
OUT=ROOT/'assets/source/town/approved-nx1-physical-20261030-v1'
SELECTION=json.loads((HERE/'selected/selection.json').read_text(encoding='utf8'))
SIZE=(800,374)
TRIMS={'mageGuild4':[(0,99),(130,99),(130,130),(0,130)],
       'special1':[(130,100),(198,100),(198,115),(130,115)],
       'special3':[(0,0),(225,0),(225,119),(0,119)],
       'dwellingUpLvl6':[(210,185),(342,185),(342,207),(210,207)],
       'resourceSilo':[(515,175),(627,175),(627,190),(515,190)],
       'dwellingUpLvl2':[(522,237),(660,237),(660,250),(522,250)],
       'dwellingUpLvl5':[(638,176),(740,176),(740,190),(638,190)],
       'dwellingUpLvl7':[(716,284),(799,284),(799,300),(716,300)]}
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def binary(im,t=128):return im.getchannel('A').point(lambda a:255 if a>=t else 0)
def poly(points):
 m=Image.new('L',SIZE);ImageDraw.Draw(m).polygon(points,fill=255);return m
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 approved=Image.open(HERE.parent/'approved-nx1-20261029-v1/approved-native.png').convert('RGBA')
 background=Image.open(ROOT/SELECTION['background']['path']).convert('RGBA');rows={r['state']:r for r in SELECTION['states']};layers={};bodies={};newrows={};terrain_owner=Image.new('L',SIZE)
 for state,row in rows.items():
  im=Image.open(ROOT/row['native_layer']).convert('RGBA')
  if row['site']!='coast':
   actual=Image.open(HERE/'structures'/state/'area.png').getchannel('A')
   apron=ImageChops.subtract(im.getchannel('A'),actual)
   # Preserve real upper roof/banners/fringes; only lower public frontage may
   # return to terrain ownership. A broad polygon is not a matting oracle.
   lower=poly([(0,max(0,row['entrance'][1]-4)),(799,max(0,row['entrance'][1]-4)),(799,373),(0,373)])
   public_apron=ImageChops.multiply(apron,lower);terrain_owner=ImageChops.lighter(terrain_owner,public_apron);im.putalpha(ImageChops.subtract(im.getchannel('A'),public_apron))
  if state in TRIMS:
   trim=poly(TRIMS[state]);removed=ImageChops.multiply(im.getchannel('A'),trim);terrain_owner=ImageChops.lighter(terrain_owner,removed);im.putalpha(ImageChops.subtract(im.getchannel('A'),trim))
  layers[state]=im;bodies[state]=binary(im);save(OUT/'structures'/state/'layer.png',im);save(OUT/'structures'/state/'body.png',bodies[state])
 background.paste(approved,(0,0),terrain_owner);save(OUT/'terrain/background.png',background);save(OUT/'terrain/public-terrain-reassignment.png',terrain_owner)
 full=background.copy()
 ordinary=[r['state'] for r in rows.values() if r['site']!='coast']
 sites={}
 for state in ordinary:sites.setdefault(rows[state]['site'],[]).append(state)
 top=[]
 for site,states in sites.items():top.append(states[-1])
 for state in sorted(top,key=lambda s:rows[s]['native_z']):full.alpha_composite(layers[state])
 save(OUT/'full.png',full);save(OUT/'empty.png',background)
 # Diagnostic: free public land component with all possible solid projections removed.
 union=Image.new('L',SIZE)
 for state in ordinary:union=ImageChops.lighter(union,bodies[state])
 ground=poly([(0,97),(20,97),(34,93),(125,92),(230,103),(302,109),(510,108),(518,131),(550,144),(621,161),(641,145),(650,111),(768,111),(799,129),(799,373),(0,373)])
 free=ImageChops.subtract(ground,union);save(OUT/'terrain/free-land-diagnostic.png',free)
 components=[];seen=set();pix=free.load()
 for y in range(374):
  for x in range(800):
   if not pix[x,y] or (x,y)in seen:continue
   todo=deque([(x,y)]);seen.add((x,y));part=[]
   while todo:
    p=todo.popleft();part.append(p)
    for q in ((p[0]+1,p[1]),(p[0]-1,p[1]),(p[0],p[1]+1),(p[0],p[1]-1)):
     if 0<=q[0]<800 and 0<=q[1]<374 and q not in seen and pix[q[0],q[1]]:seen.add(q);todo.append(q)
   components.append(part)
 largest=max(components,key=len);network=Image.new('L',SIZE)
 for p in largest:network.putpixel(p,255)
 save(OUT/'terrain/main-free-component.png',network)
 print('components',len(components),'main',len(largest),'full_diff',ImageChops.difference(full.convert('RGB'),approved.convert('RGB')).getbbox())
 print('old entry, nearest main-free point distance; diagnostics only')
 for state in ordinary:
  x,y=rows[state]['entrance'];point=min(largest,key=lambda p:abs(p[0]-x)+abs(p[1]-y));print(state,(x,y),point,abs(point[0]-x)+abs(point[1]-y))
if __name__=='__main__':main()
