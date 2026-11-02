"""Reassemble existing painted Leviathan poses without the rejected frontal idle.

No artwork is synthesized. Existing full native pose pixels are selected intact;
the native reverse join is the sole technical reflection. Preview-only scaling
uses one common camera across every action and never changes battle pixels.
"""
from __future__ import annotations
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
from PIL import Image, ImageOps

HERE = Path(__file__).resolve().parent
PROJECT = next(p for p in HERE.parents if (p / 'content/creatures.json').is_file())
WORKSPACE = PROJECT.parent
UNITS = ('shoreLeviathan', 'elderShoreLeviathan')

def sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else Path(value).read_bytes()).hexdigest()

def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()

def relative(path):
    return Path(path).relative_to(PROJECT).as_posix()

def png(image):
    output = io.BytesIO()
    image.save(output, format='PNG', compress_level=9)
    return output.getvalue()

def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)

def descriptor(path, size):
    return {'source': relative(path), 'source_sha256': sha(path), 'source_canvas': list(size)}

def selected(history):
    recipe = json.loads(history.read_bytes())
    for group in recipe['groups']:
        for frame in group['frames']:
            if sha(PROJECT / frame['source']) != frame['source_sha256']:
                raise ValueError('Painted native input changed: ' + frame['source'])
    return recipe

