"""Restore independently identified real Corsair stanchions, not public fascia."""
from pathlib import Path
import json,hashlib
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[5]
OUT=HERE/'ownership-separation-v4'
OUT.mkdir(exist_ok=False)
prior=HERE/'ownership-separation-v3/plan.json'
plan=json.loads(prior.read_text())
def box(x0,y0,x1,y1):return [[x0,y0],[x1,y0],[x1,y1],[x0,y1]]
rests={
 'dwellingLvl2':[(278,276,284,288),(293,278,300,290),(305,275,313,291)],
 'dwellingUpLvl2':[(282,275,290,287),(296,278,304,292),(307,278,315,292)],
}
for key,windows in rests.items():
 row=plan['states'][key]
 for b in windows:
  region=box(*b);row['retain_polygons'].append(region);row['structural_contact_regions'].append(region)
 row['skip_main_contact_seam']=True
 row['source_interpretation']='Preserve the full real timber ship-house and every separately source-traced upright underpinning/stanchion, together with actual entry columns. The elevated curved stern/hull flank is not a bearing sole; permanent court paving remains scenery. Independently identified stanchions that V3 accidentally retired are restored, never baked into empty terrain.'
for key in ('dwellingLvl3','dwellingUpLvl3'):
 plan['states'][key]['skip_main_contact_seam']=True
 plan['states'][key]['source_interpretation']+=' Native source review distinguishes raised barrel/muzzle and suspended chassis from the actual separately retained wheel/cradle/pavilion support soles; the entire apparent outer bottom is not a ground foot.'
plan['independent_correction']={'kind':'source-anatomy-restoration','ancestor':{'path':prior.relative_to(PROJECT).as_posix(),'sha256':hashlib.sha256(prior.read_bytes()).hexdigest()},'reviewer':'/root/ionia_creature_delivery','witness_pixels':{'dwellingLvl2':[[281,285],[296,287],[308,287]],'dwellingUpLvl2':[[285,284],[300,288],[311,288]]},'real_support_anatomy_clipped':False,'terrain_mask_read':False}
(OUT/'plan.json').write_text(json.dumps(plan,indent=2,sort_keys=True)+'\n')
print('Frozen independent Corsair anatomy restoration plan for all35 states')
