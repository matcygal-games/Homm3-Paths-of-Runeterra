"""Search bounded integer translations of the whole existing Menagerie family.
Only reports proposals. Frozen source art and entry masks are never changed.
"""
from pathlib import Path
from PIL import Image, ImageChops
import json, hashlib
import numpy as np
HERE = Path(__file__).resolve().parent
TOWN = HERE.parent
ROOT = HERE.parents[4]
REPORT = ROOT / 'build/reports/complete-town-20261027-v2/geometry-final-v2/menagerie-translation-search-v1'
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path): return json.loads(path.read_text(encoding='utf8'))
def main():
    if REPORT.exists(): raise ValueError('Preserve previous search')
    REPORT.mkdir(parents=True)
    selection = load(TOWN / 'candidate-final-v5/selection.json')
    entries = {row['state']: row for row in load(TOWN / 'entry-spans-v2/entries.json')['states']}
    state_rows = {row['state']: row for row in selection['states']}
    def blank(): return Image.new('L', (800, 374))
    def pack(image): return (np.asarray(image) > 0, image.getbbox())
    bodies, roots, doors, silhouettes = {}, {}, {}, {}
    pins = {}
    for site in selection['sites']:
        body, root, door, silhouette = blank(), blank(), blank(), blank()
        for state in site['states']:
            path = ROOT / state_rows[state]['native_layer']
            if sha(path) != state_rows[state]['native_layer_sha256']: raise ValueError('Frozen frame changed: '+state)
            pins[str(path.relative_to(ROOT))] = sha(path)
            image = Image.open(path).convert('RGBA')
            body = ImageChops.lighter(body, image.getchannel('A').point(lambda a: 255 if a >= 128 else 0))
            silhouette = ImageChops.lighter(silhouette, image.getchannel('A').point(lambda a: 255 if a >= 8 else 0))
            root = ImageChops.lighter(root, Image.open(TOWN / 'physical-v10' / state / 'foundation.png').convert('L'))
            path = ROOT / entries[state]['mask']['path']
            if sha(path) != entries[state]['mask']['sha256']: raise ValueError('Frozen entry changed')
            door = ImageChops.lighter(door, Image.open(path).convert('L'))
        bodies[site['id']], roots[site['id']], doors[site['id']], silhouettes[site['id']] = map(pack, (body, root, door, silhouette))
    sites = {site['id']: site for site in selection['sites']}
    def overlap(moved, other, dx=0, dy=0):
        array, box = moved
        other_array, other_box = other
        left, top = max(box[0]+dx, other_box[0], 0), max(box[1]+dy, other_box[1], 0)
        right, bottom = min(box[2]+dx, other_box[2], 800), min(box[3]+dy, other_box[3], 374)
        if left >= right or top >= bottom: return 0
        return int(np.count_nonzero(array[top-dy:bottom-dy, left-dx:right-dx] & other_array[top:bottom, left:right]))
    target = 'dwellingRose'
    depth = sites[target]['native_z']
    original_pairs = set()
    for sid, site in sites.items():
        if site['native_z'] < depth and overlap(bodies[target], roots[sid]): original_pairs.add((sid, target))
        if site['native_z'] > depth and overlap(roots[target], bodies[sid]): original_pairs.add((target, sid))
    water = pack(Image.open(HERE / 'water.png').convert('L'))
    box = silhouettes[target][1]
    accepted, cleared_with_new_pairs = [], []
    for dx in range(-30, 31):
        for dy in range(-30, 31):
            if not (0 <= box[0]+dx < box[2]+dx <= 800 and 0 <= box[1]+dy < box[3]+dy <= 374): continue
            if overlap(roots[target], water, dx, dy): continue
            conflicts, pair_counts = [], []
            for sid, site in sites.items():
                if sid == target: continue
                if site['native_z'] < depth:
                    count = overlap(bodies[target], doors[sid], dx, dy)
                    if count: conflicts.append({'rear': sid, 'front': target, 'entry_pixels': count})
                    count = overlap(bodies[target], roots[sid], dx, dy)
                    if count: pair_counts.append({'behind': sid, 'front': target, 'pixels': count})
                elif site['native_z'] > depth:
                    count = overlap(doors[target], bodies[sid], dx, dy)
                    if count: conflicts.append({'rear': target, 'front': sid, 'entry_pixels': count})
                    count = overlap(roots[target], bodies[sid], dx, dy)
                    if count: pair_counts.append({'behind': target, 'front': sid, 'pixels': count})
            if conflicts: continue
            new_pairs = [row for row in pair_counts if (row['behind'],row['front']) not in original_pairs]
            record = {'dx': dx, 'dy': dy, 'distance_squared': dx*dx+dy*dy, 'manhattan': abs(dx)+abs(dy), 'all_family_entry_conflicts': [], 'root_projection_pairs': pair_counts, 'new_root_projection_pairs': new_pairs, 'silhouette_bbox': [box[0]+dx,box[1]+dy,box[2]+dx,box[3]+dy], 'root_union_bbox': [value+offset for value,offset in zip(roots[target][1], (dx,dy,dx,dy))]}
            (cleared_with_new_pairs if new_pairs else accepted).append(record)
    key = lambda row: (row['distance_squared'], row['manhattan'], abs(row['dy']), row['dx'], row['dy'])
    accepted.sort(key=key)
    cleared_with_new_pairs.sort(key=key)
    for relative, pin in pins.items():
        if sha(ROOT / relative) != pin: raise ValueError('Frame changed during search')
    result = {'status': 'design proposal', 'scope': 'Whole base+upgrade Menagerie family integer translation only; all actual current family entry spans versus every other source body/entry, exact root pair inventory, native frame bounds and external water checked. No placement or art modified.', 'source_selection_sha256': sha(TOWN/'candidate-final-v5/selection.json'), 'source_entries_sha256': sha(TOWN/'entry-spans-v2/entries.json'), 'source_frame_pins': pins, 'search_bounds': [-30,-30,30,30], 'original_target_root_pairs': [list(pair)for pair in sorted(original_pairs)], 'candidates_clearing_entries_without_new_root_pairs': accepted[:20], 'smaller_candidates_that_clear_entries_but_add_root_pairs': cleared_with_new_pairs[:20], 'candidate_count_no_new_root_pairs': len(accepted), 'candidate_count_with_new_root_pairs': len(cleared_with_new_pairs), 'remaining_requirements': ['Actual final floor support and independently traced approach routes at new feet.', 'Exact all-state silhouette overlaps, complete source scene and source-case evidence must be regenerated.', 'Coordinator/source owner review of corrected full city and source fidelity.', 'No whole-town positive or native acceptance is implied.']}
    (REPORT/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'best_without_new_root_pairs': accepted[:5], 'best_allowing_new_root_pairs': cleared_with_new_pairs[:5], 'candidates_no_new_pairs':len(accepted)}))
if __name__ == '__main__': main()
