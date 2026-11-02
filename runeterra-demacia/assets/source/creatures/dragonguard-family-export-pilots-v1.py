"""First measured own native walk/holding/thrust source candidates only."""
from pathlib import Path
import json
import sys
from PIL import Image,ImageDraw

PROJECT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(PROJECT/'scripts'))
from creature_family_motion_art import calibrate_generation,export_generation,proof,write
from creature_padding import crop_padding

# Human helmet top and planted sole; deliberately exclude a higher pole tip.
LANDMARKS={
 'dragonguard':{0:(94,490,245),2:(110,490,255),12:(178,558,319)},
 'veteranDragonguard':{0:(83,480,250),2:(92,451,250),12:(158,538,305)},
}
units=[]
for unit,groups in LANDMARKS.items():
 folder=PROJECT/'assets/source/creatures'/unit/'dragonguard-rig-v3';actions=[];recipe_groups=[];padding=[]
 for group,(top,ground,root) in groups.items():
  generation_path=folder/f'paint-action-g{group:02}-atlas-v{2 if group==12 else 1}-generation.json';generation=json.loads(generation_path.read_text())
  factor=1 if group==12 else generation['returned_cell'][0]/512
  camera=calibrate_generation(PROJECT,generation_path,reference_index=0,head_top_y=top*factor,ground_y=ground*factor,
   root_x=root*factor,target_height=80 if unit=='dragonguard' else 84,
   basis=f'Actually inspected first complete human pose: helmet/winged-helmet topY{top}, supporting front soleY{ground}, projected pelvisX{root}, on{768 if group==12 else 512}px coordinate review. Higher pole tip excluded from human camera height. One common atlas scale only, no per-pose size fitting or raw/painted pixel equality claim.')
  camera_path=folder/f'paint-action-g{group:02}-camera-v1.json';initial=export_generation(PROJECT,generation_path,camera_path);placements=[]
  if group==0:
   raw_bottoms=[]
   for i in range(6):
    with Image.open(folder/f'raw-native-review/g00/g00-f{i:03}.png') as im:raw_bottoms.append(im.getchannel('A').point(lambda a:255 if a>=8 else 0).getbbox()[3])
  for item in initial['frames']:
   target=267+raw_bottoms[item['index']]-raw_bottoms[0] if group==0 else 267
   placements.append({'index':item['index'],'native_translation':[0,target-item['alpha8_bbox'][3]],'reviewed':True,
    'basis':f'Actual observed supporting-sole native bottom{item["alpha8_bbox"][3]} corrected to{target} with whole-frame integer translation. Walk retains the genuine rig projected stride relative ground variation; holding/thrust use shared support. No resize or limb warp, and no generated geometry equivalence is assumed.',
    'evidence':[proof(PROJECT,generation_path),proof(PROJECT,PROJECT/item['output'])]})
  final=export_generation(PROJECT,generation_path,camera_path,version=2,placements=placements,placement_version=1)
  native_frames=[];gif=[];board=Image.new('RGB',(len(final['frames'])*220,350),'#303b35');draw=ImageDraw.Draw(board)
  draw.text((3,4),f'{unit} g{group:02} actual own painted PILOT; one camera/whole-frame placement; NOT accepted',fill='white')
  for i,item in enumerate(final['frames']):
   source=PROJECT/item['output'];target=folder/f'native-pilot-final-v1/g{group:02}/g{group:02}-f{i:03}.png'
   conversion=crop_padding(source,target,PROJECT);padding.append(conversion);native_frames.append({'source':conversion['output'],'sha256':conversion['sha256']})
   with Image.open(target) as image:
    crop=image.crop((100,150,320,290))
    for row,color in ((0,'#d6d6c6'),(1,'#283b31')):
     tile=Image.new('RGBA',crop.size,color);tile.alpha_composite(crop);board.paste(tile.convert('RGB'),(i*220,row*160+20))
     draw.line((i*220,row*160+137,(i+1)*220-1,row*160+137),fill='#718b71')
    frame=Image.new('RGBA',(240,160),'#c3c5b2');frame.alpha_composite(image.crop((90,145,330,305)));gif.append(frame.convert('RGB'))
  contact=folder/f'paint-action-g{group:02}-native-light-dark-review-v1.png';board.save(contact)
  gif[0].save(folder/f'paint-action-g{group:02}-native-motion-review-v1.gif',save_all=True,append_images=gif[1:],duration=150,loop=0,disposal=2)
  recipe_groups.append({'group':group,'frames':native_frames[:1] if group==2 else native_frames})
  actions.append({'group':group,'generation':proof(PROJECT,generation_path),'camera':proof(PROJECT,camera_path),
   'placement':final['placement_record'],'native_export':proof(PROJECT,folder/f'paint-action-g{group:02}-native-export-v2-placement-v1.json'),'contact':proof(PROJECT,contact)})
 write(folder/'painted-pilot-padding-v1.json',{'unit':unit,'conversions':padding,'active_assets_modified':False,'visual_approval_granted':False})
 recipe={'recipe_type':'vcmi_animation','output_path':f'Content/Sprites/runeterra/demacia/creatures/{unit}/battle.json','canvas':[450,400],
  'pivot':{'x':197,'y':266},'generateShadow':1,'generateOverlay':1,'groups':recipe_groups,
  'status':'PARTIAL source-only walk/hold/thrust pilot; all remaining action groups still missing; no active promotion',
  'acceptance':'No final native art/gameplay/release acceptance. A three-group source pilot cannot pass complete-creature validation.'}
 recipe_path=folder/'battle-pilot-v1.recipe.json';write(recipe_path,recipe)
 units.append({'id':unit,'blend':proof(PROJECT,folder/f'{unit}-dragonguard-rig-v3.blend'),'raw_pose_metadata':proof(PROJECT,folder/'dragonguard-production-v3.json'),
  'actions':actions,'candidate_recipe':proof(PROJECT,recipe_path),'actual_painted_source_cells':16,'registered_frame_entries':13,
  'open_issues':['Only walk, first calm holding and straight thrust painted; other actions remain raw3D only.',
    'Actual thrust blade/pole projection is longer than the raw rig at its impact pose; compare native weapon reach/identity before further painting.',
    'Generated cloth/body/shaft geometry changes slightly across poses and source-row framing required measured translations.',
    'Native gait/foot contact, two-hand visual continuity, full crest and renderer shadow/selection behavior remain unapproved.']})
write(PROJECT/'assets/source/creatures/dragonguard-painted-pilots-v1.json',{'units':units,
 'status':'First source-only measured native pilots, not complete battle assets or native render acceptance','active_assets_modified':False,'visual_approval_granted':False})
print('Exported32actual own painted native pilot frames; partial source recipes13entries each, no active writes.')
