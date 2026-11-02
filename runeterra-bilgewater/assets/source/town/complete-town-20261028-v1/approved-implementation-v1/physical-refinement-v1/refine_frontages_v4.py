"""Versioned source-inspected access candidates for the remaining real states.

These are doorway/frontage observations, not a physical terrain or contact pass.
All old terrain inputs remain fixed and every unresolved floor/route stays open.
"""
from pathlib import Path
from copy import deepcopy
import hashlib
import json
from PIL import Image, ImageDraw, ImageChops

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[5]
OUT = HERE / 'semantic-candidate-v4'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')

def trace(row):
    mask = Image.new('L', (800,374))
    draw = ImageDraw.Draw(mask)
    for polygon in row.get('polygons', []):
        draw.polygon(list(map(tuple, polygon)), fill=255)
    for line in row.get('lines', []):
        draw.line(list(map(tuple, line['points'])), width=line['width'], fill=255)
    for point in row.get('pixels', []):
        draw.point(tuple(point), fill=255)
    return mask

OUT.mkdir(exist_ok=False)
ancestry = HERE / 'semantic-candidate-v3/annotations.json'
annotation = json.loads(ancestry.read_text())
annotation['frontage_ancestry'] = {'path': ancestry.relative_to(PROJECT).as_posix(), 'sha256': sha(ancestry)}
index = json.loads((HERE / 'lower-roost-registration-v1/states.json').read_text())
edits = {
    'castle': ([248,90], [[243,82],[254,82],[256,95],[269,103],[271,108],[260,106],[246,98],[243,94]], [[270,107],[275,110]], 'The developed fortress portal is the eastern lit opening, not the former225,90 central wall/column anchor; the route follows its actual entrance steps.'),
    'fort': ([189,87], [[182,80],[193,80],[195,92],[203,97],[203,100],[193,96],[183,92]], [[201,99],[202,103]], 'Lower fortress central gate and its short stone threshold; no long traversal across the entire retaining fascia is declared.'),
    'citadel': ([205,87], [[198,80],[211,80],[212,92],[217,96],[217,100],[208,97],[199,92]], [[216,99],[218,103]], 'Intermediate fortress gate and real entrance sill; its lower whole-layer registration is inherited from the released parent cohort.'),
    'dwellingLvl1': ([133,240], [[128,232],[139,232],[141,246],[147,249],[147,252],[135,250],[130,245]], [[146,251],[151,252]], 'Sailors lodge lit doorway and its open right deck exit, excluding the timber retaining fascia below the floor.'),
    'dwellingUpLvl1': ([133,240], [[128,232],[139,232],[141,246],[147,249],[147,252],[135,250],[130,245]], [[146,251],[151,252]], 'Developed sailors lodge doorway and right deck landing; its independently painted hidden timber bed is not relabelled as an open route.'),
    'dwellingLvl2': ([335,270], [[330,261],[341,261],[342,278],[348,280],[348,285],[332,285],[331,276]], [[347,284],[352,287]], 'Corsair hall eastern ground doorway and right end of its own porch, rather than the former route through front support posts.'),
    'dwellingUpLvl2': ([336,273], [[330,265],[341,265],[343,280],[349,282],[349,286],[332,286],[330,278]], [[348,285],[353,288]], 'Developed corsair hall eastern open landing and lower porch. The main mast/canopy is not treated as access.'),
    'dwellingLvl3': ([308,175], [[303,168],[312,168],[315,179],[318,180],[318,183],[307,182],[304,178]], [[317,182],[324,184]], 'Open cannon-battery eastern deck exit, beside its pavilion, not a line across the closed front retaining face.'),
    'dwellingUpLvl3': ([315,174], [[309,168],[319,168],[321,178],[321,184],[311,184],[309,178]], [[320,183],[326,186]], 'Developed battery open eastern platform frontage; cannon muzzles, retaining wall and roof remain solid.'),
    'special1': ([652,200], [[647,193],[656,193],[658,205],[656,211],[646,211],[645,205]], [[652,210],[652,215]], 'Small Buhru shrine portal and its central entry steps. Lateral retaining faces are not a walkable approach.'),
    'dwellingLvl4': ([631,195], [[626,185],[637,185],[639,201],[639,210],[626,210],[625,202]], [[632,209],[632,214]], 'Lower temple doorway is the left lit opening around631,195, not the later grand temple doorway at651,200.'),
    'dwellingUpLvl4': ([651,192], [[643,185],[660,185],[661,203],[656,211],[656,223],[643,223],[643,212],[640,205]], [[650,222],[649,228]], 'Grand Buhru central portal and the actual tapered staircase to its lower sole. No lateral passage through the left serpent pedestal is declared.'),
    'dwellingLvl6': ([570,139], [[565,130],[575,130],[577,144],[580,147],[580,149],[567,149],[566,143]], [[579,148],[582,151]], 'Lower captains lodge real right-hand doorway and its east porch, avoiding the old brush extending below the native frame.'),
    'dwellingUpLvl6': ([565,140], [[560,131],[570,131],[572,146],[573,152],[561,152],[559,145]], [[570,151],[570,156]], 'Developed captains lodge ground doorway and central forward steps, not the roof or upper balcony.'),
    'special2': ([576,140], [[570,133],[581,133],[583,144],[587,147],[587,149],[573,149],[571,145]], [[586,148],[591,151]], 'Captains flag-and-monument open forecourt; east edge of its real paving rather than an out-of-bounds central brush.'),
    'resourceSilo': ([29,211], [[24,203],[34,203],[37,216],[40,220],[40,223],[30,220],[25,215]], [[39,222],[44,226]], 'Supply warehouse ground opening and front wooden quay threshold. The elevated loading crane is not the entrance.'),
    'tavern': ([622,270], [[616,261],[628,261],[631,278],[635,283],[635,287],[620,286],[617,278]], [[634,286],[639,290]], 'Tavern eastern porch opening and its right-hand public landing. The route does not cross the support wall below its deck.'),
    'grail': ([330,310], [[327,306],[334,306],[336,312],[336,314],[327,314],[326,311]], [[335,313],[341,314]], 'Open beacon pedestal frontage on the quay; the flame itself is not an entrance or structural contact.'),
    'shipyard': ([638,305], [[634,302],[646,302],[649,306],[646,310],[637,309]], [[638,308],[630,307]], 'The original coastal jetty shore landing. Only actual bounded deck/piling and hull contacts may claim marine support.'),
    'ship': ([638,305], [[634,302],[646,302],[649,306],[646,310],[637,309]], [[638,308],[630,307]], 'The real replacement ship state includes the jetty and moored hull. Shore access uses the jetty landing; no walk on open water or duplicate boat is invented.'),
}
for key, (anchor, door, approach, note) in edits.items():
    row = annotation['states'][key]
    row['entrance'] = anchor
    row['door'] = {'polygons': [door]}
    row['approach'] = {'lines': [{'points': approach, 'width': 2}]}
    row['frontage_interpretation'] = note
    row['source_frontage_review'] = 'Native source inspected; terrain level, complete contacts and global route remain separately unaccepted.'
