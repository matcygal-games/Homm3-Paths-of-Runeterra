"""Candidate-only technical composition of existing painted Bandle masters.

Does not publish, stage, edit active recipes/design or generate new artwork.
"""
from pathlib import Path
from copy import deepcopy
import hashlib, itertools, json
from PIL import Image, ImageOps, ImageDraw, ImageFilter, ImageChops

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
OUT=ROOT/'build/reports/town-depth-20261024-v2'
RECTS={
 'hall':[175,42,105,100], 'fortification':[335,42,145,94],
 'guild':[34,40,80,100], 'tavernAcademy':[143,250,143,106],
 'market':[292,241,123,77], 'engineering':[420,257,161,117],
 'portal':[519,91,85,83], 'garden':[450,180,95,64],
 'fountain':[330,150,76,84], 'dwelling1':[0,253,141,117],
 'dwelling2':[167,142,125,105], 'dwelling3':[686,202,114,103],
 'dwelling4':[582,253,105,86], 'dwelling5':[610,149,105,105],
 'dwelling6':[0,145,151,112], 'dwelling7':[658,45,96,100],
 'coast':[689,312,111,62], 'grailOrnament':[392,68,31,35],
}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
rel=lambda p:Path(p).relative_to(ROOT).as_posix()
def write(p,v):
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def save(p,im):
 p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9,optimize=False)
