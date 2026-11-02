"""Explicit reviewed same-pose rectangular layout assembly, no pixel repaint."""
from pathlib import Path
import json
import sys

PROJECT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT / 'scripts'))
from creature_dragonguard_motion_art import repack

survey = json.loads((PROJECT / 'references/prototypes/dragonguard-family-v3/alpha8-components-survey-v1.json').read_text())
failures = []
for item in survey:
    unit, group = item['unit'], item['group']
    folder = PROJECT / 'assets/source/creatures' / unit / 'dragonguard-rig-v3'
    path = folder / f'paint-action-g{group:02}-atlas-v1-generation.json'
    record = json.loads(path.read_text())
    columns, rows = record['layout']
    cell_width, cell_height = record['returned_cell']
    actual_width, actual_height = record['returned_dimensions']
    frames = [None] * (columns * rows)
    parts = [component for component in item['components_alpha8_at_least40pixels'] if component['pixels'] > 1000]
    assert len(parts) == len(frames)
    for part in parts:
        x0, y0, x1, y1 = part['bounds']
        col, row = int((x0+x1)/2/cell_width), int((y0+y1)/2/cell_height)
        index = row * columns + col
        assert frames[index] is None
        rectangle = [max(0,x0-2), max(0,y0-2), min(actual_width,x1+2), min(actual_height,y1+2)]
        frames[index] = {'reviewed': True, 'neighbor_pixels_absent': True,
            'basis': 'Actual full creative atlas and alpha8 body/weapon component bounds inspected. This exact same-pose rectangular ROI recovers complete boots/long polearm across nominal grid gutters; no resize, mask painting, pose manufacture or limb warp. Near-transparent outside-ROI speckles excluded. One common64px translation relative to original cell origin.',
            'pieces': [{'source_rect': rectangle, 'destination_offset': [int(rectangle[0]-col*cell_width+64), int(rectangle[1]-row*cell_height+64)]}]}
    # Shared gutters with genuine different poses in separate vertical bands
    # require explicit same-translation split rectangles rather than a box fit.
    overrides = {
        ('dragonguard',5): {4: [[539,772,1032,880],[539,880,1049,930]], 5: [[1032,788,1536,880],[1049,880,1536,943]]},
        ('dragonguard',11): {3: [[91,538,600,650],[91,650,612,977]], 4: [[600,586,980,650],[612,650,980,975]]},
        ('dragonguard',13): {3: [[39,654,594,800],[39,800,645,970]], 4: [[597,603,1044,800],[645,800,1044,971]]},
        ('veteranDragonguard',5): {3: [[47,653,532,730],[47,730,508,943]], 4: [[511,739,1013,943]]},
        ('veteranDragonguard',11): {3: [[58,545,655,700],[58,700,600,969]], 4: [[655,578,1023,700],[604,700,1023,962]]},
        ('veteranDragonguard',13): {3: [[44,635,616,775],[44,775,616,954]], 4: [[619,592,1076,962]]},
    }
    for index, rectangles in overrides.get((unit,group), {}).items():
        col,row=index%columns,index//columns
        frames[index]['pieces']=[{'source_rect':rectangle, 'destination_offset':[int(rectangle[0]-col*cell_width+64),int(rectangle[1]-row*cell_height+64)]} for rectangle in rectangles]
        frames[index]['basis'] += ' Explicit shared-gutter bands inspected; each retained piece has the SAME integer translation.'
    try:
        repack(PROJECT, path, frames, cell_size=768, version=3 if (unit,group) in {('veteranDragonguard',11),('dragonguard',5)} else 2)
        print(unit, group, 'lossless exact-pose layout assembled')
    except ValueError as error:
        failures.append({'unit': unit, 'group': group, 'error': str(error)})
        print(unit, group, 'REQUIRES REVIEW', error)
report = PROJECT / 'assets/source/creatures/dragonguard-family-repack-survey-v1.json'
report.write_text(json.dumps({'source_review': 'references/prototypes/dragonguard-family-v3/alpha8-components-survey-v1.json',
    'failures': failures, 'active_assets_modified': False, 'visual_approval_granted': False}, indent=2)+'\n',encoding='utf-8')
if failures: raise SystemExit(1)
