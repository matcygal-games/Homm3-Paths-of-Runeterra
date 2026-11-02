"""Project complete battle canvases into the actual ordinary-MONSTER source tile.

No pose fitting or source crop: fixed affine projection, actor reflection about
the battle ground pivot, and independently checked transparent export margins.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import shutil

from PIL import Image, ImageDraw

from ionia_creature_art import PROJECT, UNITS, PREFIX, sha, rel, write

CANVAS = (96, 64)
ANCHOR = (80, 60)
MAP_SCALE = .5
ATTACK_SCALE = .28
VERSION = 'adventure-anchor-v1'
HISTORY = PROJECT / 'assets/source/creatures/history/map-anchor-before-v1-20261022'
REPORT = PROJECT / 'build/reports/creature-art/20261022-v6-adventure-anchor'


def affine(pivot, scale, mirrored=False, anchor=ANCHOR):
    """Pillow inverse mapping; source pivot maps exactly to native anchor."""
    sx = -scale if mirrored else scale
    return (1 / sx, 0, pivot[0] - anchor[0] / sx,
            0, 1 / scale, pivot[1] - anchor[1] / scale)


def project(image, pivot, scale, mirrored=False, canvas=CANVAS, anchor=ANCHOR):
    return image.convert('RGBA').transform(canvas, Image.Transform.AFFINE,
        affine(pivot, scale, mirrored, anchor), Image.Resampling.BICUBIC)


def bounds(image, threshold=8):
    return image.getchannel('A').point(lambda a: 255 if a >= threshold else 0).getbbox()


def measure(image, pivot, scale, mirrored=False):
    """Render into oversized audit canvas, measure every excluded alpha pixel."""
    pad = 128
    expanded = project(image, pivot, scale, mirrored,
        (CANVAS[0] + pad * 2, CANVAS[1] + pad * 2),
        (ANCHOR[0] + pad, ANCHOR[1] + pad))
    a = expanded.getchannel('A')
    total = sum(v >= 8 for v in a.getdata())
    inside = a.crop((pad, pad, pad + CANVAS[0], pad + CANVAS[1]))
    b = bounds(expanded)
    return {'source_alpha8_bbox': bounds(image),
        'projected_alpha8_bbox_unclipped': [v - pad for v in b],
        'opaque_pixels_outside_canvas': total - sum(v >= 8 for v in inside.getdata()),
        'projected_opaque_pixels': total}


def recipe_paths():
    return sorted((PROJECT / 'assets/recipes/creatures').glob('*.json'))


def protected_hashes():
    """All existing mesh-v8 files except explicitly owned old map/attack sources."""
    paths = [PROJECT / 'design/projectile-registration.json']
    paths += [p for p in recipe_paths()
              if not any(p.name.endswith('-' + role + '.json')
                         for role in ('map', 'attackLeft', 'attackRight'))]
    for unit in UNITS:
        for path in (PROJECT / f'assets/source/creatures/{unit}/mesh-v8').rglob('*'):
            if path.is_file() and VERSION not in path.parts:
                paths.append(path)
    return {rel(p): sha(p) for p in sorted(paths)}


def preserve():
    target = HISTORY / 'snapshot.json'
    if target.exists():
        return json.loads(target.read_text(encoding='utf-8'))
    records = []
    for path in recipe_paths():
        if not any(path.name.endswith('-' + role + '.json')
                   for role in ('map', 'attackLeft', 'attackRight')):
            continue
        recipe = json.loads(path.read_text(encoding='utf-8'))
        sources = ([PROJECT / f['source'] for g in recipe['groups'] for f in g['frames']]
                   if 'groups' in recipe else [PROJECT / recipe['source']])
        for source in [path, *sources]:
            dest = HISTORY / rel(source)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
            records.append({'source': rel(source), 'source_sha256': sha(source),
                            'preserved': rel(dest), 'preserved_sha256': sha(dest)})
    for source in [Path(__file__), PROJECT / 'scripts/ionia_creature_art.py',
                   PROJECT / 'assets/source/creatures/production-contract.json']:
        dest = HISTORY / rel(source)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        records.append({'source': rel(source), 'source_sha256': sha(source),
                        'preserved': rel(dest), 'preserved_sha256': sha(dest)})
    data = {'status': 'authored configuration', 'records': records,
            'protected': protected_hashes()}
    write(target, data)
    return data


def register_unit(unit, common=None):
    family = UNITS[unit][0]
    pivot = (218 if family == 'warden' else 197, 266)
    source = PROJECT / f'assets/source/creatures/{unit}/mesh-v8/native'
    target = source.parent / VERSION
    target.mkdir(exist_ok=True)
    recipes = PROJECT / 'assets/recipes/creatures'
    rows = []
    def prepare(name, image, scale, mirrored=False):
        proof = measure(image, pivot, scale, mirrored)
        if proof['opaque_pixels_outside_canvas']:
            raise ValueError(f'{unit} {name} clips: {proof}')
        out = project(image, pivot, scale, mirrored)
        path = target / (name + '.png')
        out.save(path, format='PNG', compress_level=9)
        rows.append({'unit': unit, 'role': name, 'scale': scale,
            'battle_pivot': list(pivot), 'anchor': list(ANCHOR),
            'actor_mirrored_about_pivot': mirrored, 'source': rel(path),
            'sha256': sha(path), 'actual_alpha8_bbox': bounds(out), **proof})
        return {'source': rel(path), 'sha256': sha(path),
                'source_sha256': sha(path), 'source_canvas': list(CANVAS)}
    path = recipes / f'{unit}-map.json'
    recipe = json.loads(path.read_text(encoding='utf-8'))
    frames = [prepare(f'map-f{i:03}', Image.open(source / f'g00-f{i:03}.png'), MAP_SCALE)
              for i in range(6)]
    recipe.update({'canvas': list(CANVAS), 'pivot': dict(zip(('x', 'y'), ANCHOR)),
        'groups': [{'group': 0, 'frames': frames}]})
    write(path, recipe)
    attack = Image.open(source / 'g12-f003.png').convert('RGBA')
    for role, mirrored in [('attackRight', False), ('attackLeft', True)]:
        path = recipes / f'{unit}-{role}.json'
        recipe = json.loads(path.read_text(encoding='utf-8'))
        recipe.update(prepare(role, attack, ATTACK_SCALE, mirrored))
        recipe.update({'size': list(CANVAS), 'fit': 'contain'})
        write(path, recipe)
    write(target / 'projection.json', {'unit': unit, 'version': VERSION,
        'status': 'authored configuration', 'native_playback': 'not_run',
        'source_battle_canvas': [450, 400], 'source_crop': None,
        'per_frame_bbox_refit': False, 'map_scale': MAP_SCALE,
        'attack_scale': ATTACK_SCALE, 'canvas': list(CANVAS),
        'native_anchor': list(ANCHOR), 'frames': rows})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--register', action='store_true')
    args = parser.parse_args()
    if args.register:
        snapshot = preserve()
        rows = [row for unit in UNITS for row in register_unit(unit)]
        unchanged = {p: sha(PROJECT / p) == h for p, h in snapshot['protected'].items()}
        if not all(unchanged.values()):
            raise ValueError('Protected source changed: ' + repr([p for p, ok in unchanged.items() if not ok]))
        REPORT.mkdir(parents=True, exist_ok=True)
        write(REPORT / 'placement-proof.json', {'status': 'authored configuration',
            'native_playback': 'not_run', 'visual_approval_granted': False,
            'units': len(UNITS), 'frames': rows,
            'protected_files_checked': len(unchanged), 'protected_files_changed': [],
            'history': rel(HISTORY / 'snapshot.json')})
        # Exact exported pixels and anchor-tile boundaries, no display scaling.
        sheet = Image.new('RGB', (96 * 8, 84 * len(UNITS)), (39, 48, 37))
        draw = ImageDraw.Draw(sheet)
        for i, unit in enumerate(UNITS):
            for j, row in enumerate(r for r in rows if r['unit'] == unit):
                im = Image.open(PROJECT / row['source'])
                x, y = j * 96, i * 84 + 18
                sheet.paste(im, (x, y), im)
                draw.rectangle((x + 64, y + 32, x + 95, y + 63), outline=(104, 118, 80))
                draw.line((x + 77, y + 60, x + 83, y + 60), fill=(230, 185, 80))
                draw.text((x + 2, y - 15), unit if j == 0 else row['role'], fill=(225, 220, 194))
        sheet.save(REPORT / 'native-all-map-and-attack-poses.png')
        print(f'{len(rows)} projections; {len(unchanged)} protected files unchanged')


if __name__ == '__main__':
    main()
