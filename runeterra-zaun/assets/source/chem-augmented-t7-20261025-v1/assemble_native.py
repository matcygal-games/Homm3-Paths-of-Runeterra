"""Deterministic canvas/root conversion of genuine whole painted2D poses."""
from pathlib import Path
import json,io,hashlib
import numpy as np
from PIL import Image
from prepare_pose_sources_v2 import S,P,W,R,sha,enc,put,png,rel
def run():
 plan_path=S/'registration-plan-v1.json';plan=json.loads(plan_path.read_text());scales={(r['unit'],r['cohort']):r['one_uniform_scale'] for r in plan['cohort_scales']};records=[]
 for b in plan['bindings']:
  source=P/b['isolated_source'];assert sha(source)==b['isolated_source_sha256'];im=Image.open(source).convert('RGBA');role=b['role'];size=b['native_canvas'];out=Image.new('RGBA',tuple(size),(0,0,0,0));unit=b['unit']
  if role=='battle':
   factor=b['uniform_scale'];assert factor==scales[(unit,b['cohort'])];native=im.resize((max(1,round(im.width*factor)),max(1,round(im.height*factor))),Image.Resampling.LANCZOS);window=b['source_window'];sx=b['source_root'][0]-window[0];sy=b['source_root'][1]-window[1];offset=[round(218-sx*factor),round(266-sy*factor)];assert offset[0]>=0 and offset[1]>=0 and offset[0]+native.width<=450 and offset[1]+native.height<=400;out.alpha_composite(native,tuple(offset));filename=f'g{b["group"]:02d}-f{b["frame"]:03d}.png'
  elif role=='map':
   factor=b['target_body_height']/max(1,im.getchannel('A').point(lambda v:255 if v>=128 else 0).getbbox()[3]-im.getchannel('A').point(lambda v:255 if v>=128 else 0).getbbox()[1]);native=im.resize((round(im.width*factor),round(im.height*factor)),Image.Resampling.LANCZOS);a=np.array(native)[:,:,3];ys,xs=np.where(a>=128);offset=[round(64-(xs.min()+xs.max())/2),63-int(ys.max())];assert offset[0]>=0 and offset[1]>=0 and offset[0]+native.width<=96 and offset[1]+native.height<=64;out.alpha_composite(native,tuple(offset));filename='map.png'
  else:
   margin=b['native_margin'];factor=min((size[0]-2*margin)/im.width,(size[1]-2*margin)/im.height);native=im.resize((max(1,round(im.width*factor)),max(1,round(im.height*factor))),Image.Resampling.LANCZOS);offset=[(size[0]-native.width)//2,(size[1]-native.height)//2];out.alpha_composite(native,tuple(offset));filename=role+'.png'
  path=S/unit/'native-v1'/filename;png(path,out);a=np.array(out)[:,:,3];assert a.max()>0;bounds=out.getchannel('A').point(lambda v:255 if v>=16 else 0).getbbox();records.append({**b,'native':rel(path),'native_sha256':sha(path),'source_uniform_scale':factor,'native_offset':offset,'visible_alpha16_bounds':bounds,'body_or_limb_warp':False})
 for unit in ('chemGolem','pressureColossus'):
  assert sha(S/unit/'native-v1/g22-f000.png')==sha(S/unit/'native-v1/g05-f005.png')
 receipt={'status':'authored configuration','registration_plan':rel(plan_path),'registration_plan_sha256':sha(plan_path),'producer':rel(Path(__file__)),'producer_sha256':sha(Path(__file__)),'records':records,'whole_source_pose_assembly_only':True,'no_per_frame_body_scale':True,'no_old_guided_pixel_inputs':True,'selected_or_staged':False,'runtime_verified':False,'release_accepted':False};put(S/'native-assembly-receipt-v1.json',enc(receipt));print('Authored native slots:',len(records))
if __name__=='__main__':run()