def derive(unit, output):
    history = HERE / 'history' / (unit + '-battle.json')
    old = selected(history)
    source = {(g['group'], n): f for g in old['groups'] for n, f in enumerate(g['frames'])}
    # The standing side pose (m0) and side head-rise are already painted with
    # the same fixed camera, ground root and physical dimensions as the attacks.
    replacement = {(2, 0): (0, 0)}
    replacement.update({(1, n): key for n, key in enumerate(((0, 0), (3, 2), (3, 2), (0, 0), (0, 0)))})
    replacement.update({(g, 7): (0, 0) for g in (11, 12, 13)})
    replacement.update({(g, 4): (0, 0) for g in (3, 4)})
    replacement[(20, 0)] = (0, 0)
    replacement[(20, 1)] = (0, 2)
    replacement[(21, 1)] = (0, 0)
    # Preserve native TURN_L -> facing/reposition -> TURN_R display continuity.
    replacement.update({(7, n): key for n, key in enumerate(((0, 0), (7, 1), (7, 1), (7, 1), (7, 1)))})
    replacement.update({(8, n): key for n, key in enumerate((None, None, (7, 1), (0, 0), (0, 0)))})
    recipe = copy.deepcopy(old)
    groups = []
    records = []
    images = {}
    for group in old['groups']:
        row = {'group': group['group'], 'frames': []}
        for number, original in enumerate(group['frames']):
            key = (group['group'], number)
            chosen = replacement.get(key, key)
            join = chosen is None
            chosen = (7, 1) if join else chosen
            im = Image.open(PROJECT / source[chosen]['source']).convert('RGBA')
            if join:
                transformed = Image.new('RGBA', (450, 400))
                transformed.paste(ImageOps.mirror(im), (-14, 0))
                im = transformed
            name = f'g{key[0]:02d}-f{key[1]:03d}.png'
            target = output / unit / 'right' / name
            # Exact source bytes retained for every non-reflected painted key.
            put(target, png(im) if join else (PROJECT / source[chosen]['source']).read_bytes())
            row['frames'].append(descriptor(target, (450, 400)))
            images[key] = im
            records.append({'group': key[0], 'frame': key[1], 'original': original,
                            'selected_existing_pose': source[chosen], 'selected_pose_group': chosen[0],
                            'selected_pose_frame': chosen[1], 'native_turn_join': join,
                            'output': descriptor(target, (450, 400))})
        groups.append(row)
    recipe['groups'] = groups
    common = copy.deepcopy(recipe['generation'])
    ledger = output / unit / 'source-generation.json'
    dependencies = [{'path': relative(history), 'sha256': sha(history)},
                    {'path': relative(Path(__file__)), 'sha256': sha(Path(__file__))}]
    dependencies.extend(common.get('production_inputs', []))
    ledger_value = {'schema_version': 1, 'status': 'authored configuration', 'selected': False,
                    'unit': unit, 'workflow': 'genuine-painted-2d-imagegen', 'derived_from_blender': False,
                    'new_image_generation_used': False,
                    'method': 'Existing genuine side-painted native poses selected intact; technical reverse turn join only.',
                    'parent_generation': old['generation'], 'source_files': dependencies,
                    'frames': records, 'native_execution': False, 'release_accepted': False,
                    'limitations': ['Repeated existing painted keys retain cadence; no new unique idle anatomy claimed.',
                                    'Native motion and visual acceptance remain separate.']}
    put(ledger, encoded(ledger_value))
    common['provenance'] = relative(ledger)
    common['provenance_sha256'] = sha(ledger)
    common['source_generation_ledger'] = relative(ledger)
    common['source_generation_ledger_sha256'] = sha(ledger)
    common['production_inputs'] = dependencies
    common['prompt'] += ' User correction: remove frontal holding/fidget/recovery camera. Existing painted side poses are selected intact; technical mirroring only, no new artwork generated.'
    recipe['generation'] = common
    recipe['selected'] = False
    recipe['acceptance'] = 'Side-facing candidate only. Native motion, visual/crest and rights acceptance remain pending.'
    battle_recipe = output / unit / 'recipes/battle.json'
    put(battle_recipe, encoded(recipe))
    # Full-side holding no longer needs a frontal pose to fit the old crop.
    # An explicit preview camera keeps every action inside the native 100x130 UI.
    union = None
    for im in images.values():
        b = im.getchannel('A').getbbox()
        if b:
            union = b if union is None else (min(union[0], b[0]), min(union[1], b[1]), max(union[2], b[2]), max(union[3], b[3]))
    scale = min(92 / (union[2]-union[0]), 118 / (union[3]-union[1]))
    camera = {'canvas': [100, 130], 'source_union': list(union), 'uniform_scale': scale,
              'destination_left': 4, 'destination_top': 6, 'fixed_across_actions': True}
    preview = copy.deepcopy(recipe)
    preview.update(canvas=[100, 130], pivot={'x': 50, 'y': 124}, generateShadow=0, generateOverlay=0,
                   output_path=f'Content/Sprites/runeterra/bilgewater/creatures/{unit}/sidePreview.json')
    for group in preview['groups']:
        for number, frame in enumerate(group['frames']):
            im = images[(group['group'], number)]
            cut = im.crop(union).resize((round((union[2]-union[0])*scale), round((union[3]-union[1])*scale)), Image.Resampling.LANCZOS)
            result = Image.new('RGBA', (100, 130))
            result.paste(cut, (4, 6))
            p = output / unit / 'preview' / f'g{group["group"]:02d}-f{number:03d}.png'
            put(p, png(result))
            group['frames'][number] = descriptor(p, (100, 130))
    put(output / unit / 'recipes/preview.json', encoded(preview))
    put(output / unit / 'camera.json', encoded(camera))
    return {'unit': unit, 'battle_recipe': relative(battle_recipe), 'battle_recipe_sha256': sha(battle_recipe),
            'preview_recipe': relative(output / unit / 'recipes/preview.json'),
            'preview_recipe_sha256': sha(output / unit / 'recipes/preview.json'), 'camera': camera,
            'changed_slots': sum(key in replacement for key in images), 'total_slots': len(images),
            'original_recipe_sha256': sha(history)}

def main():
    output = HERE / 'candidate-v2'
    records = [derive(unit, output) for unit in UNITS]
    put(output / 'candidate.json', encoded({'status': 'authored configuration', 'selected': False,
        'units': records, 'producer_sha256': sha(Path(__file__)), 'native_execution': False}))
    print(json.dumps(records, indent=2))

if __name__ == '__main__':
    main()
