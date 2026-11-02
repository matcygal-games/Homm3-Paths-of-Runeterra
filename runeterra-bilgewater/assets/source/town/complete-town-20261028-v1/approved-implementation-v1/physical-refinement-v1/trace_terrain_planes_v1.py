"""Independent terrain ownership and genuine hidden horizontal-top tracing.

Only actual selected painted terrain and its native masters are inputs. This
writer never reads building roots, door masks, proposed displacement or errors.
It does not infer a support bed from a desired contact mask.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw, ImageChops

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[5]
BASE = HERE.parent
OUT = HERE / 'terrain-planes-v1'
OUT.mkdir(exist_ok=False)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def ref(path):
    return {'path':path.relative_to(PROJECT).as_posix(),'sha256':sha(path)}

def polygon(points):
    image = Image.new('L',(800,374))
    ImageDraw.Draw(image).polygon(list(map(tuple,points)),fill=255)
    return image

def union(images):
    result = Image.new('L',(800,374))
    for image in images:
        result = ImageChops.lighter(result,image)
    return result

prior_path = BASE / 'physical-tools-v1/manual-inputs-v3/terrain-annotations.json'
plan = json.loads(prior_path.read_text())
plan['ancestry'] = ref(prior_path)
plan['background'] = ref(BASE / 'background-hidden-support-v6.png')
plan['status'] = 'design proposal'
plan['scope'] = 'Source-observed horizontal tops, individual stairs and dry island ownership. No connected public route or full physical pass is claimed by this terrain-only writer.'
plan['dry_ownership_polygon'] = [[0,99],[35,100],[70,110],[95,98],[110,52],[150,57],[190,66],[240,84],[280,92],[310,101],[335,104],[380,104],[420,107],[465,108],[489,109],[520,110],[550,111],[570,107],[600,104],[628,100],[650,101],[700,110],[712,131],[715,160],[730,164],[730,189],[717,207],[723,222],[745,226],[760,236],[773,251],[785,275],[782,283],[771,279],[761,255],[750,250],[739,251],[731,261],[724,271],[719,282],[707,295],[689,301],[666,300],[649,309],[647,329],[633,342],[611,349],[585,354],[553,356],[526,353],[500,352],[472,354],[443,361],[412,373],[389,369],[365,366],[342,364],[327,360],[310,358],[292,357],[272,354],[260,350],[254,347],[247,354],[230,356],[206,359],[179,357],[151,356],[120,356],[90,355],[58,354],[27,352],[0,350]]
# These are complete horizontal floor/top contours seen in genuine native
# paintings, independent of actor roots. Use only pixels actually selected from
# those paintings; unselected cliff RGB cannot acquire level semantics.
painted_tops = [
    {'id':'genuine-defenses-garden-cap','polygon':[[103,80],[148,85],[189,89],[231,94],[276,102],[280,111],[233,109],[190,104],[147,99],[102,91]],
     'native':'defenses-hidden-support-native-v1.png','selection':'defenses-selected-hidden-support-mask-v1.png','selection_receipt':'defenses-hidden-support-selection-v1.json'},
    {'id':'genuine-archive-paved-top','polygon':[[465,121],[533,120],[536,136],[500,139],[465,133]],
     'native':'archive-hidden-support-native-v1.png','selection':'archive-selected-hidden-support-mask-v1.png','selection_receipt':'additional-hidden-support-selection-v1.json'},
    {'id':'genuine-basin-paved-top','polygon':[[94,173],[126,174],[163,177],[194,176],[200,187],[171,192],[127,192],[94,186]],
     'native':'basin-hidden-support-native-v1.png','selection':'basin-selected-hidden-support-mask-v1.png','selection_receipt':'additional-hidden-support-selection-v1.json'},
    {'id':'genuine-treasury-paved-top','polygon':[[444,184],[520,184],[524,201],[480,205],[444,198]],
     'native':'treasury-hidden-support-native-v1.png','selection':'treasury-selected-hidden-support-mask-v1.png','selection_receipt':'additional-hidden-support-selection-v1.json'},
]
support = union(polygon(row['polygon']) for row in plan['support_regions'])
for row in painted_tops:
    selected_path = BASE / row.pop('selection')
    selected = Image.open(selected_path).convert('L').point(lambda p:255 if p else 0)
    horizontal = ImageChops.multiply(polygon(row['polygon']),selected)
    row['native_source'] = ref(BASE / row.pop('native'))
    row['selected_actual_source_pixels'] = ref(selected_path)
    row['selection_record'] = ref(BASE / row.pop('selection_receipt'))
    support = ImageChops.lighter(support,horizontal)
plan['genuine_selected_horizontal_tops'] = painted_tops
stairs = union(polygon(row['polygon']) for row in plan['stairs_regions'])
water = union(polygon(row['polygon']) for row in plan['water_regions'])
# Dry ownership includes non-walkable cliff/retaining faces. Its shoreline is
# independent of the much smaller horizontal support/stair topology.
land = ImageChops.subtract(polygon(plan['dry_ownership_polygon']),water)
land = ImageChops.lighter(land,union([support,stairs]))
plan['boundary_conflicts'] = {
    'support_stairs_pixels':sum(bool(v) for v in ImageChops.multiply(support,stairs).get_flattened_data()),
    'support_water_pixels':sum(bool(v) for v in ImageChops.multiply(support,water).get_flattened_data()),
    'stairs_water_pixels':sum(bool(v) for v in ImageChops.multiply(stairs,water).get_flattened_data()),
}
paths = Image.open(BASE / 'physical-tools-v1/manual-inputs-v4/paths.png').convert('L')
for role,image in [('land',land),('support',support),('stairs',stairs),('water',water),('paths',paths)]:
    image.save(OUT / (role+'.png'))
plan['masks'] = {role:ref(OUT / (role+'.png')) for role in ('land','support','stairs','water','paths')}
(OUT / 'terrain-plan.json').write_text(json.dumps(plan,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(plan['boundary_conflicts']))
