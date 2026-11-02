"""Candidate painted-lane ownership preflight; no canonical source writes."""
from pathlib import Path
import importlib.util,json,sys
from PIL import Image,ImageDraw,ImageChops,ImageFilter
import assemble_lane_repair as repair
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
PRIOR=HERE.parent/'approved-nx1-finish-20261030-v1'
S=json.loads((PRIOR/'selected/selection.json').read_text());ROWS={r['state']:r for r in S['states']};SIZE=(800,374)
spec=importlib.util.spec_from_file_location('nx1_prototype_components',HERE.parent/'approved-nx1-physical-20261030-v1/prototype_roofs.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
def save(path,im):path.parent.mkdir(parents=True,exist_ok=True);im.save(path,compress_level=9)
def binary(im,t=8):return im.getchannel('A').point(lambda a:255 if a>=t else 0)
def main():
 out=HERE/'decomposition-v1';out.mkdir(exist_ok=True)
 native=Image.open(HERE/'repaired-native-v1.png').convert('RGBA');road=Image.new('L',SIZE);draw=ImageDraw.Draw(road)
 for path in repair.PATHS:draw.line(path,fill=255,width=5)
 save(out/'public-lanes.png',road)
 site_groups={}
 for s,r in ROWS.items():site_groups.setdefault(r['site'],[]).append(s)
 tops={states[-1] for site,states in site_groups.items() if site!='coast'}
 layers={};moved=[];union=Image.new('L',SIZE)
 for state,row in ROWS.items():
  old=Image.open(ROOT/row['native_layer']).convert('RGBA')
  if state in tops:
   alpha=ImageChops.subtract(old.getchannel('A'),road);layer=native.copy();layer.putalpha(alpha);union=ImageChops.lighter(union,alpha)
  elif row['site']=='coast':layer=old
  else:
   # Move genuine predecessor pixels as one complete painted subject. Never cut
   # a roof/wall to force a road through the older source.
   best=None
   for dx in range(-8,9):
    for dy in range(-8,9):
     trial=Image.new('RGBA',SIZE);trial.alpha_composite(old,(dx,dy))
     if ImageChops.multiply(binary(trial),road).getbbox():continue
     score=abs(dx)+abs(dy)
     if best is None or score<best[0]:best=(score,dx,dy,trial)
   if best is None:
    print('NO COMPLETE PREDECESSOR FIT',state);layer=old
   else:
    _,dx,dy,layer=best
    if dx or dy:moved.append([state,dx,dy])
  layers[state]=layer;save(out/'structures'/state/'layer.png',layer)
 background=Image.composite(Image.open(ROOT/S['background']['path']).convert('RGBA'),native,union)
 save(out/'background.png',background)
 scene=background.copy()
 for state in sorted(tops,key=lambda s:ROWS[s]['native_z']):scene.alpha_composite(layers[state])
 save(out/'full.png',scene)
 body=Image.new('L',SIZE)
 for s,im in layers.items():
  if ROWS[s]['site']!='coast':body=ImageChops.lighter(body,binary(im,128))
 land=p.poly([(0,97),(20,97),(34,93),(125,92),(230,103),(302,109),(510,108),(518,131),(550,144),(621,161),(641,145),(650,111),(768,111),(799,129),(799,373),(0,373)])
 land=ImageChops.lighter(land,road);free=ImageChops.subtract(land,body);parts=p.components(free);parts.sort(key=len,reverse=True);index={q:i for i,part in enumerate(parts) for q in part}
 save(out/'walkable-diagnostic.png',free)
 print('complete predecessor translations',moved,'full RGB diff',ImageChops.difference(scene.convert('RGB'),native.convert('RGB')).getbbox(),'components',len(parts),'main',len(parts[0]))
 for line in repair.PATHS:print('lane',line[0],index.get(tuple(line[0])),line[-1],index.get(tuple(line[-1])))
 (out/'preflight.json').write_text(json.dumps({'status':'authored configuration','source_only':True,'predecessor_translations':moved,'whole_scene_reconstruction_diff':ImageChops.difference(scene.convert('RGB'),native.convert('RGB')).getbbox(),'component_count':len(parts),'main_component_pixels':len(parts[0])},indent=2)+'\n')
if __name__=='__main__':main()
