"""Prepare four genuine palette edits; never paint pixels or publish a stage.

prepare writes versioned own native sources, candidate recipes and diagnostics.
Canonical recipes remain unchanged until an exact independent review and an
explicit coordinator selection window permit the separate deliver command.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys
from PIL import Image,ImageDraw

PROJECT=Path(__file__).resolve().parents[1]
BASE=PROJECT/'assets/source/auxiliary/chemtech-palette-v7'
REVIEW=PROJECT/'assets/reviews/aux-palette-v7'
REPORT=PROJECT/'build/reports/aux-palette-v7'
FAMILIES={
 'siege-background':('assets/source/siege/SGZABACK/chemtech-palette-v7',(800,556),'assets/recipes/siege/SGZABACK.json'),
 'guild-window':('assets/source/interface/chemtech-palette-v7/guildWindow',(141,217),'assets/recipes/town/ui/guildWindow.json'),
 'puzzle-master':('assets/source/puzzle/chemtech-palette-v7',(592,544),None),
 'pressure-projectile':('assets/source/projectiles/pressureShot/chemtech-palette-v7',(64,64),'assets/recipes/projectiles/pressureShot.json'),
}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def rel(path):return path.relative_to(PROJECT).as_posix()
def keep(path,payload):
 path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists() and path.read_bytes()!=payload:raise ValueError(f'Preserve versioned output: {path}')
 if not path.exists():path.write_bytes(payload)
def encoded(value):return (json.dumps(value,indent=2,sort_keys=True,ensure_ascii=False)+'\n').encode()
def dump(path,value):keep(path,encoded(value))
def png(path,picture):
 import io
 output=io.BytesIO();picture.save(output,format='PNG');keep(path,output.getvalue())
def uniform_full_canvas(image,size):
 """One uniform whole-image camera resample and <=1px technical center crop."""
 scale=max(size[0]/image.width,size[1]/image.height)
 scaled=(max(size[0],round(image.width*scale)),max(size[1],round(image.height*scale)))
 if abs(scaled[0]-size[0])>2 or abs(scaled[1]-size[1])>2:raise ValueError('Imagegen camera/aspect drift needs genuine repair')
 resized=image.resize(scaled,Image.Resampling.LANCZOS);x=(scaled[0]-size[0])//2;y=(scaled[1]-size[1])//2
 return resized.crop((x,y,x+size[0],y+size[1])),{'uniform_scale':scale,'resampled_canvas':list(scaled),'technical_crop':[x,y,x+size[0],y+size[1]]}
def prepare():
 records=[];exports={};native_info={}
 for family,(folder,size,recipe_name) in FAMILIES.items():
  root=PROJECT/folder;raw=root/'master-generated.png';generation=json.loads((root/'generation.json').read_text())
  if generation['master_sha256']!=sha(raw) or generation['image_generation_used'] is not True:raise ValueError('Real master pin missing')
  with Image.open(raw) as image:image=image.convert('RGBA')
  if family!='pressure-projectile':
   native,technical=uniform_full_canvas(image,size)
   path=root/('master-592x544.png' if family=='puzzle-master' else 'native.png');png(path,native)
   exports[family]=path;native_info[family]={'native':rel(path),'sha256':sha(path),'size':list(size),'raw_master':rel(raw),'raw_sha256':sha(raw),**technical}
  else:
   cells=[]
   for index in range(8):
    rect=(round(index%4*image.width/4),round(index//4*image.height/2),round((index%4+1)*image.width/4),round((index//4+1)*image.height/2))
    cell=image.crop(rect);bounds=cell.getchannel('A').point(lambda a:255 if a>=8 else 0).getbbox()
    if not bounds:raise ValueError('Empty projectile painting')
    box=(max(0,bounds[0]-3),max(0,bounds[1]-3),min(cell.width,bounds[2]+3),min(cell.height,bounds[3]+3))
    cells.append((cell,rect,box,bounds))
   scale=28/max(max(b[2]-b[0],b[3]-b[1]) for _,_,_,b in cells);frames=[]
   for index,(cell,rect,box,bounds) in enumerate(cells):
    sprite=cell.crop(box);sprite=sprite.resize((round(sprite.width*scale),round(sprite.height*scale)),Image.Resampling.LANCZOS)
    native=Image.new('RGBA',size);xy=((size[0]-sprite.width)//2,(size[1]-sprite.height)//2);native.alpha_composite(sprite,xy)
    path=root/f'native/g00/g00-f{index:03d}.png';png(path,native)
    frames.append({'source':rel(path),'sha256':sha(path),'source_cell':list(rect),'whole_subject_crop':list(box),'native_translation':list(xy)})
   cohort={'status':'built-unreviewed','visual_approval_granted':False,'canvas':[64,64],'source_center':[32,32],
    'master':rel(raw),'master_sha256':sha(raw),'whole_cohort_scale':scale,'frames':frames,
    'first_five_angle_views':[90,45,0,-45,-90],'last_three_roll_views_unused_by_angle_selection':True,
    'painting_used':'genuine palette edit of all8 own painted angle/roll views; no Python rotation, recolor or alpha erasure',
    'no_renderer_pivot_claim':True,'geometry_and_nozzle_offsets_changed':False}
   path=root/'cohort.json';dump(path,cohort);exports[family]=path
   native_info[family]={'native':rel(path),'sha256':sha(path),'size':[64,64],'raw_master':rel(raw),'raw_sha256':sha(raw),'frames':frames,'uniform_scale':scale}
 for family,(folder,size,recipe_name) in FAMILIES.items():
  root=PROJECT/folder;generation=json.loads((root/'generation.json').read_text());names=[recipe_name] if recipe_name else [f'assets/recipes/puzzle/piece{i:02d}.json' for i in range(48)]
  if family=='puzzle-master':
   with Image.open(exports[family]) as master:master=master.convert('RGBA')
   rebuilt=Image.new('RGBA',master.size)
   for index,name in enumerate(names):
    source_recipe=json.loads((PROJECT/name).read_text());crop=source_recipe['composition']['crop'];box=(crop['x'],crop['y'],crop['x']+crop['width'],crop['y']+crop['height'])
    expected=((index%8)*74,(index//8)*91,74,89 if index>=40 else 91)
    if (crop['x'],crop['y'],crop['width'],crop['height'])!=expected:raise ValueError('Puzzle crop/reveal geometry changed')
    piece=master.crop(box);path=root/f'piece{index:02d}.png';png(path,piece);rebuilt.alpha_composite(piece,(crop['x'],crop['y']))
   if rebuilt.tobytes()!=master.tobytes():raise ValueError('Puzzle pieces create seams or lose pixels')
   native_info[family]['puzzle_reconstructs_exact_pixel_bytes']=True
  for index,name in enumerate(names):
   canonical=PROJECT/name;old=canonical.read_bytes();recipe=json.loads(old)
   history=BASE/'previous-recipes'/name.removeprefix('assets/recipes/');keep(history,old)
   source=root/f'piece{index:02d}.png' if family=='puzzle-master' else exports[family]
   recipe.update({'source':rel(source),'source_sha256':sha(source),'production_status':'delivered','status':'built-unreviewed','visual_approval_granted':False,
    'credits':{'author':'Runeterra Zaun project using OpenAI built-in image_gen','license':None,'redistribution':'unresolved; release prohibited'},
    'generation':{'provider':'OpenAI built-in image_gen','model':None,'model_disclosure':'The built-in tool did not expose a model identifier.',
     'image_generation_used':True,'painted_master':rel(root/'master-generated.png'),'painted_master_sha256':sha(root/'master-generated.png'),
     'prompt':rel(root/'prompt.txt'),'returned_provenance':generation['returned_output_hint'],'route':'genuine green/purple/brown palette painting edit; uniform native resample/crop only'},
    'delivery':{'status':'built-unreviewed','visual_approval_granted':False,'runtime_verified':False,
     'sources':[{'path':rel(source),'sha256':sha(source)},{'path':rel(root/'master-generated.png'),'sha256':sha(root/'master-generated.png')}],
     'palette_policy':'design/chemtech-art-direction.json','palette_provenance':rel(root/'generation.json'),
     'independent_review':None,'independent_review_sha256':None}})
   if family=='puzzle-master':recipe['composition'].update({'master':rel(exports[family]),'master_sha256':sha(exports[family])})
   if family=='pressure-projectile':
    recipe['groups'][0]['frames']=[{'source':f['source'],'sha256':f['sha256']} for f in native_info[family]['frames']]
    recipe['art_direction']='Physical bronze/iron pressure ampoule with luminous green reagent glass and a violet marker; five native angle views plus3unused roll views, no beam/cloud/trail or spinning claim.'
   candidate=BASE/'candidate-recipes'/name.removeprefix('assets/recipes/');dump(candidate,recipe)
   records.append({'family':family,'canonical_recipe':name,'canonical_before_sha256':sha(canonical),'previous_recipe':rel(history),
    'candidate_recipe':rel(candidate),'candidate_sha256':sha(candidate),'source':rel(source),'source_sha256':sha(source)})
 # Read-only own-before/own-after diagnostics; no original-game pixels are used.
 for family,old_path in [('siege-background','assets/source/siege/SGZABACK/painted-v2/master.png'),('guild-window','assets/source/interface/painted-v2/guildWindow.png'),('puzzle-master','assets/source/puzzle/painted-v2/master-592x544.png')]:
  with Image.open(PROJECT/old_path) as old:old=old.convert('RGBA')
  with Image.open(exports[family]) as new:new=new.convert('RGBA')
  board=Image.new('RGBA',(new.width*2,new.height),(105,108,112,255));board.alpha_composite(old,(0,0));board.alpha_composite(new,(new.width,0));png(REVIEW/f'{family}-native-before-after.png',board)
 old_recipe=json.loads((PROJECT/FAMILIES['pressure-projectile'][2]).read_text());board=Image.new('RGBA',(8*64,2*64),(105,108,112,255))
 for i,(old,new) in enumerate(zip(old_recipe['groups'][0]['frames'],native_info['pressure-projectile']['frames'])):
  board.alpha_composite(Image.open(PROJECT/old['source']).convert('RGBA'),(i*64,0));board.alpha_composite(Image.open(PROJECT/new['source']).convert('RGBA'),(i*64,64))
 png(REVIEW/'pressure-projectile-native-before-after.png',board)
 selection={'status':'built-unreviewed','painter_id':'/root/zaun_aux_art','canonical_recipes_changed':False,'affected_recipe_count':len(records),
  'recipes':records,'native_sources':native_info,'native_boards':{rel(p):sha(p) for p in sorted(REVIEW.glob('*-native-before-after.png'))},
  'runtime_verified':False,'release_accepted':False,'visual_approval_granted':False,'held_for_coordinator_selection':True}
 dump(BASE/'selection.json',selection);dump(REPORT/'prepared-sources.json',selection)
 print(json.dumps({'affected_recipes':len(records),'source_selection':rel(BASE/'selection.json'),'selection_sha256':sha(BASE/'selection.json'),'canonical_recipes_changed':False,'boards':selection['native_boards']}))

if __name__=='__main__':
 if sys.argv[1:]==['prepare']:prepare()
 else:raise ValueError('Only prepare is available before independent review/coordinator selection.')
