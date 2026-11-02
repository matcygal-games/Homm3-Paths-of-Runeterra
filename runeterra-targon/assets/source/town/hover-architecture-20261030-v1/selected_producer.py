"""Reproduce authored Targon hover masks; painted layers and click masks are inputs."""
import argparse,hashlib,json
from pathlib import Path
from collections import deque
from PIL import Image,ImageChops,ImageDraw,ImageFilter
SIZE=(800,374);GOLD=(225,190,80,255);SHADOW=(38,29,15,208)
NEIGHBOURS=[(dx,dy) for dy in (-1,0,1) for dx in (-1,0,1) if dx or dy]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def exclude_sky(image,base):
 pixels=image.load();body=base.load();sky=Image.new('L',SIZE);sp=sky.load();seen=set();queue=deque()
 # Only exterior-connected transparent background may seed sky removal.
 exterior=set();outside=deque()
 for x in range(800):
  for y in (0,373):
   if not body[x,y]:exterior.add((x,y));outside.append((x,y))
 for y in range(374):
  for x in (0,799):
   if not body[x,y] and (x,y) not in exterior:exterior.add((x,y));outside.append((x,y))
 while outside:
  x,y=outside.popleft()
  for dx,dy in NEIGHBOURS:
   nx,ny=x+dx,y+dy
   if 0<=nx<800 and 0<=ny<374 and not body[nx,ny] and (nx,ny) not in exterior:exterior.add((nx,ny));outside.append((nx,ny))
 for y in range(374):
  for x in range(800):
   r,g,b,a=pixels[x,y]
   if body[x,y] and b>130 and b-r>45 and b-g>12 and g>65:
    sp[x,y]=255
 for y in range(374):
  for x in range(800):
   if sp[x,y] and any(not(0<=x+dx<800 and 0<=y+dy<374) or (x+dx,y+dy) in exterior for dx,dy in NEIGHBOURS):queue.append((x,y));seen.add((x,y))
 removed=Image.new('L',SIZE);rp=removed.load()
 while queue:
  x,y=queue.popleft();rp[x,y]=255
  for dx,dy in NEIGHBOURS:
   nx,ny=x+dx,y+dy
   if 0<=nx<800 and 0<=ny<374 and sp[nx,ny] and (nx,ny) not in seen:seen.add((nx,ny));queue.append((nx,ny))
 return ImageChops.subtract(base,removed),removed

def produce(project,selection_path,output):
 project=Path(project).resolve();output=Path(output).resolve()
 if output.exists() and any(output.iterdir()):raise ValueError('Use an empty reproduction directory')
 output.mkdir(parents=True,exist_ok=True);selection=json.loads(Path(selection_path).read_text());result={}
 for name,row in sorted(selection['states'].items()):
  source=(project/row['source']['path']).resolve()
  if not source.is_relative_to(project) or sha(source)!=row['source']['sha256']:raise ValueError('Painted source changed '+name)
  with Image.open(source) as im:
   if im.mode!='RGBA' or im.size!=SIZE:raise ValueError('Expected native RGBA layer')
   image=im.copy()
  base=image.getchannel('A').point(lambda v:255 if v>=128 else 0);mask,removed=exclude_sky(image,base) if row['remove_exterior_sky'] else (base,Image.new('L',SIZE))
  if row.get('preserve_polygons_native'):
   preserve=Image.new('L',SIZE);draw=ImageDraw.Draw(preserve)
   for points in row['preserve_polygons_native']:draw.polygon([tuple(p) for p in points],fill=255)
   mask=ImageChops.lighter(mask,ImageChops.multiply(base,preserve))
  if not mask.getbbox():raise ValueError('Empty architecture '+name)
  near=mask.filter(ImageFilter.MaxFilter(3));far=mask.filter(ImageFilter.MaxFilter(5));border=Image.new('RGBA',SIZE);shadow=Image.new('RGBA',SIZE,SHADOW);shadow.putalpha(ImageChops.subtract(far,near).point(lambda v:208 if v else 0));border.alpha_composite(shadow);edge=Image.new('RGBA',SIZE,GOLD);edge.putalpha(ImageChops.subtract(near,mask));border.alpha_composite(edge)
  target=output/name;target.mkdir();mask.save(target/'architecture-mask.png');border.save(target/'border.png');result[name]={'mask_sha256':sha(target/'architecture-mask.png'),'border_sha256':sha(target/'border.png')}
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--project',type=Path,required=True);p.add_argument('--selection',type=Path,default=Path(__file__).with_name('selection-selected.json'));p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(produce(a.project,a.selection,a.output),indent=2))
