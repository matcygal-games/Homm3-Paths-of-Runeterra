"""Portable, strictly pinned 2D crest assembly. Never writes live selections.

Run --check to replay only; --write materializes the owned candidate artifacts.
Inputs are delivered edited paintings, actual original 2D frames, explicit masks,
prompts and template snapshots. No report, private reference or generator service
is required to reproduce the prepared frames and sixteen recipes.
"""
from pathlib import Path
import argparse, hashlib, io, json, re
import numpy as np
from PIL import Image

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
PLAN=HERE/'inputs-v2.json'

def digest(raw): return hashlib.sha256(raw).hexdigest()
def sha(path): return digest(path.read_bytes())
def encoded(value):return (json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
def png(image):
 stream=io.BytesIO();image.save(stream,format='PNG',compress_level=9,optimize=False);return stream.getvalue()
def image(raw):return Image.open(io.BytesIO(raw)).convert('RGBA')
def safe(name):
 if (not isinstance(name,str) or not name.startswith('assets/source/') or '\\' in name or ':' in name
     or any(not p or p in ('.','..') or p.rstrip(' .')!=p or re.match(r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)',p,re.I) for p in name.split('/'))):
  raise ValueError('Unsafe own source path')
 path=PROJECT/name
 for part in (path,*path.parents):
  if part==PROJECT:break
  if part.is_symlink() or part.exists() and getattr(part.stat(),'st_file_attributes',0)&0x400:
   raise ValueError('Redirected own input')
 if not path.resolve().is_relative_to(PROJECT):raise ValueError('Escaping own input')
 return path

def build():
 plan=json.loads(PLAN.read_text(encoding='utf-8'))
 if plan.get('schema')!='shurima-crest-assembly-v2' or {r['state'] for r in plan['states']}!={'villageHall','townHall','cityHall','capitol'}:
  raise ValueError('Wrong assembly contract')
 inputs={}
 for name,pin in plan['input_sha256'].items():
  path=safe(name)
  if not path.is_file():raise ValueError('Missing assembly input: '+name)
  raw=path.read_bytes()
  if digest(raw)!=pin:raise ValueError('Changed assembly input: '+name)
  inputs[name]=raw
 def blob(name):
  if name not in inputs:raise ValueError('Undeclared assembly input: '+name)
  return inputs[name]
 outputs={};notes=[]
 dependencies=[{'path':Path(__file__).relative_to(PROJECT).as_posix(),'sha256':sha(Path(__file__))},
               {'path':PLAN.relative_to(PROJECT).as_posix(),'sha256':sha(PLAN)},
               *({'path':name,'sha256':pin} for name,pin in sorted(plan['input_sha256'].items()))]
 for job in plan['states']:
  state=job['state'];folder=HERE/state
  old=image(blob(job['original_frame']));box=tuple(job['native_bbox']);crop=old.crop(box)
  mask=image(blob(job['mask'])).convert('L');assert mask.size==crop.size
  m=np.array(mask)>0;before=np.array(crop);after=before.copy()
  edited=image(blob(job['painted_edit'])).resize(crop.size,Image.Resampling.LANCZOS)
  after[m,:3]=np.array(edited)[m,:3]
  assert np.array_equal(after[:,:,3],before[:,:,3]) and np.array_equal(after[~m],before[~m])
  candidate=old.copy();candidate.paste(Image.fromarray(after,'RGBA'),box[:2]);outputs[folder/'candidate-frame.png']=png(candidate)
  generation={'provider':'OpenAI built-in imagegen','image_generation_used':True,'model':'not exposed by built-in tool',
              'painted_master':job['painted_edit'],'painted_master_sha256':plan['input_sha256'][job['painted_edit']],
              'prompt_file':job['prompt'],'prompt':blob(job['prompt']).decode('utf-8'),
              'producer':Path(__file__).relative_to(PROJECT).as_posix(),'producer_sha256':sha(Path(__file__)),
              'method':'Genuine crest-only painted crop, declared surface mask; exact original native alpha and every non-crest body pixel preserved.',
              'source_generation_ledger':(folder/'generation-v2.json').relative_to(PROJECT).as_posix()}
  record={'schema':'painted-crest-origin-v2','region':'shurima','state':state,'image_generation_used':True,
          'provider':'OpenAI built-in imagegen','model':'not exposed by built-in tool',
          'painted_master':job['painted_edit'],'painted_master_sha256':plan['input_sha256'][job['painted_edit']],
          'prompt_file':job['prompt'],'prompt_sha256':plan['input_sha256'][job['prompt']],
          'original_painted_master':job['lineage_master'],'original_painted_master_sha256':plan['input_sha256'][job['lineage_master']],
          'original_generation_record':job['lineage_ledger'],'original_generation_record_sha256':plan['input_sha256'][job['lineage_ledger']],
          'native_execution':False,'visual_approval_granted':False,'release_accepted':False}
  record_path=folder/'generation-v2.json';outputs[record_path]=encoded(record)
  recipe_deps=[*dependencies,{'path':record_path.relative_to(PROJECT).as_posix(),'sha256':digest(outputs[record_path])}]
  for role,template in job['templates'].items():
   r=json.loads(blob(template));r['generation']=generation;r['dependencies']=recipe_deps
   r['visual_approval_granted']=False;r['status']='painted-candidate'
   if role=='animation':
    source=folder/'candidate-frame.png';raw=outputs[source]
    r['groups'][0]['frames'][0].update(source=source.relative_to(PROJECT).as_posix(),source_sha256=digest(raw),sha256=digest(raw))
   elif role in ('area','border'):
    source=folder/(role+'.png');raw=blob(r['source']);outputs[source]=raw
    r.update(source=source.relative_to(PROJECT).as_posix(),source_sha256=digest(raw))
   else:
    original=image(blob(r['source']));arr=np.array(original);ib=original.getchannel('A').getbbox();assert ib
    iw,ih=ib[2]-ib[0],ib[3]-ib[1];patch=Image.fromarray(after,'RGBA').resize((iw,ih),Image.Resampling.LANCZOS)
    mm=np.array(mask.resize((iw,ih),Image.Resampling.LANCZOS))>8
    view=arr[ib[1]:ib[3],ib[0]:ib[2]];view[mm,:3]=np.array(patch)[mm,:3]
    source=folder/'campaign.png';raw=png(Image.fromarray(arr,'RGBA'));outputs[source]=raw
    r.update(source=source.relative_to(PROJECT).as_posix(),source_sha256=digest(raw))
   outputs[HERE/'recipes-v2'/f'{state}-{role}.json']=encoded(r)
  notes.append({'state':state,'frame_sha256':digest(outputs[folder/'candidate-frame.png']),
                'alpha_exact':True,'outside_declared_crest_rgba_exact':True})
 for name,raw in inputs.items():
  if not safe(name).is_file() or safe(name).read_bytes()!=raw:raise ValueError('Assembly input changed during replay: '+name)
 return outputs,notes

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');parser.add_argument('--check',action='store_true');args=parser.parse_args()
 artifacts,notes=build()
 for path,raw in artifacts.items():
  if not path.resolve().is_relative_to(HERE):raise ValueError('Output escaped candidate source')
  if path.is_file():
   if path.read_bytes()!=raw:raise ValueError('Candidate replay differs: '+path.name)
  elif args.write:
   path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
  else:raise ValueError('Missing prepared candidate: '+path.name)
 print(json.dumps({'ok':True,'status':'authored configuration','artifacts':len(artifacts),'states':notes,
                   'native_execution':False,'release_accepted':False}))

if __name__=='__main__':main()
