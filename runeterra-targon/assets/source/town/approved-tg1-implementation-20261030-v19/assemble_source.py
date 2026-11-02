"""Self-contained painted TG1 compositor; alpha-zero RGB is always zero.

Editable native alpha masks, genuine painted RGB masters and genuine hidden
faces are source. No prior sliced full-RGB frame cache or3D is needed.
"""
import hashlib,io,json
from pathlib import Path
from PIL import Image,ImageChops

HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[3]
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_bytes())
def load(reference):
    path=PROJECT/reference['path']
    if path.resolve()!=path.absolute()or path.stat().st_nlink!=1 or digest(path)!=reference['sha256']:raise ValueError('Painted input missing/changed/aliased')
    with Image.open(path)as opened:opened.load();return opened.convert('RGBA')
def write(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists()and path.read_bytes()!=raw:raise ValueError('Preserve authored TG1 source: '+str(path))
    if not path.exists():path.write_bytes(raw)
def save(path,image):
    output=io.BytesIO();image.save(output,format='PNG',compress_level=9,optimize=False);write(path,output.getvalue())
def main():
    config=read(HERE/'source-config.json');alphas={s:load(row['alpha']).convert('L')for s,row in config['states'].items()}
    layers={}
    for state,row in config['states'].items():
        alpha=alphas[state]
        if any(alpha.histogram()[1:255]):raise ValueError('Authored architecture alpha must be opaque/transparent')
        # Only source pixels with nonzero alpha are ever copied into a layer.
        layer=Image.new('RGBA',(800,374));layer.paste(load(row['master']),(0,0),alpha)
        for face in row['hidden_faces']:
            budget=ImageChops.multiply(alpha,alphas[face['front_state']])
            layer.paste(load(face['painting']),(0,0),budget)
        layer.putalpha(alpha);layers[state]=layer;save(HERE/'frames'/(state+'.png'),layer)
    union=Image.new('L',(800,374))
    for state in config['complete_scene_states']:union=ImageChops.lighter(union,alphas[state])
    approved=load(config['approved']);background=approved.copy();background.paste(load(config['empty_recovery']),(0,0),union)
    full=background.copy()
    for state in config['complete_scene_states']:full.alpha_composite(layers[state])
    if full.tobytes()!=approved.tobytes():raise ValueError('Approved TG1 full RGBA changed')
    save(HERE/'background-native.png',background);save(HERE/'fully-built.png',full)
    print(json.dumps({'status':'authored configuration','states':len(layers),'alpha_zero_RGB_zero':True,'approved_RGBA_changes':0,'staging_or_native':False}))

if __name__=='__main__':main()
