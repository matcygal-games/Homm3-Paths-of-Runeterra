from pathlib import Path
import hashlib,json
from PIL import Image
S=Path(__file__).resolve().parent;P=S.parents[3]
d=json.loads((S/'derivation.json').read_text())
def pinned(name,pin):
 p=P/name
 if hashlib.sha256(p.read_bytes()).hexdigest()!=pin:raise ValueError('Changed painted input: '+name)
 return p
bg=Image.open(pinned(d['background']['path'],d['background']['sha256'])).convert('RGBA')
for row in d['cards']:
 layer=Image.open(pinned(row['layer'],row['layer_sha256'])).convert('RGBA')
 scene=Image.alpha_composite(bg,layer).convert('RGB')
 card=scene.crop(row['viewport']).resize((150,70),Image.Resampling.LANCZOS).convert('RGBA')
 card.save(P/row['output'])
print(json.dumps({'cards':len(d['cards']),'status':'authored configuration'}))
