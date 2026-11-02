"""Bounded source-plane proof and reviewable, unselected stair alternative.

This does not infer walkability from colour or a body-free path. It preserves
the actual hand-observed upper paving and separately labels the exposed cliff.
"""
from pathlib import Path
from collections import deque
import hashlib
import json
from PIL import Image, ImageDraw, ImageChops

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[5]
BASE = HERE.parent
OUT = HERE / 'route-conflict-v1'
OUT.mkdir(exist_ok=False)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def ref(path):
    return {'path': path.relative_to(PROJECT).as_posix(), 'sha256': sha(path)}

def count(mask):
    return sum(bool(v) for v in mask.get_flattened_data())

def mask(polygon):
    result = Image.new('L', (800,374))
    ImageDraw.Draw(result).polygon(list(map(tuple,polygon)),fill=255)
    return result

def component(allowed,start):
    seen = {tuple(start)}
    queue = deque(seen)
    while queue:
        x,y = queue.popleft()
        for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0 <= nx < 800 and 0 <= ny < 374 and (nx,ny) not in seen and allowed.getpixel((nx,ny)):
                seen.add((nx,ny))
                queue.append((nx,ny))
    result = Image.new('L',allowed.size)
    draw = ImageDraw.Draw(result)
    for point in seen:
        draw.point(point,fill=255)
    return result

index_path = HERE / 'lower-roost-registration-v1/states.json'
index = json.loads(index_path.read_text())
annotation_path = HERE / 'semantic-candidate-v6/annotations.json'
annotation = json.loads(annotation_path.read_text())
approved_path = BASE / 'approved-full-source-v1.png'
assert sha(approved_path) == '4f8cac4f1801ed366e0bacd4934084e9b76e0d25c282b3f3b36fda3835cd0712'
approved = Image.open(approved_path).convert('RGBA')
background_path = PROJECT / index['background']
background = Image.open(background_path).convert('RGBA')

# Exact horizontal top contour observed in native empty and developed source.
# Below it are upright retaining/ivy faces, not another horizontal pavement.
upper_paving_polygon = [[599,103],[623,102],[646,104],[666,104],[684,104],[695,107],[697,111],[688,113],[671,114],[650,113],[629,111],[607,109],[599,108]]
upper = mask(upper_paving_polygon)
upper.save(OUT / 'observed-upper-horizontal-paving.png')
cliff_polygon = [[598,111],[611,112],[633,116],[651,116],[666,116],[689,116],[700,114],[700,156],[678,171],[649,171],[622,164],[609,150],[597,143]]
cliff = mask(cliff_polygon)
cliff.save(OUT / 'observed-vertical-cliff-zone.png')
all_body = Image.new('L', (800,374))
full_body = Image.new('L', (800,374))
for key,row in index['states'].items():
    alpha = Image.open(PROJECT / row['frame']).convert('RGBA').getchannel('A')
    body = alpha.point(lambda p:255 if p>=128 else 0)
    all_body = ImageChops.lighter(all_body, body)
    if key in annotation['complete_scene_states']:
        full_body = ImageChops.lighter(full_body, body)
all_body.save(OUT / 'all35-actual-opaque-bodies.png')
full_body.save(OUT / 'current-full-actual-opaque-bodies.png')
start,end = [624,108],[591,172]
free_upper = ImageChops.subtract(upper,all_body)
assert free_upper.getpixel(tuple(start))
reached = component(free_upper,start)
reached.save(OUT / 'upper-free-connected-component.png')

parent_study_path = BASE / 'route-feasibility-v1/study.json'
parent_study = json.loads(parent_study_path.read_text())
assert parent_study['candidate_path_under_full_functional_opaque_budget'] == 0
assert parent_study['candidate_path_pixels'] == 98

overlay = approved.copy()
for region, colour in ((upper,(30,220,240,120)),(cliff,(245,50,100,70))):
    layer = Image.new('RGBA',(800,374),colour)
    layer.putalpha(region.point(lambda p:colour[3] if p else 0))
    overlay = Image.alpha_composite(overlay,layer)
draw = ImageDraw.Draw(overlay)
draw.ellipse((621,105,627,111),fill=(0,255,255))
draw.ellipse((588,169,594,175),fill=(255,210,0))
overlay.save(OUT / 'source-plane-overlay.png')
overlay.crop((536,84,710,181)).resize((1044,582),Image.Resampling.NEAREST).save(OUT / 'source-plane-nearest6x.png')
approved.crop((536,84,710,181)).resize((1044,582),Image.Resampling.NEAREST).save(OUT / 'current-native-nearest6x.png')
background.crop((536,84,710,181)).resize((1044,582),Image.Resampling.NEAREST).save(OUT / 'empty-native-nearest6x.png')

