"""Two-pixel/one-pixel whole-family corner clearance, with exact contact moves."""
from pathlib import Path
from copy import deepcopy
import hashlib,json
from PIL import Image,ImageOps,ImageChops,ImageFilter
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
OUT=HERE/'candidate-final-v2'
REPORT=ROOT/'build/reports/complete-town-20261027-v2/final-v2'
DELTAS={'special2':(2,0),'dwellingLvl6':(-1,0),'dwellingUpLvl6':(-1,0)}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf8')
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
def rel(p):return p.relative_to(ROOT).as_posix()
def alpha(im,t):return im.getchannel('A').point(lambda v:255 if v>=t else 0)
def move(im,xy):out=Image.new(im.mode,im.size);out.paste(im,xy);return out
def main():
 base=HERE/'candidate-final-v1';selection=deepcopy(load(base/'selection.json'));faction=deepcopy(load(base/'factions.candidate.json'));recipes={n:deepcopy(load(base/'candidate-recipes'/n)) for n in selection['recipes']};annotations={r['state']:deepcopy(r) for r in load(HERE/'physical-v9/annotations.json')['states']};layers={};roots={}
 for row in selection['states']:
  state=row['state'];im=Image.open(ROOT/row['native_layer']).convert('RGBA');root=Image.open(HERE/'physical-v9'/state/'foundation.png').convert('L');zone=Image.open(HERE/'physical-v9'/state/'manual-semantic-ground-zone.png').convert('L');record=annotations[state]
  if state in DELTAS:
   dx,dy=DELTAS[state];moved=move(im,(dx,dy))
   if alpha(im,8).histogram()!=alpha(moved,8).histogram():raise ValueError('Clipped corner repair '+state)
   im=moved;root=move(root,(dx,dy));zone=move(zone,(dx,dy));folder=HERE/'structures-final-v2'/state;save(folder/'layer.png',im);solid=alpha(im,128);area=Image.new('RGBA',(800,374),(255,255,255,0));area.putalpha(solid);border=Image.new('RGBA',(800,374),(255,230,100,0));border.putalpha(ImageChops.subtract(solid.filter(ImageFilter.MaxFilter(5)),solid));save(folder/'area.png',area);save(folder/'border.png',border)
   row['native_layer']=rel(folder/'layer.png');row['native_layer_sha256']=sha(folder/'layer.png');row['native_position']=[row['native_position'][0]+dx,row['native_position'][1]+dy];row['composition_rectangle'][0]+=dx;row['composition_rectangle'][1]+=dy;row['entrance_intent']=[row['entrance_intent'][0]+dx,row['entrance_intent'][1]+dy];row['alpha8_bbox']=list(alpha(im,8).getbbox());row['solid_bbox']=list(solid.getbbox());row['last_corner_clearance']={'translation':[dx,dy],'script':rel(Path(__file__)),'script_sha256':sha(Path(__file__)),'prior_complete_ground_mask_sha256':sha(HERE/'physical-v9'/state/'foundation.png')}
   for key in ('manual_native_contact_polyline','additional_manually_classified_ground_points','excluded_opaque_column_endpoints_outside_semantic_zone'):
    record[key]=[[p[0]+dx,p[1]+dy] for p in record[key]]
   for role in ('animation','area','border'):
    recipe=recipes[f'assets/recipes/town/structures/{state}-{role}.json'];p=folder/('layer.png' if role=='animation' else role+'.png');recipe.update(source_sha256=sha(p),sha256=sha(p));recipe['building_contract']['native_ground_contact']=row['composition_rectangle'];recipe['generation']['last_corner_clearance']=row['last_corner_clearance']
    if role=='animation':recipe['groups'][0]['frames'][0].update(source=rel(p),source_sha256=sha(p),sha256=sha(p))
    else:recipe['source']=rel(p)
  folder=HERE/'physical-v10'/state;save(folder/'foundation.png',root);save(folder/'manual-semantic-ground-zone.png',zone);save(folder/'body.png',alpha(im,128));save(folder/'silhouette.png',alpha(im,8));record.update(layer=row['native_layer'],layer_sha256=row['native_layer_sha256'],foundation=rel(folder/'foundation.png'),foundation_sha256=sha(folder/'foundation.png'),semantic_zone_sha256=sha(folder/'manual-semantic-ground-zone.png'),bbox=list(root.getbbox()));layers[state]=im;roots[state]=root
  view=im.copy();color=Image.new('RGBA',(800,374),(20,255,220,0));color.putalpha(root);view.alpha_composite(color);bb=alpha(im,8).getbbox();save(folder/'contact-review-4x.png',view.crop(bb).resize(((bb[2]-bb[0])*4,(bb[3]-bb[1])*4),Image.Resampling.NEAREST))
 for site in selection['sites']:
  if site['states'][0] in DELTAS:
   dx,dy=DELTAS[site['states'][0]];site['composition_rectangle'][0]+=dx;site['composition_rectangle'][1]+=dy;site['entrance_intent']=[site['entrance_intent'][0]+dx,site['entrance_intent'][1]+dy]
 selection['recipes']={}
 for name,recipe in recipes.items():p=OUT/'candidate-recipes'/name;write(p,recipe);selection['recipes'][name]=sha(p)
 write(OUT/'selection.json',selection);write(OUT/'factions.candidate.json',faction);write(HERE/'physical-v10/annotations.json',{'status':'authored configuration','prior_semantic_annotation_sha256':sha(HERE/'physical-v9/annotations.json'),'script_sha256':sha(Path(__file__)),'states':list(annotations.values())})
 sites={s['id']:s for s in selection['sites']};pairs=[]
 for a in sites.values():
  ru=Image.new('L',(800,374))
  for state in a['states']:ru=ImageChops.lighter(ru,roots[state])
  for b in sites.values():
   if a['native_z']>=b['native_z']:continue
   bu=Image.new('L',(800,374))
   for state in b['states']:bu=ImageChops.lighter(bu,alpha(layers[state],128))
   hit=ImageChops.multiply(ru,bu)
   if hit.getbbox():pairs.append({'behind':a['id'],'front':b['id'],'pixels':hit.histogram()[255],'bbox':list(hit.getbbox())})
 background=Image.open(ROOT/selection['terrain']['native']).convert('RGBA');rows={r['state']:r for r in selection['states']};save(REPORT/'empty-native.png',background)
 for mode in ('full','base','early','coast','grail','guild-absent'):
  chosen=[site['states'][0] if mode=='base' else site['top'] for site in selection['sites'] if site['id'] not in ('coast','grail')]
  if mode=='early':chosen=['villageHall','fort','dwellingLvl1','tavern']
  if mode=='coast':chosen.append('ship')
  if mode=='grail':chosen.append('grail')
  if mode=='guild-absent':chosen.remove('mageGuild4')
  out=background.copy()
  for state in sorted(chosen,key=lambda s:rows[s]['native_z']):out.alpha_composite(layers[state])
  save(REPORT/(mode+'-native.png'),out)
 write(REPORT/'all-state-contact-intersections.json',{'status':'authored configuration','pairs':pairs,'exposed_all_actual_feet':True,'classification_source':rel(HERE/'semantic_ground_points_v1.py')});print(json.dumps({'candidate':rel(OUT),'remaining_pairs':pairs}))
if __name__=='__main__':main()
