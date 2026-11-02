"""Transfer only genuine successor painted glyph RGB; preserve original gear/alpha."""
from pathlib import Path
import hashlib,io,json
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
S=Path(__file__).resolve().parent;P=S.parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write_png(p,im):
 b=io.BytesIO();im.save(b,format='PNG',compress_level=9,optimize=False);p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists() and p.read_bytes()!=b.getvalue():raise ValueError('Frozen material differs; use successor')
 p.write_bytes(b.getvalue())
def main():
 plan=json.loads((S/'materials/glyph-transfer-v3.json').read_text())
 paths={k:P/plan[k]['path'] for k in ('original','successor')}
 for k,p in paths.items():
  if sha(p)!=plan[k]['sha256']:raise ValueError('Material source drift')
 original=Image.open(paths['original']).convert('RGBA');new=Image.open(paths['successor']).convert('RGBA')
 if original.size!=new.size:raise ValueError('Successor canvas changed')
 allowed=Image.new('L',original.size);d=ImageDraw.Draw(allowed)
 for box in plan['glyph_rois']:d.rectangle(tuple(box),fill=255)
 # Alpha-only edge erosion preserves the existing leather silhouette/stitch border.
 interior=original.getchannel('A').point(lambda v:255 if v>=16 else 0).filter(ImageFilter.MinFilter(9))
 mask=(np.array(allowed)>0)&(np.array(interior)>0);a=np.array(original);b=a.copy();c=np.array(new);b[mask,:3]=c[mask,:3]
 assert np.array_equal(a[:,:,3],b[:,:,3]) and np.array_equal(a[~mask],b[~mask])
 out=P/plan['output'];mp=P/plan['mask'];write_png(out,Image.fromarray(b));write_png(mp,Image.fromarray(mask.astype(np.uint8)*255))
 oldvariants=json.loads((S/'materials/variants-v1.json').read_text());variants=[]
 for old in oldvariants['variants']:
  x0,y0,_,_=old['whole_object_window'];l,t,r,bottom=old['alpha16_crop_with2px_support'];crop=(x0+l,y0+t,x0+r,y0+bottom);dest=S/f'materials/variants-v3/{old["index"]}.png';write_png(dest,Image.open(out).crop(crop));variants.append({**old,'path':dest.relative_to(P).as_posix(),'sha256':sha(dest)})
 receipt={'status':'authored configuration','original_alpha_exact':True,'outside_glyph_ROI_RGBA_exact':True,'changed_pixels':int(np.any(a!=b,axis=2).sum()),'output':{'path':out.relative_to(P).as_posix(),'sha256':sha(out)},'mask':{'path':mp.relative_to(P).as_posix(),'sha256':sha(mp)},'producer':{'path':Path(__file__).relative_to(P).as_posix(),'sha256':sha(Path(__file__))},'plan':{'path':(S/'materials/glyph-transfer-v3.json').relative_to(P).as_posix(),'sha256':sha(S/'materials/glyph-transfer-v3.json')},'scope':'Only genuine imagegen successor glyph RGB inside tight manual paint ROIs; original gear geometry,alpha and exterior RGBA exact. No code glyph.'}
 metadata={'raw':receipt['output'],'variants':variants,'scope':receipt['scope']}
 for path,value in [(S/'materials/variants-v3.json',metadata),(S/'materials/glyph-transfer-receipt-v3.json',receipt)]:
  data=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
  if path.exists() and path.read_bytes()!=data:raise ValueError('Frozen receipt differs')
  path.write_bytes(data)
 print(json.dumps({'variants':len(variants),'changed_material_pixels':receipt['changed_pixels'],'all_original_alpha_exact':True,'exterior_RGBA_exact':True}))
if __name__=='__main__':main()
