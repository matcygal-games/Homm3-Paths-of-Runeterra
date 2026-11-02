"""Unselected six-address development expansion of frozen reviewed contacts.

No paint/UV/geometry/camera changes. Materials are real immutable inputs; each
assembly solves and rasterizes all six poses independently, never copying idle.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys

import numpy as np
import PIL
from PIL import Image, ImageOps

HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(HERE.parent))
import finish_contacts as frozen

PROJECT=frozen.PROJECT
WORKSPACE=PROJECT.parent
REPORT=frozen.REPORT.parent/'six-phase-development-v1'
UNITS=frozen.UNITS
DURATION_MS=100
SEMANTICS=('contact A: near heel/sole lead, far toe-off',
           'passing A: near stance, far swing rising',
           'late stance A / far reach; continuous near push-off follows',
           'contact B: far heel/sole lead, near toe-off',
           'passing B: far stance, near swing rising',
           'late stance B / near return-reach; continuous far push-off follows')


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_text(encoding='utf-8'))
def encoded(value):return json.dumps(value,indent=2,sort_keys=True)+'\n'
def root_for(unit):return frozen.root_for(unit)/HERE.name


def write_new(path,value):
    if path.exists():raise ValueError('Preserve '+str(path))
    path.write_text(encoded(value),encoding='utf-8')


def preservation():
    groups=load(REPORT/'before-pins.json')['groups']
    return {name:{'checked':len(entries),'changed_or_missing':[path for path,value in entries.items()
                  if not (WORKSPACE/path).is_file() or sha(WORKSPACE/path)!=value]}
            for name,entries in groups.items()}


def dependencies(unit):
    paths={PROJECT/name:value for name,value in frozen.source_pins(unit).items()}
    paths[Path(__file__)]=sha(Path(__file__))
    for path in (frozen.root_for(unit)/'materials-editable').iterdir():
        if path.is_file():paths[path]=sha(path)
    for path in (frozen.root_for(unit)/'finish-contract.json',frozen.root_for(unit)/'source-pins.json'):
        paths[path]=sha(path)
    return {path.relative_to(PROJECT).as_posix():value for path,value in sorted(paths.items())}


def materials(unit):
    root=frozen.root_for(unit)/'materials-editable'
    provenance=load(root/'paint-source.json')['own_material_provenance']['materials']
    result={}
    for name,row in provenance.items():
        path=root/(name+'.png')
        assert sha(path)==row['sha256'],name
        result[name]={'pixels':np.asarray(Image.open(path).convert('RGB'),float),'baked':True}
    return result


def contract(unit):
    return {'unit':unit,'status':'built-unreviewed','selected':False,'registered':False,
            'purpose':'Private battle-sprite six-phase development walk; not a map animation or production recipe',
            'source_dependencies':dependencies(unit),'canvas':[450,400],'pivot':[197,266],
            'camera':frozen.contract(unit)['camera'],'cycle_duration_ms':600,'duration_ms_each':DURATION_MS,
            'pose_sampling':'t=i/6; zero-order-held discrete poses, no engine interpolation claimed',
            'continuous_sample_mapping':[{ 'sample':sample,'t':sample/60,
                  'address':min(5,sample//10) if sample<60 else 0,
                  'exact_selected_pose':sample in (0,10,20,30,40,50,60),
                  'loop_endpoint':sample==60} for sample in range(61)],
            'frames':[{'address':i,'t':i/6,'exact_dense_sample':i*10,'duration_ms':DURATION_MS,
                 'display_window_ms':[i*DURATION_MS,(i+1)*DURATION_MS],
                 'semantic':SEMANTICS[i],'file':f'g00-f{i:03}.png'} for i in range(6)],
            'push_off_precision':'Existing continuous stance pitch begins at local stance phase .38; samples2/5 are late-stance/reach, with toe-off between2->3 and5->0. No changed pose to satisfy a label.',
            'frozen_materials':True,'paint_uv_or_geometry_changes':False,
            'mirror_only':{'mapping':'discrete pixel x_mirror=393-x; y unchanged',
                 'native_pivot_preserved':[197,266],
                 'scope':'Renderer-facing reflection check ONLY; not independent3D turn,8-direction movement or runtime evidence'},
            'timing_limit':'100ms/pose is a development preview contract, not measured VCMI timing or movement speed',
            'identity_notes':['Known darker compact feather fan and weak Veteran pale tip retained without tuning',
                              'Known shoulder/waist/leather cosmetic differences retained']}


def mirror(image):
    result=Image.new('RGBA',image.size)
    # Mirror pixel centres around197, not the arbitrary225-pixel canvas centre.
    result.paste(ImageOps.mirror(image),(-56,0))
    return result


def assemble(unit,label):
    root=root_for(unit)
    root.mkdir(parents=True,exist_ok=True)
    spec=contract(unit)
    if label=='run-a':
        before=preservation()
        assert all(not row['changed_or_missing'] for row in before.values()),before
        write_new(root/'phase-contract.json',spec)
    else:assert load(root/'phase-contract.json')==spec
    out=root/label
    out.mkdir(exist_ok=False)
    (out/'materials').mkdir();(out/'mirror-renderer-only').mkdir()
    mats=materials(unit)
    for name in mats:
        # Preserved editable paint inputs, not a new material generation pass.
        path=frozen.root_for(unit)/'materials-editable'/(name+'.png')
        (out/'materials'/path.name).write_bytes(path.read_bytes())
    mtl=[]
    for name in mats:mtl+=['newmtl '+name,'Kd 1 1 1','map_Kd materials/'+name+'.png','']
    (out/'materials.mtl').write_text('\n'.join(mtl),encoding='ascii')
    atlas=Image.new('RGBA',(2700,400));mirror_atlas=Image.new('RGBA',(2700,400))
    records=[]
    for i in range(6):
        mesh,joints=frozen.author(i/6,unit)
        image=frozen.render(mesh,mats)
        path=out/f'g00-f{i:03}.png';obj=out/f'phase{i}.obj'
        image.save(path);mesh.export_obj(obj)
        reflected=mirror(image)
        reflected.save(out/'mirror-renderer-only'/path.name)
        atlas.paste(image,(450*i,0));mirror_atlas.paste(reflected,(450*i,0))
        records.append({'address':i,'t':i/6,'duration_ms':DURATION_MS,'semantic':SEMANTICS[i],
             'png_sha256':sha(path),'obj_sha256':sha(obj),'mirror_only_sha256':sha(out/'mirror-renderer-only'/path.name),
             'triangles':len(mesh.faces),'vertices':len(mesh.vertices),'joints':joints})
    atlas.save(out/'six-phase-atlas.png');mirror_atlas.save(out/'six-phase-mirror-renderer-only.png')
    first,_=frozen.author(0,unit)
    write_new(out/'editable-uv-topology.json',{'uv':first.uv,'faces':first.faces,'parts':first.parts,
                  'materials':first.materials,'note':'Stable topology/UV across phases; phase OBJ carries actual posed coordinates'})
    write_new(out/'private-animation.json',{'format':'UNREGISTERED-DEVELOPMENT-ONLY','unit':unit,
         'canvas':[450,400],'pivot':[197,266],'cycle_ms':600,
         'frames':[{'address':i,'image':f'g00-f{i:03}.png','duration_ms':100,
                    'atlas_rect':[450*i,0,450*(i+1),400]} for i in range(6)],
         'not_registered_in_manifest_or_recipe':True})
    files={path.relative_to(out).as_posix():sha(path) for path in out.rglob('*') if path.is_file()}
    receipt={'unit':unit,'status':'built-unreviewed','selected':False,'human_visual_approval':False,
         'native_verified':False,'production_ready':False,'phase_contract_sha256':sha(root/'phase-contract.json'),
         'source_dependencies':dependencies(unit),'files':files,'frames':records,
         'runtime_environment':{'python':sys.version,'numpy':np.__version__,'pillow':PIL.__version__}}
    write_new(out/'receipt.json',receipt)
    print(encoded({'unit':unit,'assembly':label,'receipt_sha256':sha(out/'receipt.json'),
                   'frames':[{'address':row['address'],'sha256':row['png_sha256']} for row in records]}))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('unit',choices=UNITS);parser.add_argument('assembly',choices=('run-a','run-b'))
    args=parser.parse_args();assemble(args.unit,args.assembly)
