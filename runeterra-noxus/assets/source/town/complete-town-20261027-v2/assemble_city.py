"""Source-only deterministic assembly of the reviewed complete Noxian city.

Every body is genuine painted2D derived from this full master, including all
predecessor states. No canonical selection, publication or private mount changes.
"""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys
from PIL import Image,ImageOps,ImageChops,ImageFilter,ImageDraw
from city_plan import SITES

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
REPORT=ROOT/'build/reports/complete-town-20261027-v2'
CANDIDATE=HERE/'candidate'
SIZE=(800,374)
ALIASES={'castle':'castle-extraction'}
SMALL={'villageHall':.72,'townHall':.86,'cityHall':.95,'fort':.88,'citadel':.95,'mageGuild1':.70,'mageGuild2':.82,'mageGuild3':.91,'special4':.72}
for tier in range(1,8):SMALL[f'dwellingLvl{tier}']=.90
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_text(encoding='utf-8'))
def write(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def save(path,image):path.parent.mkdir(parents=True,exist_ok=True);image.save(path,compress_level=9)
def rel(path):return path.relative_to(ROOT).as_posix()
def mask(im,t=128):return im.getchannel('A').point(lambda v:255 if v>=t else 0)
def count(im):return im.histogram()[255]

def prepare():
 REPORT.mkdir(parents=True,exist_ok=True)
 master=ImageOps.fit(Image.open(HERE/'complete-city-master-v2.png').convert('RGBA'),SIZE,method=Image.Resampling.LANCZOS)
 background=ImageOps.fit(Image.open(HERE/'terrain/master.png').convert('RGBA'),SIZE,method=Image.Resampling.LANCZOS)
 save(HERE/'terrain/native.png',background.convert('RGB'))
 sites=deepcopy(SITES)
 sites['coast']={'states':['shipyard','ship'],'top':'ship','rect':[748,122,49,70],'door':[751,172],'z':207,'poly':[]}
 sites['grail']={'states':['grail'],'top':'grail','rect':[219,120,18,26],'door':[228,145],'z':147,'poly':[]}
 rows=[];layers={};recipes={};templates={p.relative_to(ROOT).as_posix():load(p) for p in (ROOT/'assets/recipes/town').rglob('*.json')}
 faction=deepcopy(load(ROOT/'content/factions.json'));names=faction['noxus']['town']['buildings']
 for site,entry in sites.items():
  for state in entry['states']:
   provider=HERE/'state-art'/ALIASES.get(state,state)/'master.png';im=Image.open(provider).convert('RGBA');bb=mask(im,8).getbbox()
   if not bb:raise ValueError('Empty genuine source '+state)
   x,y,w,h=entry['rect'];factor=SMALL.get(state,1.0);fitted=ImageOps.contain(im.crop(bb),(max(8,round(w*factor)),max(8,round(h*factor))),Image.Resampling.LANCZOS)
   xy=[x+(w-fitted.width)//2,y+h-fitted.height]
   layer=Image.new('RGBA',SIZE);layer.alpha_composite(fitted,xy)
   # Preserve exact visible master RGB where source registration is confirmed by
   # the traced subject and matching reconstructed extraction. Keep extracted
   # alpha/openings, and retain genuinely painted hidden faces elsewhere.
   preserve=Image.new('L',SIZE)
   if state==entry['top'] and site not in ('coast','grail'):
    poly=Image.new('L',SIZE);ImageDraw.Draw(poly).polygon(entry['poly'],fill=255)
    for other,info in sites.items():
     if other!=site and info['z']>entry['z'] and info['poly']:
      ImageDraw.Draw(poly).polygon(info['poly'],fill=0)
    preserve=ImageChops.multiply(poly,mask(layer,240)).filter(ImageFilter.MinFilter(3))
    # Matching painted colours gate preservation at source edges rather than
    # copying scenery or moving an architectural feature to hide registration.
    pixels=preserve.load();a=layer.load();b=master.load()
    for py in range(SIZE[1]):
     for px in range(SIZE[0]):
      if pixels[px,py] and max(abs(a[px,py][c]-b[px,py][c]) for c in range(3))>28:pixels[px,py]=0
    restore=master.copy();restore.putalpha(preserve);layer.alpha_composite(restore)
   folder=HERE/'structures'/state;save(folder/'layer.png',layer);save(folder/'master-visible-preservation-mask.png',preserve)
   solid=mask(layer);area=Image.new('RGBA',SIZE,(255,255,255,0));area.putalpha(solid);border=Image.new('RGBA',SIZE,(255,230,100,0));border.putalpha(ImageChops.subtract(solid.filter(ImageFilter.MaxFilter(5)),solid));save(folder/'area.png',area);save(folder/'border.png',border)
   bbox=list(mask(layer,8).getbbox());row={'state':state,'site':site,'master':rel(provider),'master_sha256':sha(provider),'whole_city_master':'assets/source/town/complete-town-20261027-v2/complete-city-master-v2.png','whole_city_master_sha256':sha(HERE/'complete-city-master-v2.png'),'native_layer':rel(folder/'layer.png'),'native_layer_sha256':sha(folder/'layer.png'),'composition_rectangle':entry['rect'],'source_crop':list(bb),'native_position':xy,'native_size':list(fitted.size),'native_z':entry['z'],'alpha8_bbox':bbox,'solid_bbox':list(solid.getbbox()),'full_silhouette_pixels':count(mask(layer,8)),'native_master_rgb_preserved_pixels':count(preserve),'entrance_intent':entry['door'],'visual_approval_granted':False}
   rows.append(row);layers[state]=layer
   faction['noxus']['town']['structures'][state].update(x=0,y=0,z=entry['z'])
   for role in ('animation','area','border'):
    key=f'assets/recipes/town/structures/{state}-{role}.json';recipe=deepcopy(templates[key]);source=folder/('layer.png' if role=='animation' else role+'.png')
    recipe.update(source_sha256=sha(source),sha256=sha(source),source_canvas=list(SIZE),fit='exact',production_status='painted-master-complete' if role=='animation' else 'derived-technical-mask-complete',status='built-unreviewed',visual_approval_granted=False)
    recipe['building_contract'].update(full_canvas_placement={'x':0,'y':0,'z':entry['z']},native_ground_contact=entry['rect'],name=names[state].get('name',state))
    recipe['generation']={'image_generation_used':role=='animation','provider':'OpenAI built-in image_gen' if role=='animation' else None,'model':'Not exposed by built-in tool','painted_master':rel(provider),'painted_master_sha256':sha(provider),'generation_record':rel(provider.with_name('generation.json')),'generation_record_sha256':sha(provider.with_name('generation.json')),'whole_city_master':row['whole_city_master'],'whole_city_master_sha256':row['whole_city_master_sha256'],'conversion':{'method':'Whole genuine painted source uniform alpha crop/contain into the approved complete-city site; visible matching master RGB retained under explicit technical preservation mask. No new architecture drawn by code.','source_crop':list(bb),'native_position':xy,'native_size':list(fitted.size),'site':site,'assembly_script':rel(Path(__file__)),'assembly_script_sha256':sha(Path(__file__)),'preserved_master_pixels':count(preserve),'preservation_mask':rel(folder/'master-visible-preservation-mask.png'),'preservation_mask_sha256':sha(folder/'master-visible-preservation-mask.png')}}
    if role=='animation':recipe['groups'][0]['frames'][0].update(source=rel(source),source_sha256=sha(source),sha256=sha(source))
    else:recipe['source']=rel(source);recipe['generation']['method']='Exact native alpha128 area and MaxFilter5-minus-area outward border.'
    recipes[key]=recipe
 # Sparse native construction IDs are preserved; all pictured architecture is
 # regenerated from the new selected city-derived state cohort.
 key='assets/recipes/town/buildingIcons.json';recipe=deepcopy(templates[key])
 for frame in recipe['frames']:
  state=frame['building'];image=layers[state];bb=mask(image,8).getbbox();icon=Image.new('RGBA',(150,70));fit=ImageOps.contain(image.crop(bb),(146,66),Image.Resampling.LANCZOS);icon.alpha_composite(fit,((150-fit.width)//2,68-fit.height));path=HERE/'construction'/f'{state}.png';save(path,icon);frame.update(source=rel(path),source_sha256=sha(path),sha256=sha(path))
 recipe['generation']={'image_generation_used':False,'method':'Construction icons uniformly derived from all new genuine complete-city state bodies, preserving native sparse IDs.','assembly_script':rel(Path(__file__)),'assembly_script_sha256':sha(Path(__file__))};recipes[key]=recipe
 key='assets/recipes/town/background.json';recipe=deepcopy(templates[key]);source=HERE/'terrain/native.png';recipe.update(source=rel(source),source_sha256=sha(source),sha256=sha(source),source_canvas=list(SIZE),fit='exact',production_status='painted-master-complete',status='built-unreviewed',visual_approval_granted=False);recipe['generation']={'image_generation_used':True,'provider':'OpenAI built-in image_gen','model':'Not exposed by built-in tool','prompt':(HERE/'terrain/prompt.txt').read_text(),'painted_master':rel(HERE/'terrain/master.png'),'painted_master_sha256':sha(HERE/'terrain/master.png'),'generation_record':rel(HERE/'terrain/generation.json'),'generation_record_sha256':sha(HERE/'terrain/generation.json'),'conversion':'Uniform cover fit to800x374, no functional architecture baked into terrain.'};recipes[key]=recipe
 for key,recipe in recipes.items():write(CANDIDATE/'candidate-recipes'/key,recipe)
 write(CANDIDATE/'factions.candidate.json',faction)
 selection={'status':'authored configuration','canvas':list(SIZE),'state_count':len(rows),'site_count':len(sites),'ordinary_land_sites':17,'states':rows,'sites':[{'id':key,'states':value['states'],'top':value['top'],'composition_rectangle':value['rect'],'native_z':value['z'],'entrance_intent':value['door']} for key,value in sites.items()],'recipes':{key:sha(CANDIDATE/'candidate-recipes'/key) for key in recipes},'terrain':{'master':rel(HERE/'terrain/master.png'),'master_sha256':sha(HERE/'terrain/master.png'),'native':rel(HERE/'terrain/native.png'),'native_sha256':sha(HERE/'terrain/native.png')},'complete_master':{'path':rel(HERE/'complete-city-master-v2.png'),'sha256':sha(HERE/'complete-city-master-v2.png')},'native_verified':False,'release_accepted':False}
 write(CANDIDATE/'selection.json',selection)
 save(REPORT/'empty-native.png',background)
 for mode in ('full','city-hall','base','early','coast','grail','guild-absent'):
  chosen=[(entry['states'][0] if mode=='base' else entry['top']) for site,entry in sites.items() if site not in ('coast','grail')]
  if mode=='city-hall':chosen[chosen.index('capitol')]='cityHall'
  if mode=='early':chosen=['villageHall','fort','dwellingLvl1','tavern']
  if mode=='coast':chosen.append('ship')
  if mode=='grail':chosen.append('grail')
  if mode=='guild-absent':chosen=[state for state in chosen if state!='mageGuild4']
  lookup={row['state']:row for row in rows};out=background.copy()
  for state in sorted(chosen,key=lambda item:lookup[item]['native_z']):out.alpha_composite(layers[state])
  save(REPORT/(mode+'-native.png'),out)
 print(json.dumps({'candidate':rel(CANDIDATE),'states':len(rows),'sites':len(sites),'recipes':len(recipes),'master_rgb_preserved_pixels':sum(r['native_master_rgb_preserved_pixels'] for r in rows)}))

if __name__=='__main__':prepare()
