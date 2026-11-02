"""Reproduce painted portrait crops with uniform scale and alpha composition."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageOps
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if p.name=='runeterra-targon')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def render():
 cfg=json.loads((HERE/'derivation.json').read_text())
 bg=PROJECT/cfg['background']['path'];assert sha(bg)==cfg['background']['sha256']
 scene=Image.open(bg).convert('RGBA').crop(tuple(cfg['background']['crop'])).resize((58,64),Image.Resampling.LANCZOS)
 results={}
 for rec in cfg['records']:
  raw=PROJECT/rec['master'];assert sha(raw)==rec['master_sha256'];im=Image.open(raw).convert('RGBA');assert list(im.size)==rec['master_canvas']
  for role,entry in rec['outputs'].items():
   size=tuple(entry['canvas']);subject=ImageOps.contain(im.crop(tuple(entry['crop'])),size,Image.Resampling.LANCZOS)
   canvas=scene.copy() if role=='large' else Image.new('RGBA',size)
   canvas.alpha_composite(subject,((size[0]-subject.width)//2,size[1]-subject.height))
   output=PROJECT/entry['path'];output.parent.mkdir(parents=True,exist_ok=True);canvas.save(output,format='PNG',compress_level=9)
   assert sha(output)==entry['sha256'],(rec['unit'],role)
   results[entry['path']]=sha(output)
 return results
if __name__=='__main__':print(json.dumps({'outputs':render()},sort_keys=True,indent=2))
