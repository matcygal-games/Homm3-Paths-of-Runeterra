"""Measured painted-map conversion. No artwork or new actor geometry is drawn.

The only painted-pixel change clears authorized red edge matte alpha; all RGB
channels remain unchanged. Masks and diagnostic grids are technical artifacts.
"""
from __future__ import annotations
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

HERE = Path(__file__).resolve().parent
PROJECT = next(path for path in HERE.parents if path.name == 'runeterra-piltover')
WORKSPACE = PROJECT.parent
sys.path.insert(0, str(WORKSPACE / 'scripts'))
from faction_art_compile import create_compiler


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rel(path):
    return Path(path).relative_to(PROJECT).as_posix()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def chunks(path):
    raw = Path(path).read_bytes()
    offset, names = 8, []
    while offset < len(raw):
        size = struct.unpack('>I', raw[offset:offset + 4])[0]
        names.append(raw[offset + 4:offset + 8].decode('ascii'))
        offset += size + 12
    return names


def portable_copy(source, destination):
    with Image.open(source) as opened:
        original = opened.convert('RGBA')
        original.load()
    clean_container = Image.frombytes('RGBA', original.size, original.tobytes())
    destination.parent.mkdir(parents=True, exist_ok=True)
    clean_container.save(destination, compress_level=9)
    if Image.open(destination).tobytes() != original.tobytes():
        raise ValueError('Metadata-only portable copy changed RGBA pixels')
    return clean_container, {
        'original': rel(source), 'original_sha256': sha(source),
        'portable_copy': rel(destination), 'portable_sha256': sha(destination),
        'decoded_rgba_unchanged': True,
        'original_png_chunks': chunks(source), 'portable_png_chunks': chunks(destination),
    }


def clear_red_edge(image):
    before = np.array(image)
    after = before.copy()
    rgb = after[:, :, :3].astype(np.int32)
    red = ((rgb[:, :, 0] >= 180) & (rgb[:, :, 1] <= 60) & (rgb[:, :, 2] <= 60)
           & (rgb[:, :, 0] > 2 * rgb[:, :, 1]) & (rgb[:, :, 0] > 2 * rgb[:, :, 2]))
    passes = []
    for _ in range(4):
        zero = Image.fromarray((after[:, :, 3] == 0).astype('uint8') * 255)
        adjacent = np.asarray(zero.filter(ImageFilter.MaxFilter(3))) > 0
        selected = red & (after[:, :, 3] > 0) & adjacent
        count = int(selected.sum())
        passes.append(count)
        after[selected, 3] = 0
        if not count:
            break
    if not np.array_equal(before[:, :, :3], after[:, :, :3]):
        raise ValueError('Edge cleanup altered RGB')
    return Image.fromarray(after), {'alpha_pixels_cleared': sum(passes), 'passes': passes,
                                    'all_rgb_byte_identical': True,
                                    'interior_rgba_changed': False}


def owner_overlay(image, region):
    source = np.array(image)
    rgb = source[:, :, :3].astype(np.float32)
    bounds = np.zeros(source.shape[:2], dtype=bool)
    x0, y0, x1, y1 = region
    bounds[y0:y1, x0:x1] = True
    selected = (bounds & (source[:, :, 3] > 16) & (rgb[:, :, 2] >= 35)
                & (rgb[:, :, 2] > 1.25 * rgb[:, :, 0])
                & (rgb[:, :, 2] > 1.08 * rgb[:, :, 1])
                & (rgb[:, :, 0] < 130) & (rgb[:, :, 1] < 155))
    overlay = np.zeros_like(source)
    gray = np.rint(np.clip(1.5 * rgb[:, :, 2] + 32, 64, 245)).astype('uint8')
    for channel in range(3):
        overlay[:, :, channel] = np.where(selected, gray, 0)
    overlay[:, :, 3] = np.where(selected, source[:, :, 3], 0)
    if not selected.any():
        raise ValueError('Measured cloth region contains no selected pixels')
    return Image.fromarray(overlay), {'source_region': region,
                                     'painted_cloth_pixels_selected': int(selected.sum()),
                                     'outside_region_pixels_selected': 0,
                                     'gold_marks_preserved': True}


