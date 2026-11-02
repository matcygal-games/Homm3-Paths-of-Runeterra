"""Purely technical conversion of independently painted Seer poses.
Run from workspace root with project Python. Writes owned new sources and report only.
"""
from pathlib import Path
import hashlib,json,sys
from PIL import Image,ImageOps,ImageDraw,ImageFilter
WORKSPACE=Path(__file__).resolve().parents[6]
PROJECT=WORKSPACE/'runeterra-freljord'
REPORT=PROJECT/'build/reports/painted-seers-20261024-v1'
UNITS=('starlitSeer','winterVeilSeer')
GROUPS={
0:[f'walk-{i}' for i in range(6)],1:['fidget','idle-breath'],
2:['standing','idle-breath'],3:['hit','standing'],4:['brace','standing'],
5:['death-recoil','death-fall','death-rest'],7:['turn-front','standing'],8:['turn-back','standing'],
11:['melee-prep','melee-up','standing'],12:['melee-prep','melee-front','standing'],13:['melee-prep','melee-down','standing'],
14:['standing','shot-prep1','shot-prep2','shot-aim-up','shot-release-up','shot-recover','standing'],
15:['standing','shot-prep1','shot-prep2','shot-aim-front','shot-release-front','shot-recover','standing'],
16:['standing','shot-prep1','shot-prep2','shot-aim-down','shot-release-down','shot-recover','standing'],
30:['cast-prep','cast-up','standing'],31:['cast-prep','cast-front','standing'],32:['cast-prep','cast-down','standing']}
CATEGORIES={'locomotion':[f'walk-{i}' for i in range(6)],
'idle-impact':['standing','idle-breath','fidget','hit','brace','turn-front','turn-back'],
'death-melee':['death-recoil','death-fall','death-rest','melee-prep','melee-up','melee-front','melee-down'],
'shot-preparation':['shot-prep1','shot-prep2','shot-aim-up','shot-aim-front','shot-aim-down'],
'shot-release-cast':['shot-release-up','shot-release-front','shot-release-down','shot-recover','cast-prep','cast-up','cast-front','cast-down']}
BATTLE_EXTENT=113
SOURCE_ANCHOR=(850,1198)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def dump(path,value):
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def desc(path):
 with Image.open(path) as im:size=list(im.size)
 return dict(source=path.relative_to(PROJECT).as_posix(),source_sha256=sha(path),source_canvas=size)
def source_for(unit,name):
 base=PROJECT/f'assets/source/creatures/painted-20261024/{unit}/masters'
 gait=base.parent/'gait-selection-v1.json'
 if name.startswith('walk-') and gait.exists():
  selections={p['key']:p['master'] for p in json.loads(gait.read_text())['phases']}
  return base/selections[name]
 separated=base.parent/'release-split-v1'/f'{name}-body.png'
 if separated.exists():return separated
 return base/('standing-v2.png' if name=='standing' else name+'.png')
def conversion(path,size,root,extent,registration=None):
 im=Image.open(path).convert('RGBA')
 # Low-alpha codec residue is removed only during technical conversion; masters remain exact.
 im.putalpha(im.getchannel('A').point(lambda v:0 if v<16 else v))
 scale=extent/1254
 mini=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS)
 anchor=(registration or {}).get('source_anchor',SOURCE_ANCHOR)
 native_anchor=(registration or {}).get('native_anchor',root)
 offset=(round(native_anchor[0]-anchor[0]*scale),round(native_anchor[1]-anchor[1]*scale))
 body=Image.new('RGBA',size)
 body.alpha_composite(mini,offset)
 return body,dict(source_canvas=list(im.size),reference_canvas_extent=extent,scale=scale,
     source_anatomical_anchor=list(anchor),native_anchor=list(native_anchor),translation=list(offset),
     opaque_bbox_fit=False,alpha_residue_cutoff=16,registration=registration)
