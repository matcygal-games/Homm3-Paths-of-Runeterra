"""Technical ground-shadow candidates derived only from own painted alpha.

No actor artwork is created. These are unselected candidates until the shared
compiler supports explicit shadow_source and the coordinator integrates them.
"""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageFilter
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if p.name=='runeterra-piltover')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
for unit in ('hextechRotorwing','hextechStormwing'):
 out=HERE/'shadow-candidates'/unit;out.mkdir(parents=True,exist_ok=True)
 for p in sorted((HERE/'native'/unit/'battle').glob('g??-f???.png')):
  im=Image.open(p).convert('RGBA');alpha=im.getchannel('A');ground=266.;shear=.5;vertical=.35
  mask=alpha.transform(im.size,Image.Transform.AFFINE,(1,-shear/vertical,shear/vertical*ground,0,1/vertical,-(1-vertical)/vertical*ground),Image.Resampling.BILINEAR)
  mask=mask.point(lambda a:round(a*96/255)).filter(ImageFilter.GaussianBlur(.55))
  shadow=Image.new('RGBA',im.size);shadow.putalpha(mask);target=out/(p.stem+'-SHADOW.png');shadow.save(target,compress_level=9)
  rows.append({'unit':unit,'actor_source':p.relative_to(PROJECT).as_posix(),'actor_sha256':sha(p),'shadow_source':target.relative_to(PROJECT).as_posix(),'shadow_sha256':sha(target),'canvas':[450,400],'projected_ground_y':266,'shear_x':.5,'vertical_projection':.35,'maximum_alpha':96,'method':'Affine projection of exact own painted actor alpha onto fixed floor; never a procedural actor or arbitrary ellipse'})
result={'status':'authored configuration','selected':False,'gate':'Optional explicit shadow_source compiler support and coordinator integration, followed by native visual observation','sources':rows}
p=HERE/'shadow-candidates/receipts-v1.json';p.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'shadow_candidates':len(rows),'selected':False,'receipt_sha256':sha(p)}))