def affine_native(image, scale, root, target, canvas):
    # Inverse affine transform performs exactly the declared scale and root
    # translation, with no per-state bounding-box fit or independent zoom.
    dx, dy = target[0] - root[0] * scale, target[1] - root[1] * scale
    result = image.transform(tuple(canvas), Image.Transform.AFFINE,
                             (1 / scale, 0, -dx / scale, 0, 1 / scale, -dy / scale),
                             resample=Image.Resampling.BICUBIC)
    source_bbox = image.getchannel('A').getbbox()
    projected_bbox = [source_bbox[0] * scale + dx, source_bbox[1] * scale + dy,
                      source_bbox[2] * scale + dx, source_bbox[3] * scale + dy]
    return result, {'scale': scale, 'translation': [dx, dy],
                    'source_alpha_bbox': list(source_bbox), 'projected_alpha_bbox': projected_bbox,
                    'full_alpha_canvas_fits': projected_bbox[0] >= 0 and projected_bbox[1] >= 0
                    and projected_bbox[2] <= canvas[0] and projected_bbox[3] <= canvas[1]}


def generation(master, prompt):
    return {'image_generation_used': True, 'provider': 'OpenAI built-in imagegen',
            'model': 'Exact model identifier not exposed by tool',
            'prompt': prompt.read_text(encoding='utf-8'),
            'painted_master': rel(master), 'painted_master_sha256': sha(master)}


