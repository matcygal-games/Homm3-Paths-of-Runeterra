"""Derive native scenic town portraits from the selected own painted city.

Only selected layer compositing, scenic crops, uniform resampling and reuse of
the existing own painted construction marker occur. No new painting/staging.
"""
from pathlib import Path
import copy, hashlib, json, sys
from PIL import Image, ImageChops, ImageFilter

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
WORKSPACE = PROJECT.parent
REPORT = WORKSPACE / 'reports/town-portrait-repair-20261030-v1/zaun'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text(encoding='utf-8'))

def write(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')

def save(p, im):
    p.parent.mkdir(parents=True, exist_ok=True)
    im.save(p, compress_level=9)

def main():
    plan = read(HERE / 'selection.json')
    for item in plan['inputs']:
        if sha(PROJECT / item['path']) != item['sha256']:
            raise ValueError('Selected portrait input changed: ' + item['path'])
    layout = read(PROJECT / plan['layout'])
    families = read(PROJECT / plan['families'])['families']
    bg = Image.open(PROJECT / layout['background']['path']).convert('RGBA')
    ordered = sorted(families, key=lambda f: next(s['depth'] for s in layout['sites'] if f['states'][0] in s['states']))
    scenes = {}
    for state in ('village', 'fort'):
        scene = bg.copy()
        for family in ordered:
            if family['id'] in ('shipyard', 'codeOfProgress'):
                continue
            if state == 'village' and family['id'] == 'sumpRampart':
                continue
            selected = family['states'][-1]
            scene.alpha_composite(Image.open(PROJECT / layout['frames'][selected]['path']).convert('RGBA'))
        scenes[state] = scene
        save(HERE / ('scene-' + state + '.png'), scene)
    # Native UI built-state marker, clipped from our existing painted icon.
    old = Image.open(PROJECT / plan['marker']).convert('RGBA').crop(tuple(plan['marker_crop']))
    red = Image.new('L', old.size)
    red.putdata([255 if r > 140 and g < 90 and b < 90 and r > g * 1.8 and r > b * 1.8 and a > 0 else 0 for r,g,b,a in old.get_flattened_data()])
    mask = red.filter(ImageFilter.MaxFilter(3))
    marker = old.copy()
    marker.putalpha(ImageChops.multiply(old.getchannel('A'), mask))
    marker = marker.crop(mask.getbbox())
    records = []
    candidate = PROJECT / 'assets/candidates/town-portraits-20261030-v1/recipes'
    for state in ('village', 'fort'):
        for size_name, size in (('large', (58,64)), ('small',(48,32))):
            crop = plan['crops'][state][size_name]
            picture = scenes[state].crop(crop).resize(size, Image.Resampling.LANCZOS)
            for built in (False, True):
                name = state + ('_built_' if built else '_normal_') + size_name
                result = picture.copy()
                if built:
                    dimension = 15 if size_name == 'large' else 12
                    cross = marker.resize((dimension,dimension), Image.Resampling.LANCZOS)
                    result.alpha_composite(cross,(size[0]-dimension,size[1]-dimension))
                source = HERE / 'native' / (name + '.png')
                save(source,result)
                recipe = read(PROJECT / 'assets/recipes/town/icons' / (name+'.json'))
                recipe.update({'source':source.relative_to(PROJECT).as_posix(),'source_sha256':sha(source),'fit':'contain','require_alpha':False,
                    'art_direction':'Full-frame native scenic portrait of the currently selected painted Zaun city. Fort gate state differs from unfortified village; built state retains own painted native red X.',
                    'identity_review':(HERE/'pixel-review.json').relative_to(PROJECT).as_posix(),'native_visual_review':'pending','visual_approval_granted':False,'status':'built-unreviewed'})
                generation = copy.deepcopy(read(PROJECT/'assets/recipes/town/background.json')['generation'])
                generation['route'] = 'Native scenic crop of selected complete painted city layers; deterministic composition/crop/resampling only, existing own painted red construction marker reused.'
                generation['master'] = (HERE/('scene-'+state+'.png')).relative_to(PROJECT).as_posix()
                generation['master_sha256'] = sha(HERE/('scene-'+state+'.png'))
                generation['painted_master'] = 'assets/source/town/complete-town-20261027-v2/complete-design/provider-master-v2.png'
                generation['painted_master_sha256'] = sha(PROJECT / generation['painted_master'])
                generation['prompt'] = 'Reuse the selected own complete painted Zaun city and its genuine state layers. This derivative makes native scenic closeups and reuses the existing own painted construction X; no new image generation was performed.'
                recipe['generation'] = generation
                recipe['dependencies'] = plan['inputs'] + [{'path':(HERE/'selection.json').relative_to(PROJECT).as_posix(),'sha256':sha(HERE/'selection.json')},{'path':Path(__file__).relative_to(PROJECT).as_posix(),'sha256':sha(Path(__file__))}]
                write(candidate/(name+'.json'),recipe)
                records.append({'name':name,'source':source.relative_to(PROJECT).as_posix(),'source_sha256':sha(source),'recipe':(candidate/(name+'.json')).relative_to(PROJECT).as_posix(),'recipe_sha256':sha(candidate/(name+'.json')),'dimensions':list(size),'alpha_extrema':list(result.getchannel('A').getextrema()),'crop':crop})
    write(REPORT/'candidate-inventory.json',{'status':'authored configuration','icons':records,'source_inputs':plan['inputs'],'selected':False,'staged':False})

if __name__ == '__main__':
    main()