for key in ('dwellingLvl3','dwellingUpLvl3','special2'):
    annotation['states'][key]['access_kind'] = 'open-site'
write(OUT / 'annotations.json', annotation)
measurements = {}
for key, row in annotation['states'].items():
    frame = Image.open(PROJECT / index['states'][key]['frame']).convert('RGBA')
    alpha = frame.getchannel('A')
    body = alpha.point(lambda p: 255 if p >= 128 else 0)
    full = alpha.point(lambda p: 255 if p >= 8 else 0)
    door = trace(row['door'])
    approach = trace(row['approach'])
    bbox = full.getbbox()
    inside = Image.new('L', frame.size)
    ImageDraw.Draw(inside).rectangle((bbox[0],bbox[1],bbox[2]-1,bbox[3]-1), fill=255)
    crossing = ImageChops.multiply(approach, ImageChops.subtract(body,door))
    outside = ImageChops.subtract(door,inside)
    measurements[key] = {
        'own_solid_crossing_pixels': sum(bool(v) for v in crossing.get_flattened_data()),
        'door_outside_native_bbox_pixels': sum(bool(v) for v in outside.get_flattened_data()),
        'anchor_in_frontage': bool(door.getpixel(tuple(row['entrance']))),
        'terrain_or_public_route_pass_claimed': False,
    }
write(OUT / 'local-frontage-measurements.json', {'status': 'authored configuration', 'state_count': len(measurements), 'measurements': measurements})
print(json.dumps(measurements, indent=2))
