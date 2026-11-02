"""Portable candidate compiler. Pure technical assembly of genuine painted keys."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps
import copy,hashlib,json,sys,io
sys.dont_write_bytecode=True
SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
WORKSPACE=PROJECT.parent
REPORT=PROJECT/'build/reports/playable-creatures-20261028-v1'
CANVAS=(450,400)
ROOT=(218,266)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(PROJECT).as_posix()
def put(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def png(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
def descriptor(p):
 record={'source':rel(p),'source_sha256':sha(p)}
 if p.suffix.lower()=='.png':record['source_canvas']=list(Image.open(p).size)
 return record
def fixed(im,canvas,root,source_root,scale):
 return im.transform(canvas,Image.Transform.AFFINE,(1/scale,0,source_root[0]-root[0]/scale,0,1/scale,source_root[1]-root[1]/scale),Image.Resampling.BICUBIC)
def resource_transform(im,canvas,root,source_root,scale,keys):
 if keys.get('canvas_registration'):
  source_root=keys['canvas_registration'][str(im.width)+'x'+str(im.height)]
 if keys.get('logical_canvas'):
  logical=keys['logical_canvas'];factor=im.width/logical[0]
  if abs(im.height-logical[1]*factor)>2:raise ValueError('Unexpected whole-canvas aspect; never body-fit')
  return fixed(im,canvas,root,(source_root[0]*factor,source_root[1]*factor),scale/factor)
 return fixed(im,canvas,root,source_root,scale)
def edge(im):
 a=im.getchannel('A');w,h=im.size
 return max(a.crop(b).getextrema()[1] for b in ((0,0,w,1),(0,h-1,w,h),(0,0,1,h),(w-1,0,w,h)))
def checkbg(size):
 im=Image.new('RGBA',size,(105,105,105,255));d=ImageDraw.Draw(im)
 for y in range(0,size[1],8):
  for x in range(0,size[0],8):
   if (x//8+y//8)%2:d.rectangle((x,y,x+7,y+7),fill=(145,145,145,255))
 return im
def finish(unit,battle,standing,attack,source_root,scale,keys,old_recipe=None):
 outdir=SOURCE/unit;outdir.mkdir(parents=True,exist_ok=True)
 groups={r['group']:r['frames'] for r in battle['groups']}
 # Native HIT begins when currentFrame*2 >= frame count: contact must survive index3/6.
 for g in (11,12,13):
  old=groups[g]
  if len(old)==5:groups[g]=[old[0],old[1],old[2],old[2],old[3],old[4]]
 groups[22]=[copy.deepcopy(groups[5][-1])]
 groups[20]=[copy.deepcopy(groups[2][0]),copy.deepcopy(groups[0][0])]
 groups[21]=[copy.deepcopy(groups[0][-1]),copy.deepcopy(groups[2][0])]
 battle['groups']=[{'group':g,'frames':v} for g,v in sorted(groups.items())]
 conversion={'status':'authored configuration','unit':unit,'producer':descriptor(Path(__file__)),
   'source_keys':keys,'source_dependency_pins':[descriptor(PROJECT/p) for p in keys.get('all_keys',keys['walk'])],
   'native_battle_root':[battle['pivot']['x'],battle['pivot']['y']],'native_battle_canvas':CANVAS,
   'terminal_corpse':'DEAD22 is byte-identical to final DEATH5 frame',
   'melee_contact':'Five-frame cohorts become six with genuine contact held at2/3. Existing2-frame contacts remain at1. No interpolation.',
   'source_root':source_root,'battle_scale':scale,'per_pose_fit':False,
   'map_canvas':[96,64],'map_root':[64,60],'encounter_canvas':[64,64],'encounter_root':[32,60],
   'map_scale':keys.get('map_scale',.032),'map_registered_right_world_contact':[-32,-4],
   'map_facing':'actual native FromRight requires visually LEFT; FromLeft visually RIGHT',
   'visual_approval_granted':False,'native_execution':False}
 if old_recipe:conversion['retained_source_recipe']=descriptor(old_recipe)
 provenance=outdir/'conversion-v1.json';put(provenance,conversion)
 generation=copy.deepcopy(battle['generation']);generation['provenance']=rel(provenance)
 generation['painted_master']=rel(standing);generation['painted_master_sha256']=sha(standing)
 generation['method']='Genuine independently painted2D action keys, uniform family scale/root; exact native consumer roles and terminal corpse. No3D source, no IDLE translations as locomotion.'
 battle.update(generation=generation,unit=unit,status='authored configuration',visual_approval_granted=False,
   acceptance='Technical candidate. See actual pixel review and unresolved crest findings; native gameplay/visual/rights acceptance not granted.')
 recipes=SOURCE/'recipe-payload'/unit
 put(recipes/'battle.json',battle)
 frames={};mapwalk=[]
 # Map locomotion uses actual articulated walk masters; no translated holding picture.
 for i,key in enumerate(keys['walk']):
  im=Image.open(PROJECT/key).convert('RGBA')
  view=resource_transform(im,(96,64),(64,60),source_root,keys.get('map_scale',.032),keys)
  p=outdir/'resources'/f'map-{i:03d}.png';png(p,view);mapwalk.append(descriptor(p))
 reaction=resource_transform(Image.open(attack).convert('RGBA'),(64,64),(32,60),source_root,keys.get('map_scale',.032),keys)
 # This mapping follows native Castle selector, not misleading resource filenames.
 frames['attackLeft']=reaction
 frames['attackRight']=ImageOps.mirror(reaction)
 # Full-canvas mirror has a one-pixel root change32->31, preserved explicitly.
 # Native map opposite is controlled by its real consumer, not an extra source frame.
 stand=Image.open(standing).convert('RGBA');cropbox=keys['portrait_crop']
 if keys.get('logical_canvas'):cropbox=[round(n*stand.width/keys['logical_canvas'][0]) for n in cropbox]
 crop=stand.crop(cropbox)
 for role,size in [('large',(58,64)),('small',(32,32))]:
  factor=min(size[0]/crop.width,size[1]/crop.height);wh=(round(crop.width*factor),round(crop.height*factor))
  view=crop.resize(wh,Image.Resampling.LANCZOS);im=Image.new('RGBA',size);im.paste(view,((size[0]-wh[0])//2,(size[1]-wh[1])//2));frames[role]=im
 for role,im in frames.items():png(outdir/'resources'/f'{role}.png',im)
 base={k:copy.deepcopy(v) for k,v in battle.items() if k not in ('groups','pivot','canvas','generateOverlay','generateShadow','recipe_type','output_path')}
 prefix='Content/Sprites/runeterra/shurima/creatures/'+unit+'/'
 for role in ('map','attackLeft','attackRight','large','small'):
  recipe=copy.deepcopy(base);recipe['output_path']=prefix+role+('.json' if role=='map' else '.png')
  if role=='map':recipe.update(recipe_type='vcmi_animation',canvas=[96,64],pivot={'x':64,'y':60},generateShadow=0,generateOverlay=1,groups=[{'group':0,'frames':mapwalk}])
  else:recipe.update(recipe_type='raster',**descriptor(outdir/'resources'/f'{role}.png'),size=list(frames[role].size),fit='exact',require_alpha=True)
  put(recipes/(role+'.json'),recipe)
 sys.path.insert(0,str(WORKSPACE/'scripts'));import faction_art_compile
 compiler=faction_art_compile.create_compiler('shurima');runs=[];receipts=[]
 for run in (1,2):
  pins={}
  for recipe in sorted(recipes.glob('*.json')):
   outputs,receipt=compiler.plan(PROJECT,recipe)
   if run==1:receipts.append(receipt)
   for path,data in outputs.items():
    pins[path]=hashlib.sha256(data).hexdigest()
    if run==1:
     dest=REPORT/'compiled'/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
  runs.append(pins)
 assert runs[0]==runs[1]
 assert groups[22][0]['source_sha256']==groups[5][-1]['source_sha256']
 # Full-canvas native reverse, matching CreatureAnimation::verticalFlip.
 rois=(115,135,335,292);w=220;h=175;tiles=[]
 for g,seq in groups.items():
  images=[Image.open(PROJECT/f['source']).convert('RGBA') for f in seq]
  for i,im in enumerate(images):
   bg=checkbg((w,h));bg.alpha_composite(im.crop(rois),(0,18));ImageDraw.Draw(bg).text((2,1),f'g{g:02} f{i:03}',fill='white');tiles.append(bg)
  if len(images)>1:
   displays=[]
   for im in images:
    bg=checkbg((450,175));bg.alpha_composite(im.crop(rois),(0,18));bg.alpha_composite(ImageOps.mirror(im).crop((115,135,335,292)),(230,18));displays.append(bg.convert('RGB'))
   dest=REPORT/unit/f'g{g:02}-both-native.gif';dest.parent.mkdir(parents=True,exist_ok=True)
   displays[0].save(dest,save_all=True,append_images=displays[1:],duration=160,loop=0,disposal=2)
 board=Image.new('RGBA',(1320,((len(tiles)+5)//6)*h),(32,32,32,255))
 for i,im in enumerate(tiles):board.paste(im,((i%6)*w,(i//6)*h))
 png(REPORT/unit/'all-actions-native1x.png',board)
 put(REPORT/unit/'compiler-proof-v1.json',{'status':'authored configuration','unit':unit,'actual_shared_compiler_runs':2,'two_runs_byte_exact':True,'resource_count':6,'physical_output_count':len(runs[0]),'outputs':runs[0],'recipes':{rel(p):sha(p) for p in recipes.glob('*.json')},'group_counts':{g:len(v) for g,v in groups.items()},'receipts':receipts,'selected':False,'runtime_verified':False,'visual_approval_granted':False})
 return {'unit':unit,'recipe_directory':rel(recipes),'compiled_outputs':len(runs[0]),'groups':{g:len(v) for g,v in groups.items()}}
def runner(unit):
 old=SOURCE/'inputs/historical-2d-recipes/ruinRunner-battle.json'
 battle=json.loads(old.read_text());src=PROJECT/'assets/source/creatures/painted-v2'/unit
 if unit=='ruinRunner':
  walk=[rel(PROJECT/f['source']).replace('/native/','/') for f in battle['groups'][0]['frames']]
 else:
  for row in battle['groups']:
   for frame in row['frames']:
    name=Path(frame['source']).name
    raw=SOURCE/unit/(name.removesuffix('.png')+'-raw.png')
    if raw.exists():
     im=Image.open(raw).convert('RGBA');assert im.size in [(1330,1182),(1331,1182)]
     out=fixed(im,CANVAS,ROOT,(640,1130),.095);dest=SOURCE/unit/'native'/name;png(dest,out);frame.update(descriptor(dest),sha256=sha(dest))
    else:
     dest=src/'native'/name
     # Reversed frontal boundary reuses the actually mirrored genuine turn image.
     if not dest.exists() and name=='turn-front-v1-left.png':
      target=SOURCE/unit/'native/turn-front-v1.png';out=Image.new('RGBA',CANVAS);out.paste(ImageOps.mirror(Image.open(target)),(-13,0));dest=SOURCE/unit/'native'/name;png(dest,out)
     frame.update(descriptor(dest),sha256=sha(dest))
  walk=[rel(src/(Path(f['source']).name)) for f in battle['groups'][0]['frames']]
  battle['output_path']=battle['output_path'].replace('/ruinRunner/','/'+unit+'/')
 standing=src/'grounded-standing-v1.png'
 attack=(SOURCE/unit/'attack-front-contact-v2-raw.png') if unit=='duneVeteran' else src/'attack-front-contact-v2.png'
 keys={'walk':walk,'portrait_crop':[440,30,1000,720]}
 keys['all_keys']=sorted({f['source'] for row in battle['groups'] for f in row['frames']})+sorted(rel(p) for p in (SOURCE/unit).glob('*-raw.png'))
 return finish(unit,battle,standing,attack,(640,1130),.095,keys,old)
def rockbear(unit):
 old=SOURCE/'inputs/historical-2d-recipes/rockbear-battle.json'
 battle=json.loads(old.read_text());directory=PROJECT/'assets/source/creatures/painted-v2'/unit
 stand='standing-v2';walk=['walk-contact-a-v1','walk-down-a-v1','walk-passing-a-v1','walk-contact-b-v1','walk-down-b-v1','walk-passing-b-v2' if unit=='rockbear' else 'walk-passing-b-v1']
 groups={0:walk,1:[stand,'fidget-look-v1',stand],2:[stand],3:[stand,'hit-recoil-v1',stand],4:[stand,'defend-brace-v1',stand],5:[stand,'death-buckle-v1','death-fall-v1','death-corpse-v1'],7:[stand,'turn-quarter-v1','turn-front-v1'],8:['turn-front-v1-left','turn-quarter-v1',stand],11:[stand,'attack-preparation-v1','attack-up-contact-v1','attack-recovery-v1',stand],12:[stand,'attack-preparation-v1','attack-front-contact-v1','attack-recovery-v1',stand],13:[stand,'attack-preparation-v1','attack-down-contact-v1','attack-recovery-v1',stand]}
 keys={'walk':[rel(directory/(k+'.png')) for k in walk],'portrait_crop':[1250,380,1970,1000],'logical_canvas':[2048,1152],'map_scale':.028 if unit=='elderRockbear' else .032}
 allkeys=set(k for seq in groups.values() for k in seq)
 for key in sorted(allkeys):
  if key.endswith('-left'):continue
  path=directory/(key+'.png');im=Image.open(path).convert('RGBA');out=resource_transform(im,CANVAS,ROOT,(1037,992),.075,keys)
  png(SOURCE/unit/'native'/(key+'.png'),out)
 front=Image.open(SOURCE/unit/'native/turn-front-v1.png');mirror=Image.new('RGBA',CANVAS);mirror.paste(ImageOps.mirror(front),(-13,0));png(SOURCE/unit/'native/turn-front-v1-left.png',mirror)
 battle['groups']=[{'group':g,'frames':[dict(descriptor(SOURCE/unit/'native'/(k+'.png')),sha256=sha(SOURCE/unit/'native'/(k+'.png'))) for k in seq]} for g,seq in groups.items()]
 battle['output_path']=battle['output_path'].replace('/rockbear/','/'+unit+'/')
 keys['all_keys']=sorted(rel(directory/(k+'.png')) for k in allkeys if not k.endswith('-left'))
 return finish(unit,battle,directory/'standing-v2.png',directory/'attack-front-contact-v1.png',(1037,992),.075,keys,old)
def sunforged(unit):
 directory=PROJECT/'assets/source/creatures/painted-v2'/unit
 names=['standing','walk-contact-a','walk-down-a','walk-pass-a','walk-contact-b','walk-down-b','walk-pass-b','fidget','hit','defend','death-kneel','death-fall','death-rest','turn-front','melee-prepare','melee-up','melee-front','melee-down']
 paths={}
 for name in names:
  path=directory/((('standing-candidate' if unit=='sunforgedColossus' else 'standing')+'-v'+('1' if unit=='sunforgedColossus' else '2')+'.png') if name=='standing' else name+'-v1.png')
  if name=='turn-front':path=SOURCE/'sunforgedColossus-turn-front-v1-raw.png' if unit=='sunforgedColossus' else SOURCE/unit/'turn-front-v1-raw.png'
  if unit=='awakenedSunforged' and name in ('melee-prepare','melee-up','melee-down'):path=SOURCE/unit/(name+'-v2-raw.png')
  if unit=='awakenedSunforged' and name=='melee-front':path=SOURCE/unit/'melee-front-v1-raw.png'
  im=Image.open(path).convert('RGBA');assert im.size==(1536,1024),(path,im.size)
  clean=im.copy();clean.putalpha(im.getchannel('A').point(lambda a:0 if a<8 else a))
  out=fixed(clean,CANVAS,ROOT,(590,833),.11);dest=SOURCE/unit/'native'/(name+'.png');png(dest,out);paths[name]=path
 front=Image.open(SOURCE/unit/'native/turn-front.png');reverse=Image.new('RGBA',CANVAS);reverse.paste(ImageOps.mirror(front),(-13,0));png(SOURCE/unit/'native/turn-front-left.png',reverse)
 stand='standing';walk=['walk-contact-a','walk-down-a','walk-pass-a','walk-contact-b','walk-down-b','walk-pass-b']
 groups={0:walk,1:[stand,'fidget',stand],2:[stand],3:[stand,'hit',stand],4:[stand,'defend',stand],5:[stand,'death-kneel','death-fall','death-rest'],7:[stand,'turn-front'],8:['turn-front-left',stand]}
 for g,direction in ((11,'up'),(12,'front'),(13,'down')):groups[g]=[stand,'melee-prepare','melee-'+direction,'melee-'+direction,'melee-prepare',stand]
 battle={'status':'authored configuration','production_status':'painted-master-complete-unapproved','unit':unit,'visual_approval_granted':False,
  'credits':{'author':'Project-directed OpenAI built-in imagegen paintings; technical2D assembly','license':None,'redistribution':'unresolved; release prohibited'},
  'generation':{'image_generation_used':True,'provider':'OpenAI built-in imagegen; independently painted2D action masters','model':'not exposed by built-in tool','painted_master':rel(paths['standing']),'painted_master_sha256':sha(paths['standing']),'provenance':rel(SOURCE/unit/'conversion-v1.json'),'prompt':'Portable historical action requests plus new playable-completion exact-action prompts; no3D or render inputs.'},
  'recipe_type':'vcmi_animation','canvas':list(CANVAS),'pivot':{'x':218,'y':266},'generateShadow':0,'generateOverlay':1,
  'output_path':'Content/Sprites/runeterra/shurima/creatures/'+unit+'/battle.json',
  'groups':[{'group':g,'frames':[dict(descriptor(SOURCE/unit/'native'/(k+'.png')),sha256=sha(SOURCE/unit/'native'/(k+'.png'))) for k in seq]} for g,seq in groups.items()]}
 keys={'walk':[rel(paths[k]) for k in walk],'portrait_crop':[350,150,1250,850],'all_keys':[rel(p) for p in paths.values()],'source_alpha_processing':'Uniform alpha<8 ->0 in battle only, all body alpha retained'}
 return finish(unit,battle,paths['standing'],paths['melee-front'],(590,833),.11,keys)
def sun_archer():
 unit='sunArcher';old=SOURCE/'inputs/historical-2d-recipes/shurimanArcher-battle.json'
 battle=json.loads(old.read_text());directory=PROJECT/'assets/source/creatures/painted-v3/sunArcher'
 plan=json.loads((directory/'pose-plan-v1.json').read_text())['actions']+[{'group':2,'frame':0,'key':'g02-f000-v2'}]
 # Explicit projected ground-plane annotations. They do not measure the lowest opaque toe.
 registration={'1254x1254':[625,1190],'1330x1182':[663,1130],'1331x1182':[663,1130],
  '1287x1222':[641.5,1170],'1328x1184':[662,1130],'1330x1183':[663,1130],
  '1321x1191':[658.5,1135],'1536x1024':[766,976],'1329x1183':[662.5,1130],
  '1205x1305':[600.5,1240],'1312x1199':[654,1145],'1315x1197':[655.5,1145]}
 keys={'walk':[],'portrait_crop':[300,20,1100,870],'canvas_registration':registration,'all_keys':[],
  'registration_review':'Authored projected ground-plane annotations; preserve genuine stride and review pelvis/bow stability, not alpha-bounds fitting.'}
 groups={};selected={}
 for row in sorted(plan,key=lambda r:(r['group'],r['frame'])):
  g,i=row['group'],row['frame'];key=row['key']
  if (g,i) in ((0,3),(7,0)) or g==14:key=key.removesuffix('-v1')+'-v2'
  path=directory/'masters'/(key+'.png');im=Image.open(path).convert('RGBA')
  clean=im.copy();clean.putalpha(im.getchannel('A').point(lambda a:0 if a<16 else a))
  out=resource_transform(clean,CANVAS,(196,267),(663,1130),76/1131,keys)
  dest=SOURCE/unit/'native'/f'g{g:02}-f{i:03}.png';png(dest,out)
  groups.setdefault(g,[]).append(dict(descriptor(dest),sha256=sha(dest)));selected[g,i]=path;keys['all_keys'].append(rel(path))
  if g==0:keys['walk'].append(rel(path))
 battle.update(unit=unit,canvas=[450,400],pivot={'x':196,'y':267},output_path='Content/Sprites/runeterra/shurima/creatures/sunArcher/battle.json',groups=[{'group':g,'frames':v} for g,v in groups.items()])
 return finish(unit,battle,selected[2,0],selected[15,3],(663,1130),76/1131,keys,old)
if __name__=='__main__':
 print(json.dumps([(rockbear(u) if u in ('rockbear','elderRockbear') else sunforged(u) if u in ('sunforgedColossus','awakenedSunforged') else sun_archer() if u=='sunArcher' else runner(u)) for u in sys.argv[1:]]))
