"""Pure 2D preparation of four new painted Rakkor civic building states.

No model, scene, original-game image, private reference or legacy rendered PNG
is a producer input. Only the delivered paintings/prompts, native numeric site
envelopes and projected technical recipe templates are read. Live selections,
manifests and stages are never written.
"""
from pathlib import Path
import argparse,hashlib,io,json,re
from PIL import Image,ImageChops,ImageFilter

HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[3];PLAN=HERE/'inputs-v1.json'
digest=lambda raw:hashlib.sha256(raw).hexdigest()
sha=lambda path:digest(path.read_bytes())
encoded=lambda value:(json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
def png(image):
 stream=io.BytesIO();image.save(stream,format='PNG',compress_level=9,optimize=False);return stream.getvalue()
def safe(name):
 if (not isinstance(name,str) or not name.startswith('assets/source/') or '\\' in name or ':' in name
     or any(not p or p in ('.','..') or p.rstrip(' .')!=p or re.match(r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)',p,re.I) for p in name.split('/'))):raise ValueError('Unsafe source input')
 path=PROJECT/name
 for part in (path,*path.parents):
  if part==PROJECT:break
  if part.is_symlink() or part.exists() and getattr(part.stat(),'st_file_attributes',0)&0x400:raise ValueError('Redirected source input')
 if not path.resolve().is_relative_to(PROJECT):raise ValueError('Escaping source input')
 return path
def thumb(image,size):
 solid=image.getchannel('A').point(lambda n:255 if n>=128 else 0)
 box=solid.getbbox()
 if box is None:raise ValueError('Empty painted building')
 crop=image.crop(box);crop.thumbnail((size[0]-4,size[1]-4),Image.Resampling.LANCZOS)
 out=Image.new('RGBA',size);out.alpha_composite(crop,((size[0]-crop.width)//2,size[1]-crop.height-2));return out

def build():
 plan=json.loads(PLAN.read_text(encoding='utf-8'))
 if plan.get('schema')!='targon-painted-civic-v1' or {r['state'] for r in plan['states']}!={'villageHall','townHall','cityHall','capitol'}:raise ValueError('Wrong source contract')
 inputs={}
 for name,pin in plan['input_sha256'].items():
  p=safe(name)
  if not p.is_file():raise ValueError('Missing painted source: '+name)
  raw=p.read_bytes()
  if digest(raw)!=pin:raise ValueError('Changed painted source: '+name)
  inputs[name]=raw
 def blob(name):
  if name not in inputs:raise ValueError('Undeclared source input: '+name)
  return inputs[name]
 dependencies=[{'path':Path(__file__).relative_to(PROJECT).as_posix(),'sha256':sha(Path(__file__))},
               {'path':PLAN.relative_to(PROJECT).as_posix(),'sha256':sha(PLAN)},
               *({'path':name,'sha256':pin} for name,pin in sorted(plan['input_sha256'].items()))]
 outputs={};records=[];icon_patches=[]
 for job in plan['states']:
  state=job['state'];folder=HERE/state;master=Image.open(io.BytesIO(blob(job['master']))).convert('RGBA')
  bodybox=master.getchannel('A').getbbox()
  if not bodybox:raise ValueError('Empty painted source')
  body=master.crop(bodybox);x0,y0,x1,y1=job['native_envelope'];w,h=x1-x0,y1-y0
  # One explicit fixed transform per state, bounded by the already selected
  # numeric envelope. Neither a legacy body nor per-pixel scene guides are read.
  body.thumbnail((w,h),Image.Resampling.LANCZOS)
  at=(x0+(w-body.width)//2,y1-body.height)
  frame=Image.new('RGBA',(800,374));frame.alpha_composite(body,at)
  solid=frame.getchannel('A').point(lambda n:255 if n>=128 else 0)
  area=Image.new('RGBA',frame.size,(255,255,255,0));area.putalpha(solid)
  border=Image.new('RGBA',frame.size,(225,190,80,0));border.putalpha(ImageChops.subtract(solid.filter(ImageFilter.MaxFilter(3)),solid))
  surfaces={'frame':frame,'area':area,'border':border,'campaign':thumb(frame,(58,64)),'construction':thumb(frame,(150,70))}
  for role,image in surfaces.items():outputs[folder/('prepared-'+role+'.png')]=png(image)
  generation={'provider':'OpenAI built-in imagegen','image_generation_used':True,'model':'not exposed by built-in tool',
              'painted_master':job['master'],'painted_master_sha256':plan['input_sha256'][job['master']],
              'prompt_file':job['prompt'],'prompt':blob(job['prompt']).decode('utf-8'),
              'producer':Path(__file__).relative_to(PROJECT).as_posix(),'producer_sha256':sha(Path(__file__)),
              'method':'Genuine new painted 2D civic architecture prepared at explicit native numeric envelopes, with independently derived visible click masks/highlights. No rendered architectural body or scene input.',
              'source_generation_ledger':(folder/'generation-v1.json').relative_to(PROJECT).as_posix()}
  record={'schema':'painted-civic-origin-v1','state':state,'provider':'OpenAI built-in imagegen','image_generation_used':True,
          'master':job['master'],'master_sha256':plan['input_sha256'][job['master']],
          'prompt_file':job['prompt'],'prompt_sha256':plan['input_sha256'][job['prompt']],
          'creative_input_basis':'Fresh painted Rakkor village source; successive states use only that clean 2D source plus primary regional/environment/native-game style references privately. No rendered predecessor is an image input.',
          'crest_reference':plan['crest_reference'],'native_envelope':job['native_envelope'],'source_crop':list(bodybox),'resampled_size':list(body.size),'placement':list(at),
          'native_execution':False,'visual_approval_granted':False,'release_accepted':False}
  ledger=folder/'generation-v1.json';outputs[ledger]=encoded(record)
  deps=[*dependencies,{'path':ledger.relative_to(PROJECT).as_posix(),'sha256':digest(outputs[ledger])}]
  for role,template in job['templates'].items():
   r=json.loads(blob(template));r['generation']=generation;r['dependencies']=deps
   r['credits']={'author':'Project-directed OpenAI built-in imagegen; deterministic painted 2D source preparation','license':None,'redistribution':'unresolved; release prohibited'}
   r['visual_approval_granted']=False;r['status']='painted-candidate'
   source=folder/('prepared-'+('frame' if role=='animation' else role)+'.png');raw=outputs[source]
   if role=='animation':
    r['groups']=[{'group':0,'frames':[{'source':source.relative_to(PROJECT).as_posix(),'source_sha256':digest(raw),'sha256':digest(raw),'source_canvas':[800,374]}]}]
   else:r.update(source=source.relative_to(PROJECT).as_posix(),source_sha256=digest(raw))
   outputs[HERE/'recipes-v1'/f'{state}-{role}.json']=encoded(r)
  icon=folder/'prepared-construction.png'
  icon_patches.append({'building':state,'frame':job['construction_id'],'source':icon.relative_to(PROJECT).as_posix(),'sha256':digest(outputs[icon]),'source_canvas':[150,70]})
  records.append(record)
 outputs[HERE/'construction-frame-patches-v1.json']=encoded({'scope':'Replace only the four named descriptors in the existing indexed buildingIcons recipe. Other existing UI frames/provenance remain legacy debt, not new painted-art approval.','frames':icon_patches,'native_execution':False,'release_accepted':False})
 for name,raw in inputs.items():
  if not safe(name).is_file() or safe(name).read_bytes()!=raw:raise ValueError('Painted input changed during preparation: '+name)
 return outputs,records

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');parser.add_argument('--check',action='store_true');args=parser.parse_args()
 artifacts,records=build()
 for path,raw in artifacts.items():
  if not path.resolve().is_relative_to(HERE):raise ValueError('Candidate output escaped source leaf')
  if path.is_file():
   if path.read_bytes()!=raw:raise ValueError('Prepared candidate differs: '+path.name)
  elif args.write:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
  else:raise ValueError('Prepared candidate missing: '+path.name)
 print(json.dumps({'ok':True,'status':'authored configuration','artifacts':len(artifacts),'states':len(records),'native_execution':False,'release_accepted':False}))

if __name__=='__main__':main()
