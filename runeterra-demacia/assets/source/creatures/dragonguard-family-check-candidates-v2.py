"""Check own native source packets and execute real assembler twice, isolated."""
from pathlib import Path
import json
import shutil
import sys
import runpy
import contextlib
import io
import numpy as np
from PIL import Image,ImageChops,ImageDraw

PROJECT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(PROJECT/'scripts'))
from animation import assemble
from creature_family_motion_art import proof,sha,write
from identity import canonical_action_groups,animation_groups

with contextlib.redirect_stdout(io.StringIO()):
    components=runpy.run_path(str(PROJECT/'references/prototypes/dragonguard-component-survey-v1.py'))['components']

family_path=PROJECT/'assets/source/creatures/dragonguard-painted-battle-candidates-v2.json'
family=json.loads(family_path.read_text());creatures=json.loads((PROJECT/'content/creatures.json').read_text())
sandbox=PROJECT/'references/prototypes/dragonguard-family-v3/assembler-sandbox-v2'
sandbox.mkdir(parents=True,exist_ok=True)
report={'source_candidates':proof(PROJECT,family_path),'units':[],'errors':[],
    'active_assets_modified':False,'visual_approval_granted':False,'native_runtime_tested':False}
for unit in family['units']:
    candidate=PROJECT/unit['candidate']['path'];assert proof(PROJECT,candidate)==unit['candidate']
    recipe=json.loads(candidate.read_text());groups={item['group']:item['frames'] for item in recipe['groups']}
    required=canonical_action_groups(recipe,creatures)
    assert set(groups)==set(required)|{22} and recipe['pivot']=={'x':197,'y':266}
    assert len(groups[2])==1 and groups[22]==[groups[5][-1]]
    idle=groups[2][0]['sha256'];actual_count=0;coverage=[]
    production=PROJECT/recipe['provenance']['path'];assert proof(PROJECT,production)==recipe['provenance']
    data=json.loads(production.read_text())
    for action in data['actions']:
        for field in ('generation','camera','placement','native_export'):
            item=action[field];assert proof(PROJECT,PROJECT/item['path'])==item
        gen=json.loads((PROJECT/action['generation']['path']).read_text());original=PROJECT/gen['atlas_repack']['source']['path']
        assert proof(PROJECT,original)==gen['atlas_repack']['source']
        with Image.open(original) as image:
            visible=image.getchannel('A').point(lambda v:255 if v>=8 else 0).convert('1');selected=Image.new('1',image.size);draw=ImageDraw.Draw(selected)
            parts,labels=components(np.array(image.getchannel('A'))>=8,True)
            source_generation=json.loads((PROJECT/gen['atlas_repack']['source_generation']['path']).read_text())
            cell_width,cell_height=source_generation['returned_cell'];columns=source_generation['layout'][0]
            main_parts=[part for part in parts if part['pixels']>1000]
            expected={int((part['bounds'][1]+part['bounds'][3])/2/cell_height)*columns+int((part['bounds'][0]+part['bounds'][2])/2/cell_width):part['label'] for part in main_parts}
            all_main=np.isin(labels,[part['label'] for part in main_parts])
            for frame in gen['atlas_repack']['frames']:
                own_mask=np.zeros(labels.shape,dtype=bool)
                for part in frame['pieces']:
                    rect=part['source_rect'];draw.rectangle((rect[0],rect[1],rect[2]-1,rect[3]-1),fill=255)
                    own_mask[rect[1]:rect[3],rect[0]:rect[2]]=True
                own_label=labels==expected[frame['index']]
                assert not (own_label&~own_mask).any(),'True pose component clipped or assigned to neighbor'
                assert not (all_main&~own_label&own_mask).any(),'Neighbor weapon/body component assigned to this pose'
            assert not ImageChops.logical_and(visible,ImageChops.invert(selected)).getbbox(),'Visible source tip/limb omitted'
        coverage.append({'group':action['group'],'selected_generation':action['generation'],'all_alpha8_source_pixels_recovered':True,
            'each_full_body_weapon_component_in_its_correct_frame':True,'neighbor_body_weapon_pixels_retained':False})
        for frame in action['converted_frames']:
            source=PROJECT/frame['output'];before=PROJECT/frame['source']
            assert sha(source)==frame['sha256'] and sha(before)==frame['source_sha256']
            assert frame['maximum_discarded_alpha']<8 and frame['retained_rgba_pixels_identical']
            with Image.open(source) as image,Image.open(before) as original:
                bounds=image.getchannel('A').getbbox();assert image.mode=='RGBA' and image.size==(450,400)
                assert bounds and 0<bounds[0]<bounds[2]<450 and 0<bounds[1]<bounds[3]<400
                rect=tuple(frame['retained_rectangle']);assert image.crop(rect).tobytes()==original.crop(rect).tobytes()
            actual_count+=1
    for group,frames in groups.items():
        if group not in (2,22):
            assert len(frames)>=required[group] and len({frame['sha256'] for frame in frames})>=4
            assert all(frame['sha256']!=idle for frame in frames),'Complete action replaced with idle'
        for frame in frames:
            source=PROJECT/frame['source'];assert sha(source)==frame['sha256']
            target=sandbox/frame['source'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    target=sandbox/candidate.relative_to(PROJECT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(candidate,target)
    first=assemble(sandbox,target,resume=False);second=assemble(sandbox,target,resume=True)
    assert first['ok'] and second['ok']
    checksums=lambda result:{item['output_path']:item['sha256'] for item in result['outputs']}
    assert checksums(first)==checksums(second)
    definition=json.loads((sandbox/'assets/generated'/recipe['output_path']).read_text())
    native=animation_groups(definition,complete=True)
    assert set(native)==set(groups) and all(len(native[group])==len(frames) for group,frames in groups.items())
    report['units'].append({'unit':unit['unit'],'candidate':unit['candidate'],'actual_painted_native_frames_checked':actual_count,
        'registered_groups':sorted(groups),'registered_frame_count':first['frame_count'],'source_coverage':coverage,
        'canonical_action_minima_met':True,'corpse_is_actual_final_fall':True,'retained_rgba_identical':True,
        'actual_calls':[first,second],'identical_repeated_output_hashes':True})
report['status']='Real source frames, canonical groups and deterministic real assembler2x checked; native/playback/final visual acceptance still separate'
write(PROJECT/'references/prototypes/dragonguard-family-v3/source-candidate-assembly-v2.json',report)
print([(unit['unit'],unit['actual_painted_native_frames_checked'],unit['registered_frame_count']) for unit in report['units']])
