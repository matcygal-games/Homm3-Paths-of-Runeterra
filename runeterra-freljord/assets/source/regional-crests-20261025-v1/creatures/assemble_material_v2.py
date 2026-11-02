"""Apply genuine painted cloth only to authored physical planes; never warp bodies."""
from pathlib import Path
import hashlib,io,json
import numpy as np
from PIL import Image,ImageDraw
SOURCE=Path(__file__).resolve().parent;PROJECT=SOURCE.parents[3]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def local(name):
 if not isinstance(name,str) or ':' in name or '\\' in name or any(x in ('','.','..') for x in name.split('/')):raise ValueError('Unsafe source path')
 p=(PROJECT/name).resolve()
 if not p.is_relative_to(PROJECT):raise ValueError('Source escape')
 return p
def png(p,im):
 p.parent.mkdir(parents=True,exist_ok=True);buf=io.BytesIO();im.save(buf,format='PNG',compress_level=9,optimize=False)
 if p.exists() and p.read_bytes()!=buf.getvalue():raise ValueError('Frozen output differs; author a successor '+str(p))
 p.write_bytes(buf.getvalue())
def warp_material(tile,quad,canvas):
 scale=4;target=[(x*scale,y*scale) for x,y in quad];uv=[(0,0),(tile.width,0),(tile.width,tile.height),(0,tile.height)];a=[];b=[]
 for (x,y),(u,v) in zip(target,uv):a.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]]);b.extend([u,v])
 coeff=np.linalg.solve(np.asarray(a,float),np.asarray(b,float));high=tile.transform((canvas[0]*scale,canvas[1]*scale),Image.Transform.PERSPECTIVE,tuple(coeff),Image.Resampling.BICUBIC)
 return high.resize(canvas,Image.Resampling.LANCZOS)
def assemble(plan_path):
 plan=read(plan_path);records=[]
 for e in plan['attachments']:
  original=local(e['source']);tile=local(e['painted_variant']);assert sha(original)==e['source_sha256'];assert sha(tile)==e['painted_variant_sha256']
  im=Image.open(original).convert('RGBA');before=np.asarray(im);after=before.copy();allowed=np.zeros(before.shape[:2],dtype=bool);coverage=None
  if e.get('surface_quad'):
   layer=np.asarray(warp_material(Image.open(tile).convert('RGBA'),e['surface_quad'],im.size));polygon=Image.new('L',im.size);draw=ImageDraw.Draw(polygon);draw.polygon([tuple(x) for x in e.get('visible_material_polygon',e['surface_quad'])],fill=255)
   for occluder in e.get('occluder_polygons',[]):draw.polygon([tuple(x) for x in occluder],fill=0)
   visible=np.asarray(polygon)>0;ink=layer[:,:,3]>0;opaque=before[:,:,3]>=248;allowed=ink&opaque&visible;coverage=float((ink&opaque).sum()/max(1,ink.sum()))
   amount=layer[:,:,3:4].astype(float)/255.;mixed=np.rint(layer[:,:,:3]*amount+before[:,:,:3]*(1-amount)).astype(np.uint8);after[allowed,:3]=mixed[allowed,:3]
  if not np.array_equal(after[:,:,3],before[:,:,3]) or not np.array_equal(after[~allowed],before[~allowed]):raise ValueError('Original alpha or external RGBA changed')
  out=local(e['candidate']);mask=local(e['mask']);png(out,Image.fromarray(after));png(mask,Image.fromarray(allowed.astype(np.uint8)*255));records.append({**e,'candidate_sha256':sha(out),'mask_sha256':sha(mask),'changed_pixels':int(np.any(after!=before,axis=2).sum()),'original_alpha_exact':True,'outside_attachment_RGBA_exact':True,'actor_coverage':coverage})
 return {'status':'design proposal','plan':plan_path.relative_to(PROJECT).as_posix(),'plan_sha256':sha(plan_path),'producer':Path(__file__).relative_to(PROJECT).as_posix(),'producer_sha256':sha(Path(__file__)),'records':records,'native_execution':False,'release_accepted':False}
if __name__=='__main__':
 import sys
 path=local(sys.argv[1]);receipt=assemble(path);target=path.with_name(path.stem+'-assembly.json');target.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n');print(json.dumps({'contexts':len(receipt['records']),'changed_pixels':sum(x['changed_pixels'] for x in receipt['records'])}))
