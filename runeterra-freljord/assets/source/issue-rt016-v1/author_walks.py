"""RT-016: continue the surfaced Hunter cohort, with editable local finish.

Old sources are read-only imports. Every new file remains below this directory
or the uniquely named report directory; this script cannot select or publish.
"""
from pathlib import Path
import copy
import hashlib
import json
import math
import shutil
import sys

sys.dont_write_bytecode = True
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
OLD = PROJECT / 'assets/source/creatures/iceHunter/walk-v6-offline/walk-v7-nativefinish-review1'
sys.path.insert(0, str(OLD))
import finish_contacts as previous
fit, original = previous.fit, previous.original
REPORT = PROJECT / 'build/reports/issue-resolution-20261023/walks-rt016-finish-v1'
UNITS = ('iceHunter', 'veteranIceHunter')
GAPS = ('iceHunter','veteranIceHunter','frostTroll','rimeTroll','ursineWarrior','stormChosen',
        'spiritWalker','primalShaman','druvaskRider','winterOutrider','feralYeti','ancientYeti')
SEMANTICS = ('near contact / far toe-off', 'near support / far passing rise',
             'near late support / far reach', 'far contact / near toe-off',
             'far support / near passing rise', 'far late support / near recovery reach')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path = Path(path)
    if path.exists():
        raise ValueError('Preserve existing output: ' + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True)+'\n', encoding='utf-8')


def config():
    return json.loads((HERE / 'finish-source.json').read_text())


def contract(unit):
    value = copy.deepcopy(previous.contract(unit))
    change = config()['units'][unit]
    value['phases'] = list(range(6))
    value['feather_axial_length_world'] = change['feather_length_world']
    value['feather_vane_width_world'] = change['feather_width_world']
    value['limits'] = ['Unselected authored configuration; no native or human approval',
                       'Single-view source does not establish every unseen surface']
    return value


def author(t, unit):
    # The previous surface builder still solves all real leg and arm chains.
    # Only its equipment dimensions are changed by this local explicit contract.
    old_contract = previous.contract
    try:
        previous.contract = lambda u: contract_from_original(u, old_contract)
        mesh, joints = previous.author(t, unit)
    finally:
        previous.contract = old_contract
    return mesh, joints


def contract_from_original(unit, old_contract):
    spec = copy.deepcopy(old_contract(unit))
    change = config()['units'][unit]
    spec['feather_axial_length_world'] = change['feather_length_world']
    spec['feather_vane_width_world'] = change['feather_width_world']
    return spec


def materials(unit, output):
    """One opaque UV material per mesh island, unchanged across the cycle."""
    output.mkdir(parents=True, exist_ok=False)
    root = previous.root_for(unit) / 'materials-editable'
    provenance = json.loads((root/'paint-source.json').read_text())['own_material_provenance']['materials']
    changes = config()['units'][unit]
    result, pins = {}, {}
    for name, record in provenance.items():
        source = root / (name+'.png')
        assert sha(source) == record['sha256'], 'Preserved paint changed: '+name
        pixels = np.asarray(Image.open(source).convert('RGB'), float)
        if name == 'finish_feather':
            # Author a warm ochre vane with pale shaft, distinct barbs and dark
            # outside edge. No stochastic noise or frame-dependent UVs.
            h,w = pixels.shape[:2]
            yy,xx = np.mgrid[:h,:w]
            x,y = xx/max(1,w-1), yy/max(1,h-1)
            base = np.asarray(changes['feather_rgb'])
            edge = np.clip(np.minimum(x,1-x)/.12,0,1)
            ridge = np.exp(-((x-.48)/.045)**2)
            barbs = np.where(((y*13 + np.abs(x-.48)*5)%1)<.16,.78,1.)
            pixels = base[None,None,:]*(.72+.28*edge[:,:,None])*barbs[:,:,None]
            pixels = pixels*(1-ridge[:,:,None]*.72)+np.asarray(changes['feather_shaft_rgb'])[None,None,:]*ridge[:,:,None]*.72
        elif name == 'finish_bow' and unit == 'veteranIceHunter':
            h,w = pixels.shape[:2]
            yy,xx = np.mgrid[:h,:w]
            y = yy/max(1,h-1)
            # Broad inlay across real hooked tips. The old sampled tip was
            # mostly dark source background; this is deliberate opaque paint.
            end = np.maximum(np.clip((.20-y)/.07,0,1),np.clip((y-.77)/.07,0,1))
            pale = np.asarray(changes['bow_tip_rgb'])
            grain = .88+.12*np.cos((xx/max(1,w-1)-.35)*math.pi)
            pixels = pixels*(1-end[:,:,None])+pale[None,None,:]*grain[:,:,None]*end[:,:,None]
        elif name in ('finish_calf','finish_foot','finish_knee'):
            # Keep source brush variation, adjust values once across the shared
            # calf/vamp islands; this never changes opacity or anatomy.
            pixels *= changes['boot_value_multiplier']
        target = output / (name+'.png')
        Image.fromarray(np.clip(pixels,0,255).astype(np.uint8)).save(target)
        result[name] = {'pixels': np.asarray(Image.open(target).convert('RGB'),float),'baked':True}
        pins[name] = {'source':source.relative_to(PROJECT).as_posix(),'source_sha256':sha(source),
                      'output_sha256':sha(target),'baked':True}
    write_json(output/'paint-provenance.json',pins)
    return result


