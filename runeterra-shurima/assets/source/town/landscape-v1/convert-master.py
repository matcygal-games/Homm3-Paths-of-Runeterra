"""Deterministic centre-cover conversion of the retained generated raster master.

This is resizing/cropping only; it does not synthesize artwork or grant acceptance.
Run from any directory. Keep the source and conversion receipt together.
"""
from pathlib import Path
import hashlib, json
from PIL import Image, __version__ as pillow_version

HERE = Path(__file__).resolve().parent
source = HERE / 'geometry-adjusted-master.png'
destination = HERE / 'master.png'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

with Image.open(source) as original:
    original.load()
    image = original.convert('RGB')
    width, height = image.size
    target_width, target_height = 800, 374
    if width * target_height > height * target_width:
        crop_width = (height * target_width) // target_height
        left = (width - crop_width) // 2
        crop = (left, 0, left + crop_width, height)
    else:
        crop_height = (width * target_height) // target_width
        top = (height - crop_height) // 2
        crop = (0, top, width, top + crop_height)
    image = image.crop(crop).resize((target_width, target_height), Image.Resampling.LANCZOS)
    image.save(destination, optimize=False, compress_level=9)

receipt = {
    'status': 'built-unreviewed',
    'scope': 'generated terrain candidate; no active selection, runtime or final art acceptance',
    'source': {'path': source.name, 'sha256': sha(source), 'dimensions': [width, height]},
    'operation': 'integer centre-cover crop, RGB conversion, Pillow LANCZOS resize',
    'crop_left_top_right_bottom': list(crop),
    'pillow_version': pillow_version,
    'converter_sha256': sha(Path(__file__)),
    'output': {'path': destination.name, 'sha256': sha(destination), 'dimensions': [800, 374]},
}
(HERE/'master-conversion.json').write_text(json.dumps(receipt, sort_keys=True, indent=2)+'\n', encoding='utf-8')
print(json.dumps(receipt, sort_keys=True))
