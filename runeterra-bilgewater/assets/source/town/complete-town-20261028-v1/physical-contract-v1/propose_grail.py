"""Whole-ornament technical placement proposals, never selected game artwork.

The held thirty-four-frame cohort and the genuinely painted beacon are read
only. Native context review must still choose/verify an actual level landing.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[4]
TOWN = HERE.parent
REPORT = PROJECT / 'build/reports/complete-town-20261028-v1/physical-contract-v1/grail-proposals-v1'
INDEX_PIN = 'c5eb6af7e638b86a879b51fda03236f0c86eb7f6763724bd4ec6b329139ac0e3'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def points(mask):
    bounds = mask.getbbox()
    return {(x, y) for y in range(bounds[1], bounds[3]) for x in range(bounds[0], bounds[2]) if mask.getpixel((x, y))}


def main():
    REPORT.mkdir(parents=True, exist_ok=False)
    index_path = TOWN / 'derived-v1/states.json'
    if sha(index_path) != INDEX_PIN:
        raise ValueError('Held candidate index changed')
    data = json.loads(index_path.read_text())
    support = Image.open(HERE / 'terrain-trace-v1/support.png').convert('L')
    occupied = set()
    pins = {}
    for state, record in data['states'].items():
        if state == 'grail':
            continue
        path = PROJECT / record['frame']
        if sha(path) != record['frame_sha256']:
            raise ValueError('Held frame changed: ' + state)
        body = Image.open(path).convert('RGBA').getchannel('A').point(lambda a: 255 if a >= 128 else 0)
        occupied.update(points(body))
        pins[state] = sha(path)
    record = data['states']['grail']
    grail_path = PROJECT / record['frame']
    if sha(grail_path) != record['frame_sha256']:
        raise ValueError('Reusable genuine beacon changed')
    native = Image.open(grail_path).convert('RGBA')
    body = native.getchannel('A').point(lambda a: 255 if a >= 128 else 0)
    bounds = native.getchannel('A').getbbox()
    root = record['target_root']
    full_points = points(body)
    # Actual small stone base/contact region in the genuine beacon pixels.
    foot_region = Image.new('L', body.size)
    ImageDraw.Draw(foot_region).polygon([(309, 317), (313, 316), (320, 317), (321, 319), (318, 320), (312, 320), (309, 319)], fill=255)
    feet = full_points & points(foot_region)
    if len(feet) < 10:
        raise ValueError('Actual beacon base witness is missing')
    body_local = {(x - root[0], y - root[1]) for x, y in full_points}
    feet_local = {(x - root[0], y - root[1]) for x, y in feet}
    support_points = points(support)
    candidates = []
    for x, y in sorted(support_points, key=lambda p: (p[1], p[0])):
        dx, dy = x - root[0], y - root[1]
        if not (0 <= bounds[0] + dx < bounds[2] + dx <= 800 and 0 <= bounds[1] + dy < bounds[3] + dy <= 374):
            continue
        if any((x + px, y + py) not in support_points for px, py in feet_local):
            continue
        if any((x + px, y + py) in occupied for px, py in body_local):
            continue
        score = min((x - 447) ** 2 + (y - 116) ** 2,
                    (x - 315) ** 2 + (y - 300) ** 2 + 400,
                    (x - 425) ** 2 + (y - 215) ** 2 + 900)
        candidates.append((score, x, y))
    chosen = []
    for score, x, y in sorted(candidates):
        if all((x - px) ** 2 + (y - py) ** 2 >= 25 ** 2 for _, px, py in chosen):
            chosen.append((score, x, y))
            if len(chosen) == 6:
                break
    scene_path = PROJECT / 'build/reports/complete-town-20261028-v1/derived-v1/full-native.png'
    scene = Image.open(scene_path).convert('RGBA')
    rows = []
    for number, (score, x, y) in enumerate(chosen, 1):
        moved = Image.new('RGBA', native.size)
        moved.paste(native, (x - root[0], y - root[1]))
        combined = Image.alpha_composite(scene, moved)
        combined.convert('RGB').save(REPORT / f'proposal-{number}-native.png')
        crop_bounds = [max(0, x - 45), max(0, y - 55), min(800, x + 45), min(374, y + 30)]
        crop = combined.crop(tuple(crop_bounds))
        crop.resize((crop.width * 5, crop.height * 5), Image.Resampling.NEAREST).save(REPORT / f'proposal-{number}-context-5x.png')
        rows.append({'proposal': number, 'target_root': [x, y], 'offset_from_unselected_old_registration': [x - root[0], y - root[1]],
                     'base_pixels_on_manually_traced_level_support': len(feet),
                     'body_intersections_with_all_34_other_candidate_states': 0,
                     'context_native_bounds': crop_bounds, 'not_selected': True})
    receipt = {'status': 'design proposal', 'candidate_index_sha256': INDEX_PIN,
               'background_sha256': data['background_sha256'], 'held_34_frame_pins': pins,
               'genuine_beacon_source': record['frame'], 'genuine_beacon_source_sha256': sha(grail_path),
               'terrain_annotations_sha256': sha(HERE / 'terrain-trace-v1/annotations.json'),
               'proposals': rows, 'source_files_modified': False,
               'scope': 'Supported/unoccluded technical proposals only; native pixel/context and connected access review must choose a final placement.',
               'native_executed': False, 'release_accepted': False}
    (REPORT / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(rows, indent=2))


if __name__ == '__main__':
    main()
