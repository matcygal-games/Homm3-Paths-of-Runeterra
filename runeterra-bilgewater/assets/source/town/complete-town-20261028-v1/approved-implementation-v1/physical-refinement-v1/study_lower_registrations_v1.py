"""Read-only whole-actor placement study on fixed genuine terrain planes."""
from pathlib import Path
import json
from PIL import Image

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[5]
OUT = HERE / 'lower-registration-study-v1'
OUT.mkdir(exist_ok=False)
annotation = json.loads((HERE / 'physical-plan-v2/annotations.json').read_text())
index = json.loads((HERE / 'complete-floor-selection-v3/states.json').read_text())
support = Image.open(PROJECT / annotation['terrain']['support']['path']).convert('L')
stairs = Image.open(PROJECT / annotation['terrain']['stairs']['path']).convert('L')
states = ['fort','citadel','townHall','mageGuild1','mageGuild2','dwellingLvl1','dwellingLvl4','dwellingLvl5','dwellingLvl6','dwellingLvl7','special1','special2']
results = {}
for key in states:
    assert key not in index['full_scene_states']
    row = annotation['states'][key]
    roots = row['foundation']['pixels']
    frame = Image.open(PROJECT / index['states'][key]['frame']).convert('RGBA')
    bbox = frame.getchannel('A').getbbox()
    valid = []
    original_bad = []
    for x,y in roots:
        if not support.getpixel((x,y)) or stairs.getpixel((x,y)):
            original_bad.append([x,y])
    for dy in range(-8,9):
        for dx in range(-6,7):
            if bbox[0]+dx<0 or bbox[1]+dy<0 or bbox[2]+dx>800 or bbox[3]+dy>374:
                continue
            if all(support.getpixel((x+dx,y+dy)) and not stairs.getpixel((x+dx,y+dy)) for x,y in roots):
                valid.append([dx,dy])
    valid.sort(key=lambda value:(abs(value[0])+abs(value[1]),abs(value[0]),abs(value[1]),value))
    results[key] = {'unsupported_before':original_bad,'best_whole_placement_deltas':valid[:12],
        'full_approved_state':False,'anatomy_crop_or_deformation_proposed':False,'fixed_terrain_modified':False}
(OUT / 'study.json').write_text(json.dumps({'status':'design proposal','states':results},indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({key:{'unsupported':len(row['unsupported_before']),'deltas':row['best_whole_placement_deltas'][:4]} for key,row in results.items()},indent=2))