def crop(im):
 b=im.getchannel('A').point(lambda v:255 if v>=8 else 0).getbbox()
 b=[max(0,b[0]-8),max(0,b[1]-8),min(im.width,b[2]+8),min(im.height,b[3]+8)]
 return im.crop(b),b
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 old=json.loads((ROOT/'design/town-visuals.json').read_text(encoding='utf-8'))
 design=deepcopy(old);design.pop('selected_sources',None)
 design['layout_note']='Forced theatrical HoMM3 depth: large near framing services/homes, reduced distant landmarks; irregular rooted community; all16 land sites,7 in-place dwelling pairs and optional coast preserved.'
 recipes=[];layers={};masks={};rows=[];files=set();bindings=[]
 water=Image.new('L',(800,374));ImageDraw.Draw(water).polygon([tuple(p) for p in old['terrain']['water_polygon']],fill=255)
 for site in design['sites']:
  x,y,w,h=RECTS[site['id']];z=y+h
  if site['id']=='grailOrnament':z=137
  if site['id']=='coast':z=374
  site.update(composition_rectangle=[x,y,w,h],center=[x+w//2,y+h//2],native_z=z,layer_origin=[0,0],selected_state_art={})
  for state in site['states']:
   master=ROOT/site['source'][state];raw=Image.open(master).convert('RGBA');im,b=crop(raw)
   fitted=ImageOps.contain(im,(w,h),Image.Resampling.LANCZOS)
   layer=Image.new('RGBA',(800,374));layer.alpha_composite(fitted,(x+(w-fitted.width)//2,y+h-fitted.height))
   dest=HERE/'structures'/state;save(dest/'layer.png',layer)
   mask=layer.getchannel('A').point(lambda v:255 if v>=128 else 0)
   for role,ch in [('area',mask),('border',ImageChops.subtract(mask.filter(ImageFilter.MaxFilter(5)),mask))]:
    image=Image.new('RGBA',(800,374),(255,235,32,0));image.putalpha(ch);save(dest/(role+'.png'),image)
   # Icons stay byte-identical; screen perspective must not alter construction UI.
   olddir=ROOT/next(s for s in old['sites'] if s['id']==site['id'])['selected_state_art'][state]['native_layer']
   for name in ['campaign.png','hall-icon.png']:
    target=dest/name;target.write_bytes((olddir.parent/name).read_bytes())
   foot=mask.copy();mb=mask.getbbox();foot.paste(0,(0,0,800,max(0,mb[3]-10)))
   wet=sum(ImageChops.multiply(foot,water).histogram()[128:])
   statez=375 if state=='ship' else z
   row={'state':state,'site':site['id'],'master':rel(master),'master_sha256':sha(master),'source_crop_xyxy':b,
    'fit_size':list(fitted.size),'native_layer':rel(dest/'layer.png'),'native_layer_sha256':sha(dest/'layer.png'),
    'native_z':statez,'composition_rectangle':[x,y,w,h],'click_bbox':mb,'click_pixels':sum(mask.histogram()[128:]),
    'footing_water_pixels':wet,'visual_approval_granted':False}
   site['selected_state_art'][state]=row;rows.append(row);layers[state]=layer;masks[state]=mask
   for role in ['animation','area','border','campaign']:
    active=f'assets/recipes/town/structures/{state}-{role}.json'
    recipe=json.loads((ROOT/active).read_text(encoding='utf-8'))
    source=dest/('layer.png' if role=='animation' else role+'.png')
    desc={'source':rel(source),'source_sha256':sha(source),'source_canvas':list(Image.open(source).size)}
    if role=='animation':recipe['groups'][0]['frames']=[desc]
    else:recipe.update(desc)
    recipe['generation']['conversion']={'revision':HERE.name,'source_crop_xyxy':b,'fit_size':list(fitted.size),'composition_rectangle':[x,y,w,h],'native_z':statez,'method':'Uniform LANCZOS technical scale/place of original painted2D master; no new art, warp or recolor'}
    target=HERE/'recipes/structures'/f'{state}-{role}.json';write(target,recipe);recipes.append(rel(target));files.add(target)
    bindings.append({'candidate':rel(target),'active':active,'sha256':sha(target)})
   for name in ['layer.png','area.png','border.png','hall-icon.png','campaign.png']:files.add(dest/name)
   files.add(master)
   for name in ['generation.json','prompt.txt']:
    if (master.parent/name).is_file():files.add(master.parent/name)
 for name in ['background','buildingIcons']:
  active=f'assets/recipes/town/{name}.json';recipe=json.loads((ROOT/active).read_text(encoding='utf-8'))
  if name=='buildingIcons':
   for frame in recipe['frames']:
    source=HERE/'structures'/frame['building']/'hall-icon.png';frame.update(source=rel(source),source_sha256=sha(source))
  target=HERE/'recipes'/f'{name}.json';write(target,recipe);recipes.append(rel(target));files.add(target)
  bindings.append({'candidate':rel(target),'active':active,'sha256':sha(target)})
 for key in ['master','native']:files.add(ROOT/design['terrain'][key])
 for name in ['generation.json','prompt.txt','water-annotation.png']:
  p=(ROOT/design['terrain']['master']).parent/name
  if p.is_file():files.add(p)
 design['recipe_paths']=recipes
 selection={'schema_version':1,'revision':HERE.name,'status':'authored configuration','visual_approval_granted':False,
  'sites':design['sites'],'terrain':design['terrain'],'recipe_bindings':bindings,'files':{rel(p):sha(p) for p in sorted(files)},
  'preparation_policy':'Validate exact selected closure before coordinator integration; candidate only, no active writes.'}
 write(HERE/'selection.json',selection)
 design['selected_sources']={'path':rel(HERE/'selection.json'),'sha256':sha(HERE/'selection.json'),
  'terrain_master':design['terrain']['master'],'terrain_master_sha256':design['terrain']['master_sha256'],
  'terrain_native':design['terrain']['native'],'terrain_native_sha256':design['terrain']['native_sha256']}
 write(HERE/'town-visuals.candidate.json',design)
 overlaps=[]
 for a,b in itertools.combinations(rows,2):
  if a['site']==b['site'] or 'grailOrnament' in (a['site'],b['site']):continue
  overlap=ImageChops.multiply(masks[a['state']],masks[b['state']]);n=sum(overlap.histogram()[128:])
  if n:overlaps.append({'a':a['state'],'b':b['state'],'sites':[a['site'],b['site']],'pixels':n,'bbox':overlap.getbbox()})
 for variant in ['base','upgraded','coastal','grail']:
  canvas=Image.open(ROOT/design['terrain']['native']).convert('RGBA');chosen=[]
  for site in design['sites']:
   if site['id']=='coast':
    if variant in ['coastal','grail']:chosen+=site['states']
   elif site['id']=='grailOrnament':
    if variant=='grail':chosen+=site['states']
   else:chosen.append(site['states'][0 if variant=='base' else -1])
  for state in sorted(chosen,key=lambda s:next(r['native_z'] for r in rows if r['state']==s)):canvas.alpha_composite(layers[state])
  save(OUT/(variant+'-native.png'),canvas)
 write(OUT/'geometry.json',{'rows':rows,'cross_site_opaque_overlaps':overlaps,
  'wet_land':[r for r in rows if r['site']!='coast' and r['footing_water_pixels']],
  'selection_sha256':sha(HERE/'selection.json'),'design_sha256':sha(HERE/'town-visuals.candidate.json')})
 print(json.dumps({'states':len(rows),'recipes':len(bindings),'overlaps':len(overlaps),'wet_land':len([r for r in rows if r['site']!='coast' and r['footing_water_pixels']]),'candidate':rel(HERE/'town-visuals.candidate.json')}))
if __name__=='__main__':main()
