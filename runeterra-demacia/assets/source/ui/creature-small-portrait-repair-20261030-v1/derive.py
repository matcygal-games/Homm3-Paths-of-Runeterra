"""Native CPRSMALL crops from existing own painted actors; no creative edits."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

PROJECT = Path(__file__).resolve().parents[4]
ROOT = Path(__file__).resolve().parent
PAINTED = 'assets/source/creatures/painted-20261025-replacement-v1/'
SPECS = {
    'loyalBadgerbear': {'source': PAINTED + 't1/loyalBadgerbear-master-v1-public.png', 'crop': [700, 100, 1400, 800]},
    'veteranBadgerbear': {'source': PAINTED + 't1/veteranBadgerbear-master-v1-public.png', 'crop': [700, 120, 1400, 820]},
    'mageseekerInciter': {'source': PAINTED + 't3/inciter-utility-v1-public.png', 'matte': PAINTED + 't3/mattes/mageseekerInciter-hold.png', 'crop': [130, 3, 255, 128]},
    'seniorInciter': {'source': PAINTED + 't3/senior-utility-v1-public.png', 'matte': PAINTED + 't3/mattes/seniorInciter-hold.png', 'crop': [128, 18, 270, 160]},
    'silverwingLancer': {'source': PAINTED + 't7/silverwingLancer/holding-v1/painted-master.png', 'crop': [440, 300, 1100, 960]},
    'elderSilverwingLancer': {'source': PAINTED + 't7/elderSilverwingLancer/holding-v2/painted-master.png', 'crop': [380, 230, 1110, 960]},
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def derive(unit, spec):
    source = PROJECT / spec['source']
    picture = Image.open(source).convert('RGBA')
    inputs = [{'path': spec['source'], 'sha256': sha(source)}]
    if 'matte' in spec:
        matte_path = PROJECT / spec['matte']
        matte = Image.open(matte_path).convert('L')
        if matte.size != picture.size:
            raise ValueError('Selected actor matte has a different source canvas')
        picture.putalpha(matte)
        inputs.append({'path': spec['matte'], 'sha256': sha(matte_path)})
    box = spec['crop']
    if box[2] - box[0] != box[3] - box[1]:
        raise ValueError('Small portrait must use a square source crop')
    picture = picture.crop(tuple(box))
    destination = ROOT / (unit + '-cutout.png')
    picture.save(destination, format='PNG')
    return {'unit': unit, 'inputs': inputs, 'crop': box,
            'source': destination.relative_to(PROJECT).as_posix(),
            'source_sha256': sha(destination), 'dimensions': list(picture.size),
            'method': 'Unchanged own painted pixels, selected whole-actor matte where already authored, square crop only; no drawing, masking inference, body warp or aspect distortion.'}


def main():
    records = {unit: derive(unit, spec) for unit, spec in SPECS.items()}
    ledger = {'status': 'authored configuration', 'image_generation_used': False,
              'existing_own_painted_art_only': True, 'native_reference': 'CPRSMALL transparent unit cutout, 32x32',
              'large_portraits_unchanged': True, 'records': records,
              'producer': {'path': Path(__file__).relative_to(PROJECT).as_posix(), 'sha256': sha(Path(__file__))},
              'visual_approval_granted': False, 'native_gameplay_verified': False, 'release_accepted': False}
    (ROOT / 'derivation.json').write_text(json.dumps(ledger, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({'derived': len(records), 'ledger_sha256': sha(ROOT / 'derivation.json')}))


if __name__ == '__main__':
    main()
