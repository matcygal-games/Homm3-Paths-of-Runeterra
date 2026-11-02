"""Small real-image placement/landing corrections; versioned source candidate."""
from pathlib import Path
from copy import deepcopy
import hashlib,json
from PIL import Image,ImageOps,ImageChops,ImageFilter
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
OUT=HERE/'candidate-clearance-v1'
REPORT=ROOT/'build/reports/complete-town-20261027-v2/clearance-v1'
TRANSFORMS={'resourceSilo':{'position':[665,173],'size':[104,86],'z':259},'special2':{'position':[697,102],'size':[69,58],'z':160}}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf8')
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
def rel(p):return p.relative_to(ROOT).as_posix()
def alpha(im,t=128):return im.getchannel('A').point(lambda v:255 if v>=t else 0)
def main():
 base=HERE/'candidate-access-v2';selection=deepcopy(load(base/'selection.json'));faction=deepcopy(load(base/'factions.candidate.json'));recipes={n:deepcopy(load(base/'candidate-recipes'/n)) for n in selection['recipes']};layers={};physical=[]
 background=Image.open(ROOT/selection['terrain']['native']).convert('RGBA');patches=[]
 # Artist-created floors are cropped, uniformly cover-fitted and composed.
 # No paving, walls or architecture is drawn by code. The academy floor crop
 # excludes the new incidental brazier from the actual foundation strip.
 for name,crop,box in [('academy',(0,370,1800,650),(0,116,85,132)),('hall',(0,73,2172,648),(75,135,225,175)),('knife',(0,0,2078,757),(0,170,115,212))]:
  master=HERE/'terrain'/(name+'-support-master-v2.png');patch=ImageOps.fit(Image.open(master).convert('RGBA').crop(crop),(box[2]-box[0],box[3]-box[1]),method=Image.Resampling.LANCZOS);background.alpha_composite(patch,(box[0],box[1]));patches.append({'master':rel(master),'sha256':sha(master),'source_crop':list(crop),'native_rectangle':list(box),'conversion':'Uniform cover-fit of genuine painted floor/court crop, exact composition only; no procedural artwork.'})
 native=HERE/'terrain/support-clearance-native-v1.png';save(native,background);selection['terrain'].update(native=rel(native),native_sha256=sha(native),west_support_repair={'patches':patches,'script':rel(Path(__file__)),'script_sha256':sha(Path(__file__))})
 old_annotations={r['state']:r for r in load(HERE/'physical-v4/annotations.json')['states']}
 for row in selection['states']:
  state=row['state'];source=ROOT/row['native_layer'];im=Image.open(source).convert('RGBA');foundation=Image.open(HERE/'physical-v4'/state/'foundation.png').convert('L');annotation=deepcopy(old_annotations[state])
  if state in TRANSFORMS:
   t=deepcopy(TRANSFORMS[state]);bb=list(alpha(im,8).getbbox());size=tuple(t['size']);xy=tuple(t['position']);bodycrop=im.crop(bb).resize(size,Image.Resampling.LANCZOS);placed=Image.new('RGBA',(800,374));placed.alpha_composite(bodycrop,xy);im=placed;rootcrop=foundation.crop(bb).resize(size,Image.Resampling.NEAREST);foundation=Image.new('L',(800,374));foundation.paste(rootcrop,xy);foundation=ImageChops.multiply(foundation,alpha(im));folder=HERE/'structures-clearance-v1'/state
   save(folder/'layer.png',im);solid=alpha(im);area=Image.new('RGBA',(800,374),(255,255,255,0));area.putalpha(solid);border=Image.new('RGBA',(800,374),(255,230,100,0));border.putalpha(ImageChops.subtract(solid.filter(ImageFilter.MaxFilter(5)),solid));save(folder/'area.png',area);save(folder/'border.png',border)
   def point(p):return [xy[0]+round((p[0]-bb[0])*size[0]/(bb[2]-bb[0])),xy[1]+round((p[1]-bb[1])*size[1]/(bb[3]-bb[1]))]
   row['entrance_intent']=point(row['entrance_intent']);row['native_layer']=rel(folder/'layer.png');row['native_layer_sha256']=sha(folder/'layer.png');row['native_z']=t['z'];row['native_position']=list(xy);row['native_size']=list(size);row['composition_rectangle']=[*xy,*size];row['alpha8_bbox']=list(alpha(im,8).getbbox());row['solid_bbox']=list(solid.getbbox());row['placement_clearance']={**t,'prior_native_alpha8_crop':bb,'prior_layer':rel(source),'prior_layer_sha256':sha(source),'script':rel(Path(__file__)),'script_sha256':sha(Path(__file__)),'reason':'Remove same-plaza root/body intersection without inventing a height boundary.'};annotation['manual_native_contact_polyline']=[point(p) for p in annotation['manual_native_contact_polyline']]
   faction['noxus']['town']['structures'][state]['z']=t['z']
   for role in ('animation','area','border'):
    recipe=recipes[f'assets/recipes/town/structures/{state}-{role}.json'];p=folder/('layer.png' if role=='animation' else role+'.png');recipe.update(source_sha256=sha(p),sha256=sha(p));recipe['building_contract'].update(full_canvas_placement={'x':0,'y':0,'z':t['z']},native_ground_contact=row['composition_rectangle']);recipe['generation']['placement_clearance']=row['placement_clearance']
    if role=='animation':recipe['groups'][0]['frames'][0].update(source=rel(p),source_sha256=sha(p),sha256=sha(p))
    else:recipe['source']=rel(p)
   for site in selection['sites']:
    if site['id']==row['site']:site.update(composition_rectangle=row['composition_rectangle'],native_z=t['z'],entrance_intent=row['entrance_intent'])
  layers[state]=im;folder=HERE/'physical-v5'/state;save(folder/'foundation.png',foundation);save(folder/'body.png',alpha(im));save(folder/'silhouette.png',alpha(im,8));annotation.update(layer=row['native_layer'],layer_sha256=row['native_layer_sha256'],depth=row['native_z'],foundation=rel(folder/'foundation.png'),foundation_sha256=sha(folder/'foundation.png'),pixels=foundation.histogram()[255],bbox=list(foundation.getbbox()),prior_semantic_foundation_sha256=sha(HERE/'physical-v4'/state/'foundation.png'));physical.append(annotation)
  view=im.copy();color=Image.new('RGBA',(800,374),(20,255,220,0));color.putalpha(foundation);view.alpha_composite(color);bb=alpha(im,8).getbbox();save(folder/'contact-review-4x.png',view.crop(bb).resize(((bb[2]-bb[0])*4,(bb[3]-bb[1])*4),Image.Resampling.NEAREST))
 for frame in recipes['assets/recipes/town/buildingIcons.json']['frames']:
  state=frame['building'];im=layers[state];bb=alpha(im,8).getbbox();icon=Image.new('RGBA',(150,70));fit=ImageOps.contain(im.crop(bb),(146,66),Image.Resampling.LANCZOS);icon.alpha_composite(fit,((150-fit.width)//2,68-fit.height));p=HERE/'construction-clearance-v1'/f'{state}.png';save(p,icon);frame.update(source=rel(p),source_sha256=sha(p),sha256=sha(p))
 recipes['assets/recipes/town/buildingIcons.json']['generation']['assembly_script']=rel(Path(__file__));recipes['assets/recipes/town/buildingIcons.json']['generation']['assembly_script_sha256']=sha(Path(__file__))
 recipe=recipes['assets/recipes/town/background.json'];recipe.update(source=rel(native),source_sha256=sha(native),sha256=sha(native));recipe['generation']['west_support_repair']=selection['terrain']['west_support_repair'];selection['recipes']={}
 for name,recipe in recipes.items():p=OUT/'candidate-recipes'/name;write(p,recipe);selection['recipes'][name]=sha(p)
 write(OUT/'selection.json',selection);write(OUT/'factions.candidate.json',faction);write(HERE/'physical-v5/annotations.json',{'status':'authored configuration','script_sha256':sha(Path(__file__)),'states':physical,'scope':'Faithful native contact profiles; two actual whole-image transforms; no same-plane projection exemption.'})
 rows={r['state']:r for r in selection['states']};save(REPORT/'empty-native.png',background)
 for mode in ('full','base','early','coast','grail','guild-absent'):
  chosen=[site['states'][0] if mode=='base' else site['top'] for site in selection['sites'] if site['id'] not in ('coast','grail')]
  if mode=='early':chosen=['villageHall','fort','dwellingLvl1','tavern']
  if mode=='coast':chosen.append('ship')
  if mode=='grail':chosen.append('grail')
  if mode=='guild-absent':chosen.remove('mageGuild4')
  out=background.copy()
  for state in sorted(chosen,key=lambda s:rows[s]['native_z']):out.alpha_composite(layers[state])
  save(REPORT/(mode+'-native.png'),out)
 for name,im in [('empty',background),('full',Image.open(REPORT/'full-native.png'))]:save(REPORT/(name+'-west-support-4x.png'),im.crop((0,100,225,212)).resize((900,448),Image.Resampling.NEAREST));save(REPORT/(name+'-east-clearance-4x.png'),im.crop((575,90,800,280)).resize((900,760),Image.Resampling.NEAREST))
 print(json.dumps({'candidate':rel(OUT),'background_sha256':sha(native),'transforms':TRANSFORMS,'genuine_masters_preserved':True}))
if __name__=='__main__':main()