def shadow(body,ground):
 alpha=body.getchannel('A').point(lambda v:round(v*.30))
 shear,flatten=-.35,.22
 inverse=(1,-shear/flatten,shear*ground/flatten,0,1/flatten,ground*(1-1/flatten))
 mask=alpha.transform(body.size,Image.Transform.AFFINE,inverse,Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(.4))
 sh=Image.new('RGBA',body.size);sh.putalpha(mask)
 out=sh.copy();out.alpha_composite(body)
 return out,sh
def native_pose(unit,key):
 return PROJECT/f'assets/source/creatures/painted-20261024/{unit}/native-v1/{key}.png'
def make_sheets(available=False):
 REPORT.mkdir(parents=True,exist_ok=True)
 for category,names in CATEGORIES.items():
  sheet=Image.new('RGB',(880,len(names)*210),(78,77,70));d=ImageDraw.Draw(sheet)
  for row,name in enumerate(names):
   for u,unit in enumerate(UNITS):
    path=native_pose(unit,name)
    if not path.exists():continue
    im=Image.open(path)
    for reverse in (0,1):
     drawn=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if reverse else im
     crop=(115,120,335,310) if not reverse else (115,120,335,310)
     tile=drawn.crop(crop);x=(u*2+reverse)*220;y=row*210+20
     sheet.paste(tile,(x,y),tile)
     d.text((x+3,row*210+3),unit+' '+name+(' L' if reverse else ' R'),fill='white')
  dest=REPORT/'private'/f'native1x-{category}.png'
  dest.parent.mkdir(exist_ok=True);sheet.save(dest)
