"""Whole painted scene first, conservative technical ownership candidate."""
from pathlib import Path
import importlib.util,json
from PIL import Image,ImageDraw,ImageChops,ImageFilter
import assemble_lane_repair as repair
import assemble_edge_gap_v2 as edge
import ownership_trace
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];PRIOR=HERE.parent/'approved-nx1-finish-20261030-v1';PHYSICAL=HERE.parent/'approved-nx1-physical-20261030-v1';SIZE=(800,374)
S=json.loads((PRIOR/'selected/selection.json').read_text());ROWS={r['state']:r for r in S['states']}
spec=importlib.util.spec_from_file_location('nx1_preflight_components',PHYSICAL/'prototype_roofs.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
PATHS=repair.PATHS[:3]+[repair.PATHS[3][:9]]
def save(path,im):path.parent.mkdir(parents=True,exist_ok=True);im.save(path,compress_level=9)
def binary(im,t=128):return im.getchannel('A').point(lambda a:255 if a>=t else 0)
def main():
 out=HERE/'decomposition-v5';out.mkdir(exist_ok=True)
 native=Image.open(HERE.parent/'approved-nx1-20261029-v1/approved-native.png').convert('RGBA');gen=Image.open(HERE/'whole-lane-repair-master.png').convert('RGBA').resize(SIZE,Image.Resampling.LANCZOS)
 region=Image.new('L',SIZE);d=ImageDraw.Draw(region)
 for path in PATHS:d.line(path,fill=255,width=15)
 region=region.filter(ImageFilter.GaussianBlur(.5));native=Image.composite(gen,native,region)
 extra=Image.open(HERE/'edge-gap-master-v2.png').convert('RGBA').resize(SIZE,Image.Resampling.LANCZOS);extra_mask=Image.open(HERE/'edge-gap-region-v2.png').convert('L');native=Image.composite(extra,native,extra_mask)
 gate=Image.open(HERE/'hound-service-gate-master-v3.png').convert('RGBA').resize(SIZE,Image.Resampling.LANCZOS)
 gate_mask=p.poly([(532,190),(551,190),(560,199),(559,213),(544,217),(531,210)]).filter(ImageFilter.GaussianBlur(.5));native=Image.composite(gate,native,gate_mask)
 save(out/'hound-gate-region.png',gate_mask);save(out/'complete-painted.png',native)
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
   cut=road
   if state=='blacksmith':
    cut=ImageChops.lighter(cut,p.poly([(777,282),(799,293),(799,374),(788,374),(788,301),(777,290)]))
   alpha=ImageChops.subtract(old.getchannel('A'),cut);layer=native.copy();layer.putalpha(alpha);union=ImageChops.lighter(union,alpha)
  else:layer=old
  if state=='special4':
   layer=Image.new('RGBA',SIZE);layer.alpha_composite(old,(0,-14));moved.append({'state':state,'translation':[0,-14],'reason':'Complete lower binding altar rests on the upper level landing, above the existing foreground stairs.'})
  if state=='dwellingLvl1':
   bbox=old.getbbox();subject=old.crop(bbox);scale=.62;subject=subject.resize((round(subject.width*scale),round(subject.height*scale)),Image.Resampling.LANCZOS)
   layer=Image.new('RGBA',SIZE);layer.alpha_composite(subject,(186,243-subject.height));moved.append({'state':state,'scale':scale,'box':[186,243-subject.height,subject.width,subject.height],'reason':'Complete smaller Legion guardhouse fits the approved side arch lane without cutting its roof or walls.'})
  if state=='dwellingLvl2':
   layer=Image.composite(gate,layer,ImageChops.multiply(gate_mask,layer.getchannel('A')))
  layer=ownership_trace.apply(state,layer)
  if state=='dwellingUpLvl3':
   # Preserve the separately painted hidden wall, under the Barracks' actual
   # shared masonry buttress. The wall is needed in knife-guild-only states.
   hidden=p.poly([(227,190),(237,186),(240,246),(228,247)])
   patch=old.copy();patch.putalpha(ImageChops.multiply(old.getchannel('A'),hidden));layer.alpha_composite(patch)
  if state in ('fort','citadel','castle'):
   keep=p.poly([(0,0),(799,0),(799,104),(714,104),(714,111),(701,111),(701,104),(0,104)])
   layer.putalpha(ImageChops.multiply(layer.getchannel('A'),keep))
  if state in tops:union=ImageChops.lighter(union,layer.getchannel('A'))
  layers[state]=layer;save(out/'structures'/state/'layer.png',layer)
 union=Image.new('L',SIZE)
 for state in tops:union=ImageChops.lighter(union,layers[state].getchannel('A'))
 background=Image.composite(Image.open(ROOT/S['background']['path']).convert('RGBA'),native,union)
 clean=Image.open(HERE/'empty-frontage-clean-master-v4.png').convert('RGBA').resize(SIZE,Image.Resampling.LANCZOS)
 clean_region=p.poly([(128,198),(178,198),(181,249),(128,249)]).filter(ImageFilter.GaussianBlur(.5))
 clean_region=ImageChops.multiply(clean_region,union.point(lambda v:255 if v==255 else 0))
 background=Image.composite(clean,background,clean_region);save(out/'empty-clean-region.png',clean_region);save(out/'background.png',background)
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
