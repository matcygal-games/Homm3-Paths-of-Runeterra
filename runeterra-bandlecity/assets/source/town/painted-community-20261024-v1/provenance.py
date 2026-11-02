"""Record actual built-in imagegen masters, never invent a model identifier."""
from pathlib import Path
import hashlib,json
from PIL import Image
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
for directory in [HERE/'background']+[p for p in HERE.iterdir() if p.is_dir() and p.name.startswith('dwelling')]:
    master=directory/'master.png'
    if not master.is_file():continue
    with Image.open(master) as im:canvas=list(im.size)
    record={'status':'authored configuration','image_generation_used':True,'tool':'image_gen.imagegen',
        'provider':'OpenAI built-in imagegen','model':'not exposed by built-in tool',
        'painted_master':master.relative_to(ROOT).as_posix(),'painted_master_sha256':hashlib.sha256(master.read_bytes()).hexdigest(),
        'master_canvas':canvas,'prompt':(directory/'prompt.txt').read_text(encoding='utf-8').strip(),
        'prompt_file':(directory/'prompt.txt').relative_to(ROOT).as_posix(),
        'transparent_background_requested':directory.name!='background','visual_approval_granted':False,
        'rights':'unresolved','production':'painted 2D; no 3D production or code-generated artwork'}
    if directory.name.startswith('dwellingUp'):
        base=HERE/directory.name.replace('Up','')/'master.png'
        record['reference_images']=[{'path':base.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(base.read_bytes()).hexdigest(),'role':'Exact base building edit target; same physical site'}]
    if directory.name!='background':
        card={'2':'05BC177','5':'05BC175','7':'05BC151'}[directory.name[-1]]
        reference=ROOT/'references/private/roster-20261024'/f'{card}-full.png'
        record['regional_reference']={'path':reference.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(reference.read_bytes()).hexdigest(),
            'role':'Official LoR subject reference inspected; no copied card pixels; private reference excluded from distributable assets'}
    (directory/'generation.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n',encoding='utf-8')
