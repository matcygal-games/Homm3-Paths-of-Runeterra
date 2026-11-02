"""Proposal only: uniformly convert genuine painted stair source at native size.

No selected source is modified. The fixed source-observed visible corridor and
all protected architecture are immutable controls, not runtime mask waivers.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageChops, ImageDraw

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[5]
BASE = HERE.parent
OUT = HERE / 'proposal-only/native-alternative-v1'
OUT.mkdir(exist_ok=False)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def ref(path):
    return {'path': path.relative_to(PROJECT).as_posix(), 'sha256': sha(path)}

approved_path = BASE / 'approved-full-source-v1.png'
approved = Image.open(approved_path).convert('RGBA')
assert sha(approved_path) == '4f8cac4f1801ed366e0bacd4934084e9b76e0d25c282b3f3b36fda3835cd0712'
raw_path = HERE / 'proposal-only/stair-alternative-master-v3-raw.png'
painted = Image.open(raw_path).convert('RGBA').resize((62, 76), Image.Resampling.LANCZOS)
painted.save(OUT / 'painted-stair-native.png', compress_level=9)
mask_path = HERE / 'proposal-only/permitted-correction-visible-mask.png'
mask = Image.open(mask_path).convert('L')
protected = Image.open(HERE / 'proposal-only/protected-full-architecture.png').convert('L')
assert not ImageChops.multiply(mask, protected).getbbox()
full_painted = approved.copy()
full_painted.paste(painted, (576, 102))
alternative = Image.composite(full_painted, approved, mask)
alternative.save(OUT / 'full-proposal-only.png', compress_level=9)
different = ImageChops.difference(alternative.convert('RGB'), approved.convert('RGB')).convert('L').point(lambda p: 255 if p else 0)
different.save(OUT / 'actual-visible-change-mask.png')
assert not ImageChops.multiply(different, protected).getbbox()
alternative.crop((576, 102, 638, 178)).resize((620, 760), Image.Resampling.NEAREST).save(OUT / 'native-proposal-nearest10x.png')
approved.crop((576, 102, 638, 178)).resize((620, 760), Image.Resampling.NEAREST).save(OUT / 'native-current-nearest10x.png')
outside = ImageChops.subtract(different, mask)
assert not outside.getbbox()
record = {
    'status': 'design proposal',
    'selected': False,
    'current_full': ref(approved_path),
    'genuine_painted_master': ref(raw_path),
    'prompt': ref(HERE / 'proposal-only/stair-alternative-prompt-v3.txt'),
    'native_crop_box': [576, 102, 638, 178],
    'conversion': 'Uniform LANCZOS resize to native62x76, fixed placement576,102; select only preplanned unprotected visible corridor.',
    'permitted_visible_change_mask': ref(mask_path),
    'actual_visible_change_mask': ref(OUT / 'actual-visible-change-mask.png'),
    'actual_visible_changed_pixels': len([v for v in different.getdata() if v]),
    'approved_architecture_changed_pixels': 0,
    'outside_planned_corridor_changed_pixels': 0,
    'alternative': ref(OUT / 'full-proposal-only.png'),
    'physical_review_pending': True,
    'selected_full_remains_immutable': True,
    'native_executed': False,
    'release_accepted': False,
}
(OUT / 'receipt.json').write_text(json.dumps(record, indent=2, sort_keys=True) + '\n', encoding='utf-8')
print(json.dumps(record))
