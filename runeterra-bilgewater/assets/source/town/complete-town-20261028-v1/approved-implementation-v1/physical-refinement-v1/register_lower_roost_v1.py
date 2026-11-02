"""Candidate whole-layer base Roost registration; approved full is immutable."""
from pathlib import Path
from copy import deepcopy
import hashlib
import json

from PIL import Image, ImageChops

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
PROJECT = HERE.parents[5]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path):
    return {'path': path.relative_to(PROJECT).as_posix(), 'sha256': sha(path)}


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def main():
    index_path = BASE / 'states-hidden-support-v6.json'
    if sha(index_path) != 'd5892fe9be62c096dc2d33cb2a4ca4dcad2b0e9303d3354021509a6244773529':
        raise ValueError('Released cohort changed')
    before = json.loads(index_path.read_text())
    after = deepcopy(before)
    key, shift = 'dwellingLvl5', (0, -2)
    old = before['states'][key]
    output = HERE / 'lower-roost-registration-v1'
    output.mkdir(exist_ok=False)
    inputs = {}
    for role in ('frame','alpha_mask','area','border'):
        path = PROJECT / old[role]
        if sha(path) != old[role + '_sha256']:
            raise ValueError('Released Roost source changed: ' + role)
        with Image.open(path) as opened:
            source = opened.copy()
        if role == 'frame':
            bounds = source.getchannel('A').getbbox()
            if bounds[1] < 2:
                raise ValueError('Whole layer would clip visible pixels')
        registered = Image.new(source.mode, source.size, 0)
        registered.paste(source, shift)
        target = output / (role + '.png')
        registered.save(target, compress_level=9, optimize=False)
        after['states'][key][role] = ref(target)['path']
        after['states'][key][role + '_sha256'] = sha(target)
        inputs[role] = {'before':ref(path),'after':ref(target)}
    old_frame = Image.open(PROJECT / old['frame']).convert('RGBA')
    new_frame = Image.open(PROJECT / after['states'][key]['frame']).convert('RGBA')
    old_bounds = old_frame.getchannel('A').getbbox()
    new_bounds = new_frame.getchannel('A').getbbox()
    if old_frame.crop(old_bounds).tobytes() != new_frame.crop(new_bounds).tobytes():
        raise ValueError('Whole registered actor changed shape or colour')
    row = after['states'][key]
    row['delta'] = [old['delta'][0], old['delta'][1] - 2]
    row['entrance'] = [old['entrance'][0], old['entrance'][1] - 2]
    row['alpha_bounds'] = list(new_bounds)
    row['registration_note'] = 'Unapproved lower form moved up2px intact to the independently observed upper paving cap; highest Roost/full composition unchanged.'
    for other in before['states']:
        if other != key and before['states'][other] != after['states'][other]:
            raise ValueError('Unrelated state changed')
    background = Image.open(PROJECT / after['background']).convert('RGBA')
    for state in sorted(after['full_scene_states'], key=lambda name:after['states'][name]['z']):
        background.alpha_composite(Image.open(PROJECT / after['states'][state]['frame']).convert('RGBA'))
    approved = Image.open(BASE / 'approved-full-source-v1.png').convert('RGBA')
    if background.tobytes() != approved.tobytes():
        raise ValueError('Approved full changed')
    background.convert('RGB').save(output / 'full-native.png')
    base = Image.open(PROJECT / after['background']).convert('RGBA')
    for state in sorted(after['base_scene_states'], key=lambda name:after['states'][name]['z']):
        base.alpha_composite(Image.open(PROJECT / after['states'][state]['frame']).convert('RGBA'))
    base.convert('RGB').save(output / 'base-native.png')
    receipt = {
        'status':'design proposal','input_cohort':ref(index_path),'helper':ref(Path(__file__).resolve()),
        'changed_state':key,'whole_layer_translation':[0,-2],'inputs':inputs,
        'visible_pixels_clipped':0,'actor_shape_and_RGBA_cropped_bytes_identical':True,
        'unchanged_other_states':34,'unchanged_selected_top_states':16,
        'construction_and_campaign_icons_retained_byte_exact':True,
        'approved_full':ref(BASE / 'approved-full-source-v1.png'),
        'approved_full_decoded_changed_pixels':0,'physical_baseline_passed':False,
        'native_verified':False,'route_gap_not_repaired':True}
    save(output / 'registration-inputs.json', receipt)
    after['physical_refinement_registration'] = ref(output / 'registration-inputs.json')
    after['cohort'] = 'BL2-full-preserved-lower-roost-registration-candidate-v1'
    save(output / 'states.json', after)
    print(json.dumps({'changed_state':key,'other34_unchanged':True,'approved_full_changed_pixels':0,'cohort':ref(output / 'states.json')}))


if __name__ == '__main__':
    main()
