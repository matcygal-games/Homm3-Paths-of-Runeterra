"""Whole-family native placement correction preserving genuine painted sources.

Rift moves twenty native pixels down as a complete three-state family to uncover
the actual upgraded menagerie gate. This is a review candidate, not selection.
"""
from pathlib import Path
from copy import deepcopy
import hashlib,json
from PIL import Image,ImageChops,ImageFilter
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
OUT=HERE/'candidate-access-v1'
REPORT=ROOT/'build/reports/complete-town-20261027-v2/access-v1'
SHIFT=(0,20)
FAMILY={'special4','dwellingLvl7','dwellingUpLvl7'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf8')
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
def rel(p):return p.relative_to(ROOT).as_posix()
def alpha(im,t=128):return im.getchannel('A').point(lambda v:255 if v>=t else 0)
def main():
 base=HERE/'candidate-compatible-v1';selection=deepcopy(load(base/'selection.json'));faction=deepcopy(load(base/'factions.candidate.json'));layers={}
 recipes={n:deepcopy(load(base/'candidate-recipes'/n)) for n in selection['recipes']}
 for row in selection['states']:
  state=row['state'];p=ROOT/row['native_layer']
  if sha(p)!=row['native_layer_sha256']:raise ValueError('Changed source '+state)
  im=Image.open(p).convert('RGBA')
  if state in FAMILY:
   moved=Image.new('RGBA',(800,374));moved.alpha_composite(im,SHIFT)
   if sum(alpha(im,8).histogram()[1:])!=sum(alpha(moved,8).histogram()[1:]):raise ValueError('Clipped shifted body')
   im=moved;folder=HERE/'structures-access-v1'/state;save(folder/'layer.png',im)
   solid=alpha(im);area=Image.new('RGBA',(800,374),(255,255,255,0));area.putalpha(solid);border=Image.new('RGBA',(800,374),(255,230,100,0));border.putalpha(ImageChops.subtract(solid.filter(ImageFilter.MaxFilter(5)),solid));save(folder/'area.png',area);save(folder/'border.png',border)
   row['native_layer']=rel(folder/'layer.png');row['native_layer_sha256']=sha(folder/'layer.png');row['composition_rectangle'][1]+=20;row['native_position'][1]+=20;row['native_z']+=20;row['entrance_intent'][1]+=20
   row['alpha8_bbox']=list(alpha(im,8).getbbox());row['solid_bbox']=list(solid.getbbox());row['placement_repair']={'shift':list(SHIFT),'basis':'Uncover genuine upgraded menagerie gate and stairfoot; complete three-state Rift family translated without repaint/crop/scale.','script':rel(Path(__file__)),'script_sha256':sha(Path(__file__))}
   faction['noxus']['town']['structures'][state]['z']+=20
   for role in ('animation','area','border'):
    recipe=recipes[f'assets/recipes/town/structures/{state}-{role}.json'];source=folder/('layer.png' if role=='animation' else role+'.png');recipe.update(source_sha256=sha(source),sha256=sha(source));recipe['building_contract']['full_canvas_placement']['z']+=20;recipe['building_contract']['native_ground_contact'][1]+=20
    if role=='animation':recipe['groups'][0]['frames'][0].update(source=rel(source),source_sha256=sha(source),sha256=sha(source))
    else:recipe['source']=rel(source)
    recipe['generation']['placement_repair']=row['placement_repair']
  layers[state]=im
 for site in selection['sites']:
  if site['id']=='bindingRift':site['composition_rectangle'][1]+=20;site['native_z']+=20;site['entrance_intent'][1]+=20
 selection['recipes']={}
 for name,recipe in recipes.items():p=OUT/'candidate-recipes'/name;write(p,recipe);selection['recipes'][name]=sha(p)
 selection['access_repair']={'script':rel(Path(__file__)),'script_sha256':sha(Path(__file__)),'base_selection_sha256':sha(base/'selection.json'),'shifted_family':sorted(FAMILY),'shift':list(SHIFT),'source_pixel_appearance_unchanged':True,'composition_review_required':True,'geometry_admitted':False}
 write(OUT/'selection.json',selection);write(OUT/'factions.candidate.json',faction)
 lookup={r['state']:r for r in selection['states']}
 for mode in ('full','base','early','guild-absent','rose-absent','rift-absent','coast','grail'):
  chosen=[s['states'][0] if mode=='base' else s['top'] for s in selection['sites'] if s['id'] not in ('coast','grail')]
  if mode=='early':chosen=['villageHall','fort','dwellingLvl1','tavern']
  if mode=='guild-absent':chosen.remove('mageGuild4')
  if mode=='rose-absent':chosen.remove('dwellingUpLvl4')
  if mode=='rift-absent':chosen.remove('dwellingUpLvl7')
  if mode=='coast':chosen.append('ship')
  if mode=='grail':chosen.append('grail')
  scene=Image.open(ROOT/selection['terrain']['native']).convert('RGBA')
  for state in sorted(chosen,key=lambda s:lookup[s]['native_z']):scene.alpha_composite(layers[state])
  save(REPORT/(mode+'-native.png'),scene)
 probes=[]
 for rose,point in [('dwellingLvl4',(548,192)),('dwellingUpLvl4',(509,190))]:
  for rift in sorted(FAMILY):
   body=alpha(layers[rift]);probes.append({'rose_state':rose,'rift_state':rift,'actual_stairfoot':list(point),'foreground_body_at_stairfoot':bool(body.getpixel(point))})
 write(REPORT/'actual-gate-probes.json',{'status':'authored configuration','probes':probes,'limitation':'Point checks alone do not establish complete gate or route clearance; requires full native image/mask review.'})
 print(json.dumps({'candidate':rel(OUT),'actual_gate_probes':probes}))
if __name__=='__main__':main()
