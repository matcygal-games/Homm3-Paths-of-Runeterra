"""Explicit source-layout translations; retain whole-atlas zoom and true poses."""
from pathlib import Path
import hashlib
import json
import sys

from PIL import Image, ImageDraw

PROJECT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT / 'scripts'))
from creature_family_motion_art import export_generation

# Observed belt/root and planted-foot positions on the actual coordinate boards.
# Walking keeps the original3D projected stride's differing toe/sole positions;
# no requirement is imposed that every walking bbox bottom equal267.
TRANSLATIONS = {
    'demacianRanger': {
        0: [(0, 0), (-1, 0), (-7, -1), (-2, 6), (-3, 5), (-7, 4)],
        2: [(0, -1)] * 4,
        15: [(0, 0)] * 4 + [(0, 3), (0, 2), (0, 2), (0, 2)],
    },
    'veteranRanger': {
        0: [(0, 0), (-1, 0), (-2, -1), (0, 4), (-2, 4), (-3, 3)],
        2: [(0, -1)] * 4,
        15: [(0, 0)] * 4 + [(0, 4)] * 4,
    },
}

def proof(path):
    return {'path': path.relative_to(PROJECT).as_posix(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


all_records = []
for unit, groups in TRANSLATIONS.items():
    folder = PROJECT / 'assets/source/creatures' / unit / 'ranger-rig-v4'
    for group, translations in groups.items():
        evidence = []
        if group in (0, 15):
            evidence.append(proof(PROJECT / f'references/prototypes/ranger-family-v4/{unit}-g{group:02}-source-coordinate-review-v1.png'))
        evidence.append(proof(folder / f'paint-action-g{group:02}-native-light-dark-review-v1.png'))
        basis = ('Measured constant torso/belt projection against the original rig source and visible support foot: remove generator row/column layout shifts, retaining genuine opposite strides and1–3px projected-ground variation. Native gait/camera continuity remains unapproved.' if group == 0 else
                 'Observed quiet holding soles are one native raster row below target267 after whole-atlas resampling; uniform -1 translation of every real holding pose.' if group == 2 else
                 'Actual source feet are planted in every shooting/reload pose; lower atlas row was shifted upward by the generator. Restore those sole positions with integer whole-frame translation; retain actual arm, recoil and reload geometry unchanged.')
        placements = [{'index': index, 'native_translation': list(translation), 'reviewed': True,
                       'basis': basis, 'evidence': evidence} for index, translation in enumerate(translations)]
        result = export_generation(PROJECT, folder / f'paint-action-g{group:02}-atlas-v1-generation.json',
            folder / f'paint-action-g{group:02}-camera-v1.json', version=2, placements=placements, placement_version=1)
        all_records.append(result)
        board = Image.new('RGB', (len(result['frames']) * 130, 300), '#303b35')
        draw = ImageDraw.Draw(board)
        draw.text((4, 4), f'{unit} g{group:02} measured camera + reviewed translation; SOURCE ONLY', fill='white')
        frames = []
        for index, frame in enumerate(result['frames']):
            with Image.open(PROJECT / frame['output']) as native:
                crop = native.crop((145, 170, 275, 300))
                for row, color in ((0, '#d6d6c6'), (1, '#283b31')):
                    tile = Image.new('RGBA', crop.size, color);tile.alpha_composite(crop)
                    board.paste(tile.convert('RGB'), (index * 130, row * 140 + 20))
                    draw.line((index * 130, row * 140 + 117, (index + 1) * 130 - 1, row * 140 + 117), fill='#718b71')
                draw.text((index * 130 + 4, 283), f'f{index}', fill='white')
                preview = Image.new('RGBA', (160, 150), '#c6c7b5');preview.alpha_composite(native.crop((135, 160, 295, 310)))
                frames.append(preview.convert('RGB'))
        board.save(folder / f'paint-action-g{group:02}-native-light-dark-review-v2.png')
        frames[0].save(folder / f'paint-action-g{group:02}-native-motion-review-v2.gif', save_all=True,
            append_images=frames[1:], duration=140 if group == 0 else 180, loop=0, disposal=2)

report = {'units': ['demacianRanger', 'veteranRanger'], 'groups': [0, 2, 15],
    'actual_rendered_frames': 36, 'native_canvas': [450, 400],
    'source_records': [proof(PROJECT / result['generation_record']['path']) for result in all_records],
    'native_export_records': [proof(PROJECT / 'assets/source/creatures' / result['unit'] / 'ranger-rig-v4' / f"paint-action-g{result['group']:02}-native-export-v2-placement-v1.json") for result in all_records],
    'pose_semantics': {'g00': 'Six genuine opposite contact/pass phases per female scout.',
        'g02': 'Four quiet holding poses; legitimate repeated holds are retained.',
        'g15': 'Eight genuine raise, aim, intentional aim hold, release at zero-based4, recoil, cock and reload phases; no pixel noise or invented extra action.'},
    'transparency_review': 'Actually viewed native light/dark alpha composites. Diffuse RGB outside sprites lies mainly underalpha0; alpha1–7 speckles exist but no visible native backdrop halo was observed. No alpha clipping, repaint or original pixels used.',
    'limitations': ['Only three groups produced per variant; directional shots, hit, defense, death/corpse, turns, fidgets and knife attacks remain raw3D only.',
        'Generated source camera and framing changed; independently measured whole-atlas scale and explicit whole-frame translations record that correction.',
        'Body/cloth form varies slightly across painted poses; temporal/native renderer review remains required.',
        'Shooting projectile origins must be remeasured from these actual painted release frames before any production promotion.',
        'Crest is present but complete heraldic shape at native battle scale remains unapproved.',
        'No active recipes, generated assets, manifests, stage files or final art acceptance changed.'],
    'status': 'source-only first native-ready pilot for parent review; no game renderer acceptance or release approval',
    'visual_approval_granted': False, 'active_assets_modified': False}
(PROJECT / 'assets/source/creatures/ranger-painted-pilots-production-v1.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print('Wrote36 source native frames, six actual light/dark boards and motion GIFs, all unapproved.')
