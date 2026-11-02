"""Technical-only fixedpixel conversion and report-only strict compiler proof."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter,ImageOps
import hashlib,json,sys
PROJECT=next(p for p in Path(__file__).resolve().parents if p.name=='runeterra-freljord')
WORKSPACE=PROJECT.parent
SOURCE=PROJECT/'assets/source/creatures/painted-20261024/draklornInquisitor'
REPORT=PROJECT/'build/reports/painted-draklorn-inquisitor-actions-20261024-v1'
UNIT='draklornInquisitor'
GROUPS={
0:['walk-contact-a-v1','walk-down-a-v1','walk-pass-a-v1','walk-contact-b-v1','walk-down-b-v1','walk-pass-b-v1'],
1:['standing']*2+['fidget-v1']*3+['fidget-settle-v1']*2+['standing']*2,
2:['standing'],3:['hit-v1','standing'],4:['defend-v1','standing'],
5:['death-kneel-v1']*2+['death-fall-v3']*2+['death-rest-v4']*2,
7:['turn-front-v1','standing'],8:['turn-back-v1','standing'],
11:['standing','melee-ready-v1','melee-prepare-v1','melee-up-v1','melee-recover-v1','standing'],
12:['standing','melee-ready-v1','melee-prepare-v1','melee-front-v1','melee-recover-v1','standing'],
13:['standing','melee-ready-v1','melee-prepare-v1','melee-down-v1','melee-recover-v1','standing']}
CATEGORIES={'gait':GROUPS[0],'idle-guard-turn':['standing','fidget-v1','fidget-settle-v1','hit-v1','defend-v1','turn-front-v1','turn-back-v1'],
'death':['death-kneel-v1','death-fall-v3','death-rest-v4'],
'melee':['melee-ready-v1','melee-prepare-v1','melee-up-v1','melee-front-v1','melee-down-v1','melee-recover-v1']}
# Manual source-ground contacts from actual boots/knee/corpse, never scale fitting.
GROUND={'death-kneel-v1':936,'death-fall-v1':860,'death-rest-v1':900,
'death-fall-v3':810,'death-rest-v4':750,
'melee-front-v1':950,'melee-down-v1':930,'walk-contact-a-v1':992,'walk-contact-b-v1':976,
'fidget-v1':980,'fidget-settle-v1':990,'melee-ready-v1':970,'melee-prepare-v1':970,
'melee-recover-v1':990,'walk-down-a-v1':990,'walk-down-b-v1':970,
'walk-pass-a-v1':970,'walk-pass-b-v1':970}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def dump(path,value):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def master(key):return SOURCE/'standing-v2.png' if key=='standing' else SOURCE/'actions-v1'/f'{key}.png'
def descriptor(path):
 return dict(source=path.relative_to(PROJECT).as_posix(),source_sha256=sha(path),source_canvas=list(Image.open(path).size))
def converted(path,canvas=(450,400),root=(193,266),scale=.100,source_anchor=(780,1000)):
 im=Image.open(path).convert('RGBA')
 im.putalpha(im.getchannel('A').point(lambda v:0 if v<16 else v))
 offset=(root[0]-source_anchor[0]*scale,root[1]-source_anchor[1]*scale)
 inverse=(1/(scale*4),0,source_anchor[0]-root[0]/scale,0,1/(scale*4),source_anchor[1]-root[1]/scale)
 out=im.transform((canvas[0]*4,canvas[1]*4),Image.Transform.AFFINE,inverse,
      resample=Image.Resampling.BICUBIC,fillcolor=(0,0,0,0)).resize(canvas,Image.Resampling.LANCZOS)
 return out,dict(source_canvas=list(im.size),fixed_pixel_scale=scale,source_anatomical_anchor=list(source_anchor),
     native_root=list(root),translation=list(offset),opaque_bbox_fitting=False,alpha_residue_cutoff=16,
     uniform_inverse_affine_4x=list(inverse),samples_per_native_pixel=4)
def shadowed(body,ground):
 alpha=body.getchannel('A').point(lambda v:round(v*.30));shear,flatten=-.35,.22
 matrix=(1,-shear/flatten,shear*ground/flatten,0,1/flatten,ground*(1-1/flatten))
 alpha=alpha.transform(body.size,Image.Transform.AFFINE,matrix,Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(.4))
 shadow=Image.new('RGBA',body.size);shadow.putalpha(alpha);out=shadow.copy();out.alpha_composite(body)
 return out,shadow
def native(key):return SOURCE/'technical-v1/native'/f'{key}.png'
def make_sheets():
 for category,keys in CATEGORIES.items():
  board=Image.new('RGB',(500,len(keys)*210),(67,66,61));draw=ImageDraw.Draw(board)
  for row,key in enumerate(keys):
   image=Image.open(native(key))
   for rev in (0,1):
    im=image.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if rev else image
    tile=im.crop((80,120,330,310));x=rev*250;y=row*210+20
    board.paste(tile,(x,y),tile);draw.text((x+3,row*210+3),key+(' L' if rev else ' R'),fill='white')
  board.save(REPORT/'private'/f'native1x-{category}.png')
def main(partial=False):
 sys.path.insert(0,str(WORKSPACE/'scripts'))
 from faction_art_compile import create_compiler
 from freljord_asset_manifest import required_groups
 compiler=create_compiler('freljord')
 keys=sorted({key for sequence in GROUPS.values() for key in sequence})
 for key in keys:
  if not master(key).is_file():raise ValueError('Missing genuine painted pose '+key)
 records=[]
 for key in keys:
  path=master(key);ground=GROUND.get(key,1000)
  body,transform=converted(path,source_anchor=(780,ground))
  dest=SOURCE/'technical-v1/native';(dest/'body').mkdir(parents=True,exist_ok=True);(dest/'shadow').mkdir(exist_ok=True)
  body.save(dest/'body'/f'{key}.png')
  image,shadow=shadowed(body,266);image.save(native(key));shadow.save(dest/'shadow'/f'{key}.png')
  records.append(dict(pose=key,master=descriptor(path),native=descriptor(native(key)),body=descriptor(dest/'body'/f'{key}.png'),
    shadow=descriptor(dest/'shadow'/f'{key}.png'),conversion=transform,
    measured_opaque_bounds=body.getchannel('A').point(lambda v:255 if v>=128 else 0).getbbox()))
 dump(SOURCE/'technical-v1/fixed-conversion-v1.json',dict(status='authored configuration',poses=records,
   method='Uniform .100 pixel scale and manual anatomical contact translation; source camera and body dimensions retained.',
   source_standing_pin=descriptor(master('standing')),shadow=dict(method='Technical alpha-derived ground matte, bodypixels saved separately.',
   shear_x=-.35,scale_y=.22,ground_y=266,alpha_multiplier=.30,blur_native_pixels=.4),
   battle_facing='ActualCreatureAnimation full450pixel mirror x_new=449-x_old.',visual_approval_granted=False))
 make_sheets()
 if partial:return
 resources=SOURCE/'technical-v1/resources-v2';resources.mkdir(exist_ok=True)
 # One adventure scale across standing and the genuine compact preparation indicator.
 adventure_scale=.046
 for name,key in [('map','adventure-standing-v1'),('attackRight','adventure-guard-v1')]:
  im,transform=converted(master(key),(64,64),(48,60),adventure_scale,(780,1000))
  im.save(resources/(name+'-body.png'));im,_=shadowed(im,60);im.save(resources/(name+'.png'))
  dump(resources/(name+'-conversion.json'),dict(pose=key,**transform))
 attack=Image.open(resources/'attackRight.png')
 attack.transform((64,64),Image.Transform.AFFINE,(-1,0,97,0,1,0),Image.Resampling.NEAREST).save(resources/'attackLeft.png')
 body=Image.open(resources/'attackRight-body.png')
 body.transform((64,64),Image.Transform.AFFINE,(-1,0,97,0,1,0),Image.Resampling.NEAREST).save(resources/'attackLeft-body.png')
 im=Image.open(master('standing')).convert('RGBA');im.putalpha(im.getchannel('A').point(lambda v:0 if v<16 else v))
 crops={'large':(490,180,1030,800),'small':(670,200,960,490)}
 for name,box in crops.items():
  size=(58,64) if name=='large' else (32,32)
  crop=ImageOps.contain(im.crop(box),size,Image.Resampling.LANCZOS)
  target=Image.new('RGBA',size);target.alpha_composite(crop,((size[0]-crop.width)//2,(size[1]-crop.height)//2));target.save(resources/(name+'.png'))
 dump(SOURCE/'technical-v1/generation-provenance-v1.json',dict(status='authored configuration',
  provider='OpenAI built-in imagegen',model='not exposed by built-in tool',
  method='One independently painted2D action per tool call; fixedcamera technical conversion and anatomical registration.',
  selected_master=descriptor(master('standing')),painted_actions=[dict(pose=k,**descriptor(master(k))) for k in keys],
  adventure_masters=[descriptor(master(k)) for k in ('adventure-standing-v1','adventure-guard-v1')],
  all_preserved_action_masters=[descriptor(p) for p in sorted((SOURCE/'actions-v1').glob('*.png'))],
  prompts=[dict(pose=p.stem,**json.loads(p.read_text())) for p in sorted((SOURCE/'prompts-v1').glob('*.json'))],
  private_reference_identifiers=['LoR04FR006','core:swordsman','core:pikeman'],reference_images_redistributable=False,
  selected_standing_generation_request='requests/standing-v2.json',visual_approval_granted=False))
 generation=dict(image_generation_used=True,provider='OpenAI built-in imagegen',model='not exposed by built-in tool',
  prompt='See technical-v1/generation-provenance-v1.json and exact selectedstanding request; one genuinelypainted action per call.',
  painted_master=master('standing').relative_to(PROJECT).as_posix(),painted_master_sha256=sha(master('standing')),
  method='Painted2D fullbody action masters; commonpixel scale and recorded anatomical registration.')
 common=dict(unit=UNIT,status='authored configuration',production_status='painted-master-complete-unapproved',
   generation=generation,visual_approval_granted=False,
   credits=dict(author='Project-directed OpenAI built-in imagegen and technical2Dassembly',license=None,redistribution='unresolved; release prohibited'))
 prefix=f'Content/Sprites/runeterra/freljord/creatures/{UNIT}/';payload=REPORT/'recipe-payload/creatures/painted-20261024'/UNIT
 battle=dict(common,recipe_type='vcmi_animation',canvas=[450,400],pivot=dict(x=193,y=266),generateShadow=0,generateOverlay=1,
  output_path=prefix+'battle.json',groups=[dict(group=g,frames=[dict(descriptor(native(key)),frame=i) for i,key in enumerate(sequence)]) for g,sequence in GROUPS.items()])
 dump(payload/'battle.json',battle)
 content=json.loads((PROJECT/'content/creatures.json').read_text(encoding='utf-8'))
 required=required_groups(prefix+'battle.json',content);actual={str(g):len(seq) for g,seq in GROUPS.items()}
 if any(actual.get(g,0)<count for g,count in required.items()):raise AssertionError((required,actual))
 if len(GROUPS[2])!=1 or len(GROUPS[1])!=9:raise AssertionError('Quietidle/fidget timing broken')
 for g,key in [(11,'melee-up-v1'),(12,'melee-front-v1'),(13,'melee-down-v1')]:
  if GROUPS[g][3]!=key or len(GROUPS[g])!=6:raise AssertionError('Meleecontact not at native midpoint')
 dump(REPORT/'native-action-contract-v1.json',dict(status='authored configuration',required_groups=required,actual_groups=actual,
  quiet_holding_single_source=True,fidget_held_ticks=9,fidget_native_fps=10,
  melee_contact_zero_based=3,melee_frames=6,melee_hit_consumer='BattleAnimationClasses.cpp:currentFrame*2>=totalFrames',
  idle_consumer='CreatureAnimation.cpp:HOLDING returns idleAnimationTime asFPS, MOUSEON returns base10FPS.',
  contract_weakened=False,runtime_verified=False))
 map_generation=dict(generation,painted_master=master('adventure-standing-v1').relative_to(PROJECT).as_posix(),painted_master_sha256=sha(master('adventure-standing-v1')))
 dump(payload/'map.json',dict(common,generation=map_generation,recipe_type='vcmi_animation',canvas=[64,64],pivot=dict(x=48,y=60),generateShadow=0,generateOverlay=1,
  output_path=prefix+'map.json',groups=[dict(group=0,frames=[dict(descriptor(resources/'map.png'),frame=0)])]))
 for name,size in [('large',[58,64]),('small',[32,32]),('attackLeft',[64,64]),('attackRight',[64,64])]:
  resource_generation=dict(generation,painted_master=master('adventure-guard-v1').relative_to(PROJECT).as_posix(),painted_master_sha256=sha(master('adventure-guard-v1'))) if name.startswith('attack') else generation
  dump(payload/(name+'.json'),dict(common,generation=resource_generation,recipe_type='raster',size=size,fit='exact',output_path=prefix+name+'.png',**descriptor(resources/(name+'.png'))))
 receipts=[]
 for recipe in sorted(payload.glob('*.json')):
  outputs,receipt=compiler.plan(PROJECT,recipe);outputs2,receipt2=compiler.plan(PROJECT,recipe)
  if outputs!=outputs2 or receipt!=receipt2:raise AssertionError('Nondeterministic shared compiler '+str(recipe))
  for name,data in outputs.items():
   target=REPORT/'compiled'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
  receipts.append(dict(recipe=recipe.relative_to(PROJECT).as_posix(),two_plan_runs_identical=True,receipt=receipt,outputs={n:hashlib.sha256(b).hexdigest() for n,b in outputs.items()}))
 dump(REPORT/'strict-repeat-compile-v1.json',dict(status='authored configuration',recipes=receipts,recipe_count=len(receipts),
    output_count=sum(len(x['outputs']) for x in receipts),stage_changed=False,visual_approval_granted=False))
 print(json.dumps(dict(recipes=len(receipts),outputs=sum(len(x['outputs']) for x in receipts),selected_pose_keys=len(keys))))
if __name__=='__main__':main('--partial' in sys.argv)

