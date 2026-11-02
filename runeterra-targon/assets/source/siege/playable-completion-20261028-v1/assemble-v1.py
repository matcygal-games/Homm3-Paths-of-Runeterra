"""Technical registration of genuine painted siege pieces; no artwork synthesis.

The editable selection pins every master, crop and whole-family translation.
No original game pixels, Blender files or code-painted geometry are inputs.
"""
from pathlib import Path
import argparse
import hashlib
import io
import json
from PIL import Image

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def png(image):
    out = io.BytesIO()
    image.save(out, format='PNG', optimize=False)
    return out.getvalue()


def source(name, expected):
    path = (PROJECT / name).resolve()
    if not path.is_relative_to(PROJECT.resolve()) or path.stat().st_nlink != 1:
        raise ValueError('Nonportable source: ' + name)
    raw = path.read_bytes()
    if sha(raw) != expected:
        raise ValueError('Changed selected source: ' + name)
    return raw


def plans(selection):
    outputs, recipes, measurements = {}, {}, []
    dependencies = selection['shared_inputs']
    for dep in dependencies:
        source(dep['path'], dep['sha256'])
    for row in selection['assets']:
        raw = source(row['master'], row['master_sha256'])
        im = Image.open(io.BytesIO(raw)).convert('RGBA')
        if list(im.size) != row['master_dimensions']:
            raise ValueError('Master dimensions changed: ' + row['id'])
        if row.get('master_crop'):
            im = im.crop(tuple(row['master_crop']))
        local_size = tuple(row['local_canvas'])
        # Whole-canvas scaling preserves each painting's proportions. The
        # local guide aspect, independently measured from native resources,
        # was supplied to the painter rather than inferred from its bbox.
        resized = tuple(row.get('resized_dimensions', local_size))
        scale = min(resized[0] / im.width, resized[1] / im.height)
        proportional = (round(im.width * scale), round(im.height * scale))
        if any(abs(a - b) > 1 for a, b in zip(resized, proportional)):
            raise ValueError('Anisotropic resize is forbidden: ' + row['id'])
        piece = im.resize(resized, Image.Resampling.LANCZOS)
        im = Image.new('RGBA', local_size)
        im.alpha_composite(piece, tuple(row.get('resample_placement', [0, 0])))
        dx, dy = row.get('local_translation', [0, 0])
        if dx or dy:
            shifted = Image.new('RGBA', local_size)
            shifted.alpha_composite(im, (dx, dy))
            before = sum(a >= 8 for a in im.getchannel('A').getdata())
            after = sum(a >= 8 for a in shifted.getchannel('A').getdata())
            if before != after:
                raise ValueError('Whole-pose translation clips painting: ' + row['id'])
            im = shifted
        crop = row.get('local_crop', [0, 0, *local_size])
        alpha = im.getchannel('A')
        retained = Image.new('L', local_size)
        retained.paste(alpha.crop(tuple(crop)), tuple(crop[:2]))
        # Strict alpha8 catches true material and its contact shadows, not
        # hidden RGB under transparent pixels.
        clipped = sum(a >= 8 and b < 8 for a, b in zip(alpha.getdata(), retained.getdata()))
        if clipped:
            raise ValueError(f"Selected crop clips {clipped} visible pixels: {row['id']}")
        result = im.crop(tuple(crop))
        if list(result.size) != row['native_size']:
            raise ValueError('Wrong native canvas: ' + row['id'])
        if not row['require_alpha']:
            if result.getchannel('A').getextrema() != (255, 255):
                raise ValueError('Battle background is not opaque')
        elif result.getchannel('A').getextrema()[1] == 0:
            raise ValueError('Empty siege state: ' + row['id'])
        name = row['prepared']
        outputs[name] = png(result)
        inputs = dependencies + row.get('ancestry', []) + [
            {'path': row['master'], 'sha256': row['master_sha256']}]
        unique = {d['path']: d['sha256'] for d in inputs}
        for path, pin in unique.items():
            source(path, pin)
        recipe = {
            'recipe_type': 'raster', 'production_status': 'painted-master-complete-unapproved',
            'source': name, 'source_sha256': sha(outputs[name]),
            'source_canvas': row['native_size'], 'canvas': row['native_size'], 'fit': 'exact',
            'output_path': row['output_path'], 'require_alpha': row['require_alpha'],
            'role': 'siege-image', 'generation': {**row['generation'], 'workflow':'image-based-painted-2d', 'source_generation_ledger':(HERE/'source-generation-ledger-v1.json').relative_to(PROJECT).as_posix(), **({'source_generation_ledger_sha256':sha((HERE/'source-generation-ledger-v1.json').read_bytes())} if (HERE/'source-generation-ledger-v1.json').is_file() else {})},
            'production_inputs': [{'path': p, 'sha256': h} for p, h in sorted(unique.items())],
            'credits': {'author': 'Project-directed OpenAI built-in imagegen; technical 2D registration',
                        'license': None, 'redistribution': 'unresolved; release approval pending'},
            'conversion': {'uniform_resized_dimensions': list(resized),
                           'padded_local_canvas': row['local_canvas'],
                           'resample_placement': row.get('resample_placement', [0, 0]),
                           'whole_family_translation': [dx, dy], 'local_crop': crop,
                           'visible_alpha8_clipped': 0},
            'visual_approval_granted': False,
            'acceptance': 'Authored configuration; native siege, damage, tower and gate observations pending.'}
        recipes[row['recipe']] = encoded(recipe)
        measurements.append({'id': row['id'], 'dimensions': list(result.size),
                             'alpha8_bbox': result.getchannel('A').point(lambda a: 255 if a >= 8 else 0).getbbox(),
                             'clipped_alpha8': clipped, 'sha256': sha(outputs[name])})
    return outputs, recipes, measurements


