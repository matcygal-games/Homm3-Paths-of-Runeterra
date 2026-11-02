"""Replay native hero candidate PNGs and raster recipes from cached painted masters.

No image generation, creative drawing, live stage publishing or public reference
downloads occur here. The independently painted cached masters are the inputs.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageOps

BASE = Path(__file__).resolve().parent
PROJECT = BASE.parents[3]
IDS = (
    'heimerdinger', 'jayce', 'caitlyn', 'ezreal', 'seraphine', 'camille',
    'orianna', 'zevi', 'mir', 'kepple', 'lymere', 'reggie', 'jago', 'uberti', 'jae',
)
SMALL_Y = {'heimerdinger': 0.32, 'jayce': 0.15, 'caitlyn': 0.20}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay() -> dict:
    outputs = []
    for hero_id in IDS:
        folder = BASE / hero_id
        for kind, master_name, request_name, sizes in (
            ('portrait', 'master.png', 'generation-request.json',
             (('large', (58, 64)), ('small', (48, 32)))),
            ('specialty', 'specialty-master.png', 'specialty-generation-request.json',
             (('specialtyLarge', (44, 44)), ('specialtySmall', (32, 32)))),
        ):
            master = folder / master_name
            request = json.loads((folder / request_name).read_text(encoding='utf-8'))
            with Image.open(master) as opened:
                image = opened.convert('RGBA')
            for name, size in sizes:
                crop = None
                if name == 'small':
                    top = round(image.height * SMALL_Y.get(hero_id, 0.17))
                    height = round(image.width / 1.5)
                    top = min(top, image.height - height)
                    crop = (0, top, image.width, top + height)
                    output = image.crop(crop).resize(size, Image.Resampling.LANCZOS)
                else:
                    output = ImageOps.fit(image, size, Image.Resampling.LANCZOS,
                                          centering=(0.5, 0.5))
                target = folder / (name + '.png')
                output.save(target)
                source = target.relative_to(PROJECT).as_posix()
                generation = {
                    'image_generation_used': True,
                    'provider': request['provider'], 'model': 'not exposed',
                    'prompt': request['prompt'],
                    'painted_master': master.relative_to(PROJECT).as_posix(),
                    'painted_master_sha256': sha(master),
                    'master_canvas': list(image.size),
                    'derivation': 'LANCZOS same-master face crop' if crop else
                                  'LANCZOS same-master fixed native crop',
                    'small_source_crop': list(crop) if crop else None,
                    'producer': 'assets/source/heroes/painted-v1/derive_native.py',
                }
                recipe = {
                    'recipe_type': 'raster',
                    'production_status': 'painted-master-complete-unapproved',
                    'canvas': list(size),
                    'output_path': f'Content/Sprites/runeterra/piltover/heroes/{hero_id}/{name}.png',
                    'source': source, 'source_sha256': sha(target),
                    'source_canvas': list(size), 'fit': 'exact',
                    'generation': generation,
                }
                (folder / (name + '.recipe.json')).write_text(
                    json.dumps(recipe, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
                outputs.append({'id': hero_id, 'kind': kind, 'role': name,
                                'path': source, 'sha256': sha(target),
                                'canvas': list(size), 'mode': 'RGBA',
                                'master': generation['painted_master'],
                                'master_sha256': generation['painted_master_sha256']})
    result = {'status': 'painted-master-complete-unapproved', 'outputs': outputs,
              'verification_boundary': 'Deterministic technical replay only; no gameplay, art or rights acceptance.'}
    (BASE / 'native-output-index.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    print('Replayed', len(replay()['outputs']), 'native RGBA hero candidate outputs.')
