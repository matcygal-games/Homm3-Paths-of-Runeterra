"""Portrait-only native close-bust assembly; T1v3 action/map sources unchanged."""
from pathlib import Path
from copy import deepcopy
import json,hashlib,io
from PIL import Image
SELF=Path(__file__).resolve();A=SELF.parent;S=A.parent;P=next(p for p in SELF.parents if p.name=='runeterra-ionia')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):return {'path':p.relative_to(P).as_posix(),'sha256':sha(p)}
def load(p):return json.loads(p.read_text(encoding='utf8'))
def enc(v):return(json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+'\n').encode('utf8')
def put(p,v):
 b=v if isinstance(v,bytes)else enc(v);p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists()and p.read_bytes()!=b:raise ValueError('Version immutable portrait source before change: '+str(p))
 p.write_bytes(b)
def png(im):
 b=io.BytesIO();im.save(b,format='PNG',compress_level=9);return b.getvalue()
def compose(identity,background,box,size):
 """Uniform cover of a genuine painted bust over an opaque own painted scene."""
 crop=identity.crop(tuple(box));scale=max(size[0]/crop.width,size[1]/crop.height)
 crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS)
 bust=Image.new('RGBA',tuple(size));bust.alpha_composite(crop,((size[0]-crop.width)//2,0))
 bg=background.resize(tuple(size),Image.Resampling.LANCZOS).convert('RGBA');assert bg.getextrema()[3]==(255,255)
 bg.alpha_composite(bust);return bg,bust
def main():
 oldpath=S/'candidate-selection-v3.json';old=load(oldpath)
 inputs={p['path']:p['sha256']for p in old['direct_live_input_pins']}
 for f in [SELF,oldpath,A/'scenic/master.png',A/'scenic/generation.json',A/'scenic/prompt-as-sent.txt']+[P/r['path']for r in old['recipes']]:inputs[f.relative_to(P).as_posix()]=sha(f)
 camera={'ionianDisciple':{'large':[440,25,1050,700],'small':[530,45,990,505]},'enlightenedWarrior':{'large':[430,15,1040,690],'small':[530,20,1010,500]}}
 background=Image.open(A/'scenic/master.png').convert('RGBA');portrait={};records=[]
 for u,roles in camera.items():
  im=Image.open(S/u/'identity-v1/master.png').convert('RGBA')
  for role,box in roles.items():
   size=[58,64]if role=='large'else[32,32];out,bust=compose(im,background,box,size)
   f=A/u/(role+'.png');mask=A/u/(role+'-bust-alpha.png');put(f,png(out));put(mask,png(bust.getchannel('A')))
   for p in [f,mask]:inputs[p.relative_to(P).as_posix()]=sha(p)
   record={'unit':u,'role':role,'crop':box,'canvas':size,'identity':pin(S/u/'identity-v1/master.png'),'background':pin(A/'scenic/master.png'),'portrait':pin(f),'bust_alpha':pin(mask),'uniform_cover':True,'no_frame_or_filter':True};records.append(record);portrait[(u,role)]=record
 reg=A/'registration.json';put(reg,records);inputs[reg.relative_to(P).as_posix()]=sha(reg)
 pins=[]
 for row in old['recipes']:
  r=load(P/row['path']);u=r['unit'];role=(P/row['path']).stem[len(u)+1:]
  r['dependencies']=[{'path':n,'sha256':h}for n,h in sorted(inputs.items())]
  r['generation']['portrait_only_successor_producer']=pin(SELF)
  if role in ['large','small']:
   record=portrait[(u,role)];r.update(source=record['portrait']['path'],source_sha256=record['portrait']['sha256'],sha256=record['portrait']['sha256'])
   r['generation']['supplementary_painted_sources'].append(pin(A/'scenic/master.png'))
   r['generation']['portrait_scene_generation']=pin(A/'scenic/generation.json')
  f=S/'recipes-v4'/(u+'-'+role+'.json');put(f,r);pins.append({**row,'path':f.relative_to(P).as_posix(),'sha256':sha(f)})
 selection=deepcopy(old);selection.update(producer=pin(SELF),recipes=pins,direct_live_input_pins=[{'path':n,'sha256':h}for n,h in sorted(inputs.items())],portrait_only_successor_of=pin(oldpath),portrait_registration=pin(reg),portrait_scene_generation=pin(A/'scenic/generation.json'),all_action_and_map_sources_unchanged=True)
 put(S/'candidate-selection-v4.json',selection);print(json.dumps({'selection':pin(S/'candidate-selection-v4.json'),'recipes':len(pins),'inputs':len(inputs)},indent=2))
if __name__=='__main__':main()
