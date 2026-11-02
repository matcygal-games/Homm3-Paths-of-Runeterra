"""Assemble actual remaining Dragonguard raw action guides, no new poses."""
from pathlib import Path
import hashlib
import json

from PIL import Image

PROJECT = Path(__file__).resolve().parents[3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(image, path):
    if path.exists():
        with Image.open(path) as existing:
            if (existing.mode, existing.size, existing.tobytes()) != (image.mode, image.size, image.tobytes()):
                raise ValueError(f'Preserve different source: {path}')
    else:
        image.save(path)


records = []
for unit in ('dragonguard', 'veteranDragonguard'):
    folder = PROJECT / 'assets/source/creatures' / unit / 'dragonguard-rig-v3'
    metadata_path = folder / 'dragonguard-production-v3.json'
    metadata = json.loads(metadata_path.read_text())
    for group in (1, 3, 4, 5, 7, 8, 11, 13):
        poses = metadata['actions'][str(group)]
        columns, rows = (2, 2) if len(poses) == 4 else (3, 2)
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
            inputs.append({'index': index, 'path': source.relative_to(PROJECT).as_posix(), 'sha256': sha(source), 'parameters': pose['parameters']})
        original = folder / f'raw-action-g{group:02}-atlas-v1.png'
        target = folder / f'raw-action-g{group:02}-atlas-padded-v1.png'
        save(raw, original)
        save(padded, target)
        record = {'unit': unit, 'group': group, 'metadata': metadata_path.relative_to(PROJECT).as_posix(), 'metadata_sha256': sha(metadata_path),
            'layout': [columns, rows], 'cell': [512, 512], 'inputs': inputs,
            'input': original.relative_to(PROJECT).as_posix(), 'input_sha256': sha(original),
            'output': target.relative_to(PROJECT).as_posix(), 'output_sha256': sha(target),
            'scale': 420 / 512, 'offset': [46, 46], 'raw_world_origin_pixels': metadata['raw_world_origin_pixels'],
            'padding': {'scale': 420 / 512, 'offset': [46, 46], 'executed': True},
            'basis': 'Executed whole-cell uniform downsample of actual articulated 3D source renders; no creative pose fabrication or per-frame fit.',
            'status': 'Raw source preparation only; painted output absent', 'active_assets_modified': False, 'visual_approval_granted': False}
        path = folder / f'raw-action-g{group:02}-padding-transform-v1.json'
        path.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
        records.append({'unit': unit, 'group': group, 'raw_pose_count': len(poses), 'transform': {'path': path.relative_to(PROJECT).as_posix(), 'sha256': sha(path)}})

output = PROJECT / 'assets/source/creatures/dragonguard-family-remaining-raw-targets-v1.json'
output.write_text(json.dumps({'units_actions': records, 'actual_raw_pose_count': sum(record['raw_pose_count'] for record in records),
    'status': 'Only remaining genuine raw action edit targets assembled; no creative calls or active asset changes'}, indent=2) + '\n', encoding='utf-8')
print(f'Prepared{len(records)} remaining action targets from{sum(record["raw_pose_count"] for record in records)} real source renders.')
