"""Create reviewable own-source dwelling cards; never selects or stages them."""
from pathlib import Path
import copy
import hashlib
import io
import json
import sys
from PIL import Image, ImageDraw

W = next(p for p in Path(__file__).resolve().parents if (p / 'scripts/faction_art_compile.py').is_file())
REPORT = W / 'reports/ionia-ixtal-dwelling-card-backgrounds-20261030-v1'
sys.path.insert(0, str(W / 'scripts'))
import faction_art_compile

def sha(data):
    return hashlib.sha256(data).hexdigest()

def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')

def png(im):
    out = io.BytesIO()
    im.save(out, format='PNG', compress_level=9, optimize=False)
    return out.getvalue()

def prepare(slug):
    project = W / ('runeterra-' + slug)
    root = project / 'assets/source/town/dwelling-card-backgrounds-20261030-v1'
    root.mkdir(parents=True, exist_ok=True)
    recipe_path = (project / 'assets/recipes/town/buildingIcons.json.json' if slug == 'ionia'
                   else project / 'assets/recipes/town-selected/town/buildingIcons.json')
    historic = root / 'history/buildingIcons-before.json'
    historic.parent.mkdir(parents=True, exist_ok=True)
    old_bytes = historic.read_bytes() if historic.exists() else recipe_path.read_bytes()
    old = json.loads(old_bytes)
    if not historic.exists():
        historic.write_bytes(old_bytes)
    visuals = json.loads((project / 'design/town-visuals.json').read_text(encoding='utf-8-sig'))
    scene_path = visuals['background']
    scene_raw = (project / scene_path).read_bytes()
    scene = Image.open(io.BytesIO(scene_raw)).convert('RGBA')
    if scene.size != (800, 374):
        raise ValueError('Unexpected selected native town backdrop')
    # The complete own landscape remains readable at the native menu ratio.
    backdrop = scene.resize((150, 70), Image.Resampling.LANCZOS)
    backdrop.putalpha(255)
    rows = []
    new = copy.deepcopy(old)
    for frame in new['frames']:
        name = frame['building']
        if not name.startswith(('dwellingLvl', 'dwellingUpLvl')):
            continue
        raw = (project / frame['source']).read_bytes()
        if sha(raw) != frame['source_sha256']:
            raise ValueError('Selected figure source pin changed: ' + name)
        old_frame = Image.open(io.BytesIO(raw)).convert('RGBA')
        if old_frame.size != (150, 70):
            raise ValueError('Unexpected source frame size')
        retained = root / 'figures' / (name + '.png')
        retained.parent.mkdir(parents=True, exist_ok=True)
        retained.write_bytes(raw)
        subject = old_frame
        transform = {'method': 'unchanged native150x70 pixels'}
        if slug == 'ixtal':
            box = old_frame.getbbox()
            cropped = old_frame.crop(box)
            scale = min(144 / cropped.width, 64 / cropped.height)
            size = (max(1, round(cropped.width * scale)), max(1, round(cropped.height * scale)))
            cropped = cropped.resize(size, Image.Resampling.LANCZOS)
            subject = Image.new('RGBA', (150, 70))
            offset = ((150 - size[0]) // 2, (70 - size[1]) // 2)
            subject.alpha_composite(cropped, offset)
            transform = {'method': 'uniform alpha-bounds contain fit for native menu readability',
                         'source_bounds': list(box), 'fit_box': [144, 64],
                         'scaled_size': list(size), 'offset': list(offset), 'filter': 'LANCZOS'}
        after = Image.alpha_composite(backdrop, subject)
        if after.getchannel('A').getextrema() != (255, 255):
            raise ValueError('Card is not fully opaque')
        for p, q in zip(subject.get_flattened_data(), after.get_flattened_data()):
            if p[3] == 255 and p != q:
                raise ValueError('Opaque building pixels changed')
        target = root / 'cards' / (name + '.png')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(png(after))
        row = {'building': name, 'frame': frame['frame'],
               'original_source': frame['source'], 'original_source_sha256': sha(raw),
               'retained_figure': retained.relative_to(project).as_posix(),
               'source': target.relative_to(project).as_posix(),
               'source_sha256': sha(target.read_bytes()), 'foreground_transform': transform}
        rows.append(row)
        frame['source'] = row['source']
        frame['source_sha256'] = row['source_sha256']
        frame['source_canvas'] = [150, 70]
    if len(rows) != 14:
        raise ValueError('Expected exactly fourteen dwelling states')
    # Preserve the original painted ancestry and selected landscape through pins.
    producer = root / 'derive.py'
    producer.write_bytes(Path(__file__).read_bytes())
    ledger = root / 'derivation.json'
    dump(ledger, {'status': 'authored configuration', 'method': 'Existing building alpha composition onto selected own painted landscape resized uniformly to native150x70; Ixtal alpha bounds use uniform contain fit for legibility, Ionia remains exact figure pixels. No recolor or repaint.',
                  'background': {'path': scene_path, 'sha256': sha(scene_raw), 'canvas': [800, 374]},
                  'original_recipe': {'path': historic.relative_to(project).as_posix(), 'sha256': sha(old_bytes)},
                  'producer': {'path': producer.relative_to(project).as_posix(), 'sha256': sha(producer.read_bytes())},
                  'upstream_generation': old.get('generation'), 'cards': rows})
    new['generation'] = {'image_generation_used': False,
                         'method': 'Deterministic existing painted building/landscape alpha composition; original master ancestry retained in pinned derivation ledger; no new illustration, 3D, frame or layout changes.',
                         'derivation': ledger.relative_to(project).as_posix()}
    for key in ('inputs', 'dependencies'):
        new.setdefault(key, []).extend([{'path': ledger.relative_to(project).as_posix(), 'sha256': sha(ledger.read_bytes())},
                                        {'path': producer.relative_to(project).as_posix(), 'sha256': sha(producer.read_bytes())}])
    candidate = root / 'candidate-recipes/buildingIcons.json'
    dump(candidate, new)
    compiler = faction_art_compile.create_compiler(slug)
    plan_a, _ = compiler.plan(project, candidate)
    plan_b, _ = compiler.plan(project, candidate)
    if plan_a != plan_b:
        raise ValueError('Actual compiler replay differs')
    old_plan, _ = compiler.plan(project, historic)
    changed = sorted(k for k in old_plan if old_plan[k] != plan_a[k])
    expected = sorted(new['output_path'].removesuffix('.json') + '-frames/g00-f%03d.png' % row['frame'] for row in rows)
    if changed != expected:
        raise ValueError('Changed outputs exceed exact dwelling frame scope')
    board = Image.new('RGB', (660, 14 * 90), '#22272a')
    draw = ImageDraw.Draw(board)
    for i, row in enumerate(sorted(rows, key=lambda r: r['frame'])):
        y = i * 90
        draw.text((4, y), row['building'], fill='white')
        old_frame = Image.open(project / row['retained_figure']).convert('RGBA')
        after = Image.open(project / row['source']).convert('RGBA')
        board.paste(old_frame, (150, y + 18), old_frame)
        board.paste(after, (320, y + 18))
        board.paste(after.resize((150, 70), Image.Resampling.NEAREST), (490, y + 18))
    board.save(REPORT / (slug + '-before-after.png'))
    result = {'slug': slug, 'status': 'authored configuration', 'candidate_recipe': candidate.relative_to(project).as_posix(),
              'canonical_recipe': recipe_path.relative_to(project).as_posix(),
              'candidate_recipe_sha256': sha(candidate.read_bytes()),
              'selected_recipe_before_sha256': sha(old_bytes), 'actual_compiler_replays': 2,
              'changed_outputs': changed, 'preserved_outputs': len(old_plan) - len(changed),
              'frames': rows, 'canonical_selected': False, 'stage_changed': False}
    dump(REPORT / (slug + '-candidate.json'), result)
    return result

if __name__ == '__main__':
    for slug in ['ionia', 'ixtal']:
        print(json.dumps(prepare(slug), indent=2))
