"""Preserve the exact current scene-crop index; replace four civic crest frames.

All other native BuildingIDs/descriptors and decoded PNG pixels remain exact.
No live recipe/index/manifest/stage is written. --check replays owned candidates.
"""
from pathlib import Path
import argparse,hashlib,io,json,re
from PIL import Image
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[4];PLAN=HERE/'inputs-v1.json'
digest=lambda raw:hashlib.sha256(raw).hexdigest()
sha=lambda p:digest(p.read_bytes())
encoded=lambda v:(json.dumps(v,indent=2,sort_keys=True)+'\n').encode()
def png(im):
 stream=io.BytesIO();im.save(stream,format='PNG',compress_level=9,optimize=False);return stream.getvalue()
def image(raw):return Image.open(io.BytesIO(raw)).convert('RGBA')
def safe(name):
 if not isinstance(name,str) or not name.startswith('assets/source/') or '\\' in name or ':' in name or any(not p or p in ('.','..') or p.rstrip(' .')!=p or re.match(r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)',p,re.I) for p in name.split('/')):raise ValueError('Unsafe source input')
 p=PROJECT/name
 for q in (p,*p.parents):
  if q==PROJECT:break
  if q.is_symlink() or q.exists() and getattr(q.stat(),'st_file_attributes',0)&0x400:raise ValueError('Redirected source input')
 if not p.resolve().is_relative_to(PROJECT):raise ValueError('Escaping source input')
 return p
def build():
 plan=json.loads(PLAN.read_text(encoding='utf-8'))
 if plan.get('schema')!='shurima-crest-index-v1' or {r['state'] for r in plan['states']}!={'villageHall','townHall','cityHall','capitol'}:raise ValueError('Wrong index contract')
 inputs={}
 for name,pin in plan['input_sha256'].items():
  p=safe(name)
  if not p.is_file():raise ValueError('Missing indexed input: '+name)
  raw=p.read_bytes()
  if digest(raw)!=pin:raise ValueError('Changed indexed input: '+name)
  inputs[name]=raw
 def blob(name):
  if name not in inputs:raise ValueError('Undeclared indexed input: '+name)
  return inputs[name]
 old=json.loads(blob(plan['before_index']));candidate=json.loads(blob(plan['before_index']));terrain=image(blob(plan['terrain']));outputs={};checks=[]
 for job in plan['states']:
  state=job['state'];before=terrain.copy();before.alpha_composite(image(blob(job['old_frame'])));before=before.crop(tuple(job['crop'])).resize((150,70),Image.Resampling.LANCZOS)
  original=image(blob(job['before_icon']))
  if before.tobytes()!=original.tobytes():raise ValueError('Current indexed scene-crop consumer not reproduced: '+state)
  after=terrain.copy();after.alpha_composite(image(blob(job['new_frame'])));after=after.crop(tuple(job['crop'])).resize((150,70),Image.Resampling.LANCZOS)
  dest=HERE/(state+'.png');outputs[dest]=png(after)
  entry=next(r for r in candidate['frames'] if r['building']==state)
  if entry['frame']!=job['native_building_id']:raise ValueError('Native BuildingID changed')
  entry.update(source=dest.relative_to(PROJECT).as_posix(),source_sha256=digest(outputs[dest]))
  checks.append({'state':state,'native_building_id':entry['frame'],'before_current_icon_pixels_exact':True,'source':entry['source'],'source_sha256':entry['source_sha256']})
 for before,after in zip(old['frames'],candidate['frames']):
  if before['building'] not in {r['state'] for r in plan['states']} and before!=after:raise ValueError('Unrelated index frame changed')
 candidate['generation']['producer']=Path(__file__).relative_to(PROJECT).as_posix();candidate['generation']['producer_sha256']=sha(Path(__file__))
 candidate['generation']['method']='Exact current native-ID contextual scene-crop index; four Hall crests updated from current painted2D frame candidates, all other frame descriptors/pixels retained.'
 candidate['dependencies']=[{'path':Path(__file__).relative_to(PROJECT).as_posix(),'sha256':sha(Path(__file__))},{'path':PLAN.relative_to(PROJECT).as_posix(),'sha256':sha(PLAN)},*({'path':name,'sha256':pin} for name,pin in sorted(plan['input_sha256'].items()))]
 outputs[HERE/'buildingIcons-candidate-v1.json']=encoded(candidate)
 for name,raw in inputs.items():
  if not safe(name).is_file() or safe(name).read_bytes()!=raw:raise ValueError('Indexed input changed during replay: '+name)
 return outputs,checks
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');parser.add_argument('--check',action='store_true');args=parser.parse_args();artifacts,checks=build()
 for p,raw in artifacts.items():
  if not p.resolve().is_relative_to(HERE):raise ValueError('Output escaped candidate leaf')
  if p.is_file():
   if p.read_bytes()!=raw:raise ValueError('Indexed candidate differs: '+p.name)
  elif args.write:p.write_bytes(raw)
  else:raise ValueError('Missing prepared indexed candidate: '+p.name)
 print(json.dumps({'ok':True,'status':'authored configuration','four_frames':checks,'native_execution':False,'release_accepted':False}))
if __name__=='__main__':main()
