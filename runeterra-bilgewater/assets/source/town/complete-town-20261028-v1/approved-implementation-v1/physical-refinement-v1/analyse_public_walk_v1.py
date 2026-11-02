"""Actual all-state source topology, diagnostic only; no inferred routes."""
from pathlib import Path
from collections import deque
import json
import importlib.util
from PIL import Image, ImageChops, ImageDraw

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[5]
OUT = HERE / 'public-walk-diagnostics-v1'
OUT.mkdir(exist_ok=False)
spec = importlib.util.spec_from_file_location('binder',HERE / 'bind_contract.py')
binder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(binder)
annotation = json.loads((HERE / 'physical-plan-v2/annotations.json').read_text())
index = json.loads((HERE / 'complete-floor-selection-v3/states.json').read_text())
terrain = {role:Image.open(PROJECT / annotation['terrain'][role]['path']).convert('L') for role in ('land','support','stairs','water')}
level = ImageChops.lighter(terrain['support'],terrain['stairs'])
blocked = Image.new('L',(800,374))
bodies = {}
for key,row in index['states'].items():
    body = Image.open(PROJECT / row['frame']).getchannel('A').point(lambda p:255 if p>=128 else 0)
    bodies[key] = body
    blocked = ImageChops.lighter(blocked,ImageChops.subtract(body,binder.trace(annotation['states'][key]['door'])))
allowed = ImageChops.subtract(level,blocked)
allowed.save(OUT / 'actual-all35-common-body-free-walk.png')
blocked.save(OUT / 'actual-all35-common-closed-body.png')
labels = [[0]*800 for _ in range(374)]
component_sizes = {}
counter = 0
for y in range(374):
    for x in range(800):
        if labels[y][x] or not allowed.getpixel((x,y)):
            continue
        counter += 1
        queue = deque([(x,y)])
        labels[y][x] = counter
        size = 0
        while queue:
            xx,yy = queue.popleft()
            size += 1
            for nx,ny in ((xx-1,yy),(xx+1,yy),(xx,yy-1),(xx,yy+1)):
                if 0<=nx<800 and 0<=ny<374 and not labels[ny][nx] and allowed.getpixel((nx,ny)):
                    labels[ny][nx] = counter
                    queue.append((nx,ny))
        component_sizes[counter] = size
def points(mask):
    box = mask.getbbox()
    return [[x,y] for y in range(box[1],box[3]) for x in range(box[0],box[2]) if mask.getpixel((x,y))] if box else []
results = {}
for key,row in annotation['states'].items():
    roots = binder.trace(row['foundation'])
    marine = binder.trace(row['marine_support']) if row.get('marine_support') else Image.new('L',(800,374))
    unsupported = ImageChops.subtract(roots,ImageChops.lighter(terrain['support'],marine))
    approach = binder.trace(row['approach'])
    offwalk = ImageChops.subtract(approach,ImageChops.lighter(level,marine))
    intersections = {str(label):component_sizes[label] for x,y in points(approach) if (label:=labels[y][x])}
    site = index['states'][key]['site']
    other_blocks = {}
    for other,body in bodies.items():
        if index['states'][other]['site'] != site:
            crossing = ImageChops.multiply(approach,body)
            if crossing.getbbox():
                other_blocks[other] = points(crossing)
    results[key] = {'unsupported_root_pixels':points(unsupported),'root_on_stairs_pixels':points(ImageChops.multiply(roots,terrain['stairs'])),
        'approach_off_actual_walk_pixels':points(offwalk),'actual_common_walk_components_touched':intersections,
        'other_site_body_intersections':other_blocks}
record = {'status':'authored configuration','whole_physical_baseline_passed':False,'all35states_retained':True,
    'component_sizes':component_sizes,'states':results}
(OUT / 'diagnostics.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n',encoding='utf-8')
(OUT / 'labels.json').write_text(json.dumps(labels,separators=(',',':'))+'\n',encoding='utf-8')
print(json.dumps({'largest_components':sorted(component_sizes.items(),key=lambda v:-v[1])[:15],
    'states':{key:{'unsupported_roots':len(row['unsupported_root_pixels']),'root_on_stairs':len(row['root_on_stairs_pixels']),
        'offwalk_approach':len(row['approach_off_actual_walk_pixels']),'touched':row['actual_common_walk_components_touched'],
        'other_site_blocks':list(row['other_site_body_intersections'])} for key,row in results.items()}},indent=2))