def shadow(mesh):
    """Fixed-light ground projection of actual triangles; independent RGBA layer."""
    vertices = np.asarray(mesh.vertices, float).copy()
    light = original.LIGHT
    vertices[:,0] -= vertices[:,2]*light[0]/light[2]
    vertices[:,1] -= vertices[:,2]*light[1]/light[2]
    vertices[:,2] = 0
    xy = np.stack((197+vertices@fit.RIGHT*fit.SCALE,266-vertices@fit.UP*fit.SCALE),1)
    ss = 3
    layer = Image.new('L',(450*ss,400*ss))
    draw = ImageDraw.Draw(layer)
    for face, part in zip(mesh.faces,mesh.parts):
        if 'shadow' not in part:
            draw.polygon([tuple(p*ss) for p in xy[list(face)]],fill=config()['shadow_alpha'])
    layer = layer.filter(ImageFilter.GaussianBlur(.45*ss)).resize((450,400),Image.Resampling.LANCZOS)
    result = Image.new('RGBA',(450,400),(19,17,16,0))
    result.putalpha(layer)
    return result


def mirror(image):
    result = Image.new('RGBA',image.size)
    result.paste(ImageOps.mirror(image),(-56,0))
    return result


def dependencies():
    result = {}
    for unit in UNITS:
        result.update(previous.source_pins(unit))
        root = previous.root_for(unit)/'materials-editable'
        for path in root.iterdir():
            if path.is_file():result[path.relative_to(PROJECT).as_posix()] = sha(path)
    for module in tuple(sys.modules.values()):
        name = getattr(module,'__file__',None)
        if name:
            path=Path(name).resolve()
            if path.is_file() and PROJECT in path.parents and path.suffix=='.py':
                result[path.relative_to(PROJECT).as_posix()] = sha(path)
    result[(HERE/'finish-source.json').relative_to(PROJECT).as_posix()] = sha(HERE/'finish-source.json')
    return dict(sorted(result.items()))


def freeze_selected():
    paths = set()
    selection = PROJECT/'assets/production/creatures/selection-v1.json'
    data = json.loads(selection.read_text())
    paths.add(selection)
    paths.add(PROJECT/'assets/manifest.json')
    for row in data['active']:
        paths.add(PROJECT/row['source'])
        unit = row['unit']
        paths.update((PROJECT/'assets/source/creatures'/unit/'registered-v3').rglob('*'))
        paths.update((PROJECT/'assets/recipes/creatures').glob(unit+'*.json'))
    return {p.relative_to(PROJECT).as_posix():sha(p) for p in sorted(paths) if p.is_file()}


def render_all():
    if shutil.disk_usage(HERE).free < 2.2*1024**3:
        raise RuntimeError('C: reserve under 2.2GiB; coordinator scratch assignment required')
    REPORT.mkdir(parents=True,exist_ok=False)
    write_json(REPORT/'selected-before.json',freeze_selected())
    write_json(REPORT/'dependency-pins.json',dependencies())
    for unit in UNITS:
        out = HERE/'candidates'/unit
        out.mkdir(parents=True,exist_ok=False)
        mats = materials(unit,out/'materials')
        (out/'materials.mtl').write_text('\n'.join('newmtl '+name+'\nKd 1 1 1\nmap_Kd materials/'+name+'.png\n' for name in mats),encoding='ascii')
        records=[]
        for phase in range(6):
            mesh,joints = author(phase/6,unit)
            paint = previous.render(mesh,mats)
            ground = shadow(mesh)
            composite = Image.alpha_composite(ground,paint)
            for label,image in (('surface',paint),('shadow',ground),('composite',composite)):
                image.save(out/f'{label}-g00-f{phase:03}.png')
            mirror(composite).save(out/f'mirror-only-g00-f{phase:03}.png')
            obj=out/f'phase{phase}.obj'
            mesh.export_obj(obj)
            records.append({'phase':phase,'t':phase/6,'preview_duration_ms':100,'semantic':SEMANTICS[phase],
                            'joints':joints,'obj_sha256':sha(obj),
                            'surface_sha256':sha(out/f'surface-g00-f{phase:03}.png'),
                            'shadow_sha256':sha(out/f'shadow-g00-f{phase:03}.png'),
                            'composite_sha256':sha(out/f'composite-g00-f{phase:03}.png')})
            print(unit,phase,flush=True)
        write_json(out/'receipt.json',{'unit':unit,'status':'authored configuration','selected':False,
                   'human_visual_approval':False,'camera':contract(unit)['camera'],'canvas':[450,400],
                   'pivot':[197,266],'frames':records,'source_dependencies':dependencies(),
                   'shadow':'actual triangle projection, fixed light; untested native palette/behavior',
                   'mirror':'renderer reflection only; no native facing observation'})
    print('Rendered owned Hunter family candidates',flush=True)


if __name__=='__main__':
    render_all()
