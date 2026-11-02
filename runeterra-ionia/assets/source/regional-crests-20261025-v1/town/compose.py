"""Portable, local-source-only replay of genuine 2D crest paint and native fit.

No provider cache, private-reference image, generation call or full town main is
opened. Original master pixels are never normalized. Only edited fort input is
normalized when its declared three-pixel width mismatch is present.
"""
import hashlib,importlib.util,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter,ImageChops

SOURCE=Path(__file__).resolve().parent
PROJECT=Path(__file__).resolve().parents[4]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def local_path(value):
 p=(PROJECT/value).resolve()
 if Path(value).is_absolute():raise ValueError('Absolute source forbidden')
 try:p.relative_to(PROJECT)
 except ValueError:raise ValueError('Source escape forbidden')
 return p
def module(p,name):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
HELPER=module(PROJECT/'scripts/ionia_town_art.py','ionia_portable_crest_helper')
def cropbox(im):return im.getchannel('A').point(lambda v:255 if v>16 else 0).getbbox()
def product(im,kind,box):
 sprite=im.crop(cropbox(im))
 if kind=='layer':
  x,y,w,h=box;small=HELPER.fit(sprite,(w,h));size=(800,374);origin=(x+(w-small.width)//2,y+h-small.height)
 elif kind=='icon':small=HELPER.fit(sprite,(146,66));size=(150,70);origin=((150-small.width)//2,68-small.height)
 else:small=HELPER.fit(sprite,(56,62));size=(58,64);origin=((58-small.width)//2,64-small.height)
 out=Image.new('RGBA',size);out.alpha_composite(small,origin);return out,origin,small.size
def support(mask,old,kind,box):
 _,origin,size=product(old,kind,box);part=mask.crop(cropbox(old)).resize(size,Image.Resampling.LANCZOS)
 out=Image.new('L',{'layer':(800,374),'icon':(150,70),'campaign':(58,64)}[kind]);out.paste(part,origin)
 return out.filter(ImageFilter.MaxFilter(7)).point(lambda x:255 if x else 0)
def paint(before,raw,mask):
 out=Image.composite(raw,before,mask);out.putalpha(before.getchannel('A'));return out
def replay():
 layout=json.loads((PROJECT/'design/town-visuals.json').read_text());sites={k:v for v in [*layout['sites'].values(),*layout['special_sites'].values()] for k in v['keys']}
 for state in ['villageHall','townHall','cityHall','capitol','fort','citadel','castle']:
  dest=SOURCE/state;g=json.loads((dest/'generation.json').read_text());original=local_path(g['input_master']);rawpath=local_path(g['raw_edited_master']);maskpath=local_path(g['mask'])
  for p,pin in [(original,g['input_master_sha256']),(rawpath,g['raw_edited_sha256']),(maskpath,g['mask_sha256'])]:
   if sha(p)!=pin:raise ValueError('Stale local source: '+str(p.relative_to(PROJECT)))
  if sha(PROJECT/'scripts/ionia_town_art.py')!=g['preparation_helper_sha256']:raise ValueError('Preparation helper changed')
  before=Image.open(original).convert('RGBA');raw=Image.open(rawpath).convert('RGBA');mask=Image.open(maskpath).convert('L')
  if raw.size!=before.size:
   if state!='fort' or raw.size!=(1945,809) or before.size!=(1942,809):raise ValueError('Unexpected edited canvas')
   raw=raw.resize(before.size,Image.Resampling.LANCZOS)
  master=paint(before,raw,mask);master.save(dest/'master.png')
  if sha(dest/'master.png')!=g['candidate_master_sha256']:raise ValueError('Painted master replay mismatch')
  for kind in ('layer','icon','campaign'):
   image,_,_=product(master,kind,sites[state]['box']);image.save(dest/(kind+'.png'))
   if sha(dest/(kind+'.png'))!=g['products'][kind]['sha256']:raise ValueError('Native product replay mismatch')
 print('Seven locally pinned Ionia crest masters and21 derived products replayed exactly; no cache or private reference opened.')
if __name__=='__main__':replay()
