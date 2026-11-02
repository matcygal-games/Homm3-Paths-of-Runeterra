"""Measured source-only native export of six Ranger painted pilot atlases."""
from pathlib import Path
import json
import sys

from PIL import Image, ImageDraw

PROJECT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT / 'scripts'))
from creature_family_motion_art import calibrate_generation, export_generation

# Actual manually inspected landmarks on a512px review of the FIRST returned
# cell, not assumptions that the generator preserved its input coordinates.
# Head includes hood/plume; ground is front supporting sole. Rootx follows the
# vertical projection through pelvis, not the crossbow/whole-figure bbox centre.
LANDMARKS = {
    'demacianRanger': {0: (68, 491, 256), 2: (102, 479, 253), 15: (65, 499, 239)},
    'veteranRanger': {0: (79, 490, 255), 2: (79, 488, 255), 15: (50, 508, 249)},
}

for unit, groups in LANDMARKS.items():
    folder = PROJECT / 'assets/source/creatures' / unit / 'ranger-rig-v4'
    for group, (top, ground, root) in groups.items():
        generation = folder / f'paint-action-g{group:02}-atlas-v1-generation.json'
        record = json.loads(generation.read_text())
        factor = record['returned_cell'][0] / 512
        camera = calibrate_generation(PROJECT, generation, reference_index=0,
            head_top_y=top * factor, ground_y=ground * factor, root_x=root * factor,
            target_height=78 if unit == 'demacianRanger' else 80,
            basis=f'Actually viewed first-cell review normalized uniformly to512px: hood/plume topY{top}, front supporting soleY{ground}, pelvis projectionX{root}. One measured whole-atlas zoom/origin; no per-pose fitting. Other source-row framing drift remains explicitly uncorrected in this initial review export.')
        exported = export_generation(PROJECT, generation, folder / f'paint-action-g{group:02}-camera-v1.json')
        frames = []
        board = Image.new('RGB', (len(exported['frames']) * 130, 300), '#303b35')
        draw = ImageDraw.Draw(board)
        draw.text((4, 4), f'{unit} g{group:02} painted pilot - unchanged camera; NO release approval', fill='white')
        for index, frame in enumerate(exported['frames']):
            with Image.open(PROJECT / frame['output']) as native:
                crop = native.crop((145, 170, 275, 300))
                for row, color in ((0, '#d6d6c6'), (1, '#283b31')):
                    tile = Image.new('RGBA', crop.size, color)
                    tile.alpha_composite(crop)
                    board.paste(tile.convert('RGB'), (index * 130, row * 140 + 20))
                    draw.line((index * 130, row * 140 + 117, (index + 1) * 130 - 1, row * 140 + 117), fill='#718b71')
                draw.text((index * 130 + 4, 283), f'f{index}', fill='white')
                preview = Image.new('RGBA', (160, 150), '#c6c7b5')
                preview.alpha_composite(native.crop((135, 160, 295, 310)))
                frames.append(preview.convert('RGB'))
        board.save(folder / f'paint-action-g{group:02}-native-light-dark-review-v1.png')
        frames[0].save(folder / f'paint-action-g{group:02}-native-motion-review-v1.gif', save_all=True,
            append_images=frames[1:], duration=140 if group == 0 else 180, loop=0, disposal=2)
        print(unit, group, 'actual native frames:', len(exported['frames']))