def main(partial=False):
 sys.path.insert(0,str(WORKSPACE/'scripts'))
 from faction_art_compile import create_compiler
 from freljord_asset_manifest import required_groups
 compiler=create_compiler('freljord')
 allnames=sorted({n for names in GROUPS.values() for n in names})
 receipts=[];missing={}
 for unit in UNITS:
  folder=PROJECT/f'assets/source/creatures/painted-20261024/{unit}'
  missing[unit]=[n for n in allnames if not source_for(unit,n).exists()]
  if missing[unit] and not partial:raise ValueError(missing)
  registration_path=folder/'anatomical-registration-v1.json'
  registrations=json.loads(registration_path.read_text())['poses'] if registration_path.exists() else {}
  frames=folder/'native-v1';frames.mkdir(exist_ok=True)
  measurements=[]
  for name in allnames:
   master=source_for(unit,name)
   if not master.exists():continue
   registration=registrations.get(name)
   if name=='walk-5' and master.name!='walk-5.png':registration=None
   if name=='walk-2':registration=dict(source_anchor=[850,1178],native_anchor=[218,266],basis='Manually inspected supporting far toe in raised-near-knee v3source; one scale, translation only.')
   body,transform=conversion(master,(450,400),(218,266),BATTLE_EXTENT,registration)
   bodypath=frames/'body-layers'/f'{name}.png';bodypath.parent.mkdir(exist_ok=True);body.save(bodypath)
   final,sh=shadow(body,266)
   shpath=frames/'shadow-layers'/f'{name}.png';shpath.parent.mkdir(exist_ok=True);sh.save(shpath)
   output=frames/f'{name}.png';final.save(output)
   measurements.append(dict(pose=name,master=desc(master),native=desc(output),body=desc(bodypath),shadow=desc(shpath),
      transform=transform,opaque_bounds=body.getchannel('A').point(lambda v:255 if v>=128 else 0).getbbox()))
  dump(folder/'fixed-conversion-v1.json',dict(status='authored configuration',battle=measurements,
     scale_basis='One whole-canvas113/1254 scale for both variants and every battle pose; selected against original ArchMage native height.',
     registration_basis='Standing right boot toe at source850,1198 maps to native218,266; manual anatomical translations recorded individually where necessary.',
     shadow=dict(method='Alpha-derived technical ground matte from each original painted pose, body saved separately.',
                 shear_x=-.35,scale_y=.22,ground_y=266,alpha_multiplier=.30,blur_native_pixels=.4),
     mirror_basis='Actual CreatureAnimation consumer mirrors entire450pixel frame.'))
  if partial:continue
  master=source_for(unit,'standing');resources=folder/'resources-v2';resources.mkdir(exist_ok=True)
  adventure_registration=dict(source_anchor=[650,1198],native_anchor=[48,60],basis='Manual standing body ground-root between boots;64x64 originalAVWMAGE/AVWMONK and bottom-right tile consumer inspected.')
  mapim,map_transform=conversion(master,(64,64),(48,60),50,adventure_registration)
  mapim.save(resources/'map-body.png');mapim,_=shadow(mapim,60);mapim.save(resources/'map.png')
  attack,attack_transform=conversion(source_for(unit,'shot-prep2'),(64,64),(48,60),50,adventure_registration)
  attack.save(resources/'attackRight-body.png')
  attack.transform((64,64),Image.Transform.AFFINE,(-1,0,97,0,1,0),Image.Resampling.NEAREST).save(resources/'attackLeft-body.png')
  attack,_=shadow(attack,60);attack.save(resources/'attackRight.png')
  attack.transform((64,64),Image.Transform.AFFINE,(-1,0,97,0,1,0),Image.Resampling.NEAREST).save(resources/'attackLeft.png')
  original=Image.open(master)
  original.putalpha(original.getchannel('A').point(lambda v:0 if v<16 else v))
  crop=(350,120,980,820)
  cut=ImageOps.contain(original.crop(crop),(58,64),Image.Resampling.LANCZOS)
  large=Image.new('RGBA',(58,64));large.alpha_composite(cut,((58-cut.width)//2,(64-cut.height)//2));large.save(resources/'large.png')
  headcrop=(655,180,950,475) if unit=='starlitSeer' else (660,225,955,520)
  original.crop(headcrop).resize((32,32),Image.Resampling.LANCZOS).save(resources/'small.png')
  prompts=[]
  for path in sorted((folder/'prompts').glob('*.json')):
   request=json.loads(path.read_text(encoding='utf-8'))
   prompts.append(dict(pose=path.stem,prompt=request['prompt'],provider=request['provider'],model=request['model'],
       private_reference_identifiers=['LoR01FR032','core:archMage','core:monk']))
  dump(folder/'generation-provenance-v1.json',dict(status='authored configuration',provider='OpenAI built-in imagegen',
      model='not exposed by built-in tool',method='Independent painted2D action masters; uniform fixed-canvas technical conversion.',
      masters=[dict(pose=n,**desc(source_for(unit,n))) for n in allnames],prompts=prompts,
      preserved_raw_painted_masters=[desc(p) for p in sorted((folder/'masters').glob('*.png'))],
      technical_release_separation_receipt='release-split-v1/technical-alpha-split-v1.json',
      source_identity='StarlitSeer official LoR01FR032; species unspecified; cosmetic owl; physical ritual shooting is an authored adaptation.',
      private_reference_images_redistributable=False,visual_approval_granted=False))
  generation=dict(image_generation_used=True,provider='OpenAI built-in imagegen',model='not exposed by built-in tool',
      prompt='See portable generation-provenance-v1.json; one genuine painted action per built-in imagegen call.',
      painted_master=master.relative_to(PROJECT).as_posix(),painted_master_sha256=sha(master),
      method='Independently painted2D pose masters, uniform full-canvas conversion and recorded anatomical registration.')
  common=dict(unit=unit,status='authored configuration',production_status='painted-master-complete-unapproved',
      generation=generation,visual_approval_granted=False,credits=dict(author='Project-directed OpenAI built-in imagegen and technical2Dassembly',
      license=None,redistribution='unresolved; release prohibited'))
  prefix=f'Content/Sprites/runeterra/freljord/creatures/{unit}/'
  payload=REPORT/f'recipe-payload/creatures/painted-20261024/{unit}'
  battle=dict(common,recipe_type='vcmi_animation',canvas=[450,400],pivot=dict(x=218,y=266),generateShadow=0,generateOverlay=1,
     output_path=prefix+'battle.json',groups=[dict(group=g,frames=[dict(desc(native_pose(unit,n)),frame=i) for i,n in enumerate(seq)]) for g,seq in GROUPS.items()])
  dump(payload/'battle.json',battle)
  content=json.loads((PROJECT/'content/creatures.json').read_text(encoding='utf-8'))
  contract_unit=unit if unit in content else {'starlitSeer':'spiritWalker','winterVeilSeer':'primalShaman'}[unit]
  contract_content=dict(content)
  contract_content[unit]=content[contract_unit]
  required=required_groups(prefix+'battle.json',contract_content)
  actual={str(g):len(seq) for g,seq in GROUPS.items()}
  if any(actual.get(g,0)<count for g,count in required.items()):raise ValueError((required,actual))
  dump(REPORT/f'{unit}-native-action-contract-v1.json',dict(required_groups=required,actual_groups=actual,
      current_content_contract_unit=contract_unit,coordinator_new_content_published=unit in content,
      report_only_contract_alias=unit!=contract_unit,
      shots=dict(groups=[14,15,16],release_zero_based=4,source='BattleAnimationClasses.cpp:ShootingAnimation::getAttackClimaxFrame'),
      cast=dict(groups=[30,31,32],peak_zero_based=1,source='BattleAnimationClasses.cpp:CastAnimation, maxFrames/2'),
      contract_weakened=False,visual_approval_granted=False,runtime_verified=False))
  mapping=dict(common,recipe_type='vcmi_animation',canvas=[64,64],pivot=dict(x=48,y=60),generateShadow=0,generateOverlay=1,
      output_path=prefix+'map.json',groups=[dict(group=0,frames=[dict(desc(resources/'map.png'),frame=0)])])
  dump(payload/'map.json',mapping)
  for name in ('large','small','attackLeft','attackRight'):
   size=[58,64] if name=='large' else [32,32] if name=='small' else [64,64]
   dump(payload/f'{name}.json',dict(common,recipe_type='raster',size=size,fit='exact',output_path=prefix+name+'.png',**desc(resources/f'{name}.png')))
  for recipe in sorted(payload.glob('*.json')):
   first,receipt=compiler.plan(PROJECT,recipe);second,receipt2=compiler.plan(PROJECT,recipe)
   if first!=second or receipt!=receipt2:raise AssertionError(f'Nondeterministic {recipe}')
   for name,data in first.items():
    destination=REPORT/'compiled'/name;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(data)
   receipts.append(dict(recipe=recipe.relative_to(PROJECT).as_posix(),two_plan_runs_identical=True,receipt=receipt,
       outputs={n:hashlib.sha256(b).hexdigest() for n,b in sorted(first.items())}))
  dump(folder/'resource-conversion-v1.json',dict(map=map_transform,adventure_attack=attack_transform,
        large_portrait_crop=list(crop),small_portrait_crop=list(headcrop),adventure_mirror_axis_x=48,
        adventure_discrete_reflection='x_new=96-x_old; Pillow center-sampled inverse affine uses97 to preserve pixel48 exactly.',
        adventure_attack_source='Genuine compact physical ritual-shot preparation2 with held splinter, not idle or claim of release; original map combat indicator is a single static actionimage.',
        original_adventure_dimensions=[64,64],native_consumer='MapRendererObjects::getImageToRender/renderImage replaces entiremapimage; bottom-right32tilecrop.'))
 make_sheets(partial)
 dump(REPORT/('partial-conversion-checkpoint-v1.json' if partial else 'strict-repeat-compile-v1.json'),
      dict(status='authored configuration',missing=missing,recipes=receipts,active_selection_changed=False,
           stage_changed=False,visual_approval_granted=False,runtime_verified=False))
 print(json.dumps(dict(missing=missing,compiled_recipes=len(receipts),output_count=sum(len(r['outputs']) for r in receipts))))
if __name__=='__main__':main('--partial' in sys.argv)

