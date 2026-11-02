"""Composite existing selected painted portraits over existing painted Shurima scenery.

This is deterministic native UI assembly. It does not redraw subjects or use 3D.
"""
from pathlib import Path
import hashlib, json, io
from PIL import Image

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[3]
def sha(data): return hashlib.sha256(data).hexdigest()
def png(im):
    out=io.BytesIO(); im.save(out,format='PNG',compress_level=9,optimize=False); return out.getvalue()
def derive(config):
    background=PROJECT/config['background']['path']
    assert sha(background.read_bytes())==config['background']['sha256']
    crop=tuple(config['background']['crop'])
    painted=Image.open(background).convert('RGBA').crop(crop).resize((58,64),Image.Resampling.LANCZOS)
    assert painted.getchannel('A').getextrema()==(255,255)
    results={}
    for row in config['portraits']:
        raw=(PROJECT/row['source']).read_bytes()
        assert sha(raw)==row['source_sha256']
        subject=Image.open(io.BytesIO(raw)).convert('RGBA')
        assert subject.size==(58,64)
        result=Image.alpha_composite(painted,subject)
        assert result.getchannel('A').getextrema()==(255,255)
        opaque=subject.getchannel('A').point(lambda value:255 if value==255 else 0)
        from PIL import ImageChops
        assert not ImageChops.multiply(ImageChops.difference(subject.convert('RGB'),result.convert('RGB')),opaque.convert('RGB')).getbbox()
        results[row['unit']]=png(result)
    return results
def main():
    config=json.loads((ROOT/'composition.json').read_text())
    first=derive(config); second=derive(config)
    assert first==second
    for name,data in first.items():
        out=ROOT/'resources'/name/'large.png';out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(data)
    print(json.dumps({'status':'authored configuration','portraits':len(first),'double_assembly_identical':True,'outputs':{name:sha(data) for name,data in first.items()}},indent=2))
if __name__=='__main__':main()
