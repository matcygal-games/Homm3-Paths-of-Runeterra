"""Private native-size original/own comparison; no original pixels in assets."""
from pathlib import Path
import hashlib
import json

from PIL import Image, ImageDraw

PROJECT = Path(__file__).resolve().parents[3]
OUTPUT = PROJECT / 'references/prototypes/dragonguard-family-v3'
OUTPUT.mkdir(parents=True, exist_ok=True)
groups = ((2, 0), (0, 3), (12, 3))
rows = (
    ('Original Castle Pikeman (private reference)', 'cpkman', None),
    ('Own base Dragonguard painted pilot (unapproved)', None, 'dragonguard'),
    ('Original Castle Halberdier (private reference)', 'chalbd', None),
    ('Own Veteran Dragonguard painted pilot (unapproved)', None, 'veteranDragonguard'),
)
board = Image.new('RGB', (660, 720), '#303b35')
draw = ImageDraw.Draw(board)
sources = []
for row, (label, original, own) in enumerate(rows):
    draw.text((4, row * 180 + 3), label, fill='white')
    for column, (group, frame) in enumerate(groups):
        path = (PROJECT / f'references/frames/{original}/g{group:02}-f{frame:03}.png' if original else
            PROJECT / f'assets/source/creatures/{own}/dragonguard-rig-v3/native-pilot-final-v1/g{group:02}/g{group:02}-f{frame:03}.png')
        with Image.open(path) as image:
            assert image.size == (450, 400)
            tile = Image.new('RGBA', (220, 140), '#bfc4b4')
            # Exact native pixels; all subjects use one shared source rectangle.
            tile.alpha_composite(image.convert('RGBA').crop((100, 150, 320, 290)))
            board.paste(tile.convert('RGB'), (column * 220, row * 180 + 25))
            draw.line((column * 220, row * 180 + 142, (column + 1) * 220 - 1, row * 180 + 142), fill='#6a8068')
            draw.text((column * 220 + 3, row * 180 + 165), f'g{group:02} frame{frame}', fill='white')
        sources.append({'path': path.relative_to(PROJECT).as_posix(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'role': 'private original style reference' if original else 'own unapproved action pilot'})
target = OUTPUT / 'castle-own-native-pilot-comparison-v1.png'
board.save(target)
(OUTPUT / 'castle-own-native-pilot-comparison-v1.json').write_text(json.dumps({'sources': sources,
    'crop': [100, 150, 320, 290], 'scale': 1, 'output': target.relative_to(PROJECT).as_posix(),
    'output_sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'status': 'Private unscaled comparison only; no visual acceptance granted',
    'original_reference_pixels_bundled_in_mod': False, 'active_assets_modified': False}, indent=2) + '\n', encoding='utf-8')
print(target)
