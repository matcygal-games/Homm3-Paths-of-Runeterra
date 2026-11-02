"""Deterministic own-painted scenery composition for native dwelling cards.

No creative bitmap generation or rendering is performed. The existing selected
150x70 building cutouts retain their exact pixel positions and opacity; the
selected own town terrain fills the transparent area behind them.
"""
from pathlib import Path
import copy, hashlib, io, json
from PIL import Image

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
RECIPE = PROJECT / 'assets/recipes/ui/town-surfaces-v1/buildingIcons.json'
BACKGROUND_RECIPE = PROJECT / 'assets/recipes/town/background.png.json'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False)+'\n').encode()

def ref(path):
    return {'path':Path(path).relative_to(PROJECT).as_posix(), 'sha256':sha(path)}

def png(image):
    stream=io.BytesIO(); image.save(stream,format='PNG',optimize=False)
    return stream.getvalue()

def run():
    history=HERE/'buildingIcons-before.json'
    if not history.exists():
        history.write_bytes(RECIPE.read_bytes())
    old=read(history); candidate=copy.deepcopy(old)
    bg_recipe=read(BACKGROUND_RECIPE); bg_path=PROJECT/bg_recipe['source']
    if sha(bg_path)!=bg_recipe['source_sha256']:
        raise ValueError('Selected painted background changed')
    with Image.open(bg_path) as image:
        image.load(); backdrop=image.convert('RGBA').crop((0,0,650,303)).resize((150,70),Image.Resampling.LANCZOS)
    if backdrop.getchannel('A').getextrema()!=(255,255):
        raise ValueError('Selected town scenery must be opaque')
    inputs=[ref(history),ref(bg_path),ref(BACKGROUND_RECIPE),ref(Path(__file__))]
    checks=[]
    for row in candidate['frames']:
        if not 30<=row['frame']<=43:
            continue
        original=PROJECT/row['source']
        if sha(original)!=row['source_sha256']:
            raise ValueError('Selected building input changed: '+row['building'])
        with Image.open(original) as image:
            image.load(); figure=image.convert('RGBA')
        if figure.size!=(150,70): raise ValueError('Unexpected card canvas')
        composed=Image.alpha_composite(backdrop,figure)
        if composed.getchannel('A').getextrema()!=(255,255):
            raise ValueError('Construction card must fill the native scene')
        before_pixels,after_pixels=figure.tobytes(),composed.tobytes()
        for offset in range(0,len(before_pixels),4):
            if before_pixels[offset+3]==255 and before_pixels[offset:offset+4]!=after_pixels[offset:offset+4]:
                raise ValueError('Opaque building pixel changed')
        target=HERE/'cards'/f"{row['building']}.png"
        target.parent.mkdir(parents=True,exist_ok=True)
        data=png(composed)
        if not target.exists() or target.read_bytes()!=data:target.write_bytes(data)
        inputs.append(ref(original))
        checks.append({'building':row['building'],'frame':row['frame'],
                       'before':ref(original),'after':ref(target),
                       'before_alpha_extrema':list(figure.getchannel('A').getextrema()),
                       'after_alpha_extrema':[255,255],
                       'opaque_building_pixels_preserved':True})
        row['source']=target.relative_to(PROJECT).as_posix()
        row['source_sha256']=sha(target)
    if len(checks)!=14:raise ValueError('All fourteen dwelling cards required')
    ledger={'status':'authored configuration','method':'Exact alpha composite of existing own painted building card over own selected town terrain',
            'derived_from_blender':False,'new_image_generation_used':False,
            'native_canvas':[150,70],'background_crop':[0,0,650,303],
            'background_resize':'LANCZOS650x303to150x70; dry scenery without coastal water',
            'inputs':inputs,'upstream_generation':old['generation'],
            'frames':checks,'building_frame_ids_preserved':True,
            'native_visual_verified':False,'release_accepted':False}
    ledger_path=HERE/'generation-ledger.json'; ledger_path.write_bytes(encoded(ledger))
    candidate['generation']['source_generation_ledger']=ledger_path.relative_to(PROJECT).as_posix()
    candidate['generation']['source_generation_ledger_sha256']=sha(ledger_path)
    candidate['generation']['prompt']='Existing own painted SH1 architecture and terrain; deterministic native150x70 dwelling-menu scenery assembly. No new image generation; exact upstream origins and input pins in generation-ledger.json.'
    candidate_path=HERE/'buildingIcons-candidate.json';candidate_path.write_bytes(encoded(candidate))
    return ledger,candidate_path

if __name__=='__main__':
    ledger,path=run();print(json.dumps({'status':'authored configuration','candidate':path.relative_to(PROJECT).as_posix(),'dwelling_frames':len(ledger['frames'])}))
