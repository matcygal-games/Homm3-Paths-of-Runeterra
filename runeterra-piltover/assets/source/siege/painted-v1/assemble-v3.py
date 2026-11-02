"""Deterministic crop/resample/placement of delivered painted siege masters.

No artwork, damage, masonry or actors are constructed by this script. Each
structural state is independently painted in the pinned cohort master. Outputs
stay in this candidate source directory; generic SDK plan() returns bytes only.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys

from PIL import Image, ImageDraw

BASE = Path(__file__).resolve().parent
PROJECT = BASE.parents[3]
WORKSPACE = PROJECT.parent
REPORT = WORKSPACE / 'build/reports/piltover-implementation-20261025-v1/siege'
sys.path.insert(0, str(WORKSPACE / 'scripts'))
from faction_art_compile import create_compiler

SIZES = {'BACK': (800, 556), 'ARCH': (65, 225), 'towerLarge': (58, 64), 'towerSmall': (32, 32),
         'DRW1': (103, 87), 'DRW2': (103, 87), 'DRW3': (103, 87), 'DRWC': (103, 87),
         'MAN1': (80, 300), 'MAN2': (80, 300), 'MANC': (80, 300),
         'MLIP': (200, 476), 'MOAT': (213, 466), 'TPWL': (200, 80),
         'TW11': (100, 56), 'TW12': (100, 56), 'TW1C': (100, 56),
         'TW21': (50, 126), 'TW22': (48, 126), 'TW2C': (90, 110),
         'WA2': (151, 253), 'WA5': (80, 241),
         **{f'{stem}{state}': size for stem, size in
            [('WA1', (150, 206)), ('WA3', (100, 200)),
             ('WA4', (100, 200)), ('WA6', (100, 200))] for state in (1, 2, 3)}}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rel(path):
    return Path(path).relative_to(PROJECT).as_posix()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def get_master(family):
    version = 'v2' if family in ('static2', 'static5', 'arch') else 'v1'
    path = BASE / family / f'master-{version}.png'
    image = Image.open(path).convert('RGBA')
    image.load()
    return path, image


def crop_pad(image, box, common_canvas=None):
    """Fixed cohort cells may differ by one source pixel from grid rounding."""
    selected = image.crop(tuple(box))
    if common_canvas:
        cell = Image.new('RGBA', tuple(common_canvas))
        cell.alpha_composite(selected, (0, 0))
        return cell
    return selected


def place(image, canvas, *, scale=None, offset=None, anchor='center', fit='contain'):
    if scale is None:
        scale = (max if fit == 'cover' else min)(canvas[0] / image.width, canvas[1] / image.height)
    size = tuple(max(1, round(n * scale)) for n in image.size)
    resized = image.resize(size, Image.Resampling.LANCZOS)
    if offset is None:
        offset = ((canvas[0] - size[0]) // 2,
                  0 if anchor == 'top' else (canvas[1] - size[1]) // 2)
    output = Image.new('RGBA', canvas)
    output.alpha_composite(resized, tuple(offset))
    return output, {'uniform_scale': scale, 'resampled_size': list(size),
                    'placement': list(offset), 'anchor': anchor, 'fit': fit}


def assemble():
    native = BASE / 'native-candidate-v3'
    native.mkdir(exist_ok=True)
    recipes = BASE / 'candidate-recipes-v3'
    recipes.mkdir(exist_ok=True)
    compiler = create_compiler('piltover')
    records = []

    def emit(suffix, family, box=None, common=None, **placement):
        master_path, image = get_master(family)
        original_size = list(image.size)
        if box is None:
            box = [0, 0, image.width, image.height]
        selected = crop_pad(image, box, common)
        output, transform = place(selected, SIZES[suffix], **placement)
        filename = suffix if suffix.startswith('tower') else 'SGPI' + suffix
        source_path = native / (filename + '.png')
        output.save(source_path, compress_level=9)
        version = 'v2' if family in ('static2', 'static5', 'arch') else 'v1'
        prompt_path = BASE / family / f'prompt-{version}.txt'
        prompt = prompt_path.read_text(encoding='utf-8') if prompt_path.is_file() else (
            'Original built-in image_gen painted Piltover siege battlefield; native Castle geometry '
            'reference only, own town palette reference; empty left approach and right dry courtyard. '
            'The complete generation request is preserved in the tool conversation.')
        recipe = {
            'recipe_type': 'raster', 'production_status': 'painted-master-complete-unapproved',
            'source': rel(source_path), 'source_sha256': sha(source_path),
            'source_canvas': list(output.size), 'canvas': list(SIZES[suffix]), 'fit': 'exact',
            'output_path': 'Content/Sprites/runeterra/piltover/siege/' + filename + '.png',
            'generation': {'image_generation_used': True,
                           'model': 'Built-in image_gen; exact model identifier not exposed',
                           'provider': 'OpenAI built-in image_gen', 'prompt': prompt,
                           'painted_master': rel(master_path)},
            'painted_source_derivation': {
                'master_sha256': sha(master_path), 'master_canvas': original_size,
                'crop': list(box), 'common_cell_canvas': list(common) if common else None,
                **transform, 'assembly_script': rel(Path(__file__)),
                'assembly_script_sha256': sha(Path(__file__)),
                'artwork_created_by_code': False,
                'original_reference_pixels_bundled': False,
            },
            'visual_approval_granted': False,
        }
        recipe_path = recipes / (filename + '.json')
        write_json(recipe_path, recipe)
        outputs, receipt = compiler.plan(PROJECT, recipe_path)
        expected = recipe['output_path']
        if set(outputs) != {expected}:
            raise RuntimeError('Unexpected compiler outputs for ' + suffix)
        if outputs[expected] != source_path.read_bytes():
            # Pillow compression can differ from the SDK encoder, while decoded
            # pixels must be identical. Store the SDK bytes as the final candidate.
            import io
            if Image.open(io.BytesIO(outputs[expected])).tobytes() != output.tobytes():
                raise RuntimeError('Generic compiler changed decoded native pixels')
        compiled = BASE / 'compiled-candidate-v3' / (filename + '.png')
        compiled.parent.mkdir(exist_ok=True)
        compiled.write_bytes(outputs[expected])
        records.append({'suffix': suffix, 'dimensions': list(SIZES[suffix]),
                        'source': rel(source_path), 'source_sha256': sha(source_path),
                        'compiled_candidate': rel(compiled), 'compiled_sha256': sha(compiled),
                        'recipe': rel(recipe_path), 'recipe_sha256': sha(recipe_path),
                        'master': rel(master_path), 'master_sha256': sha(master_path),
                        'alpha_bbox': list(output.getchannel('A').getbbox()),
                        'compiler_receipt': receipt})

    emit('BACK', 'background', fit='cover')
    for suffix, family in [('ARCH', 'arch'), ('WA2', 'static2'), ('WA5', 'static5'), ('TPWL', 'topwall')]:
        emit(suffix, family)
    for stem, family in [('WA1', 'wall1'), ('WA3', 'wall3'), ('WA4', 'wall4'), ('WA6', 'wall6')]:
        _, image = get_master(family)
        boundaries = [round(n * image.width / 3) for n in range(4)]
        width = max(b - a for a, b in zip(boundaries, boundaries[1:]))
        for n in range(3):
            emit(stem + str(n + 1), family,
                 [boundaries[n], 0, boundaries[n + 1], image.height], (width, image.height))
    _, image = get_master('keep')
    boundaries = [round(n * image.width / 3) for n in range(4)]
    common = (max(b - a for a, b in zip(boundaries, boundaries[1:])), image.height)
    for n, suffix in enumerate(('MAN1', 'MAN2', 'MANC')):
        # The cap is isolated to the top of its painted cohort cell. The ruined
        # keep extends across the lower grid boundary and must never leak into
        # the cap overlay's otherwise empty lower canvas.
        emit(suffix, 'keep', [boundaries[n], 0, boundaries[n + 1], 350 if suffix == 'MANC' else image.height], common,
             anchor='top', offset=(0, 0 if suffix != 'MANC' else 16))
    for suffix, box, offset in [
        ('TW11', [150, 140, 830, 740], (24, 14)),
        ('TW12', [150, 750, 830, 1350], (24, 14)),
        ('TW1C', [150, 1320, 830, 1625], (24, 32)),
    ]:
        emit(suffix, 'tower1', box, scale=0.07, offset=offset)
    for suffix, box, offset in [
        ('TW21', [140, 50, 550, 1024], (0, 0)),
        ('TW22', [620, 50, 1030, 1024], (0, 0)),
        ('TW2C', [1120, 50, 1530, 1024], (20, 20)),
    ]:
        emit(suffix, 'tower2', box, scale=0.12, offset=offset)
    _, image = get_master('drawbridge')
    bounds_x, bounds_y = [0, image.width // 2, image.width], [0, image.height // 2, image.height]
    common = (max(bounds_x[1], bounds_x[2] - bounds_x[1]),
              max(bounds_y[1], bounds_y[2] - bounds_y[1]))
    for n, suffix in enumerate(('DRW1', 'DRW2', 'DRW3', 'DRWC')):
        c, r = n % 2, n // 2
        emit(suffix, 'drawbridge', [bounds_x[c], bounds_y[r], bounds_x[c + 1], bounds_y[r + 1]], common)
    _, image = get_master('moat')
    scale = min(213 / image.width, 466 / image.height)
    emit('MOAT', 'moat', scale=scale, offset=(0, 0))
    # Native bank origin is seven pixels left and ten pixels above moat origin.
    # Use the same painted path's scale and compensate those origin differences.
    emit('MLIP', 'bank', scale=scale, offset=(7, 10))
    emit('towerLarge', 'tower-portrait', fit='cover')
    emit('towerSmall', 'tower-portrait', [200, 10, 1194, 1004], fit='cover')
    if {r['suffix'] for r in records} != set(SIZES) or len(records) != 34:
        raise RuntimeError('Required native siege suffix closure failed')
    write_json(REPORT / 'candidate-conversion-v3.json', {
        'status': 'authored configuration', 'production_status': 'painted-master-complete-unapproved',
        'scope': 'Own painted Piltover siege candidate; generic SDK plan() executed without staging.',
        'count': len(records), 'native_siege_surfaces': 32, 'tower_portraits': 2,
        'visual_approval_granted': False, 'runtime_verified': False,
        'original_reference_pixels_bundled': False, 'blender_or_3d_production_used': False,
        'records': records,
    })
    return records


def previews(records):
    images = {r['suffix']: Image.open(PROJECT / r['compiled_candidate']).convert('RGBA') for r in records}
    content = json.loads((PROJECT / 'content/factions.json').read_text())['piltover']['town']['siege']
    origins = {'TPWL': content['static']['background'], 'ARCH': content['gate']['arch'],
               'WA2': content['static']['bottom'], 'WA5': content['static']['top'],
               'MOAT': content['moat']['moat'], 'MLIP': content['moat']['bank']}
    for stem, key in [('WA1', 'bottom'), ('WA3', 'bottomMid'), ('WA4', 'upperMid'), ('WA6', 'upper')]:
        for state in (1, 2, 3):
            origins[stem + str(state)] = content['walls'][key]
    for stem, key in [('MAN', 'keep'), ('TW1', 'bottom'), ('TW2', 'top')]:
        for state in ('1', '2', 'C'):
            origins[stem + state] = content['towers'][key]['tower' if state != 'C' else 'battlement']
    for state in ('1', '2', '3', 'C'):
        origins['DRW' + state] = content['gate']['gate']
    for state in (1, 2, 3):
        canvas = images['BACK'].copy()
        order = ['TPWL', 'MOAT', 'MLIP', 'TW2' + ('1' if state == 1 else '2'),
                 'WA6' + str(state), 'WA5', 'WA4' + str(state),
                 'DRW' + ('2' if state == 1 else '3'), 'ARCH',
                 'WA3' + str(state), 'WA2', 'WA1' + str(state),
                 'MAN' + ('1' if state == 1 else '2'), 'TW1' + ('1' if state == 1 else '2')]
        if state == 1:
            order += ['MANC', 'TW1C', 'TW2C', 'DRWC']
        for suffix in order:
            at = origins[suffix]
            canvas.alpha_composite(images[suffix], (at['x'], at['y']))
        canvas.save(REPORT / f'native-composite-state{state}-v3.png')
        if state == 1:
            closed = images['BACK'].copy()
            for suffix in order:
                if suffix.startswith('DRW'):
                    continue
                at = origins[suffix]
                closed.alpha_composite(images[suffix], (at['x'], at['y']))
            closed.save(REPORT / 'native-composite-closed-v3.png')
    sheet = Image.new('RGBA', (800, 5 * 320), '#42413e')
    draw = ImageDraw.Draw(sheet)
    for n, (suffix, image) in enumerate((s, im) for s, im in sorted(images.items()) if s != 'BACK'):
        col, row = n % 8, n // 8
        tile = image.copy()
        tile.thumbnail((96, 285))
        sheet.alpha_composite(tile, (col * 100 + (100 - tile.width) // 2, row * 320 + 25))
        draw.text((col * 100 + 3, row * 320 + 5), suffix if suffix.startswith('tower') else 'SGPI' + suffix, fill='white')
    sheet.save(REPORT / 'native-34-contact-v3.png')


if __name__ == '__main__':
    REPORT.mkdir(parents=True, exist_ok=True)
    records = assemble()
    previews(records)
    print(json.dumps({'candidate_count': len(records), 'sdk_plan_executed': True,
                      'runtime_verified': False, 'visual_approval_granted': False,
                      'receipt': str(REPORT / 'candidate-conversion-v3.json')}))
