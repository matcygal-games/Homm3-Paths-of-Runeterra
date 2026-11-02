"""Apply genuine painted material layers to explicit, physical attachment planes.

Only the marking layer is transformed. Original unit canvases, alpha, bodies,
roots and all pixels outside the exact pigment footprint are preserved.
"""
from pathlib import Path
import hashlib,io,json,math
import numpy as np
from PIL import Image,ImageDraw
S=Path(__file__).resolve().parent;P=S.parents[2];W=P.parent
R=W/'build/reports/regional-crests-20261025-v1/zaun-material-proof'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def enc(v):return (json.dumps(v,indent=2,sort_keys=True)+'\n').encode()
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists() and p.read_bytes()!=b:raise ValueError('Frozen output differs; make a new version: '+str(p))
 p.write_bytes(b)
def png(p,im):
 b=io.BytesIO();im.save(b,format='PNG',compress_level=9,optimize=False);put(p,b.getvalue())
def relative(p):return p.relative_to(P).as_posix()
def layer_for(glyph,quad,canvas):
 scale=4;target=[(x*scale,y*scale) for x,y in quad];source=[(0,0),(glyph.width,0),(glyph.width,glyph.height),(0,glyph.height)];a=[];b=[]
 for (x,y),(u,v) in zip(target,source):
  a.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]]);b.extend([u,v])
 coeff=np.linalg.solve(np.asarray(a,float),np.asarray(b,float));high=glyph.transform((canvas[0]*scale,canvas[1]*scale),Image.Transform.PERSPECTIVE,tuple(coeff),Image.Resampling.BICUBIC)
 return high.resize(tuple(canvas),Image.Resampling.LANCZOS)
def run(unit,version='v2'):
 prep_path=P/f'assets/source/regional-crests-20261025-v2/{unit}/preparation-v2.json';prep=json.loads(prep_path.read_text())
 plan_path=S/f'{unit}-attachments-{version}.json';plan=json.loads(plan_path.read_text());records=[];rejected=[]
 assert len(plan['attachments'])==len(prep['entries'])
 for e,attachment in zip(prep['entries'],plan['attachments']):
  assert attachment['index']==e['index'];source=P/e['slots'][0]['source'];assert sha(source)==e['slots'][0]['source_sha256'];old=Image.open(source).convert('RGBA');before=np.array(old);after=before.copy();mask=np.zeros(before.shape[:2],bool)
  if attachment.get('surface_quad'):
   variant=S/attachment['painted_variant'];glyph=Image.open(variant).convert('RGBA');layer=np.array(layer_for(glyph,attachment['surface_quad'],old.size));ink=layer[:,:,3]>0;material=before[:,:,3]>=248;coverage=float((ink&material).sum()/max(1,ink.sum()));mask=ink&material
   if coverage<.96:rejected.append({'index':e['index'],'coverage':coverage})
   amount=layer[:,:,3:4].astype(float)/255.;mixed=np.rint(layer[:,:,:3]*amount+before[:,:,:3]*(1-amount)).astype(np.uint8);after[mask,:3]=mixed[mask,:3]
  else:coverage=None
  assert np.array_equal(after[:,:,3],before[:,:,3]) and np.array_equal(after[~mask],before[~mask])
  out=S/f'native-candidates-{version}/{unit}/context-{e["index"]:03d}.png';png(out,Image.fromarray(after));maskpath=S/f'native-candidates-{version}/{unit}/masks/context-{e["index"]:03d}.png';png(maskpath,Image.fromarray(mask.astype(np.uint8)*255))
  records.append({**attachment,'slots':e['slots'],'source':relative(source),'source_sha256':sha(source),'candidate':relative(out),'candidate_sha256':sha(out),'mask':relative(maskpath),'mask_sha256':sha(maskpath),'host_coverage':coverage,'changed_pixels':int(np.any(after!=before,axis=2).sum()),'all_original_alpha_exact':True,'all_outside_pigment_RGBA_exact':True})
 for page in range((len(records)+11)//12):
  board=Image.new('RGBA',(1200,660),(42,44,41,255));d=ImageDraw.Draw(board)
  for cell,rec in enumerate(records[page*12:page*12+12]):
   old=Image.open(P/rec['source']).convert('RGBA');im=Image.open(P/rec['candidate']).convert('RGBA');box=old.getchannel('A').point(lambda v:255 if v>=16 else 0).getbbox();a=old.crop(box);b=im.crop(box);scale=min(2,95/max(a.width,1),250/max(a.height,1));x=cell%6*200;y=cell//6*330;size=(round(a.width*scale),round(a.height*scale));board.alpha_composite(a.resize(size,Image.Resampling.NEAREST),(x,y+35));board.alpha_composite(b.resize(size,Image.Resampling.NEAREST),(x+100,y+35));slot=rec['slots'][0];d.text((x,y),f"{rec['index']} {slot['role']} {slot.get('group','')}/{slot.get('frame','')}",fill='white');d.text((x,y+15),'old / new'+(' OCCLUDED' if not rec.get('surface_quad') else ''),fill='white')
  png(R/f'{unit}-complete-physical-{version}-page-{page}.png',board)
 receipt={'status':'authored configuration','unit':unit,'source_preparation':relative(prep_path),'source_preparation_sha256':sha(prep_path),'attachment_plan':relative(plan_path),'attachment_plan_sha256':sha(plan_path),'producer':relative(Path(__file__)),'producer_sha256':sha(Path(__file__)),'records':records,'rejected_physical_coverage':rejected,'no_body_warp':True,'no_original_alpha_change':True,'selected_or_staged':False,'runtime_verified':False,'release_accepted':False}
 put(S/f'{unit}-assembly-{version}.json',enc(receipt));print(json.dumps({'unit':unit,'contexts':len(records),'rejected':rejected}))
if __name__=='__main__':
 import sys
 for unit in sys.argv[1:]:run(unit)
