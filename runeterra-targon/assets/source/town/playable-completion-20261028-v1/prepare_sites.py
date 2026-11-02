"""Technical preliminary outlines from the already painted complete scene.

No artistic synthesis. The source alpha and manually authored ownership guides
are inspected before selecting any final state. Canonical inputs are untouched.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageChops, ImageDraw

HERE = Path(__file__).resolve().parent


def main():
    plan = json.loads((HERE / 'site-plan-v1.json').read_text(encoding='utf-8'))
    painted = Image.open(HERE / 'complete-selected-native-v1.png').convert('RGBA')
    alpha = Image.open(HERE / 'building-layers-master-v1-native.png').convert('RGBA').getchannel('A')
    results = []
    board = Image.new('RGB', (1000, 1000), '#3b4038')
    labels = ImageDraw.Draw(board)
    for index, (name, site) in enumerate(plan['sites'].items()):
        if site.get('new_source_required'):
            continue
        mask = Image.new('L', painted.size)
        ImageDraw.Draw(mask).polygon([tuple(p) for p in site['polygon']], fill=255)
        selected_alpha = ImageChops.multiply(alpha, mask)
        frame = painted.copy()
        frame.putalpha(selected_alpha)
        target = HERE / 'sites' / name
        target.mkdir(parents=True, exist_ok=True)
        frame.save(target / 'top-outline-study-v1.png', compress_level=9)
        bbox = selected_alpha.point(lambda v: 255 if v >= 8 else 0).getbbox()
        if bbox is None:
            raise ValueError('No painted pixels at ' + name)
        crop = frame.crop(bbox)
        crop.save(target / 'top-reference-v1.png', compress_level=9)
        xx, yy = 10 + index % 4 * 250, 24 + index // 4 * 195
        board.paste(crop, (xx, yy), crop)
        labels.text((xx, yy - 17), name, fill='#eee4ca')
        results.append({'site': name, 'top_state': site['top'], 'bbox': list(bbox),
                        'source': (target / 'top-outline-study-v1.png').relative_to(HERE).as_posix(),
                        'sha256': hashlib.sha256((target / 'top-outline-study-v1.png').read_bytes()).hexdigest()})
    board.save(HERE / 'all-sites-outline-study-v1.png')
    (HERE / 'outline-study-v1.json').write_text(json.dumps({
        'status': 'design proposal', 'not_final_masks': True, 'sites': results}, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
