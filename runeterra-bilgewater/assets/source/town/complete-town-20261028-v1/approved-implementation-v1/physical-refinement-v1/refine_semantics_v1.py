"""Explicit source-pixel frontage corrections and independent terrain review.

This writes technical candidates only. It does not certify a whole physical
baseline, author game art, modify any released frame or select a runtime stage.
"""
from pathlib import Path
from copy import deepcopy
import hashlib
import json

from PIL import Image, ImageDraw, ImageChops

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
PROJECT = HERE.parents[5]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path):
    return {'path': path.relative_to(PROJECT).as_posix(), 'sha256': sha(path)}


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def line(points, width=1):
    return {'lines': [{'points': points, 'width': width}]}


def polygon(points):
    return {'polygons': [points]}


def main():
    output = HERE / 'semantic-candidate-v1'
    output.mkdir(exist_ok=False)
    original = BASE / 'physical-tools-v1/manual-inputs-v4/annotations.json'
    annotation = json.loads(original.read_text())
    index_path = BASE / 'states-hidden-support-v6.json'
    index = json.loads(index_path.read_text())
    annotation['status'] = 'design proposal'
    annotation['ancestry'] = ref(original)
    annotation['state_index_sha256'] = sha(index_path)
    annotation['background'] = {'path': index['background'], 'sha256': index['background_sha256']}
    annotation['review_limits'] = 'Whole source baseline remains unaccepted. These are explicit source observations; unresolved route and remaining state roots stay open.'
    # The old large brushes ran beyond real silhouettes or through furnace/wall
    # pixels. Each correction follows a visible threshold and its own entry apron.
    frontages = {
        'blacksmith': ([222,294], [[216,286],[230,286],[234,305],[218,305]], [[226,305],[226,311]],
                       'The central dark workshop opening and its front floor, not the bright forge/firebox at239,284.'),
        'capitol': ([385,122], [[381,114],[391,114],[394,128],[385,128]], [[393,128],[395,133]],
                    'Central civic doorway threshold; the former five-pixel brush extended below the actual131px frame bottom.'),
        'cityHall': ([385,122], [[380,115],[391,115],[394,129],[385,129]], [[393,129],[395,133]],
                     'Central civic threshold and short front apron, excluding the public retaining face.'),
        'townHall': ([385,121], [[380,114],[391,114],[394,128],[385,128]], [[393,128],[395,133]],
                     'Central civic doorway and its short original stone apron.'),
        'villageHall': ([389,121], [[384,115],[393,115],[394,128],[386,128]], [[393,128],[395,133]],
                        'Small civic doorway and short threshold rather than a rectangle below the real cutout.'),
        'mageGuild1': ([501,126], [[498,120],[504,120],[506,132],[499,132]], [[505,132],[507,135]],
                       'Actual archive threshold with a short stone entry apron; separate tower-column feet remain structural.'),
        'mageGuild2': ([501,125], [[498,119],[504,119],[506,132],[499,132]], [[505,132],[507,135]],
                       'Archive ground doorway and its own entry sill; no upper clock face is treated as access.'),
        'mageGuild3': ([500,123], [[496,117],[504,117],[505,132],[499,132]], [[504,132],[507,135]],
                       'Tall archive ground doorway and lower sill; masonry column contacts are independently retained.'),
        'dwellingLvl5': ([655,110], [[650,103],[660,103],[661,114],[650,114]], [[654,114],[624,108]],
                         'Roost ground-floor opening and actual upper-street frontage. Connection to the lower public network is unresolved.'),
        'dwellingUpLvl5': ([655,108], [[650,102],[660,102],[661,111],[650,111]], [[654,111],[624,108]],
                           'Developed Roost opening on its real upper pavement, not the exposed ivy cliff. Global route remains unresolved.'),
        'dwellingLvl7': ([190,182], [[181,179],[192,179],[194,185],[185,185]], [[194,184],[200,184]],
                         'The accessible eastern stone-basin frontage, not a line through the entire water-spray statue.'),
        'dwellingUpLvl7': ([190,182], [[181,179],[193,179],[194,185],[185,185]], [[194,184],[200,184]],
                           'Eastern pool-side stone frontage; falling-water effects are not a walkable entrance or structural feet.'),
        'special4': ([479,191], [[474,184],[484,184],[485,201],[475,201]], [[483,201],[484,204]],
                     'Actual treasury portal base and short forward sill. Public retaining wall below remains terrain.'),
        'special3': ([105,315], [[97,307],[112,307],[112,319],[97,319]], [[111,318],[174,318]],
                     'Actual front market aisle at deck height; below-deck public marine piles are not ordinary building feet.'),
        'marketplace': ([523,317], [[352,313],[397,317],[455,319],[503,318],[544,313],[544,320],[500,324],[450,324],[397,322],[352,318]], [[543,317],[552,317]],
                        'Open trade-front aisle on the actual public quay. No solid stall roof is declared a doorway.'),
    }
    corrected = []
    for key, (entrance, doorway, approach, interpretation) in frontages.items():
        row = annotation['states'][key]
        row['entrance'] = entrance
        row['door'] = polygon(doorway)
        row['approach'] = line(approach)
        row['frontage_interpretation'] = interpretation
        row['source_frontage_review'] = 'native contact study directly inspected; full physical/occlusion checks pending'
        corrected.append(key)
    # Source-visible basin masonry is distinct from its bright falling-water
    # effect. Preserve the separate left and right actual plinth seams.
    for key in ('dwellingLvl7', 'dwellingUpLvl7'):
        annotation['states'][key]['foundation'] = {
            'lines': [
                {'points': [[99,178],[111,181],[128,183]], 'width': 1},
                {'points': [[168,183],[181,184],[191,182]], 'width': 1}],
            'pixels': [[136,184],[150,184]]}
        annotation['states'][key]['contact_interpretation'] = 'Native inspected stone basin/plinth seams and two detached actual pedestal feet. Cyan falling-water fringes below/behind are excluded as effects, not structurally cropped.'
    annotation['states']['blacksmith']['foundation'] = line([[158,288],[175,297],[197,300],[234,302],[267,297]])
    annotation['states']['blacksmith']['contact_interpretation'] = 'Complete visible workshop lower sill and separated end posts, traced on the actual timber/stone base. The former y285 trace was a wall/furnace level rather than the workshop ground seam.'
    # Terrain review is independent of the feet. The dry settlement includes
    # cliff ownership, whereas level support/stairs remain separate fields.
    terrain = json.loads((BASE / 'physical-tools-v1/manual-inputs-v3/terrain-annotations.json').read_text())
    terrain['background'] = annotation['background']
    terrain['status'] = 'design proposal'
    terrain['ancestry'] = ref(BASE / 'physical-tools-v1/manual-inputs-v3/terrain-annotations.json')
    terrain['notes'].append('V6 native source inspected. Newly painted hidden floor recoveries require their own horizontal top traces; old support strips and public-route gaps are not assumed correct.')
    save(output / 'terrain-observations.json', terrain)
    # Current terrain bitmaps stay immutable until the entire actual top/face
    # boundary is retraced; no contact-driven union or support mask growth.
    save(output / 'annotations.json', annotation)
    save(output / 'correction-scope.json', {
        'status': 'design proposal', 'approved_full': ref(BASE / 'approved-full-source-v1.png'),
        'cohort': ref(index_path), 'source_frames_modified': False,
        'corrected_frontage_states': corrected,
        'corrected_structural_trace_states': ['blacksmith','dwellingLvl7','dwellingUpLvl7'],
        'terrain_masks_modified': False, 'global_route_passed': False,
        'remaining': ['Source-faithful remaining structural contacts and doorways',
                      'Independent full level/stair/water/support retrace',
                      'Source-depicted connected public routes, especially Roost/Fleet conflict',
                      'Actual complete public-consumer baseline and meaningful displacement negatives']})
    print(json.dumps({'frontages_corrected': len(corrected), 'physical_baseline_passed': False}))


if __name__ == '__main__':
    main()
