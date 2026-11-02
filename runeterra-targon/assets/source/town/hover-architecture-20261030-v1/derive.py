"""Targon-only exterior-sky mask candidates; never changes paintings, selections or clicks."""
import argparse,json,sys
from collections import deque
from pathlib import Path
from PIL import Image,ImageChops,ImageFilter,ImageDraw
ROOT=Path(__file__).resolve().parents[5];sys.path.insert(0,str(ROOT/'scripts'))
import town_hover_outlines as h
BASE=Path(__file__).resolve().parent
NEIGHBOURS=[(dx,dy) for dy in (-1,0,1) for dx in (-1,0,1) if dx or dy]
def exclude_sky(image,base):
 pixels=image.load();body=base.load();sky=Image.new('L',h.SIZE);sp=sky.load();seen=set();queue=deque()
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
 removed=Image.new('L',h.SIZE);rp=removed.load()
 while queue:
  x,y=queue.popleft();rp[x,y]=255
  for dx,dy in NEIGHBOURS:
   nx,ny=x+dx,y+dy
   if 0<=nx<800 and 0<=ny<374 and sp[nx,ny] and (nx,ny) not in seen:seen.add((nx,ny));queue.append((nx,ny))
 return ImageChops.subtract(base,removed),removed

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
 if not out.is_relative_to(ROOT/'reports') or out.exists():raise ValueError('Use fresh workspace report path')
 out.mkdir(parents=True);selection=h.read(BASE/'selection.json');masks={};receipt={}
 for name,row in selection['states'].items():
  source=ROOT/row['source']['path'];assert h.digest(source)==row['source']['sha256'];image=h.load(source);base=h.binary(image.getchannel('A'));mask,removed=exclude_sky(image,base) if row['remove_exterior_sky'] else (base,Image.new('L',h.SIZE));
  if row.get('preserve_polygons_native'):
   preserve=Image.new('L',h.SIZE);draw=ImageDraw.Draw(preserve)
   for points in row['preserve_polygons_native']:draw.polygon([tuple(p) for p in points],fill=255)
   restored=ImageChops.multiply(base,preserve);mask=ImageChops.lighter(mask,restored);removed=ImageChops.subtract(base,mask)
  target=out/(name+'-mask.png');mask.save(target);removed.save(out/(name+'-removed.png'));masks['targon/'+name]={'path':target.relative_to(ROOT).as_posix(),'sha256':h.digest(target)};receipt[name]={'mask_sha256':h.digest(target),'selected_layer':row['source'],'removed_pixels':removed.histogram()[255],'remove_exterior_sky':row['remove_exterior_sky']}
 h.write(out/'mask-selections.json',masks);h.candidate(ROOT,out/'gallery',('targon',),masks);h.write(out/'receipt.json',{'status':'design proposal','producer_sha256':h.digest(__file__),'selection_sha256':h.digest(BASE/'selection.json'),'states':receipt,'painted_mutations':0,'click_mutations':0,'selected_recipe_mutations':0,'runtime_observed':False});print(out)
if __name__=='__main__':main()
