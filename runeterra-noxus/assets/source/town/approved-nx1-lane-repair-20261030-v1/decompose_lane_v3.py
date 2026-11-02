"""Whole painted scene first, conservative technical ownership candidate."""
from pathlib import Path
import importlib.util,json
from PIL import Image,ImageDraw,ImageChops,ImageFilter
import assemble_lane_repair as repair
import assemble_edge_gap_v2 as edge
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];PRIOR=HERE.parent/'approved-nx1-finish-20261030-v1';PHYSICAL=HERE.parent/'approved-nx1-physical-20261030-v1';SIZE=(800,374)
S=json.loads((PRIOR/'selected/selection.json').read_text());ROWS={r['state']:r for r in S['states']}
spec=importlib.util.spec_from_file_location('nx1_preflight_components',PHYSICAL/'prototype_roofs.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
PATHS=repair.PATHS[:3]+[repair.PATHS[3][:9]]
def save(path,im):path.parent.mkdir(parents=True,exist_ok=True);im.save(path,compress_level=9)
def binary(im,t=128):return im.getchannel('A').point(lambda a:255 if a>=t else 0)
def main():
 out=HERE/'decomposition-v3';out.mkdir(exist_ok=True)
 native=Image.open(HERE.parent/'approved-nx1-20261029-v1/approved-native.png').convert('RGBA');gen=Image.open(HERE/'whole-lane-repair-master.png').convert('RGBA').resize(SIZE,Image.Resampling.LANCZOS)
 region=Image.new('L',SIZE);d=ImageDraw.Draw(region)
 for path in PATHS:d.line(path,fill=255,width=15)
 region=region.filter(ImageFilter.GaussianBlur(.5));native=Image.composite(gen,native,region)
 extra=Image.open(HERE/'edge-gap-master-v2.png').convert('RGBA').resize(SIZE,Image.Resampling.LANCZOS);extra_mask=Image.open(HERE/'edge-gap-region-v2.png').convert('L');native=Image.composite(extra,native,extra_mask)
 save(out/'complete-painted.png',native)
 road=Image.new('L',SIZE);d=ImageDraw.Draw(road)
 for path in PATHS:d.line(path,fill=255,width=5)
 d.line(edge.PATHS[0],fill=255,width=3);d.line(edge.PATHS[1][1:],fill=255,width=5)
 save(out/'public-lanes.png',road)
 groups={}
 for s,r in ROWS.items():groups.setdefault(r['site'],[]).append(s)
 tops={states[-1]for site,states in groups.items()if site!='coast'};layers={};union=Image.new('L',SIZE);moved=[]
 for state,row in ROWS.items():
  old=Image.open(PHYSICAL/'structures'/state/'layer.png').convert('RGBA')
  if state in tops:
   alpha=ImageChops.subtract(old.getchannel('A'),road);layer=native.copy();layer.putalpha(alpha);union=ImageChops.lighter(union,alpha)
  else:layer=old
  if state=='dwellingLvl1':
   bbox=old.getbbox();subject=old.crop(bbox);scale=.62;subject=subject.resize((round(subject.width*scale),round(subject.height*scale)),Image.Resampling.LANCZOS)
   layer=Image.new('RGBA',SIZE);layer.alpha_composite(subject,(186,243-subject.height));moved.append({'state':state,'scale':scale,'box':[186,243-subject.height,subject.width,subject.height],'reason':'Complete smaller Legion guardhouse fits the approved side arch lane without cutting its roof or walls.'})
  layers[state]=layer;save(out/'structures'/state/'layer.png',layer)
 background=Image.composite(Image.open(ROOT/S['background']['path']).convert('RGBA'),native,union);save(out/'background.png',background)
 scene=background.copy()
 for state in sorted(tops,key=lambda s:ROWS[s]['native_z']):scene.alpha_composite(layers[state])
 save(out/'full.png',scene)
 body=Image.new('L',SIZE)
 for s,im in layers.items():
  if ROWS[s]['site']!='coast':body=ImageChops.lighter(body,binary(im))
 land=p.poly([(0,97),(20,97),(34,93),(125,92),(230,103),(302,109),(510,108),(518,131),(550,144),(621,161),(641,145),(650,111),(768,111),(799,129),(799,373),(0,373)]);land=ImageChops.lighter(land,road)
 free=ImageChops.subtract(land,body);parts=p.components(free);parts.sort(key=len,reverse=True);index={q:i for i,part in enumerate(parts)for q in part};save(out/'walkable-diagnostic.png',free)
 accesses=[]
 for state,row in ROWS.items():
  x,y=row['entrance'];near=min(parts[0],key=lambda q:abs(q[0]-x)+abs(q[1]-y));accesses.append({'state':state,'legacy_entrance':row['entrance'],'nearest_main':near,'distance':abs(near[0]-x)+abs(near[1]-y)})
 receipt={'status':'authored configuration','candidate_only':True,'predecessor_transforms':moved,'whole_scene_reconstruction_diff':ImageChops.difference(scene.convert('RGB'),native.convert('RGB')).getbbox(),'component_count':len(parts),'main_component_pixels':len(parts[0]),'access_diagnostics':accesses}
 (out/'preflight.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
