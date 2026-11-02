"""Technical-only fixed-canvas assembly of independently painted action masters.

No generated action is invented here. The named pose files must already exist.
Run from the workspace root using the project Python. Private references and
tool paths are retained in the report, never in the portable artwork packet.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
from PIL import Image, ImageDraw, ImageOps, ImageFilter

PROJECT = Path(__file__).resolve().parents[5]
REPORT = PROJECT / 'build/reports/painted-chimeras-20261024-v1'
UNITS = ('sandstoneChimera', 'gildedChimera')
GROUPS = {
    0: [f'flight-{i}' for i in range(6)],
    1: ['fidget-look', 'fidget-settle', 'standing'],
    2: ['standing', 'idle-breath'],
    3: ['hit', 'standing'],
    4: ['brace', 'standing'],
    5: ['death-recoil', 'death-fall', 'death-rest'],
    7: ['turn-front', 'standing'], 8: ['turn-back', 'standing'],
    11: ['attack-prep', 'attack-up', 'standing'],
    12: ['attack-prep', 'attack-front', 'standing'],
    13: ['attack-prep', 'attack-down', 'standing'],
    20: ['takeoff-crouch', 'takeoff-lift', 'flight-0'],
    21: ['landing-flare', 'landing-contact', 'standing'],
}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n', encoding='utf-8')

def descriptor(path):
    return {'source': path.relative_to(PROJECT).as_posix(),
            'source_sha256': sha(path.read_bytes()),
            'source_canvas': list(Image.open(path).size)}

def fixed_canvas(master, size, root, extent, registration=None):
    # Uniform scale derives from the WHOLE source canvas, never opaque bounds.
    # Root coordinates are normalized once from the original standing1254canvas.
    source = Image.open(master).convert('RGBA')
    if source.width != source.height:
        raise ValueError(f'Unexpected nonsquare master: {master}')
    image = source.resize((extent, extent), Image.Resampling.LANCZOS)
    anchor_source=(registration or {}).get('source_anchor',[621,1073])
    anchor_native=(registration or {}).get('native_anchor',root)
    source_root = (anchor_source[0] / 1254 * extent, anchor_source[1] / 1254 * extent)
    offset = (round(anchor_native[0] - source_root[0]), round(anchor_native[1] - source_root[1]))
    result = Image.new('RGBA', size)
    result.alpha_composite(image, offset)
    return result, {'source_canvas': list(source.size), 'whole_canvas_extent': extent,
                    'scale': extent/source.width, 'offset': list(offset),
                    'root': list(root), 'per_pose_opaque_fit': False,
                    'anatomical_registration': registration}

def shadow_composite(body, ground):
    # Technical alpha matte from the painted pose, not newly drawn creature art.
    # One fixed ground-plane matrix for every pose. No bbox/pivot auto-fitting.
    shear, flatten=-0.35,0.22
    alpha=body.getchannel('A').point(lambda value:round(value*0.30))
    inverse=(1,-shear/flatten,shear*ground/flatten,
             0,1/flatten,ground*(1-1/flatten))
    mask=alpha.transform(body.size,Image.Transform.AFFINE,inverse,Image.Resampling.BICUBIC)
    mask=mask.filter(ImageFilter.GaussianBlur(0.4))
    shadow=Image.new('RGBA',body.size,(0,0,0,0))
    shadow.putalpha(mask)
    result=shadow.copy()
    result.alpha_composite(body)
    return result,shadow

def main():
    sys.path.insert(0, str(PROJECT.parent / 'scripts'))
    from faction_art_compile import create_compiler
    from shurima_asset_manifest import canonical_groups
    compiler = create_compiler('shurima')
    records = []
    for unit in UNITS:
        source = PROJECT / f'assets/source/creatures/painted-v2/{unit}'
        masters = source / 'masters'
        names = sorted({key for seq in GROUPS.values() for key in seq})
        missing = [name for name in names if not (masters / f'{name}.png').is_file()]
        if missing:
            raise ValueError(f'{unit}: missing true painted poses: {missing}')
        frames = source / 'native-v1'
        frames.mkdir(exist_ok=True)
        registration_path=source/'anatomical-registration-v1.json'
        registrations=json.loads(registration_path.read_text(encoding='utf-8'))['poses'] if registration_path.is_file() else {}
        measurements = []
        pose_paths = {}
        selected_masters={}
        for name in names:
            selected=masters / (f'{name}-root-v2.png' if unit=='sandstoneChimera' and name.startswith('flight-') and name!='flight-0' else f'{name}.png')
            selected_masters[name]=selected
            image, transform = fixed_canvas(selected, (450,400), (218,266), 157, registrations.get(name))
            body_path=frames/'body-layers'/f'{name}.png'
            shadow_path=frames/'shadow-layers'/f'{name}.png'
            body_path.parent.mkdir(exist_ok=True)
            shadow_path.parent.mkdir(exist_ok=True)
            image.save(body_path)
            image,shadow=shadow_composite(image,266)
            shadow.save(shadow_path)
            path = frames / f'{name}.png'
            image.save(path)
            pose_paths[name] = path
            opaque = image.getchannel('A').point(lambda v: 255 if v >= 128 else 0).getbbox()
            measurements.append({'pose': name, 'transform': transform, 'opaque_bounds': opaque,
                                 'source': descriptor(selected), 'native': descriptor(path),
                                 'unchanged_body_layer':descriptor(body_path),
                                 'technical_shadow_layer':descriptor(shadow_path)})
        portable_prompts=[]
        prompt_inputs=sorted((source/'prompts').glob('*.json'))
        checkpoint=source/'generation-checkpoint-v1.json'
        if checkpoint.is_file():
            prompt_inputs.append(checkpoint)
        for receipt_path in prompt_inputs:
            value=json.loads(receipt_path.read_text(encoding='utf-8'))
            items=value if isinstance(value,list) else value.get('prompts',[value])
            if receipt_path.name=='initial-prompts-v1.json':
                items=[{'name':key,'prompt':text} for key,text in value.items()]
            for item in items:
                if isinstance(item.get('prompt'),str):
                    portable_prompts.append({'pose':item.get('name',item.get('pose')), 'prompt':item['prompt'],
                                            'tool':'builtin image_gen.imagegen',
                                            'no_3d_input':True})
        portable_prompts=list({(item['pose'],item['prompt']):item for item in portable_prompts}.values())
        dump(source/'generation-provenance-v1.json',{'status':'authored configuration',
             'provider':'OpenAI built-in imagegen','model':'not exposed by built-in tool',
             'source_method':'Independent painted2D anatomy/action masters, no3Dinputs.',
             'private_reference_identifiers':['core:griffin','core:stoneGargoyle','LoR04SH046'],
             'reference_images_redistributable':False,'visual_approval_granted':False,
             'masters':[{'pose':name,**descriptor(selected_masters[name])} for name in names],
             'prompts':portable_prompts})
        # Map/adventure resources share an independently recorded uniform scale.
        resources = source / 'resources-v1'
        resources.mkdir(exist_ok=True)
        map_image, map_transform = fixed_canvas(masters/'standing.png', (96,64), (64,60), 63)
        map_image,_=shadow_composite(map_image,60)
        map_image.save(resources/'map.png')
        right, attack_transform = fixed_canvas(masters/'attack-front.png', (96,64), (64,60), 63)
        right,_=shadow_composite(right,60)
        right.save(resources/'attackRight.png')
        # Reflect about the authored adventure root, not the96pxcanvas center.
        left = right.transform((96,64), Image.Transform.AFFINE, (-1,0,128,0,1,0), Image.Resampling.NEAREST)
        left.save(resources/'attackLeft.png')
        standing = Image.open(masters/'standing.png').convert('RGBA')
        canonical = standing.resize((1254,1254), Image.Resampling.LANCZOS)
        large_crop=(720,440,1100,860) if unit=='sandstoneChimera' else (720,380,1120,860)
        small_crop=(720,440,1100,820) if unit=='sandstoneChimera' else (720,380,1120,780)
        ImageOps.contain(canonical.crop(large_crop),(58,64),method=Image.Resampling.LANCZOS).save(resources/'large-crop-intermediate.png')
        large=Image.new('RGBA',(58,64))
        head=Image.open(resources/'large-crop-intermediate.png')
        large.alpha_composite(head,((58-head.width)//2,(64-head.height)//2))
        large.save(resources/'large.png')
        canonical.crop(small_crop).resize((32,32), Image.Resampling.LANCZOS).save(resources/'small.png')
        generation = {'image_generation_used': True, 'model': 'not exposed by built-in tool',
                      'provider': 'OpenAI built-in imagegen',
                      'prompt': 'See portable generation-provenance-v1.json; one genuinely painted pose per tool call.',
                      'painted_master': (masters/'standing.png').relative_to(PROJECT).as_posix(),
                      'method': 'Independent2Dpainted poses; fixed fullcanvas uniform conversion; no3Dinput or bodybbox fitting.'}
        common = {'unit': unit, 'status': 'authored configuration',
                  'production_status': 'painted-master-complete-unapproved',
                  'generation': generation, 'visual_approval_granted': False,
                  'credits': {'author': 'Project-directed built-in imagegen and technical2Dassembly',
                              'license': None, 'redistribution': 'unresolved; release prohibited'}}
        prefix = f'Content/Sprites/runeterra/shurima/creatures/{unit}/'
        recipes = REPORT / f'recipe-payload/creatures/painted-v2/{unit}'
        battle = dict(common, recipe_type='vcmi_animation', canvas=[450,400], pivot={'x':218,'y':266},generateShadow=0,generateOverlay=1,
                      output_path=prefix+'battle.json', groups=[{'group':group,
                      'frames':[dict(descriptor(pose_paths[name]), frame=i) for i,name in enumerate(seq)]}
                      for group,seq in GROUPS.items()])
        dump(recipes/'battle.json', battle)
        current_content={'creatures':json.loads((PROJECT/'content/creatures.json').read_text(encoding='utf-8'))}
        required=canonical_groups(current_content,prefix+'battle.json')
        actual={sequence['group']:len(sequence['frames']) for sequence in battle['groups']}
        if any(actual.get(group,0)<minimum for group,minimum in required.items()):
            raise AssertionError(f'Actual current native contract not fulfilled: {unit}: {required} vs {actual}')
        dump(REPORT/f'{unit}-exact-action-contract-v1.json',{'status':'authored configuration',
             'required_groups':required,'actual_groups':actual,
             'source':'scripts/shurima_asset_manifest.py:canonical_groups',
             'contract_weakened':False,'runtime_verified':False,'visual_approval_granted':False})
        mapping = dict(common, recipe_type='vcmi_animation', canvas=[96,64], pivot={'x':64,'y':60},generateShadow=0,generateOverlay=1,
                       output_path=prefix+'map.json', groups=[{'group':0,'frames':[dict(descriptor(resources/'map.png'),frame=0)]}])
        dump(recipes/'map.json',mapping)
        for name in ('large','small','attackLeft','attackRight'):
            dims = [58,64] if name=='large' else [32,32] if name=='small' else [96,64]
            dump(recipes/f'{name}.json',dict(common, recipe_type='raster', size=dims,
                 fit='exact', output_path=prefix+name+'.png', **descriptor(resources/f'{name}.png')))
        for recipe in sorted(recipes.glob('*.json')):
            first, receipt = compiler.plan(PROJECT, recipe)
            second, receipt2 = compiler.plan(PROJECT, recipe)
            if first != second or receipt != receipt2:
                raise AssertionError(f'Nondeterministic compiler plan: {recipe}')
            for name,data in first.items():
                destination=REPORT/'compiled'/name
                destination.parent.mkdir(parents=True,exist_ok=True)
                destination.write_bytes(data)
            records.append({'recipe':recipe.relative_to(PROJECT).as_posix(),
                            'two_plan_runs_identical':True, 'receipt':receipt,
                            'outputs':{name:sha(data) for name,data in sorted(first.items())}})
        dump(source/'fixed-conversion-v1.json', {'battle':measurements,'map':map_transform,
             'adventure_attack':attack_transform,'portrait_crops':{'large':large_crop,'small':small_crop},
             'shadow':{'method':'Technical alpha-derived2Dmatte; paintedbodyalpha preserved in separately checksummed bodylayer.',
                       'fixed_forward_matrix':{'shear_x':-0.35,'scale_y':0.22,'ground_y':266},
                       'alpha_multiplier':0.30,'blur_native_pixels':0.4,'per_pose_fit':False},
             'mirroring':'Battle full450canvas by actualVCMIconsumer; adventure attacks aroundroot64.'})
        # Both facings at native1x; individual rows keep a fixed450x400canvas.
        sheet=Image.new('RGB',(900,len(names)*420),(66,65,60))
        draw=ImageDraw.Draw(sheet)
        for row,name in enumerate(names):
            image=Image.open(pose_paths[name])
            sheet.paste(image,(0,row*420+20),image)
            reflected=image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            sheet.paste(reflected,(450,row*420+20),reflected)
            draw.text((8,row*420+4),name,fill='white')
            draw.text((458,row*420+4),'native consumer reflected facing',fill='white')
        sheet.save(REPORT/f'{unit}-all-poses-native-both-facings.png')
        for facing in ('right','left'):
            rows=(len(names)+4)//5
            board=Image.new('RGB',(5*225,rows*260),(66,65,60))
            labels=ImageDraw.Draw(board)
            for index,name in enumerate(names):
                image=Image.open(pose_paths[name])
                if facing=='left':
                    image=image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                crop=image.crop((120,90,340,325) if facing=='right' else (110,90,330,325))
                x=(index%5)*225
                y=(index//5)*260
                board.paste(crop,(x,y+20),crop)
                labels.text((x+2,y+3),name,fill='white')
            board.save(REPORT/f'{unit}-{facing}-native-fixed-crop.png')
        for group,names_in_group in GROUPS.items():
            motion=[]
            for name in names_in_group:
                frame=Image.new('RGBA',(450,400),(66,65,60,255))
                frame.alpha_composite(Image.open(pose_paths[name]))
                motion.append(frame)
            motion[0].save(REPORT/f'{unit}-g{group:02d}-motion.png',save_all=True,
                           append_images=motion[1:],duration=150,loop=0,disposal=0,blend=0)
    dump(REPORT/'compiler-plan-twice-v1.json',{'status':'authored configuration',
         'active_recipes_modified':False,'generated_or_stage_modified':False,
         'visual_approval_granted':False,'records':records})

if __name__ == '__main__':
    main()
