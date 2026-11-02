"""Measured own full-action source candidates; never active asset promotion."""
from pathlib import Path
import json
import sys
from PIL import Image,ImageDraw

PROJECT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(PROJECT/'scripts'))
from creature_family_motion_art import calibrate_generation,export_generation,proof,write
from creature_padding import crop_padding

GROUPS=(0,1,2,3,4,5,7,8,11,12,13)
# Actually inspected first-pose helmet-top points on512px normalized review.
# Base front-turn g08 deliberately excludes the pole blade above its helmet.
HEADS={'dragonguard':{0:92,1:120,2:109,3:93,4:108,5:119,7:91,8:83,11:137,12:112,13:127},
       'veteranDragonguard':{0:81,1:97,2:92,3:96,4:45,5:85,7:77,8:77,11:84,12:93,13:85}}
family={'units':[],'status':'Complete own source candidates; native behavior and final visual acceptance pending',
    'active_assets_modified':False,'visual_approval_granted':False}
for unit,heads in HEADS.items():
    folder=PROJECT/'assets/source/creatures'/unit/'dragonguard-rig-v3'
    actions=[];groups=[]
    for group in GROUPS:
        version=3 if (unit,group) in {('veteranDragonguard',11),('dragonguard',5)} else 2
        source=folder/f'paint-action-g{group:02}-atlas-v{version}-generation.json'
        generation=json.loads(source.read_text());original=json.loads((folder/f'paint-action-g{group:02}-atlas-v1-generation.json').read_text())
        correction=(unit,group)==('dragonguard',5)
        camera_version=3 if correction else 2
        initial_version=5 if correction else 3
        final_version=6 if correction else 4
        placement_version=3 if correction else 2
        original_cell=original['returned_cell'][0];factor=original_cell/512
        first=generation['atlas_repack']['frames'][0]['repacked_alpha8_bbox']
        root=(245 if unit=='dragonguard' and group==0 else 250 if unit=='veteranDragonguard' and group in (0,2) else
            255 if unit=='dragonguard' or group!=12 else 241)
        camera=calibrate_generation(PROJECT,source,reference_index=0,head_top_y=heads[group]*factor+64,
            ground_y=first[3],root_x=root*factor+64,target_height=80 if unit=='dragonguard' else 84,
            basis=f'Actually inspected original first-pose helmet/wing topY{heads[group]} on normalized512 cell; original cell{original_cell}px and documented lossless repack+64. Supporting sole is actual first visible-body bottom{first[3]} in768cell. Higher pole excluded. One uniform camera normalization for the whole atlas; no per-frame size fitting.',version=camera_version)
        camera_path=folder/f'paint-action-g{group:02}-camera-v{camera_version}.json'
        initial=export_generation(PROJECT,source,camera_path,version=initial_version)
        if group==0:
            raw_bottoms=[]
            for index in range(6):
                with Image.open(folder/f'raw-native-review/g00/g00-f{index:03}.png') as raw:
                    raw_bottoms.append(raw.getchannel('A').point(lambda a:255 if a>=8 else 0).getbbox()[3])
        placements=[]
        for frame in initial['frames']:
            target=267+raw_bottoms[frame['index']]-raw_bottoms[0] if group==0 else 267
            placements.append({'index':frame['index'],'native_translation':[0,target-frame['alpha8_bbox'][3]],
                'reviewed':True,'basis':f'Whole genuine frame only, supporting native bottom{frame["alpha8_bbox"][3]} to{target}; walk retains executed rig projected sole variation. Other supported poses meet shared floor, including actual fallen corpse. No resized limbs or per-frame scale.',
                'evidence':[proof(PROJECT,source),proof(PROJECT,PROJECT/frame['output'])]})
        final=export_generation(PROJECT,source,camera_path,version=final_version,placements=placements,placement_version=placement_version)
        converted=[]
        for frame in final['frames']:
            target=folder/f'native-battle-candidate-v2/g{group:02}-f{frame["index"]:03}.png'
            result=crop_padding(PROJECT/frame['output'],target,PROJECT)
            converted.append({'index':frame['index'],**result})
        frames=converted[:1] if group==2 else converted
        groups.append({'group':group,'frames':[{'source':frame['output'],'sha256':frame['sha256']} for frame in frames]})
        actions.append({'group':group,'generation':proof(PROJECT,source),'camera':proof(PROJECT,camera_path),
            'placement':final['placement_record'],'native_export':proof(PROJECT,folder/f'paint-action-g{group:02}-native-export-v{final_version}-placement-v{placement_version}.json'),
            'converted_frames':converted})
    groups.append({'group':22,'frames':[next(g for g in groups if g['group']==5)['frames'][-1]]})
    boards=[]
    for part,subset in enumerate((GROUPS[:6],GROUPS[6:]),1):
        board=Image.new('RGB',(1440,len(subset)*190),'#344037');draw=ImageDraw.Draw(board)
        for row,group in enumerate(subset):
            frames=next(action for action in actions if action['group']==group)['converted_frames']
            for column,frame in enumerate(frames):
                with Image.open(PROJECT/frame['output']) as im:
                    tile=Image.new('RGBA',(240,160),'#c6c8b6');tile.alpha_composite(im.crop((100,120,340,280)))
                    board.paste(tile.convert('RGB'),(column*240,row*190+20))
                draw.text((column*240+3,row*190+3),f'{unit} g{group:02} f{column}',fill='white')
                draw.line((column*240,row*190+167,(column+1)*240-1,row*190+167),fill='#7d9278')
        path=folder/f'all-actions-native-placed-part{part}-v2.png';board.save(path);boards.append(proof(PROJECT,path))
    production=folder/'painted-actions-production-v2.json'
    write(production,{'unit':unit,'blend':proof(PROJECT,folder/f'{unit}-dragonguard-rig-v3.blend'),
        'raw_pose_metadata':proof(PROJECT,folder/'dragonguard-production-v3.json'),'actions':actions,'native_boards':boards,
        'executed_exporter':proof(PROJECT,Path(__file__)),'executed_repack_helper':proof(PROJECT,PROJECT/'scripts/creature_dragonguard_motion_art.py'),
        'camera_rule':'Each actual painted atlas has one measured uniform camera normalization. Only declared integer whole-frame placement; no per-frame fitting or raw/painted pixel equivalence.',
        'speck_correction':'Veteran g00f5 originally included the neighboring g00f4 long pole tip across nominal512cell. Lossless reviewed per-pose ROI recovers the tip in its correct frame and omits it from f5; no creative pixel edits.',
        'death_roi_correction':'Base g05v2 swapped70 tip pixels with313 neighboring butt pixels in sharedgutter; v3 rectangles recover both true components losslessly. Earlier sources/exports remain history.',
        'superseded_source':'Veteran g11 repackv2 omitted703 visible tip pixels; preserved as rejected history. Selected repackv3 restores all alpha>=8 pixels and coverage validator now rejects any such omission.',
        'visual_approval_granted':False,'active_assets_modified':False})
    candidate=folder/'battle-candidate-v2.recipe.json'
    write(candidate,{'recipe_type':'vcmi_animation','output_path':f'Content/Sprites/runeterra/demacia/creatures/{unit}/battle.json',
        'canvas':[450,400],'pivot':{'x':197,'y':266},'generateShadow':1,'generateOverlay':1,'groups':groups,
        'provenance':proof(PROJECT,production),'status':'full-articulated-action-candidate; native-review-pending; release-blocked',
        'credits':'Original project articulated two-handed polearm rig and own selected Demacian master; built-in imagegen painted finish. Original Castle style references inspected privately; no original creature pixels copied.',
        'acceptance':'Source action candidate only; no final visual, combat or release acceptance.'})
    movies=[]
    sequence=[2,1,2,0,0,2,7,8,2,3,2,4,2,11,2,12,2,13,2,5,22]
    for label,color in (('light','#c6bea5'),('dark','#344037')):
        frames=[];durations=[]
        for group in sequence:
            for index,frame in enumerate(next(g for g in groups if g['group']==group)['frames']):
                with Image.open(PROJECT/frame['source']) as image:
                    tile=Image.new('RGBA',(240,170),color);tile.alpha_composite(image.crop((100,115,340,285)))
                    rgb=tile.convert('RGB');ImageDraw.Draw(rgb).text((3,3),f'{unit} g{group:02} f{index}',fill='black' if label=='light' else 'white')
                frames.append(rgb);durations.append(700 if group in (2,22) else 130)
        path=folder/f'native-battle-candidate-v2-{label}.gif'
        frames[0].save(path,save_all=True,append_images=frames[1:],duration=durations,loop=0,disposal=2,optimize=False);movies.append(proof(PROJECT,path))
    family['units'].append({'unit':unit,'candidate':proof(PROJECT,candidate),'production':proof(PROJECT,production),
        'native_boards':boards,'movies':movies,'actual_painted_source_cells':sum(len(a['converted_frames']) for a in actions),
        'registered_frame_entries':sum(len(g['frames']) for g in groups),'open_issues':['Minor geometry/material variation between painted action atlases remains visible.',
            'Actual native timing, footprint grounding, shadows/selection and side-by-side original-town visual approval remain pending.']})
write(PROJECT/'assets/source/creatures/dragonguard-painted-battle-candidates-v2.json',family)
print('Completed two actual52entry source candidates,108 real painted poses, no active promotion.')
