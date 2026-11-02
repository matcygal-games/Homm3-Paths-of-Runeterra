"""Reproducible V6 candidate-only assembly; active sources/staging stay untouched.

Frozen placement930 is authoritative. Creative generation replaces ONLY backdrop;
each of36 existing functional master paths/hashes must still match V5 exactly.
"""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys
from PIL import Image,ImageChops,ImageFilter,ImageOps,ImageDraw

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
REPORT=ROOT/'build/reports/urban-town-community-20261024-v6'
FROZEN=REPORT/'plan-v2/placement-plan.json'
EXPECTED='93097eded68b7c275dd689c0fe344684b0e439102d4acf5c0549ba0b0c0b88c0'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def rel(p):return p.relative_to(ROOT).as_posix()
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,optimize=False,compress_level=9)
def mask(im,t=128):return im.getchannel('A').point(lambda a:255 if a>=t else 0)
def count(im):return sum(im.histogram()[128:])
def prepare(background_version):
 if sha(FROZEN)!=EXPECTED:raise ValueError('Frozen placement changed: use a new version and review.')
 plan=load(FROZEN);old=load(ROOT/'assets/source/town/urban-community-20261024-v5/selection.json')
 oldrows={r['state']:r for r in old['states']};rows=[];layers={};recipes={}
 selected_bg=HERE/f'background-master-v{background_version}.png'
 bg=ImageOps.fit(Image.open(selected_bg).convert('RGBA'),(800,374),method=Image.Resampling.LANCZOS)
 save(HERE/f'background-native-v{background_version}.png',bg)
 templates=load(ROOT/'assets/source/town/urban-community-20261024-v5/input-recipes.json')
 names=load(ROOT/'content/factions.json')['noxus']['town']['buildings']
 for r in plan['states']:
  state=r['state'];prev=oldrows[state];master=ROOT/r['master']
  if (r['master'],r['master_sha256'])!=(prev['master'],prev['master_sha256']) or sha(master)!=r['master_sha256']:
   raise ValueError('Functional building master changed: '+state)
  layer=Image.open(HERE/'planned-structures'/state/'layer.png').convert('RGBA');layers[state]=layer
  folder=HERE/'structures'/state
  save(folder/'layer.png',layer)
  solid=mask(layer);area=Image.new('RGBA',(800,374),(255,255,255,0));area.putalpha(solid)
  border=Image.new('RGBA',(800,374),(255,230,100,0));border.putalpha(ImageChops.subtract(solid.filter(ImageFilter.MaxFilter(5)),solid))
  save(folder/'area.png',area);save(folder/'border.png',border)
  row=deepcopy(r);row.update(native_layer=rel(folder/'layer.png'),native_layer_sha256=sha(folder/'layer.png'),click_bbox=list(solid.getbbox()),click_pixels=count(solid),visual_approval_granted=False)
  row['entrance']['scope']='Frozen manually identified source doorway/stair plus planned support route; actual terrain support requires exact-pixel review. Not native pathfinding.'
  rows.append(row)
  for role in ('animation','area','border'):
   key=f'assets/recipes/town/structures/{state}-{role}.json';rec=deepcopy(templates[key])
   source=folder/('layer.png' if role=='animation' else role+'.png')
   rec.update(production_status='painted-master-complete' if role=='animation' else 'derived-technical-mask-complete',status='built-unreviewed',source_sha256=sha(source),sha256=sha(source),source_canvas=[800,374],fit='exact',visual_approval_granted=False)
   rec['building_contract'].update(full_canvas_placement={'x':0,'y':0,'z':r['native_z']},native_ground_contact=r['composition_rectangle'],name=names[state].get('name',state))
   oldrec=load(ROOT/'assets/source/town/urban-community-20261024-v5/candidate-recipes'/key)
   rec['generation']=deepcopy(oldrec['generation'])
   rec['generation']['conversion']={'method':'Uniform alpha crop/contain of the byte-exact existing painted2D master; frozen930 planned placement. No new building art, perspective warp or raster painting.','source_crop':r['source_crop'],'placement_box':r['composition_rectangle'],'native_position':r['native_position'],'native_size':r['native_size'],'site':r['site'],'mirror_x':r['mirror_x'],'assembly_script':rel(Path(__file__)),'assembly_script_sha256':sha(Path(__file__)),'frozen_plan_sha256':EXPECTED}
   if role=='animation':rec['groups'][0]['frames'][0].update(source=rel(source),source_sha256=sha(source),sha256=sha(source))
   else:
    rec['source']=rel(source);rec['generation']['image_generation_used']=False
    rec['generation']['method']='Exact alpha128 silhouette area and two-pixel outward MaxFilter5-minus-silhouette highlight.'
   recipes[key]=rec
 # Construction thumbnails are byte-exact existing derivatives of same masters;
 # source placement changes do not authorize reillustration or icon redesign.
 key='assets/recipes/town/buildingIcons.json'
 recipes[key]=load(ROOT/'assets/source/town/urban-community-20261024-v5/candidate-recipes'/key)
 key='assets/recipes/town/background.json';rec=deepcopy(templates[key]);source=HERE/f'background-native-v{background_version}.png';record=HERE/f'background-generation-v{background_version}.json'
 rec.update(source=rel(source),source_sha256=sha(source),sha256=sha(source),source_canvas=[800,374],fit='exact',production_status='painted-master-complete',status='built-unreviewed',visual_approval_granted=False)
 rec['generation']={'image_generation_used':True,'provider':'OpenAI built-in imagegen','model':'Not exposed by the built-in tool','prompt':load(record)['prompt'],'painted_master':rel(selected_bg),'painted_master_sha256':sha(selected_bg),'generation_record':rel(record),'generation_record_sha256':sha(record),'conversion':'Uniform cover-fit to native800x374; no artistic raster changes.'}
 recipes[key]=rec
 candidate=HERE/f'candidate-v{background_version}'
 for key,rec in recipes.items():write(candidate/'candidate-recipes'/key,rec)
 selection={k:deepcopy(v) for k,v in plan.items() if k not in ('states','collision_results','painting_requirements')}
 selection.update(status='authored configuration',state_count=36,states=rows,recipes={k:sha(candidate/'candidate-recipes'/k) for k in recipes},terrain={'master':rel(selected_bg),'master_sha256':sha(selected_bg),'native':rel(source),'native_sha256':sha(source),'water_polygon':plan['water_polygon']},visual_approval_granted=False,coast_semantics='Ship replaces shipyard at same site/z; selected ship image includes dock and boat.',frozen_placement_sha256=EXPECTED)
 write(candidate/'selection.json',selection)
 save(REPORT/f'empty-native-v{background_version}.png',bg)
 for mode in ('base','upgraded','coast','moored','grail','early'):
  chosen=[s['buildings'][0] if mode=='base' else s['buildings'][-1] for s in plan['sites'] if s['id'] not in ('shipyard','grail')]
  if mode=='coast':chosen.append('shipyard')
  if mode=='moored':chosen.append('ship')
  if mode=='grail':chosen.append('grail')
  if mode=='early':chosen=['villageHall','fort','dwellingLvl1','tavern']
  out=bg.copy()
  for state in sorted(chosen,key=lambda s:next(r['native_z'] for r in rows if r['state']==s)):out.alpha_composite(layers[state])
  save(REPORT/f'{mode}-native-v{background_version}.png',out)
  if mode in ('base','upgraded'):
   draw=ImageDraw.Draw(out)
   for r in rows:
    if r['state'] not in chosen:continue
    e=r['entrance'];draw.line([tuple(p) for p in e['planned_route']],fill=(40,235,225),width=1)
    x,y=e['door_point'];draw.ellipse((x-1,y-1,x+1,y+1),fill=(255,70,60))
   save(REPORT/f'{mode}-entrance-study-v{background_version}.png',out)
 print(json.dumps({'background_version':background_version,'candidate':rel(candidate),'states':len(rows),'recipes':len(recipes),'all36_master_hashes_preserved':True,'placement_sha256':EXPECTED}))
if __name__=='__main__':prepare(int(sys.argv[1]))
