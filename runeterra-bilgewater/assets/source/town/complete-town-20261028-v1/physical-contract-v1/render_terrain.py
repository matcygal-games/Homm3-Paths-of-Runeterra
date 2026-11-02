"""Render technical terrain masks from explicit manual semantic annotations."""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw, ImageChops

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[4]
TRACE = HERE / 'terrain-trace-v1'
REPORT = PROJECT / 'build/reports/complete-town-20261028-v1/physical-contract-v1'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    data = json.loads((TRACE / 'annotations.json').read_text(encoding='utf-8'))
    background = PROJECT / data['background']['path']
    if digest(background) != data['background']['sha256']:
        raise ValueError('Frozen terrain painting changed; do not trace a different background silently')
    masks = {}
    for kind in ('support', 'stairs', 'water'):
        mask = Image.new('L', (800, 374))
        draw = ImageDraw.Draw(mask)
        for record in data[kind + '_regions']:
            draw.polygon([tuple(point) for point in record['polygon']], fill=255)
        masks[kind] = mask
    land = ImageChops.lighter(masks['support'], masks['stairs'])
    draw = ImageDraw.Draw(land)
    face_mask = Image.new('L', (800, 374))
    face_draw = ImageDraw.Draw(face_mask)
    for record in data['retaining_faces']:
        polygon = [tuple(point) for point in record['polygon']]
        draw.polygon(polygon, fill=255)
        face_draw.polygon(polygon, fill=255)
    masks['land'] = land
    masks['retaining-target'] = ImageChops.subtract(face_mask, ImageChops.lighter(masks['support'], masks['stairs']))
    paths = Image.new('L', (800, 374))
    for record in data['path_polylines']:
        ImageDraw.Draw(paths).line([tuple(point) for point in record['points']], fill=255, width=record['width'])
    masks['paths'] = paths
    for name, mask in masks.items():
        # Opaque binary masks are source annotations, not painted game art.
        mask.convert('RGB').save(TRACE / (name + '.png'))
    REPORT.mkdir(parents=True, exist_ok=True)
    plain = Image.open(background).convert('RGBA')
    for name, color in [('support', (20, 240, 90)), ('stairs', (245, 170, 20)), ('water', (20, 150, 245)), ('retaining-target', (225, 40, 180))]:
        overlay = Image.new('RGBA', plain.size, color + (0,))
        overlay.putalpha(masks[name].point(lambda value: 80 if value else 0))
        Image.alpha_composite(plain, overlay).convert('RGB').save(REPORT / ('terrain-v1-' + name + '-study.png'))
    counts = {'status': 'design proposal', 'background_sha256': digest(background),
              'annotations_sha256': digest(TRACE / 'annotations.json'),
              'support_on_stairs': ImageChops.multiply(masks['support'], masks['stairs']).histogram()[255],
              'support_on_water': ImageChops.multiply(masks['support'], masks['water']).histogram()[255],
              'land_on_water': ImageChops.multiply(masks['land'], masks['water']).histogram()[255],
              'mask_pixels': {name: mask.histogram()[255] for name, mask in masks.items()},
              'full_physical_baseline_run': False, 'native_executed': False, 'release_accepted': False}
    (REPORT / 'terrain-v1-proposal.json').write_text(json.dumps(counts, indent=2) + '\n')
    print(json.dumps(counts, indent=2))


if __name__ == '__main__':
    main()
