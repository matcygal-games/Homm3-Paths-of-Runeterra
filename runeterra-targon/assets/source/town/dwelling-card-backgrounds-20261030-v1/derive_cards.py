"""Replay selected own painted card compositions from the pinned derivation."""
import hashlib,json
from pathlib import Path
from PIL import Image,ImageOps
S=Path(__file__).resolve().parent
P=next(p for p in S.parents if (p/'content/factions.json').is_file())
def check(row):
    p=P/row['path']
    if hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:raise ValueError('Changed source: '+row['path'])
    return p
def main():
    d=json.loads((S/'derivation.json').read_text())
    bg=Image.open(check(d['background'])).convert('RGBA').crop(d['background_crop']).resize((150,70),Image.Resampling.LANCZOS)
    for row in d['records']:
        fg=Image.open(check(row['old_source'])).convert('RGBA')
        if 'layer' in row:
            im=Image.open(check(row['layer'])).convert('RGBA').crop(row['layer_crop'])
            im=ImageOps.contain(im,tuple(row['fit']),Image.Resampling.LANCZOS)
            fg=Image.new('RGBA',(150,70));fg.alpha_composite(im,tuple(row['offset']))
        final=bg.copy();final.alpha_composite(fg)
        dst=P/row['new_source']['path'];final.save(dst,format='PNG',compress_level=9)
        if hashlib.sha256(dst.read_bytes()).hexdigest()!=row['new_source']['sha256']:raise ValueError('Replay differs: '+str(dst))
    print('Reproduced fourteen exact native construction cards')
if __name__=='__main__':main()
