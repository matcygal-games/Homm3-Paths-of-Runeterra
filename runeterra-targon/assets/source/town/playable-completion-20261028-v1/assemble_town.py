"""Pure technical native registration of original painted sources.

The complete town composition and explicit site registration precede extraction.
This code crops only transparent margins, scales uniformly, and composites whole
paintings. It never draws architecture, creates art, or synthesizes hidden poses.
"""
from pathlib import Path
import json
import hashlib
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    guide = json.loads((HERE / 'site-plan-v1.json').read_text(encoding='utf-8'))
    registration = json.loads((HERE / 'registration-v4.json').read_text(encoding='utf-8'))
    native = HERE / 'native-v4'
    native.mkdir(exist_ok=True)
    rows = []
    frames = {}
    top = []
    base = []
    for site, plan in guide['sites'].items():
        rule = registration['sites'][site]
        for state in plan['keys']:
            master = HERE / 'states' / state / 'master-v1-raw.png'
            if not master.is_file():
                raise ValueError('Genuine painted source not delivered: ' + state)
            source = Image.open(master).convert('RGBA')
            if 'source_crop' in rule:
                # Select a complete separately painted object from a multiobject
                # tool response; never cut a roof/wall to fake a lower stage.
                source = source.crop(rule['source_crop'])
            crop = source.getchannel('A').point(lambda p: 255 if p >= 8 else 0).getbbox()
            if not crop:
                raise ValueError('Empty genuine source: ' + state)
            cut = source.crop(crop)
            width = rule.get('state_widths', {}).get(state, rule.get('lower_width', rule['width']) if state != plan['top'] else rule['width'])
            height = round(width * cut.height / cut.width)
            painted = cut.resize((width, height), Image.Resampling.LANCZOS)
            x, y = rule['center_x'] - width // 2, rule['bottom'] - height
            if not (0 <= x < x + width <= 800 and 0 <= y < y + height <= 374):
                raise ValueError('Whole painted source leaves its native canvas: ' + state)
            frame = Image.new('RGBA', (800, 374))
            frame.alpha_composite(painted, (x, y))
            path = native / (state + '.png')
            frame.save(path, compress_level=9)
            frames[state] = frame
            rows.append({'site': site, 'state': state, 'source': master.relative_to(HERE).as_posix(), 'source_sha256': sha(master),
                         'transparent_margin_crop': list(crop), 'uniform_size': [width, height], 'position': [x, y],
                         'frame': path.relative_to(HERE).as_posix(), 'frame_sha256': sha(path),
                         'actual_alpha8_bounds': list(frame.getchannel('A').point(lambda p: 255 if p >= 8 else 0).getbbox())})
        if site != 'grail':
            top.append(plan['top'])
            base.append(plan['keys'][0])
    depths = {state: plan['z'] for plan in guide['sites'].values() for state in plan['keys']}
    background = Image.open(HERE / 'background-selected-native-v9.png').convert('RGBA')
    for label, states in [('fully-built', top), ('base-built', base), ('fully-built-grail', top + ['grail']), ('early', ['villageHall', 'fort', 'tavern', 'dwellingLvl1'])]:
        states.sort(key=lambda s: depths[s])
        scene = background.copy()
        for state in states:
            scene = Image.alpha_composite(scene, frames[state])
        scene.save(native / (label + '.png'), compress_level=9)
    board = Image.new('RGB', (1200, 1440), '#34382f')
    labels = ImageDraw.Draw(board)
    for i, row in enumerate(rows):
        frame = frames[row['state']]
        box = frame.getchannel('A').point(lambda p: 255 if p >= 8 else 0).getbbox()
        picture = frame.crop(box)
        xx, yy = 10 + (i % 5) * 240, 22 + (i // 5) * 200
        board.paste(picture, (xx, yy), picture)
        labels.text((xx, yy - 16), row['state'], fill='white')
    board.save(native / 'all35-native-board.png')
    (HERE / 'assembly-v4.json').write_text(json.dumps({'status': 'authored configuration', 'visual_approval_granted': False, 'states': rows}, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