def compose(selection, outputs, damage=1, gate=None):
    by_id = {row['id']: row for row in selection['assets']}
    def im(key):
        return Image.open(io.BytesIO(outputs[by_id[key]['prepared']])).convert('RGBA')
    canvas = im('SGTGBACK')
    # Native enum iteration is the stable tiebreaker. Battlements render at
    # both WALLS=1 and OBSTACLES=3; preserve both alpha blends. Actors between
    # them are intentionally absent from this architecture-only source view.
    tower_state = str(1 if damage < 3 else 2)
    queue = []
    enum_order = [('TPWL', -1), ('MAN' + tower_state, 7),
                  ('TW1' + tower_state, 11), ('WA1' + str(damage), 10),
                  ('WA3' + str(damage), 7), ('WA4' + str(damage), 3),
                  ('WA6' + str(damage), 0), ('TW2' + tower_state, -1),
                  (('DRW' + str(gate)) if gate else None, -1),
                  ('ARCH', 6), ('WA2', 9), ('WA5', 2),
                  ('MANC' if damage < 3 else None, 7),
                  ('TW1C' if damage < 3 else None, 11),
                  ('TW2C' if damage < 3 else None, -1)]
    for suffix, hex_row in enum_order:
        if suffix is None:
            continue
        if suffix in ('MANC', 'TW1C', 'TW2C'):
            queue.append((hex_row, 3, suffix))
        queue.append((hex_row, 1, suffix))
    if gate == 2:
        queue.append((5, 3, 'DRWC'))
    order = ['MOAT', 'MLIP'] + [entry[2] for entry in sorted(queue, key=lambda item: item[:2])]
    for suffix in order:
        row = by_id['SGTG' + suffix]
        canvas.alpha_composite(im(row['id']), tuple(row['position']))
    return png(canvas), order


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--review-dir', type=Path)
    args = parser.parse_args()
    selection = json.loads((HERE / 'selection-v1.json').read_text(encoding='utf-8'))
    outputs, recipes, measurements = plans(selection)
    errors = []
    for name, raw in {**outputs, **recipes}.items():
        path = PROJECT / name
        if args.check:
            if not path.is_file() or path.read_bytes() != raw:
                errors.append(name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    if args.review_dir:
        args.review_dir.mkdir(parents=True, exist_ok=True)
        for name, damage, gate in [('intact-closed', 1, None), ('intact-opening', 1, 1),
                                   ('intact-open', 1, 2), ('damaged', 2, 2), ('destroyed', 3, 3)]:
            raw, order = compose(selection, outputs, damage, gate)
            (args.review_dir / (name + '.png')).write_bytes(raw)
            (args.review_dir / (name + '-order.json')).write_bytes(encoded(order))
        (args.review_dir / 'conversion.json').write_bytes(encoded({
            'status': 'authored configuration', 'ok': not errors, 'errors': errors,
            'assets': measurements, 'recipes': len(recipes), 'native_approval': False}))
    print(json.dumps({'ok': not errors, 'pieces': len(outputs), 'recipes': len(recipes), 'errors': errors}))
    return 2 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
