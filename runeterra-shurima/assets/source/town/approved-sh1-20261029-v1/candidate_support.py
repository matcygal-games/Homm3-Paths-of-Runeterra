from pathlib import Path
import hashlib,json,sys
from PIL import Image,ImageDraw,ImageChops,ImageFilter
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9,optimize=False)
SLUG=read(HERE/'site-plan-v1.json')['region']
CONFIG={SLUG:{}}
def source(slug):
 if slug!=SLUG:raise ValueError('Wrong owner namespace')
 return HERE
