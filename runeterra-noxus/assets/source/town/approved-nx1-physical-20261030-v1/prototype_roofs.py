"""Isolated evidence experiment. No shared consumer or canonical input writes."""
from pathlib import Path
from collections import deque
import json,hashlib
from PIL import Image,ImageChops,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
SOURCE=HERE.parent/'approved-nx1-finish-20261030-v1'
S=json.loads((SOURCE/'selected/selection.json').read_text());ROWS={r['state']:r for r in S['states']};SIZE=(800,374)
# Hand-traced projected roof surfaces, deliberately excluding visible masonry fronts.
ROOFS={
 'tavern': [[(0,213),(29,215),(45,217),(69,207),(79,201),(101,222),(107,234),(147,242),(164,260),(169,276),(132,263),(105,257),(72,254),(0,246)]],
 'marketplace': [[(165,276),(183,252),(212,264),(244,250),(271,267),(301,273),(342,280),(353,301),(319,298),(273,291),(221,288),(170,290)],[(316,230),(346,218),(363,221),(378,229),(380,242),(355,246),(321,242)]],
 'blacksmith': [[(467,283),(492,274),(530,286),(520,309),(477,310)],[(492,282),(540,251),(562,240),(584,240),(610,248),(579,273),(530,302)],[(564,231),(579,240),(602,239),(630,240),(638,233),(649,245),(699,262),(721,271),(725,282),(679,280),(653,267),(614,270),(585,259)],[(735,290),(765,288),(799,295),(799,319),(773,315),(750,308)]],
 'dwellingUpLvl3': [[(239,190),(277,186),(294,188),(311,198),(329,207),(332,216),(241,217)]],
 'dwellingUpLvl1': [[(151,217),(179,201),(195,192),(232,186),(241,190),(241,217),(203,220)]],
 'special2': [[(340,160),(354,150),(392,142),(400,132),(411,138),(452,137),(463,132),(486,149),(514,155),(523,164),(486,169),(433,161),(383,169)]],
 'dwellingUpLvl5': [[(640,141),(651,138),(652,130),(666,125),(675,122),(681,116),(682,111),(687,114),(690,121),(707,124),(718,129),(721,136),(734,138),(736,146),(720,151),(664,149)]],
 'dwellingLvl5': [[(648,148),(657,138),(678,127),(689,125),(712,137),(729,149),(704,151),(673,151)]],
 'resourceSilo': [[(517,118),(531,112),(543,105),(555,101),(568,101),(575,97),(594,102),(615,112),(622,119),(597,123),(550,120),(520,125)]],
}
def poly(points):
 im=Image.new('L',SIZE);ImageDraw.Draw(im).polygon(points,fill=255);return im
def body(state):return Image.open(HERE/'structures'/state/'body.png').convert('L')
def components(mask):
 pix=mask.load();seen=set();parts=[]
 for y in range(374):
  for x in range(800):
   if not pix[x,y] or (x,y)in seen:continue
   todo=deque([(x,y)]);seen.add((x,y));part=[]
   while todo:
    p=todo.popleft();part.append(p)
    for q in ((p[0]-1,p[1]),(p[0]+1,p[1]),(p[0],p[1]-1),(p[0],p[1]+1)):
     if 0<=q[0]<800 and 0<=q[1]<374 and q not in seen and pix[q[0],q[1]]:seen.add(q);todo.append(q)
   parts.append(part)
 return parts
def main():
 blocked=Image.new('L',SIZE);roof_total=Image.new('L',SIZE);roofs={}
 for state,row in ROWS.items():
  if row['site']=='coast':continue
  roof=Image.new('L',SIZE)
  for points in ROOFS.get(state,[]):roof=ImageChops.lighter(roof,poly(points))
  roof=ImageChops.multiply(roof,body(state));roofs[state]=roof
  p=HERE/'roof-traces'/f'{state}.png';p.parent.mkdir(parents=True,exist_ok=True);roof.save(p)
  blocked=ImageChops.lighter(blocked,ImageChops.subtract(body(state),roof));roof_total=ImageChops.lighter(roof_total,roof)
 ground=poly([(0,97),(20,97),(34,93),(125,92),(230,103),(302,109),(510,108),(518,131),(550,144),(621,161),(641,145),(650,111),(768,111),(799,129),(799,373),(0,373)])
 free=ImageChops.subtract(ground,blocked);parts=components(free);parts.sort(key=len,reverse=True)
 free.save(HERE/'terrain/roof-prototype-walkable.png');roof_total.save(HERE/'terrain/roof-prototype-all-roofs.png')
 image=Image.open(HERE/'full.png').convert('RGBA');mark=Image.new('RGBA',SIZE,(35,190,220,0));mark.putalpha(roof_total.point(lambda v:120 if v else 0));image.alpha_composite(mark);image.save(HERE/'roof-traces-overlay.png')
 print('components',len(parts),'main',len(parts[0]))
 membership={point:i for i,part in enumerate(parts) for point in part}
 for state,row in ROWS.items():
  if row['site']=='coast':continue
  x,y=row['entrance'];near=min(membership,key=lambda p:abs(p[0]-x)+abs(p[1]-y));print(state,'nearest',near,'component',membership[near],'size',len(parts[membership[near]]),'distance',abs(near[0]-x)+abs(near[1]-y))
 print('root/wall semantic constraints NOT YET ADMITTED; this diagnostic alone proves nothing about a selected path')
if __name__=='__main__':main()
