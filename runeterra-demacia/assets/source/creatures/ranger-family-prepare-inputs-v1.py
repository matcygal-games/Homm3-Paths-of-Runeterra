"""Technical atlas assembly of genuine Ranger rig renders; no creative edits."""
from pathlib import Path
import hashlib
import json

from PIL import Image, ImageDraw


PROJECT = Path(__file__).resolve().parents[3]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_image(image, path):
    if path.exists():
        with Image.open(path) as previous:
            if previous.mode != image.mode or previous.size != image.size or previous.tobytes() != image.tobytes():
                raise ValueError(f'Preserve changed source file: {path}')
    else:
        image.save(path)


for unit in ('demacianRanger', 'veteranRanger'):
    folder = PROJECT / 'assets/source/creatures' / unit / 'ranger-rig-v4'
    metadata_path = folder / 'ranger-production-v4.json'
    metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
    for group, layout in ((0, (3, 2)), (2, (2, 2)), (15, (4, 2))):
        poses = metadata['actions'][str(group)]
        columns, rows = layout
        assert len(poses) == columns * rows
        raw = Image.new('RGBA', (columns * 512, rows * 512))
        padded = Image.new('RGBA', raw.size)
        inputs = []
        for index, pose in enumerate(poses):
            source = folder / f'raw-actions/g{group:02}/g{group:02}-f{index:03}.png'
            with Image.open(source) as image:
                image.load()
                assert image.mode == 'RGBA' and image.size == (512, 512)
                x, y = index % columns * 512, index // columns * 512
                raw.alpha_composite(image, (x, y))
                padded.alpha_composite(image.resize((420, 420), Image.Resampling.LANCZOS), (x + 46, y + 46))
            inputs.append({'index': index, 'path': source.relative_to(PROJECT).as_posix(), 'sha256': digest(source),
                           'parameters': pose['parameters']})
        original = folder / f'raw-action-g{group:02}-atlas-v1.png'
        target = folder / f'raw-action-g{group:02}-atlas-padded-v1.png'
        save_image(raw, original)
        save_image(padded, target)
        transform = {'unit': unit, 'group': group, 'metadata': metadata_path.relative_to(PROJECT).as_posix(),
            'metadata_sha256': digest(metadata_path), 'layout': list(layout), 'cell': [512, 512],
            'inputs': inputs, 'input': original.relative_to(PROJECT).as_posix(), 'input_sha256': digest(original),
            'output': target.relative_to(PROJECT).as_posix(), 'output_sha256': digest(target),
            'scale': 420 / 512, 'offset': [46, 46], 'raw_world_origin_pixels': metadata['raw_world_origin_pixels'],
            'padding': {'scale': 420 / 512, 'offset': [46, 46], 'executed': True},
            'intentional_exact_pose_holds': ([{'indices': [0, 2], 'meaning': 'Actual still holding pose recurs between authored weight shifts.'}] if group == 2 else
                [{'indices': [2, 3], 'meaning': 'Actual steady aim hold before one trigger release at index4.'}] if group == 15 else []),
            'basis': 'Executed Pillow uniform whole-cell downsample from actual articulated RGBA renders, centered in unchanged 512px cells; no pose synthesis or inferred generator resize.',
            'status': 'source guide only; no painted output or art approval', 'active_recipe_modified': False}
        (folder / f'raw-action-g{group:02}-padding-transform-v1.json').write_text(json.dumps(transform, indent=2) + '\n', encoding='utf-8')

# Private original-game style evidence only, never included in mod resources.
reference_folder = PROJECT / 'references/prototypes/ranger-family-v4'
reference_folder.mkdir(parents=True, exist_ok=True)
board = Image.new('RGB', (900, 420), '#61635c')
draw = ImageDraw.Draw(board)
for row, name in enumerate(('clcbow', 'chcbow')):
    for column, (group, index) in enumerate(((0, 0), (0, 2), (2, 0), (15, 0), (15, 4), (15, 7))):
        source = PROJECT / f'references/frames/{name}/g{group:02}-f{index:03}.png'
        with Image.open(source) as image:
            # An unchanged native pixel crop; no enlarged simulated detail.
            view = image.convert('RGBA').crop((130, 155, 280, 325))
            board.paste(view, (column * 150, row * 210 + 25), view)
        draw.text((column * 150 + 5, row * 210 + 5), f'{name} g{group:02} f{index}', fill='white')
save_image(board, reference_folder / 'castle-ranged-native-style-v1.png')
print('Prepared six genuine pose guides and private Castle native style board.')
