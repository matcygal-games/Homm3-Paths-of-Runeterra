"""Correct an overestimated far-east junction from actual native shoreline RGB.

The twenty-times native source crop proves x720..730/y193..207 is external
blue harbor water/remote background, not a city street. The provisional V1
turn polygon is withdrawn wholesale. This writer never reads actor feet or a
consumer result, and does not relabel any water as ground to obtain a pass.
"""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageChops
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[5]
OUT=HERE/'public-source-ground-v2';OUT.mkdir(exist_ok=False)
def ref(p):return {'path':p.relative_to(PROJECT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def poly(ps):
 im=Image.new('L',(800,374));ImageDraw.Draw(im).polygon(list(map(tuple,ps)),fill=255);return im
def union(ms):
 im=Image.new('L',(800,374))
 for m in ms:im=ImageChops.lighter(im,m)
 return im
prior=HERE/'public-source-ground-v1/terrain-plan.json';plan=json.loads(prior.read_text())
plan['support_regions']=[r for r in plan['support_regions']if r['id']!='eastern-buhru-street-turn']
plan['source_shoreline_correction']={'ancestor':ref(prior),'native_reference':ref(HERE/'ownership-ground-atlas-v1/east-source-shoreline.png'),'classification':'The provisional far-east turn crossed actual blue harbor/remote background; withdrawn in full. No terrain or anatomy is fitted to an expected result.'}
plan['background']=ref(HERE/'ownership-separation-v5/background-public-source.png')
support=union(poly(r['polygon'])for r in plan['support_regions'])
stairs_raw=union(poly(r['polygon'])for r in plan['stairs_regions'])
stairs=ImageChops.subtract(stairs_raw,support)
water=union(poly(r['polygon'])for r in plan['water_regions'])
land=ImageChops.subtract(poly(plan['dry_ownership_polygon']),water);land=union([land,support,stairs])
for role,im in [('support',support),('stairs',stairs),('water',water),('land',land)]:im.save(OUT/(role+'.png'))
plan['masks']={role:ref(OUT/(role+'.png'))for role in ('land','support','stairs','water')}
(OUT/'terrain-plan.json').write_text(json.dumps(plan,indent=2,sort_keys=True)+'\n')
print({'terrain_plan':ref(OUT/'terrain-plan.json'),'support_water_pixels':sum(bool(v)for v in ImageChops.multiply(support,water).get_flattened_data())})