raw = HERE / 'proposal-only/stair-alternative-master-v3-raw.png'
permit_path = HERE / 'proposal-only/permitted-correction-visible-mask.png'
permit = Image.open(permit_path).convert('L')
protected_path = HERE / 'proposal-only/protected-full-architecture.png'
protected = Image.open(protected_path).convert('L')
assert not ImageChops.multiply(permit,protected).getbbox()
painted_native = Image.open(raw).convert('RGBA').resize((62,76),Image.Resampling.LANCZOS)
painted_native.save(OUT / 'painted-stair-native.png',compress_level=9)
canvas = approved.copy()
canvas.paste(painted_native,(576,102))
alternative = Image.composite(canvas,approved,permit)
alternative.save(OUT / 'full-proposal-only.png',compress_level=9)
difference = ImageChops.difference(approved,alternative)
exact = Image.new('L',difference.size)
for band in difference.split():
    exact = ImageChops.lighter(exact,band.point(lambda p:255 if p else 0))
exact.save(OUT / 'exact-visible-change-mask.png')
assert not ImageChops.subtract(exact,permit).getbbox()
assert not ImageChops.multiply(exact,protected).getbbox()
alternative.crop((536,84,710,181)).resize((1044,582),Image.Resampling.NEAREST).save(OUT / 'alternative-native-nearest6x.png')
record = {
    'status':'design proposal','approved_full':ref(approved_path),'released_background':ref(background_path),
    'cohort':ref(index_path),'actual_frontage_annotations':ref(annotation_path),
    'upper_paving_polygon':upper_paving_polygon,'upper_paving':ref(OUT / 'observed-upper-horizontal-paving.png'),
    'observed_cliff_polygon':cliff_polygon,'source_inspection':'Native empty and fully developed painting, not inherited support-mask fitting.',
    'source_observed_route_alternatives':[
        {'direction':'west','observation':'The upper pavement meets the Fleet/Captains masonry footprint; no open ground-level gate or arcade is depicted through that architecture. The developed building roof and dark wall cannot serve as doors.'},
        {'direction':'north','observation':'The Roost timber building, raised platform and rocky rear garden occupy the upper boundary. No source-visible lower public stair exits north.'},
        {'direction':'east','observation':'The narrow pavement ends at the exposed sea cliff and palm vegetation, with open water beyond. No east stair or bridge is painted.'},
        {'direction':'south','observation':'The existing lower Fleet switchback terminates near591,172. Between it and the upper pavement are visible upright ivy/rock faces. A body-clear98pixel corridor exists, but68pixels are outside the earlier walk trace and0pixels are hidden by the current full functional actors.'},
    ],
    'actual_upper_body_clear_component_pixels':count(reached),
    'actual_upper_component_reaches_lower_stair':bool(reached.getpixel(tuple(end))),
    'component_scope':'Bounded necessary upper-landing connectivity check; it does not certify all other town floors or replace the unchanged public consumer.',
    'prior_actual_body_clear_study':ref(parent_study_path),
    'hidden_only_change_can_repaint_the_studied_gap':False,
    'reason_hidden_only_is_insufficient':'The98pixel necessary studied connection is entirely outside the current full actor opaque budget. Classifying visible upright cliff as path would change semantics without painting the required stair/support.',
    'minimal_corrective_alternatives':[
        {'id':'retain-approved-full','effect':'Keep selected pixels immutable; connected public access remains unresolved and physical acceptance cannot be claimed.'},
        {'id':'paint-narrow-supported-stair','effect':'Use the preserved genuinely painted alternative, after explicit selection and complete physical verification. No building is moved or repainted.'},
    ],
    'unselected_genuine_stair_master':ref(raw),
    'unselected_genuine_stair_prompt':ref(HERE / 'proposal-only/stair-alternative-prompt-v3.txt'),
    'proposal_preplanned_corridor_polygon':[[613,103],[632,110],[621,125],[614,141],[602,158],[598,176],[583,177],[584,158],[591,144],[598,128],[603,115]],
    'proposal_permitted_visible_change_mask':ref(permit_path),
    'proposal_actual_visible_change_mask':ref(OUT / 'exact-visible-change-mask.png'),
    'proposal_exact_visible_changed_pixels':count(exact),
    'proposal_protected_architecture_changed_pixels':0,'proposal_outside_corridor_changed_pixels':0,
    'proposal_full':ref(OUT / 'full-proposal-only.png'),
    'proposal_selected':False,'complete_physical_baseline_passed':False,'meaningful_physical_negative_controls_executed':False,
    'native_executed':False,'release_accepted':False,
}
(OUT / 'conflict-and-alternative.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({'changed_pixels':count(exact),'unchanged_current_full_sha256':sha(approved_path),'upper_component_pixels':count(reached)}))
