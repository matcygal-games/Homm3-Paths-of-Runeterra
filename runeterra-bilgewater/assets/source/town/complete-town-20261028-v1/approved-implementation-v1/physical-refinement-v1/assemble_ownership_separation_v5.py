"""Lossless source ownership correction, not a town redesign or publication.

Architectural RGB, retained alpha, real entry parts and detached anatomy stay
byte-identical. Retired permanent ground/scenery is reconstructed from the
approved whole painting outside the actual new architecture. Genuine released
absence/hidden-bed pixels remain underneath construction.
"""
from pathlib import Path
from copy import deepcopy
import hashlib
import json
from PIL import Image, ImageDraw, ImageChops, ImageFilter

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[5]
BASE = HERE.parent
OUT = HERE / 'ownership-separation-v5'
FRAMES = OUT / 'states'
FRAMES.mkdir(exist_ok=False)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def ref(path):
    return {'path':path.relative_to(PROJECT).as_posix(),'sha256':sha(path)}

def save(path,value):
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8')

def blank():
    return Image.new('L',(800,374))

def count(mask):
    return sum(bool(v) for v in mask.get_flattened_data())

index_path = HERE / 'lower-roost-registration-v1/states.json'
index = json.loads(index_path.read_text())
plan_path = OUT / 'plan.json'
plan = json.loads(plan_path.read_text())
assert set(plan['states']) == set(index['states'])
approved_path = BASE / 'approved-full-source-v1.png'
assert sha(approved_path) == '4f8cac4f1801ed366e0bacd4934084e9b76e0d25c282b3f3b36fda3835cd0712'
approved = Image.open(approved_path).convert('RGBA')
old_background_path = PROJECT / index['background']
old_background = Image.open(old_background_path).convert('RGBA')
frames = {}
records = {}
candidate = deepcopy(index)
for key,source_row in index['states'].items():
    spec = plan['states'][key]
    source_path = PROJECT / source_row['frame']
    source = Image.open(source_path).convert('RGBA')
    alpha = source.getchannel('A')
    if spec.get('retain_all'):
        keep = Image.new('L',(800,374),255)
    else:
        boundary = list(map(tuple,spec['boundary']))
        keep = blank()
        draw = ImageDraw.Draw(keep)
        draw.polygon([(0,0),(799,0),(799,boundary[-1][1]),*reversed(boundary),(0,boundary[0][1])],fill=255)
        for polygon in spec.get('permanent_ground_polygons',[]):
            draw.polygon(list(map(tuple,polygon)),fill=0)
        for polygon in spec.get('retain_polygons',[]):
            draw.polygon(list(map(tuple,polygon)),fill=255)
    actual_alpha = ImageChops.multiply(alpha,keep)
    actor = source.copy()
    actor.putalpha(actual_alpha)
    assert actor.convert('RGB').tobytes() == source.convert('RGB').tobytes()
    preserved = ImageChops.multiply(actual_alpha.point(lambda p:255 if p else 0),ImageChops.difference(actual_alpha,alpha))
    assert not preserved.getbbox()
    removed = ImageChops.subtract(alpha,actual_alpha)
    folder = FRAMES / key
    folder.mkdir()
    actor.save(folder / 'frame.png',compress_level=9,optimize=False)
    actual_alpha.save(folder / 'alpha_mask.png',compress_level=9,optimize=False)
    removed.save(folder / 'retired-public-scenery.png')
    area = Image.new('RGBA',(800,374),(255,255,255,0))
    area.putalpha(actual_alpha.point(lambda p:255 if p>=8 else 0))
    area.save(folder / 'area.png',compress_level=9,optimize=False)
    border = ImageChops.subtract(actual_alpha.filter(ImageFilter.MaxFilter(3)),actual_alpha.filter(ImageFilter.MinFilter(3))).point(lambda p:255 if p else 0)
    area.putalpha(border)
    area.save(folder / 'border.png',compress_level=9,optimize=False)
    for role in ('frame','alpha_mask','area','border'):
        target = folder / (role+'.png')
        candidate['states'][key][role] = ref(target)['path']
        candidate['states'][key][role+'_sha256'] = sha(target)
    candidate['states'][key]['source_ownership'] = {'original':ref(source_path),'plan':ref(plan_path),'helper':ref(Path(__file__))}
    records[key] = {'original_frame':ref(source_path),'new_frame':ref(folder / 'frame.png'),
        'retired_public_scenery':ref(folder / 'retired-public-scenery.png'),
        'retired_public_scenery_pixels':count(removed),'source_RGB_changed_pixels':0,
        'retained_architecture_alpha_changed_pixels':0,'construction_campaign_icons_unchanged':True,
        'retained_complete_maritime_or_stilt_anatomy':bool(spec.get('retain_all')),
        'semantic_scope':spec['source_interpretation'],'independent_anatomy_review_pending':True}
    frames[key] = actor

architecture = blank()
for key in index['full_scene_states']:
    architecture = ImageChops.lighter(architecture,frames[key].getchannel('A').point(lambda p:255 if p else 0))
architecture.save(OUT / 'actual-retained-full-architecture.png')
background = Image.composite(old_background,approved,architecture)
background_path = OUT / 'background-public-source.png'
background.save(background_path,compress_level=9,optimize=False)
candidate['background'] = ref(background_path)['path']
candidate['background_sha256'] = sha(background_path)
candidate['public_ground_source_ownership'] = {'plan':ref(plan_path),'helper':ref(Path(__file__)),'original_genuine_background':ref(old_background_path),'approved_whole_source':ref(approved_path)}
candidate['physical_layout_status'] = 'Authored source ownership candidate; actual complete physical consumer and independent anatomy review pending.'
def compose(order):
    scene = background.copy()
    for key in sorted(order,key=lambda key:index['states'][key]['z']):
        scene = Image.alpha_composite(scene,frames[key])
    return scene
full = compose(index['full_scene_states'])
assert full.tobytes() == approved.tobytes(), 'Immutable approved full changed during ownership separation'
full.save(OUT / 'full-native.png',compress_level=9,optimize=False)
background.save(OUT / 'empty-native.png',compress_level=9,optimize=False)
compose(index['base_scene_states']).save(OUT / 'base-native.png',compress_level=9,optimize=False)
for key in index['states']:
    scene = compose([key])
    scene.save(FRAMES / key / 'one-state-native.png',compress_level=9,optimize=False)
save(OUT / 'states.json',candidate)
save(OUT / 'separation-receipt.json',{'status':'design proposal','original_cohort':ref(index_path),'plan':ref(plan_path),
    'candidate_cohort':ref(OUT / 'states.json'),'background':ref(background_path),
    'genuine_hidden_beds_preserved_as_underlying_source':ref(old_background_path),
    'approved_full':ref(approved_path),'approved_full_decoded_RGBA_changed_pixels':0,
    'states':records,'source_ground_not_created_by_code':True,'source_RGB_painted_or_invented_by_code':False,
    'canonical_staging_or_native_changes':False,'physical_baseline_passed':False,'independent_anatomy_review_pending':True})
print(json.dumps({'states':len(frames),'approved_full_RGBA_changed_pixels':0,'candidate':ref(OUT / 'states.json')}))
