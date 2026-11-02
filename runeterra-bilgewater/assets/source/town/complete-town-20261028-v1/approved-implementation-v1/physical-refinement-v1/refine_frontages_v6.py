"""Use actual narrow approach centre lines at two final diagonal stair soles.

The former two-pixel diagonal raster brush spilled one corner into adjacent
masonry. Preserve each source-observed door/apron and trace its centre line.
No structural mask, actual frame, terrain or source selection changes.
"""
from pathlib import Path
import importlib.util
import json
import hashlib
from PIL import Image, ImageDraw, ImageChops

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[5]
OUT = HERE / 'semantic-candidate-v6'
OUT.mkdir(exist_ok=False)
spec = importlib.util.spec_from_file_location('binder', HERE / 'bind_contract.py')
binder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(binder)
source = HERE / 'semantic-candidate-v5/annotations.json'
annotation = json.loads(source.read_text())
annotation['frontage_ancestry'] = {'path': source.relative_to(PROJECT).as_posix(), 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()}
for key in ('citadel','dwellingUpLvl3'):
    annotation['states'][key]['approach']['lines'][0]['width'] = 1
    annotation['states'][key]['frontage_interpretation'] += ' Narrow source-visible approach centre line avoids rasterizing an adjacent diagonal masonry corner.'
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
print(json.dumps({'states':len(measurements),'local_access_valid_states':[key for key,value in measurements.items() if not value['own_solid_crossing_pixels'] and not value['door_outside_native_bbox_pixels'] and value['anchor_in_frontage']], 'not_whole_physical_baseline':True}))
