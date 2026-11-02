"""Prepare native comparisons and exact evidence for rejected own walk candidates.

Technical uniform scaling/placement only, with one fixed camera for all three
calls. No painting, warping, new action synthesis, selection or conversion.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from PIL import Image

PROJECT=Path(__file__).resolve().parents[6]
SOURCE=PROJECT/'assets/source/creatures/druvaskRider/walk-v5'
REPORT=PROJECT/'build/reports/druvask-walk-v5-20261021'
SCALE=0.11
TRANSLATION=(121,154)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n',encoding='utf-8')

def bounds(image):
    return image.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()

REPORT.mkdir(parents=True,exist_ok=True)
native=[]
items=[]
for index in (1,2,3):
    path=SOURCE/f'opposite-contact-call{index}.png'
    with Image.open(path) as opened:
        original=opened.convert('RGBA')
    picture=original.resize(tuple(round(n*SCALE) for n in original.size),Image.Resampling.LANCZOS)
    output=Image.new('RGBA',(450,400))
    output.alpha_composite(picture,TRANSLATION)
    target=SOURCE/'native-candidates'/f'call{index}-450x400.png'
    target.parent.mkdir(parents=True,exist_ok=True)
    output.save(target)
    items.append({'call':index,'master':path.relative_to(PROJECT).as_posix(),'master_sha256':digest(path),'source_size':list(original.size),'source_opaque_bbox':bounds(original),'native_candidate':target.relative_to(PROJECT).as_posix(),'native_sha256':digest(target),'native_opaque_bbox':bounds(output)})
    native.append(output)

selected=PROJECT/'assets/source/creatures/druvaskRider/registered-v3/native'
images=[Image.open(selected/'g02-f000.png').convert('RGBA'),Image.open(selected/'g00-f000.png').convert('RGBA'),*native]
sheet=Image.new('RGBA',(700,140),(56,63,66,255))
for index,image in enumerate(images):
    sheet.alpha_composite(image.crop((135,150,270,280)),(index*140,0))
sheet.save(REPORT/'native-comparison.png')

# Guides are compared as own pose evidence only; they are never final pixels.
guide_sheet=Image.new('RGBA',(900,400),(58,65,68,255))
for index,phase in enumerate((0,3)):
    with Image.open(SOURCE/'poseguides'/f'pose-{phase}.png') as image:
        guide_sheet.alpha_composite(image.resize((450,400),Image.Resampling.LANCZOS),(index*450,0))
guide_sheet.save(REPORT/'guide-opposite-contacts.png')

inputs=[]
for unit in ('druvaskRider','winterOutrider'):
    recipe=PROJECT/'assets/recipes/creatures'/f'{unit}-battle.json'
    definition=json.loads(recipe.read_text(encoding='utf-8'))
    moving=next(group for group in definition['groups'] if group['group']==0)
    frames=[]
    for frame in moving['frames']:
        path=PROJECT/frame['source']
        actual=digest(path)
        expected=frame.get('source_sha256') or frame.get('sha256')
        if actual!=expected:
            raise ValueError(f'Selected frame changed: {path}')
        frames.append({'path':frame['source'],'sha256':actual})
    inputs.append({'unit':unit,'selected_recipe':recipe.relative_to(PROJECT).as_posix(),'recipe_sha256':digest(recipe),'current_moving_frames':frames})

record={'status':'design proposal','art_accepted':False,'selected_for_production':False,'builtin_calls_executed':3,'winter_calls_executed':0,'six_phase_cycles_completed':0,'camera':{'scale':SCALE,'translation':list(TRANSLATION),'canvas':[450,400],'contract_pivot':[197,266],'method':'one fixed uniform scale and placement for all three independently painted call candidates, no per-frame fitting'},'findings':{'call1':'Opposite foreleg contact appears, but near/far hind support is not exchanged as requested.','call2':'Targeted hind-leg edit retains the same trailing near hind leg; guide is not followed.','call3':'Guide-first repaint lifts both hind hooves, producing a bound-like pose rather than planted far-hind support.','result':'No candidate establishes the complete coordinated opposite fore/hind support phase. No full cycle or upgraded unit is generated from this failure.'},'selected_inputs_verified_unchanged':inputs,'candidates':items,'native_comparison_sha256':digest(REPORT/'native-comparison.png'),'guide_comparison_sha256':digest(REPORT/'guide-opposite-contacts.png'),'remaining_input':'Artist-authored coherent six-pose druvask quadruped/rider walking cycle per variant, or a geometry-conditioned painter that demonstrably preserves all four hoof phases. Existing Blender geometry guides are not final art.'}
write(REPORT/'result.json',record)
paths=[*SOURCE.rglob('*'),REPORT/'result.json',REPORT/'native-comparison.png',REPORT/'guide-opposite-contacts.png',REPORT/'REVIEW.md']
write(REPORT/'freeze.json',{'status':'design proposal','frozen':True,'production_changed':False,'files':{p.relative_to(PROJECT).as_posix():digest(p) for p in sorted(set(paths)) if p.is_file()}})
print(json.dumps({'ok':True,'actual_imagegen_calls':3,'selected':0,'native_candidates':len(items),'freeze_sha256':digest(REPORT/'freeze.json')},indent=2))
