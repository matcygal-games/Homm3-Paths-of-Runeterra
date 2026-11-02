"""Resolve source-observed last step soles and exact native frontage extents.

This only authors explicit door/apron contours. No structural contact, fixed
terrain, body silhouette, source art or approved full scene is modified.
"""
from pathlib import Path
import importlib.util
import json
import hashlib
from PIL import Image, ImageDraw, ImageChops

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[5]
OUT = HERE / 'semantic-candidate-v5'
OUT.mkdir(exist_ok=False)
spec = importlib.util.spec_from_file_location('binder', HERE / 'bind_contract.py')
binder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(binder)
source = HERE / 'semantic-candidate-v4/annotations.json'
annotation = json.loads(source.read_text())
annotation['frontage_ancestry'] = {'path': source.relative_to(PROJECT).as_posix(), 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()}
edits = {
    'castle': ([[243,82],[254,82],[256,95],[269,103],[271,107],[260,106],[246,98],[243,94]], [[270,107],[275,110]]),
    'fort': ([[182,80],[193,80],[195,92],[203,97],[204,103],[199,103],[192,96],[183,92]], [[202,102],[205,106]]),
    'citadel': ([[198,80],[211,80],[212,92],[217,96],[220,104],[215,104],[208,97],[199,92]], [[218,103],[222,107]]),
    'dwellingLvl3': ([[303,168],[312,168],[315,179],[316,180],[316,183],[307,182],[304,178]], [[316,182],[324,184]]),
    'dwellingUpLvl1': ([[128,232],[139,232],[141,246],[146,249],[146,252],[135,250],[130,245]], [[146,251],[151,252]]),
    'dwellingUpLvl3': ([[309,168],[319,168],[321,178],[323,184],[323,186],[311,184],[309,178]], [[322,185],[326,188]]),
    'special1': ([[647,193],[656,193],[658,205],[656,213],[646,213],[645,205]], [[652,212],[652,216]]),
    'dwellingUpLvl4': ([[643,185],[660,185],[661,203],[656,211],[656,225],[643,225],[643,212],[640,205]], [[650,224],[649,229]]),
    'shipyard': ([[634,302],[646,302],[649,306],[646,310],[637,309],[634,308]], [[635,307],[630,307]]),
    'ship': ([[632,302],[646,302],[649,306],[646,310],[637,309],[632,308]], [[633,307],[628,307]]),
}
for key, (door, approach) in edits.items():
    row = annotation['states'][key]
    row['door'] = {'polygons': [door]}
    row['approach'] = {'lines': [{'points': approach, 'width': 2}]}
    row['frontage_interpretation'] += ' Exact lower source-visible entrance-step sole/deck landing is retained; no body opacity or structural footing is subtracted.'
(OUT / 'annotations.json').write_text(json.dumps(annotation,indent=2,sort_keys=True)+'\n',encoding='utf-8')
index = json.loads((HERE / 'lower-roost-registration-v1/states.json').read_text())
measurements = {}
for key, row in annotation['states'].items():
    frame = Image.open(PROJECT / index['states'][key]['frame']).convert('RGBA')
    alpha = frame.getchannel('A')
    body = alpha.point(lambda p: 255 if p >= 128 else 0)
    full = alpha.point(lambda p: 255 if p >= 8 else 0)
    door = binder.trace(row['door'])
    approach = binder.trace(row['approach'])
    bbox = full.getbbox()
    inside = Image.new('L', frame.size)
    ImageDraw.Draw(inside).rectangle((bbox[0],bbox[1],bbox[2]-1,bbox[3]-1),fill=255)
    crossing = ImageChops.multiply(approach,ImageChops.subtract(body,door))
    outside = ImageChops.subtract(door,inside)
    measurements[key] = {'own_solid_crossing_pixels': sum(bool(v) for v in crossing.get_flattened_data()),
        'door_outside_native_bbox_pixels': sum(bool(v) for v in outside.get_flattened_data()),
        'anchor_in_frontage': bool(door.getpixel(tuple(row['entrance'])))}
record = {'status':'authored configuration','state_count':len(measurements),'measurements':measurements,
    'terrain_or_public_route_pass_claimed':False,'complete_structural_contact_trace_pass_claimed':False,
    'source_art_modified':False,'approved_full_changed_pixels':0}
(OUT / 'local-frontage-measurements.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(record,indent=2))
