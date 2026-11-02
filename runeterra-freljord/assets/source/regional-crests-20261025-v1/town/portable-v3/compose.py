"""Version3: portable replay of pinned genuine crest paint; local sources only.

Reads no provider cache, absolute locator, private reference or report. Does not
generate art, call the original producer main, select recipes or publish stages.
"""
from pathlib import Path
import hashlib,importlib.util,json
from PIL import Image,ImageFilter

HERE=Path(__file__).resolve().parent
PROJECT=Path(__file__).resolve().parents[5]
STATES=('villageHall','townHall','cityHall','capitol')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def local(value):
 if not isinstance(value,str) or not value or '\\' in value or ':' in value or any(x in ('','.','..') for x in value.split('/')):raise ValueError('Unsafe local source path')
 p=(PROJECT/value).resolve()
 if not p.is_relative_to(PROJECT):raise ValueError('Local source escape')
 return p
def pinned(item):
 p=local(item['path'])
 if not p.is_file() or sha(p)!=item['sha256']:raise ValueError('Missing/stale pinned local source: '+item['path'])
 return p
def helper():
 p=PROJECT/'scripts/prepare_town_art.py';spec=importlib.util.spec_from_file_location('freljord_portable_crest_helper',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def replay():
 records=[]
 for state in STATES:
  g=read(HERE/state/'generation.json')
  for key in ('preparation_helper','edit_source','raw_source','preparation_source','mask_source'):pinned(g[key])
  records.append((state,g))
 h=helper()
 for state,g in records:
  folder=HERE.parent/state;target=pinned(g['edit_source']);raw=pinned(g['raw_source']);prep_path=pinned(g['preparation_source'])
  before=Image.open(target).convert('RGBA');generated=Image.open(raw).convert('RGBA')
  if before.size!=generated.size:raise ValueError('Edited canvas changed')
  box=tuple(g['existing_gable_box']);old=before.crop(box).convert('RGB');new=generated.crop(box).convert('RGB')
  facets=bytes(255 if ng>=og+10 and nb>=ob+10 and ng>=110 and nb>=65 and nr-nb<130 else 0 for (_,og,ob),(nr,ng,nb) in zip(old.getdata(),new.getdata()))
  part=Image.frombytes('L',old.size,facets).filter(ImageFilter.MaxFilter(3));mask=Image.new('L',before.size);mask.paste(part,box[:2])
  # Compare against immutable checked mask before retaining generated RGB.
  expected=Image.open(pinned(g['mask_source'])).convert('L')
  if mask.tobytes()!=expected.tobytes():raise ValueError('Crest selection replay differs')
  master=Image.composite(generated,before,mask);master.putalpha(before.getchannel('A'));master.save(folder/'master.png')
  prep=read(prep_path);native,_=h.place(master,prep['conversion']['rect']);icon=h.icon(master);native.save(folder/'layer.png');icon.save(folder/'icon.png')
  for item in g['products'].values():pinned(item)
 print('Portable-v3 local replay exact for4 crest masters,4 native layers and4 HALLicons; no provider cache or private reference input.')
if __name__=='__main__':replay()
