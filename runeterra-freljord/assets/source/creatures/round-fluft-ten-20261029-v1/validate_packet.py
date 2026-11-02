"""Strict source/native-payload checks for the replacement Fluft only.

Observed pixels/motion and independent art review are separate from these checks.
"""
from pathlib import Path
import hashlib
import json
import sys

from PIL import Image

COHORT='assets/source/creatures/round-fluft-ten-20261029-v1/'
CANONICAL='assets/recipes/creatures/painted-20261024/fluftOfPoros/'
GROUPS={0:6,1:6,2:1,3:4,4:4,5:8,7:3,8:3,11:7,12:7,13:7,20:4,21:4}


def sha(data): return hashlib.sha256(data).hexdigest()
def read(path): return json.loads(path.read_text(encoding='utf-8'))


def validate_payloads(payloads,expected):
    if set(payloads)!=set(expected): raise ValueError('Exact output closure differs')
    for name,payload in payloads.items():
        if sha(payload)!=expected[name]: raise ValueError('Native payload/root/body changed: '+name)
    return True


def validate_recipe(project,recipe):
    g=recipe['generation']
    for record in [{'path':g['painted_master'],'sha256':g['painted_master_sha256']}]+g['supplemental_masters']+recipe['inputs']:
        path=(project/record['path']).resolve()
        if not path.is_relative_to(project.resolve()) or sha(path.read_bytes())!=record['sha256']:
            raise ValueError('Changed/missing source dependency')
    descriptors=([d for group in recipe['groups'] for d in group['frames']]
                 if recipe['recipe_type']=='vcmi_animation' else [recipe])
    for d in descriptors:
        if not d['source'].startswith(COHORT+'native-v1/'):
            raise ValueError('Retired or foreign Fluft frame selected')
        image=Image.open(project/d['source'])
        if sha((project/d['source']).read_bytes())!=d['source_sha256']:
            raise ValueError('Changed selected source frame')
        if image.mode!='RGBA' or list(image.size)!=d['source_canvas']:
            raise ValueError('Native canvas/mode changed')
        alpha=image.getchannel('A')
        if alpha.getbbox() is None or alpha.getextrema()[0]!=0:
            raise ValueError('Missing real empty alpha background')
    if recipe['output_path'].endswith('/battle.json'):
        actual={group['group']:len(group['frames']) for group in recipe['groups']}
        if actual!=GROUPS: raise ValueError('Missing/changed native action groups')
        groups={group['group']:group['frames'] for group in recipe['groups']}
        for group,count in ((0,6),(20,4),(21,4)):
            if len({d['source_sha256'] for d in groups[group]})!=count:
                raise ValueError('Still/repeated motion replaces real roll/hop poses')
        if recipe['pivot']!={'x':193,'y':266} or recipe['canvas']!=[450,400]:
            raise ValueError('Battlefield root/canvas changed')
    return True


def validate_packet(project,*,canonical=False):
    sys.path.insert(0,str(project.parent/'scripts'))
    from faction_art_compile import create_compiler
    compiler=create_compiler('freljord')
    packet=read(project/(COHORT+'source-selection.json'))
    if len(packet['recipes'])!=6: raise ValueError('Incomplete body roles')
    payloads={}
    for record in packet['recipes']:
        selected=project/record['path']
        if sha(selected.read_bytes())!=record['sha256']: raise ValueError('Candidate recipe changed')
        active=project/CANONICAL/selected.name if canonical else selected
        if active.read_bytes()!=selected.read_bytes(): raise ValueError('Canonical recipe not exact reviewed selection')
        recipe=read(active);validate_recipe(project,recipe)
        outputs,_=compiler.plan(project,active)
        if payloads.keys()&outputs.keys(): raise ValueError('Duplicate native output')
        payloads.update(outputs)
    validate_payloads(payloads,packet['outputs'])
    creatures=read(project/'content/creatures.json')
    if creatures['fluftOfPoros']['abilities']!={'canFly':{'type':'FLYING'}}:
        raise ValueError('Obstacle-crossing native movement changed')
    if creatures['overgrownPoro']['abilities']!={}:
        raise ValueError('Single Overgrown Poro movement changed')
    if canonical:
        root=project/'assets/generated/Content/Sprites/runeterra/freljord/creatures/fluftOfPoros'
        actual={p.relative_to(project/'assets/generated').as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
        validate_payloads(actual,packet['outputs'])
    return payloads
