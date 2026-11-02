"""Reproduce fourteen native scenic cards from pinned own painted inputs."""
from pathlib import Path
import hashlib, json
from PIL import Image

ROOT=Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def derive():
    cfg=json.loads((ROOT/'derivation.json').read_text())
    bg=cfg['background']; bp=ROOT/bg['path']
    if sha(bp)!=bg['sha256']: raise ValueError('Noxian background source changed')
    with Image.open(bp) as im:
        background=im.convert('RGBA').crop(tuple(bg['crop'])).resize((58,64),Image.Resampling.LANCZOS)
    background.putalpha(255)
    outputs=[]
    for row in cfg['units']:
        ip=ROOT/row['selected_input']
        if sha(ip)!=row['selected_input_sha256']: raise ValueError('Selected creature source changed: '+row['unit'])
        with Image.open(ip) as im: original=im.convert('RGBA')
        if original.size!=(58,64): raise ValueError('Native portrait dimensions changed')
        # Existing scenic Recruit/Veteran paintings need their weak full-canvas
        # alpha made opaque; their already painted scenery and RGB remain exact.
        if original.getchannel('A').getextrema()[0]>=250:
            result=original.copy(); result.putalpha(255)
        else:
            result=Image.alpha_composite(background,original)
        result.putalpha(255)
        path=ROOT/'outputs'/row['unit']/'large.png';path.parent.mkdir(parents=True,exist_ok=True)
        result.save(path)
        outputs.append({'unit':row['unit'],'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path),'size':[58,64],'alpha':[255,255]})
    return outputs

if __name__=='__main__': print(json.dumps({'status':'authored configuration','outputs':derive()},indent=2,sort_keys=True))
