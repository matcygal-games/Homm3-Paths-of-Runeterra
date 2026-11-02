"""Bind independent source anatomy and the actual proposed painted plane set.

This remains an engineering proposal. The fine-paving visual interpretation
needs review; a positive source check cannot approve that appearance.
"""
from pathlib import Path
import json
import hashlib
import importlib.util
from PIL import Image, ImageDraw, ImageChops

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[5]
BASE = HERE.parent
OUT = HERE / 'physical-plan-v2'
OUT.mkdir(exist_ok=False)
spec = importlib.util.spec_from_file_location('binder',HERE / 'bind_contract.py')
binder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(binder)
def ref(path):
    return {'path':path.relative_to(PROJECT).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
source = HERE / 'structural-contacts-v3/annotations.json'
annotation = json.loads(source.read_text())
index_path = HERE / 'complete-floor-selection-v3/states.json'
index = json.loads(index_path.read_text())
annotation['state_index_sha256'] = ref(index_path)['sha256']
annotation['background'] = {'path':index['background'],'sha256':index['background_sha256']}
annotation['complete_scene_states'] = index['full_scene_states']
terrain = {role:Image.open(HERE / 'terrain-planes-v1' / (role+'.png')).convert('L') for role in ('land','support','stairs','water','paths')}
painted_top_path = HERE / 'complete-floor-selection-v3/all-selected-complete-horizontal-tops.png'
painted_tops = Image.open(painted_top_path).convert('L')
# The new paintings actually replace the hidden old cliff/tread pixels. The
# source-selected top mask is independent of the structural contact annotations.
terrain['support'] = ImageChops.lighter(terrain['support'],painted_tops)
terrain['stairs'] = ImageChops.subtract(terrain['stairs'],painted_tops)
terrain['land'] = ImageChops.lighter(terrain['land'],painted_tops)
# Actual west-flight first tread begins below the native stone upper landing.
# Preserve that cap as level ground and the remaining descending run as stairs.
landing_boundary = Image.new('L',(800,374))
ImageDraw.Draw(landing_boundary).polygon([(171,185),(179,185),(180,187),(173,188),(171,187)],fill=255)
terrain['stairs'] = ImageChops.subtract(terrain['stairs'],landing_boundary)
for role,image in terrain.items():
    image.save(OUT / (role+'.png'))
annotation['terrain'] = {role:ref(OUT / (role+'.png')) for role in terrain}
annotation['states']['castle']['entrance'] = [250,96]
annotation['states']['castle']['door'] = {'polygons':[[[244,92],[255,92],[259,98],[269,103],[271,107],[261,107],[249,100],[244,97]]]}
annotation['states']['castle']['frontage_interpretation'] = 'Actual ground threshold and descending entrance-step floor contour. The tall vertical portal arch above the floor is excluded from the dry-ground access mask.'
annotation['states']['dwellingLvl5']['entrance'] = [656,107]
annotation['states']['dwellingLvl5']['door'] = {'polygons':[[[650,104],[662,104],[665,110],[661,112],[652,112]]]}
annotation['states']['dwellingUpLvl5']['entrance'] = [655,105]
annotation['states']['dwellingUpLvl5']['door'] = {'polygons':[[[652,103],[658,103],[661,106],[658,110],[652,110],[650,107]]]}
for key in ('shipyard','ship'):
    row = annotation['states'][key]
    row['entrance'] = [638,305]
    row['door'] = {'polygons':[[[634,302],[646,302],[649,306],[646,310],[637,310],[634,308]]]}
    row['approach'] = {'lines':[{'points':[[638,308],[631,311]],'width':1}]}
    frame = Image.open(PROJECT / index['states'][key]['frame']).convert('RGBA')
    full = frame.getchannel('A').point(lambda p:255 if p>=8 else 0)
    role_union = ImageChops.lighter(binder.trace(row['foundation']),binder.trace(row['door']))
    actual = ImageChops.multiply(role_union,full)
    box = actual.getbbox()
    row['marine_support'] = {'pixels':[[x,y] for y in range(box[1],box[3]) for x in range(box[0],box[2]) if actual.getpixel((x,y))]}
    row['frontage_interpretation'] = 'Actual shoreward jetty landing connects to dry public quay at631,311. The bounded actual native pier/hull contact and landing mask grants no support to surrounding water.'
annotation['selected_editable_sources'] = [ref(source),ref(index_path),ref(painted_top_path),ref(HERE / 'complete-floor-selection-v3/selection.json'),ref(HERE / 'trace_terrain_planes_v1.py'),ref(Path(__file__))]
annotation['review_limits'] = 'Actual all35 source-contact spans are present. The approved full remains exact; proposed hidden plane artwork, all real public connections and separate visible Roost alternative still need complete source/native verification. No negative control is claimed from a failing baseline.'
(OUT / 'annotations.json').write_text(json.dumps(annotation,indent=2,sort_keys=True)+'\n',encoding='utf-8')
summary = {'status':'design proposal','anatomy_source':ref(source),'cohort':ref(index_path),
    'support_stairs_overlap_pixels':sum(bool(v) for v in ImageChops.multiply(terrain['support'],terrain['stairs']).get_flattened_data()),
    'level_source_is_new_genuine_painted_top_not_relabelled_old_cliff':True,'appearance_review_pending':True,'physical_baseline_passed':False}
(OUT / 'receipt.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(summary))
