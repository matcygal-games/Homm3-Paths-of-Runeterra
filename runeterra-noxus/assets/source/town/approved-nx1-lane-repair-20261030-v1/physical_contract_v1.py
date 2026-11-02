"""Isolated strict consumer candidate; source-only until independent review."""
from pathlib import Path
from collections import deque
import importlib.util,json,hashlib,sys
from PIL import Image,ImageDraw,ImageChops
import decompose_lane_v4 as D
HERE=D.HERE;ROOT=D.ROOT;ROWS=D.ROWS;SIZE=D.SIZE;LAYERS=HERE/'decomposition-v4';OUT=HERE/'physical-contract-v1'
ROUTES={
 'villageHall':[(402,115),(402,123)],'townHall':[(404,115),(404,123)],'cityHall':[(403,115),(403,123)],'capitol':[(407,110),(407,123)],
 'fort':[(709,104),(709,109),(650,109),(650,115)],'citadel':[(709,104),(709,109),(650,109),(650,115)],'castle':[(707,93),(707,109),(650,109),(650,115)],
 'mageGuild1':[(72,93),(72,100)],'mageGuild2':[(71,93),(71,100)],'mageGuild3':[(71,93),(71,100)],'mageGuild4':[(68,96),(68,100)],
 'special1':[(177,96),(177,101)],'special3':[(209,178),(217,184),(220,185)],
 'dwellingLvl6':[(277,178),(278,186)],'dwellingUpLvl6':[(277,181),(278,186)],'special2':[(429,199),(429,218)],'resourceSilo':[(570,166),(570,176)],
 'dwellingLvl5':[(688,170),(688,177),(681,177)],'dwellingUpLvl5':[(686,166),(686,177),(681,177)],
 'dwellingLvl1':[(209,240),(209,246)],'dwellingUpLvl1':[(203,232),(203,245)],'dwellingLvl3':[(285,239),(285,245)],'dwellingUpLvl3':[(281,232),(281,245)],
 'dwellingLvl2':[(590,233),(590,240),(550,240)],'dwellingUpLvl2':[(585,230),(585,240),(550,240)],
 'dwellingLvl4':[(716,233),(716,244)],'dwellingUpLvl4':[(711,226),(711,244)],
 'tavern':[(117,310),(117,333)],'marketplace':[(264,319),(264,337)],'blacksmith':[(635,322),(635,355)],
 'special4':[(757,282),(779,285),(795,300),(794,374-1)],'dwellingLvl7':[(756,282),(779,285),(795,300),(794,373)],'dwellingUpLvl7':[(754,270),(754,282),(779,285),(795,300),(794,373)],
 'grail':[(421,292),(421,306)],'shipyard':[(405,342),(405,340)],'ship':[(405,342),(405,340)]}
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.convert('RGB').save(p,compress_level=9)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def line(points,width=1):
 m=Image.new('L',SIZE);ImageDraw.Draw(m).line(points,fill=255,width=width);return m
def main():
 OUT.mkdir(exist_ok=True);images={s:Image.open(LAYERS/'structures'/s/'layer.png').convert('RGBA')for s in ROWS};bodies={s:D.binary(im)for s,im in images.items()}
 union=Image.new('L',SIZE)
 for s,b in bodies.items():
  if ROWS[s]['site']!='coast':union=ImageChops.lighter(union,b)
 land=D.p.poly([(0,97),(20,97),(34,93),(125,92),(230,103),(302,109),(510,108),(518,131),(550,144),(621,161),(641,145),(650,111),(768,111),(799,129),(799,373),(0,373)])
 land=ImageChops.lighter(land,Image.open(LAYERS/'public-lanes.png').convert('L'))
 free=ImageChops.subtract(land,union);parts=D.p.components(free);parts.sort(key=len,reverse=True);network=Image.new('L',SIZE)
 for q in parts[0]:network.putpixel(q,255)
 failures=[];stats=[];all_access=Image.new('L',SIZE)
 for s,row in ROWS.items():
  route=line(ROUTES[s]);body=bodies[s];others=Image.new('L',SIZE)
  for other,b in bodies.items():
   if ROWS[other]['site']!=row['site']:others=ImageChops.lighter(others,b)
  hit=ImageChops.multiply(route,others);own=ImageChops.multiply(route,body)
  stats.append({'state':s,'other_body_hits':hit.histogram()[255],'hit_bounds':hit.getbbox(),'touches_main':bool(ImageChops.multiply(route,network).getbbox()),'own_body_pixels':own.histogram()[255]})
  if hit.getbbox():failures.append(s+': local route crosses another actual body')
  if not ImageChops.multiply(route,network).getbbox():failures.append(s+': local route does not connect to main')
  save(OUT/'states'/s/'route.png',route);all_access=ImageChops.lighter(all_access,route)
 overlay=Image.open(LAYERS/'full.png').convert('RGBA');mark=Image.new('RGBA',SIZE,(40,250,200,0));mark.putalpha(all_access.point(lambda p:255 if p else 0));overlay.alpha_composite(mark);overlay.save(OUT/'access-diagnostic.png')
 result={'status':'authored configuration','candidate_only':True,'strict_shared_consumer_modified':False,'route_stats':stats,'failures':failures};(OUT/'preflight.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
