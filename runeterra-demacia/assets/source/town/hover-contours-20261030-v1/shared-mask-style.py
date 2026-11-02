"""Produce review-only native town hover candidates from pinned current layers.

This tool never changes selected art, click masks, recipes or stages.  Alpha is
only an initial proposal: scenery baked into a layer needs an independently
traced architectural mask and pixel review before integration.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

SIZE = (800, 374)
GOLD = (225, 190, 80, 255)
SHADOW = (38, 29, 15, 208)
REGIONS = ('demacia', 'noxus', 'freljord', 'zaun', 'bandlecity', 'ionia',
           'piltover', 'ixtal', 'bilgewater', 'targon', 'shurima')
STYLE = {'gold': list(GOLD), 'shadow': list(SHADOW),
         'gold_radius_pixels': 1, 'outer_shadow_radius_pixels': 2,
         'alpha_threshold': 128, 'connectivity': 8,
         'basis': 'Native one-pixel gold edge with one further pixel of dark support; no interior tint.'}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def load(path):
    with Image.open(path) as image:
        if image.size != SIZE or image.mode != 'RGBA':
            raise ValueError('Expected native RGBA building canvas: ' + str(path))
        return image.copy()


def binary(alpha):
    return alpha.point(lambda value: 255 if value >= 128 else 0)


def border_from_mask(mask):
    if mask.mode != 'L' or mask.size != SIZE or any(mask.histogram()[1:255]):
        raise ValueError('Architectural silhouette must be binary native L mask')
    if not mask.getbbox() or mask.getextrema() == (255, 255):
        raise ValueError('Architectural silhouette must be a nonempty cutout')
    near = mask.filter(ImageFilter.MaxFilter(3))
    far = mask.filter(ImageFilter.MaxFilter(5))
    gold = ImageChops.subtract(near, mask)
    shadow = ImageChops.subtract(far, near)
    result = Image.new('RGBA', SIZE)
    support = Image.new('RGBA', SIZE, SHADOW)
    support.putalpha(shadow.point(lambda value: SHADOW[3] if value else 0))
    result.alpha_composite(support)
    edge = Image.new('RGBA', SIZE, GOLD)
    edge.putalpha(gold)
    result.alpha_composite(edge)
    return result


def safe_input(project, name):
    path = (project / name).resolve()
    if not path.is_relative_to(project.resolve()) or not path.is_file():
        raise ValueError('Missing own project source: ' + str(path))
    return path


def recipe_index(project):
    result = {}
    def add(name, path, value):
        if name in result:
            raise ValueError('Ambiguous output recipes: ' + name + ' (' + str(result[name][0]) + ', ' + str(path) + ')')
        result[name] = (path, value)
    for path in sorted((project / 'assets/recipes').rglob('*.json')):
        value = read(path)
        if value.get('output_path'):
            add(value['output_path'], path, value)
        for kind in ('area', 'border'):
            if value.get('output_' + kind):
                add(value['output_' + kind], path, value)
    return result


def render_polygon_masks(root, traces_path, output):
    """Reproduce finite hand-traced contour candidates, never edit paintings."""
    root = root.resolve(); output = output.resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError('Use a new contour candidate directory')
    if not output.is_relative_to(root):
        raise ValueError('Contour candidates must stay within the workspace')
    output.mkdir(parents=True, exist_ok=True)
    selections = {}
    for selector, trace in read(traces_path).items():
        parts = selector.split('/')
        region = trace.get('region', parts[0])
        building = trace.get('building', parts[1] if len(parts) == 2 else 'castle')
        if region not in REGIONS:
            raise ValueError('Unknown contour region')
        if not building or not building.isalnum():
            raise ValueError('Unsafe contour building name')
        source = safe_input(root, trace['source']['path'])
        if digest(source) != trace['source']['sha256']:
            raise ValueError('Selected contour layer changed')
        points = trace.get('points_native')
        polygons = trace.get('polygons_native')
        if polygons is not None and points is not None:
            raise ValueError('Choose points_native or polygons_native, not both')
        if polygons is None and points is not None:
            polygons = [points]
        base = binary(load(source).getchannel('A'))
        if polygons is None:
            if trace.get('mode') != 'alpha128-silhouette-for-review':
                raise ValueError('Missing architectural contour without explicit review-only alpha mode')
            mask = base.copy()
        else:
            if not polygons:
                raise ValueError('Nonempty contour polygon list required')
            mask = Image.new('L', SIZE)
            for polygon in polygons:
                if (len(polygon) < 3 or any(len(p) != 2 or any(type(v) is not int for v in p)
                                          or not 0 <= p[0] < 800 or not 0 <= p[1] < 374 for p in polygon)):
                    raise ValueError('Contour points must be native integer coordinates')
                ImageDraw.Draw(mask).polygon([tuple(p) for p in polygon], fill=255)
            mask = ImageChops.multiply(mask, base)
        for box in trace.get('exclusions_native', []):
            if (len(box) != 4 or any(type(v) is not int for v in box)
                    or not 0 <= box[0] < box[2] <= 800 or not 0 <= box[1] < box[3] <= 374):
                raise ValueError('Exclusions require native integer exclusive bounds')
            ImageDraw.Draw(mask).rectangle((box[0], box[1], box[2]-1, box[3]-1), fill=0)
        border_from_mask(mask)  # Reject empty/full-canvas or malformed tracing.
        path = output / (region + '-' + building + '-architecture-mask.png')
        mask.save(path)
        selections[region + '/' + building] = {'path': path.relative_to(root).as_posix(), 'sha256': digest(path),
                                              'kind': 'manually-annotated-contour' if polygons else 'alpha128-silhouette-for-review'}
    write(output / 'mask-selections.json', selections)
    write(output / 'reproduction.json', {'status': 'design proposal', 'visual_approval_granted': False,
          'traces': {'path': traces_path.resolve().relative_to(root).as_posix(), 'sha256': digest(traces_path)},
          'producer': {'path': Path(__file__).resolve().relative_to(root).as_posix(), 'sha256': digest(__file__)},
          'masks': selections})
    return selections


def candidate(root, output, regions=REGIONS, mask_selections=None):
    root = root.resolve()
    output = output.resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError('Use a new candidate directory; historical candidates are immutable')
    output.mkdir(parents=True, exist_ok=True)
    selections = mask_selections or {}
    rows = []
    for region in regions:
        project = root / ('runeterra-' + region)
        indexed = recipe_index(project)
        content = read(project / 'content/factions.json')
        faction = content[region]
        structures = faction['town']['structures']
        structures = structures.values() if isinstance(structures, dict) else structures
        sheet_rows = []
        for structure in structures:
            if not structure.get('border'):
                continue
            name = Path(structure['border']).name.removesuffix('_border.png')
            source_name = 'Content/Sprites/' + structure['animation']
            animation_path, animation = indexed[source_name]
            source = safe_input(project, animation['groups'][0]['frames'][0]['source'])
            layer = load(source)
            base = binary(layer.getchannel('A'))
            selection = selections.get(region + '/' + name)
            if selection:
                architecture = safe_input(root, selection['path'])
                if digest(architecture) != selection['sha256']:
                    raise ValueError('Architecture mask checksum changed')
                mask = Image.open(architecture).convert('L')
                if ImageChops.subtract(mask, base).getbbox():
                    raise ValueError('Architecture mask leaves the current selected layer')
                basis = {'kind': 'independently-authored-architecture-mask', **selection}
            else:
                mask = base
                basis = {'kind': 'alpha128-proposal-only', 'accuracy_verified': False,
                         'warning': 'Opaque sky, paving or scenery in the painted layer remains unexcluded.'}
            border = border_from_mask(mask)
            recipe_path, recipe = indexed['Content/Sprites/' + structure['border']]
            previous = (project / recipe['source']) if recipe.get('recipe_type') != 'town_masks' else project / 'assets/generated' / ('Content/Sprites/' + structure['border'])
            old = load(previous)
            destination = output / region / name
            destination.mkdir(parents=True)
            border.save(destination / 'border.png')
            mask.save(destination / 'architecture-mask.png')
            background = Image.new('RGBA', SIZE, (73, 73, 73, 255))
            background.alpha_composite(layer)
            before = background.copy(); before.alpha_composite(old)
            after = background.copy(); after.alpha_composite(border)
            box = ImageChops.lighter(layer.getchannel('A'), border.getchannel('A')).getbbox()
            box = (max(0, box[0]-3), max(0, box[1]-3), min(800, box[2]+3), min(374, box[3]+3))
            before.crop(box).save(destination / 'before.png')
            after.crop(box).save(destination / 'after.png')
            colours = sorted(pixel for _, pixel in old.getcolors(SIZE[0]*SIZE[1]) if pixel[3])
            expected = ImageChops.subtract(base.filter(ImageFilter.MaxFilter(3)), base)
            mismatch = ImageChops.difference(old.getchannel('A'), expected)
            row = {'region': region, 'building': name, 'status': 'design proposal',
                   'candidate_only': True, 'visual_approval_granted': False,
                   'runtime_observed': False, 'structure': structure,
                   'animation_recipe': {'path': animation_path.relative_to(root).as_posix(), 'sha256': digest(animation_path)},
                   'selected_layer': {'path': source.relative_to(root).as_posix(), 'sha256': digest(source)},
                   'selected_border_recipe': {'path': recipe_path.relative_to(root).as_posix(), 'sha256': digest(recipe_path)},
                   'selected_border': {'path': previous.relative_to(root).as_posix(), 'sha256': digest(previous)},
                   'old_colours_rgba': [list(value) for value in colours],
                   'old_is_exact_one_pixel_alpha128_edge': mismatch.getbbox() is None,
                   'silhouette_basis': basis, 'native_crop': list(box),
                   'candidate_border': {'path': (destination/'border.png').relative_to(output).as_posix(), 'sha256': digest(destination/'border.png')},
                   'candidate_mask': {'path': (destination/'architecture-mask.png').relative_to(output).as_posix(), 'sha256': digest(destination/'architecture-mask.png')}}
            rows.append(row)
            sheet_rows.append((name, before.crop(box), after.crop(box)))
        width = 680
        height = sum(max(a.height, b.height) + 26 for _, a, b in sheet_rows)
        sheet = Image.new('RGBA', (width, height), (43, 42, 40, 255))
        drawing = ImageDraw.Draw(sheet); y = 0
        for name, before, after in sheet_rows:
            drawing.text((4, y+3), region + '/' + name + ' : current / candidate (native pixels)', fill='white')
            sheet.alpha_composite(before, (4, y+22));sheet.alpha_composite(after, (344, y+22))
            y += max(before.height, after.height) + 26
        sheet.save(output / (region + '-native-comparison.png'))
    manifest = {'status': 'design proposal', 'candidate_only': True, 'style': STYLE,
                'producer': {'path': Path(__file__).resolve().relative_to(root).as_posix(), 'sha256': digest(__file__)},
                'source_mutations': 0, 'states': rows,
                'limitations': ['No current selection, recipe, click area, painted pixel or runtime changed.',
                                'Alpha-only candidates do not establish architectural accuracy. Explicit mask tracing and visual review are required for baked scenery.',
                                'Native hover occlusion and construction-state checks remain unobserved.']}
    write(output / 'manifest.json', manifest)
    blocks = ['<!doctype html><meta charset="utf-8"><title>Town hover outline candidates</title>',
              '<style>body{background:#252321;color:#eee;font:16px sans-serif}img{image-rendering:pixelated;max-width:none}summary{padding:10px}small{display:block;color:#f5ca80}</style>',
              '<h1>Town hover outline candidates — review only</h1>',
              '<p>Each pair shows the current border and a consistent one-pixel gold edge with one additional pixel of dark support. Native-size images. Actual architectural accuracy is pending wherever scenery is baked into the selected layer. Nothing is active in game.</p>']
    for region in regions:
        blocks.append('<details><summary>'+html.escape(region)+'</summary><img src="'+region+'-native-comparison.png"></details>')
    (output / 'index.html').write_text('\n'.join(blocks), encoding='utf-8')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--region', action='append', choices=REGIONS)
    parser.add_argument('--mask-selections', type=Path)
    parser.add_argument('--trace-polygons', type=Path,
                        help='Only reproduce editable manually traced polygon masks into --output')
    args = parser.parse_args()
    if args.trace_polygons:
        value = render_polygon_masks(args.root, args.trace_polygons, args.output)
        print(json.dumps({'masks': len(value), 'status': 'design proposal'}))
        raise SystemExit(0)
    value = candidate(args.root, args.output, args.region or REGIONS,
                      read(args.mask_selections) if args.mask_selections else None)
    print(json.dumps({'states': len(value['states']), 'report': str(args.output), 'status': value['status']}))