def main():
    plan_path = HERE / 'root-plan-v1.json'
    plan = json.loads(plan_path.read_text())
    native, recipes = HERE / 'native', HERE / 'recipes'
    for directory in (native, recipes, native / 'portable', native / 'frames',
                      native / 'masks', native / 'icons', native / 'compiled', native / 'diagnostics'):
        directory.mkdir(parents=True, exist_ok=True)
    compiler = create_compiler('piltover')
    map_records, recipe_records, images, overlays = [], [], {}, {}
    production_common = [plan_path, Path(__file__)]

    def compile_recipe(name, recipe):
        path = recipes / name
        dump(path, recipe)
        outputs, receipt = compiler.plan(PROJECT, path)
        for output, data in outputs.items():
            destination = native / 'compiled' / output
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        recipe_records.append({'recipe': rel(path), 'recipe_sha256': sha(path),
                               'compiler_receipt': receipt,
                               'outputs': {name: hashlib.sha256(raw).hexdigest() for name, raw in outputs.items()}})

    for key, state in plan['states'].items():
        source = HERE / state['master']
        if sha(source) != state['sha256']:
            raise ValueError('Raw selected master changed: ' + key)
        portable, portability = portable_copy(source, native / 'portable' / (key + '-original.png'))
        clean, cleanup = clear_red_edge(portable)
        cleaned_path = native / 'portable' / (key + '-clean.png')
        clean.save(cleaned_path, compress_level=9)
        flag, flag_info = owner_overlay(clean, state['primary_owner_flag_region'])
        flag_master = native / 'masks' / (key + '-flag-source.png')
        flag.save(flag_master, compress_level=9)
        kwargs = {'scale': plan['common_uniform_scale'], 'root': state['walkup_root_source'],
                  'target': plan['native_walkup_anchor'], 'canvas': plan['canvas']}
        output, transform = affine_native(clean, **kwargs)
        overlay, _ = affine_native(flag, **kwargs)
        if not transform['full_alpha_canvas_fits']:
            raise ValueError('Full source alpha/shadow would be clipped: ' + key)
        frame = native / 'frames' / (key + '.png')
        overlay_path = native / 'masks' / (key + '-OVERLAY.png')
        output.save(frame, compress_level=9)
        overlay.save(overlay_path, compress_level=9)
        images[key], overlays[key] = output, overlay
        dependencies = production_common + [source, cleaned_path, HERE / state['prompt'], flag_master]
        recipe = {'recipe_type': 'vcmi_animation', 'production_status': 'painted-master-complete-unapproved',
                  'output_path': f'Content/Sprites/runeterra/piltover/town/map/{key}.json',
                  'canvas': plan['canvas'], 'pivot': dict(zip(('x', 'y'), plan['native_walkup_anchor'])),
                  'generateShadow': 1, 'generateOverlay': 0,
                  'groups': [{'group': 0, 'frames': [{'frame': 0, 'source': rel(frame),
                     'source_sha256': sha(frame), 'source_canvas': plan['canvas'],
                     'overlay_source': rel(overlay_path), 'overlay_sha256': sha(overlay_path)}]}],
                  'generation': generation(cleaned_path, HERE / state['prompt']),
                  'production_inputs': [{'path': rel(p), 'sha256': sha(p)} for p in dependencies],
                  'animation_scope': 'One painted static adventure-map pose, not creature motion',
                  'visual_approval_granted': False}
        compile_recipe(key + '.json', recipe)
        map_records.append({'state': key, 'portable_master': portability, 'alpha_cleanup': cleanup,
                            'clean_master': rel(cleaned_path), 'clean_master_sha256': sha(cleaned_path),
                            'frame': rel(frame), 'frame_sha256': sha(frame),
                            'owner_overlay': rel(overlay_path), 'owner_overlay_sha256': sha(overlay_path),
                            'cloth_mask': flag_info, 'transform': transform,
                            'native_walkup_anchor': plan['native_walkup_anchor'],
                            'lowest_stair_source': state['lowest_stair_source']})

    background_source = PROJECT / plan['icons']['background']
    backdrop, backdrop_portability = portable_copy(background_source, native / 'portable' / 'icon-landscape.png')
    marker_source = HERE / plan['icons']['built_status_source']
    if sha(marker_source) != plan['icons']['built_status_source_sha256']:
        raise ValueError('Own construction-status glyph changed')
    marker, marker_portability = portable_copy(marker_source, native / 'portable' / 'status-x.png')
    marker = marker.crop(tuple(plan['icons']['status_fixed_crop']))
    icon_records = []
    for kind, state in plan['icons']['source_states'].items():
        for size_name, size, marker_size in [('large', (58, 64), (12, 12)), ('small', (48, 32), (8, 8))]:
            # All icons use actual own painted scenery, not a procedural fill.
            icon = ImageOps.fit(backdrop, size, method=Image.Resampling.LANCZOS, centering=(.5, .27))
            scale = min(size[0] / images[state].width, size[1] / images[state].height)
            town_size = tuple(round(n * scale) for n in images[state].size)
            town = images[state].resize(town_size, Image.Resampling.LANCZOS)
            icon.alpha_composite(town, ((size[0] - town.width) // 2, size[1] - town.height))
            marker_native = marker.resize(marker_size, Image.Resampling.LANCZOS)
            marker_at = (size[0] - marker_size[0] - 1, size[1] - marker_size[1] - 1)
            for built in (False, True):
                output = icon.copy()
                if built:
                    output.alpha_composite(marker_native, marker_at)
                status = 'built' if built else 'normal'
                filename = f'{kind}_{status}_{size_name}.png'
                destination = native / 'icons' / filename
                output.save(destination, compress_level=9)
                chosen = plan['states'][state]
                recipe = {'recipe_type': 'raster', 'production_status': 'painted-master-complete-unapproved',
                          'output_path': 'Content/Sprites/runeterra/piltover/town/icons/' + filename,
                          'canvas': list(size), 'source': rel(destination), 'source_sha256': sha(destination),
                          'source_canvas': list(size), 'fit': 'exact',
                          'generation': generation(native / 'portable' / (state + '-clean.png'), HERE / chosen['prompt']),
                          'production_inputs': [{'path': rel(p), 'sha256': sha(p)} for p in production_common +
                              [HERE / chosen['master'], background_source, marker_source,
                               HERE / plan['icons']['built_status_prompt']]],
                          'status_marker': {'painted_master': rel(marker_source), 'sha256': sha(marker_source),
                                            'source_crop': plan['icons']['status_fixed_crop'],
                                            'dimensions': list(marker_size), 'position': list(marker_at),
                                            'enabled': built}, 'visual_approval_granted': False}
                compile_recipe(filename[:-4] + '.json', recipe)
                icon_records.append({'resource': filename, 'dimensions': list(size), 'source': rel(destination),
                                     'sha256': sha(destination), 'construction_used_marker': built})
            normal = np.array(Image.open(native / 'icons' / f'{kind}_normal_{size_name}.png'))
            built = np.array(Image.open(native / 'icons' / f'{kind}_built_{size_name}.png'))
            changed = np.any(normal != built, axis=2)
            x, y = marker_at
            outside = changed.copy()
            outside[y:y + marker_size[1], x:x + marker_size[0]] = False
            if outside.any() or not changed.any():
                raise ValueError('Construction status must change only the marker region')

    diagnostics(native, plan, images, overlays)
    spec = importlib.util.spec_from_file_location('piltover_map_privacy_guard', PROJECT / 'scripts/source_export_guard.py')
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    own_files = {PROJECT.name + '/' + rel(path): path.read_bytes()
                 for directory in (native, recipes) for path in directory.rglob('*') if path.is_file()}
    own_files[PROJECT.name + '/' + rel(plan_path)] = plan_path.read_bytes()
    own_files[PROJECT.name + '/' + rel(Path(__file__))] = Path(__file__).read_bytes()
    privacy = guard.check(PROJECT, files=own_files)
    output_count = sum(len(row['outputs']) for row in recipe_records)
    result = {'status': 'authored configuration', 'ok': privacy['source_export_eligible'],
              'native_maps': 5, 'town_icons': 8, 'recipes_executed': len(recipe_records),
              'compiler_outputs': output_count, 'common_scale': plan['common_uniform_scale'],
              'native_walkup_anchor': plan['native_walkup_anchor'], 'map_records': map_records,
              'icon_records': icon_records, 'compiler_records': recipe_records,
              'backdrop_portability': backdrop_portability, 'status_marker_portability': marker_portability,
              'privacy_admission': privacy, 'runtime_verified': False,
              'visual_approval_granted': False, 'release_accepted': False,
              'limitations': ['Native footprint, pathfinding and all ownership colors unobserved.',
                             'Native generated shadow may overlap painted contact shade; inspect current build.',
                             '2D mask/root diagnostics are technical inspections, not native screenshots.']}
    dump(native / 'conversion-v1.json', result)
    print(json.dumps({k: result[k] for k in ('ok', 'native_maps', 'town_icons', 'recipes_executed',
                                            'compiler_outputs', 'runtime_verified', 'visual_approval_granted')}))


def diagnostics(native, plan, images, overlays):
    states = list(plan['states'])
    contact = Image.new('RGBA', (len(states) * 192, 200), '#706f60')
    label = ImageDraw.Draw(contact)
    for n, key in enumerate(states):
        contact.alpha_composite(images[key], (n * 192, 25))
        label.text((n * 192 + 4, 5), key, fill='white')
        tile = Image.new('RGBA', (192, 160), '#706f60')
        tile.alpha_composite(images[key])
        grid = Image.new('RGBA', (192, 160))
        draw = ImageDraw.Draw(grid)
        for row, line in enumerate(plan['native_mask']):
            for col, symbol in enumerate(line):
                color = {'B': (240, 50, 30, 60), 'A': (20, 240, 240, 90), 'V': (230, 220, 60, 20)}[symbol]
                box = (col * 32, row * 32, (col + 1) * 32 - 1, (row + 1) * 32 - 1)
                draw.rectangle(box, fill=color, outline=(220, 220, 220, 120))
                draw.text((col * 32 + 2, row * 32 + 2), symbol, fill='white')
        root = plan['native_walkup_anchor']
        draw.line((root[0] - 5, root[1], root[0] + 5, root[1]), fill=(255, 255, 255, 255))
        draw.line((root[0], root[1] - 5, root[0], root[1] + 5), fill=(255, 255, 255, 255))
        tile.alpha_composite(grid)
        tile.resize((768, 640), Image.Resampling.NEAREST).save(native / 'diagnostics' / (key + '-mask-root-x4.png'))
        # Demonstrate bounded mask tint locally. These are explanatory composites,
        # not a claim that the native owner palette has been executed.
        colors = [(220, 35, 35), (40, 90, 220), (35, 170, 60)]
        tint_board = Image.new('RGBA', (3 * 192, 160), '#706f60')
        for col, color in enumerate(colors):
            example = images[key].copy()
            values = np.array(overlays[key])
            for channel in range(3):
                values[:, :, channel] = np.rint(values[:, :, channel].astype(float) * color[channel] / 255).astype('uint8')
            example.alpha_composite(Image.fromarray(values))
            tint_board.alpha_composite(example, (col * 192, 0))
        tint_board.save(native / 'diagnostics' / (key + '-owner-mask-example.png'))
    contact.save(native / 'diagnostics' / 'all-five-native-contact.png')
    icons = sorted((native / 'icons').glob('*.png'))
    board = Image.new('RGBA', (8 * 75, 100), '#5b584e')
    draw = ImageDraw.Draw(board)
    for n, path in enumerate(icons):
        image = Image.open(path).convert('RGBA')
        board.alpha_composite(image, (n * 75, 20))
        draw.text((n * 75 + 1, 2), path.stem.replace('_', ' ')[:13], fill='white')
    board.save(native / 'diagnostics' / 'eight-town-icons-native.png')


if __name__ == '__main__':
    main()
