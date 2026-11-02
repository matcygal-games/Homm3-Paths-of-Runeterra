"""Assemble reviewed own source action sequences, without active promotion."""
from pathlib import Path
import hashlib
import json
import sys

from PIL import Image, ImageDraw

PROJECT = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(PROJECT/'scripts'))
from creature_family_motion_art import proof,write

GROUPS=(0,1,2,3,4,5,7,8,11,12,13,14,15,16)
POINTS={'demacianRanger':{14:[227,195],15:[230,201],16:[234,220]},
        'veteranRanger':{14:[226,192],15:[236,206],16:[234,215]}}
family=[];emitters=[]
for unit in ('demacianRanger','veteranRanger'):
    folder=PROJECT/'assets/source/creatures'/unit/'ranger-rig-v4'
    raw=json.loads((folder/'ranger-production-v4.json').read_text())
    padding_path=folder/'painted-native-padding-v1.json';padding=json.loads(padding_path.read_text())
    converted={item['output']:item for item in padding['conversions']}
    groups=[];actions=[];final_frames=[];emissions=[]
    for group in GROUPS:
        export_path=folder/f'paint-action-g{group:02}-native-export-v2-placement-v1.json'
        exported=json.loads(export_path.read_text());generation=json.loads((PROJECT/exported['generation_record']['path']).read_text())
        count=len(exported['frames']);indices=list(range(count))
        correction=None
        if unit=='demacianRanger' and group==12:
            indices=[0,1,3,2,4,5]
            correction={'basis':'Actually inspected returned source cell2 is forward level knife impact; cell3 is elevated backswing. Explicitly swap these two genuine same-character source poses so native six-frame midpointindex3 contains impact. No fabricated pose, timing change, pixel warp or unrecorded source order claim.',
                'source_playback_indices':indices,'native_impact_index':3,'actual_impact_source_cell':2,
                'evidence':proof(PROJECT,folder/'all-painted-native-review-panel-2-v1.png')}
        if group==2:
            indices=[0]  # Actual calm holding only. Generated other holds are retained as unpromoted sources.
        frames=[]
        for source_index in indices:
            path=folder/f'native-actions-final-v1/g{group:02}/g{group:02}-f{source_index:03}.png'
            item=converted[path.relative_to(PROJECT).as_posix()]
            if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:
                raise ValueError('Final native source changed')
            with Image.open(path) as image:
                if image.mode!='RGBA' or image.size!=(450,400):raise ValueError('Invalid actual native frame')
            frames.append({'source':item['output'],'sha256':item['sha256']})
            final_frames.append({'group':group,'source_index':source_index,**frames[-1]})
        row={'group':group,'frames':frames}
        if correction:row['source_order_correction']=correction
        groups.append(row)
        actions.append({'group':group,'actual_creative_generation':generation.get('atlas_repack',{}).get('source_generation',exported['generation_record']),
            'assembly_generation':exported['generation_record'],'camera':exported['camera_record'],'placement':exported['placement_record'],
            'native_export':proof(PROJECT,export_path),'source_playback_indices':indices,
            'actual_pose_count':count,'source_holds':exported['source_holds'],'source_order_correction':correction})
        if group in (14,15,16):
            point=POINTS[unit][group];native=folder/f'native-actions-final-v1/g{group:02}/g{group:02}-f004.png'
            creative_record=PROJECT/(generation.get('atlas_repack',{}).get('source_generation',exported['generation_record'])['path'])
            creative=json.loads(creative_record.read_text());actual_atlas=PROJECT/creative['output']
            emissions.append({'group':group,'direction':{14:'upper',15:'straight',16:'lower'}[group],
                'release_frame_zero_based':4,'source_kind':'painted-native','native_tip_pixels':point,
                'provisional_offset':{'x':point[0]-197,'y':point[1]-265},'uncertainty_native_pixels':2,
                'source_frame':proof(PROJECT,actual_atlas),'source_cell_index':4,
                'native_frame':proof(PROJECT,native),'generation_record':proof(PROJECT,creative_record),
                'assembly_generation':exported['generation_record'],'native_calibration':exported['camera_record'],
                'native_placement':exported['placement_record'],'native_export':proof(PROJECT,export_path),
                'padding_conversion':proof(PROJECT,padding_path),
                'inspection_evidence':proof(PROJECT,folder/f'paint-g{group:02}-final-release-landmark-review-v1.png'),
                'measurement_method':'Actual final450x400painted raster inspected with nearest-neighbor coordinate grid. Forward central crossbow stock/muzzle tip, not full alpha bbox or highest prod limb. Rig is pose provenance only, never claimed pixel/geometry equivalence.',
                'runtime_trajectory_tested':False})
    corpse=next(row for row in groups if row['group']==5)['frames'][-1]
    groups.append({'group':22,'frames':[corpse],'basis':'Actual final genuine painted death pose; native persistent DEAD state.'})
    production_path=folder/'painted-actions-production-v1.json'
    recipe_path=folder/'battle-candidate-v1.recipe.json'
    production={'unit':unit,'blend':proof(PROJECT,folder/f'{unit}-ranger-rig-v4.blend'),
        'raw_pose_metadata':proof(PROJECT,folder/'ranger-production-v4.json'),
        'source_tool_provenance':proof(PROJECT,PROJECT/'assets/source/creatures/rig-production-tools-v1.json'),
        'current_master':proof(PROJECT,folder.parent/'master-v5.png'),'actions':actions,'native_padding':proof(PROJECT,padding_path),
        'registered_groups':{str(row['group']):len(row['frames']) for row in groups},'registered_frame_entries':sum(len(row['frames']) for row in groups),
        'actual_painted_source_cells':78,'pose_count_note':'Includes genuine ready/recovery/steady-aim holds, not78distinct physical motions. Native holding selects only first calm source pose; DEAD correctly aliases final death.',
        'native_canvas':[450,400],'pivot':[197,266],'generateShadow':1,'generateOverlay':1,
        'shooting':{'frames_per_direction':8,'native_one_based_attack_climax_frame':5,'release_source_index':4,
            'intentional_aim_hold_indices':[2,3],'semantics':'Ready/raise/steady aim/steady aim/release/recoil/cock/reload. No pixel-noise or idle-as-shoot/death substitution.'},
        'source_only_visual_review':'All actual final native light/dark contact panels inspected. Genuine opposite gait, flinch, brace, progressively prone death/corpse, face-turn, short-knife three-direction action and up/front/down crossbow sequences exist. No visible alpha backdrop halo at native scale.',
        'known_open_issues':['Painted body/cloth proportions vary slightly between independent action sheets; native playback remains necessary.',
            'Some drawn-knife source poses retain a small sheathed-hilt detail at the hip; this should be resolved or explicitly reviewed before final art acceptance.',
            'Returned turn-back poses include small foot stepping; these are real generated turn poses but differ from exact raw guide foot geometry.',
            'Full official crest shape at80px and generated-shadow/native ground contact are not accepted by this source record.',
            'Projectile points are manual +/-2pixel source measurements, not a native trajectory or release-timing pass.'],
        'status':'full articulated source candidate; native runtime and final art review pending; release blocked',
        'visual_approval_granted':False,'active_assets_modified':False}
    write(production_path,production)
    recipe={'recipe_type':'vcmi_animation','output_path':f'Content/Sprites/runeterra/demacia/creatures/{unit}/battle.json',
        'canvas':[450,400],'pivot':{'x':197,'y':266},'generateShadow':1,'generateOverlay':1,'groups':groups,
        'provenance':proof(PROJECT,production_path),
        'credits':'Original project volumetric female scout rig/poses, own identity/material masters, built-in imagegen painted finish. Installed Castle frames are private style comparisons only; no copied original animation frames bundled.',
        'acceptance':'All required source actions are present as unapproved candidates. This grants no native visual/gameplay/release acceptance.',
        'status':'full-articulated-action-candidate; native-review-pending; release-blocked'}
    write(recipe_path,recipe)
    # Complete1:1 source contact board and true playback sequence with explicit
    # g12 correction. No individual frame is stretched/fitted for either view.
    board=Image.new('RGB',(1200,len(groups)*140),'#d6d6c6');draw=ImageDraw.Draw(board);transition=[]
    for row,entry in enumerate(groups):
        draw.rectangle((0,row*140,1199,row*140+17),fill='#303b35')
        draw.text((4,row*140+3),f'{unit} g{entry["group"]:02} actual source playback order; NO final approval',fill='white')
        for index,frame in enumerate(entry['frames']):
            with Image.open(PROJECT/frame['source']) as image:
                tile=Image.new('RGBA',(140,120),'#d6d6c6');tile.alpha_composite(image.crop((135,170,275,290)))
                board.paste(tile.convert('RGB'),(index*140,row*140+20))
                canvas=Image.new('RGBA',(190,160),'#c6c7b5');canvas.alpha_composite(image.crop((125,155,315,315)))
                text=ImageDraw.Draw(canvas);text.text((3,3),f'{unit} g{entry["group"]:02} f{index}',fill='black')
                transition.append(canvas.convert('RGB'))
    board.save(folder/'all-painted-actions-native-contact-v1.png')
    transition[0].save(folder/'all-actions-native-transition-v1.gif',save_all=True,append_images=transition[1:],duration=140,loop=0,disposal=2)
    family.append({'id':unit,'candidate_recipe':proof(PROJECT,recipe_path),'production':proof(PROJECT,production_path),
        'groups':production['registered_groups'],'registered_frame_entries':production['registered_frame_entries'],
        'complete_native_contact':proof(PROJECT,folder/'all-painted-actions-native-contact-v1.png'),
        'transition_preview':proof(PROJECT,folder/'all-actions-native-transition-v1.gif'),'known_open_issues':production['known_open_issues']})
    emitters.append({'id':unit,'source_kind':'painted-native','source_revision':4,
        'blend':proof(PROJECT,folder/f'{unit}-ranger-rig-v4.blend'),'source_metadata':proof(PROJECT,folder/'ranger-production-v4.json'),
        'pose_provenance_note':'Editable rig is the source action guide only; independently painted geometry/camera explicitly measured, never assumed equal.',
        'measurements':emissions})
write(PROJECT/'assets/source/creatures/ranger-painted-battle-candidates-v1.json',{'units':family,
    'status':'source-only complete action candidates; no active assets or final acceptance changed','active_assets_modified':False,'visual_approval_granted':False})
write(PROJECT/'assets/source/creatures/ranger-painted-emitter-landmarks-v1.json',{'source_kind':'painted-native',
    'native_origin_authority':'BattleAnimationClasses.cpp716–735: facing-right local projectile origin=(197+offsetX,265+offsetY). ShootingAnimation getAttackClimaxFrame returns configured one-based5minus1=actual releaseindex4.',
    'units':emitters,'status':'actual manual painted-native source measurements; native projectile trajectories untested',
    'active_content_modified':False,'visual_approval_granted':False})
print('Assembled two source recipes,15groups/76entries each, six actual painted emitter measurements; no active promotion.')
