"""Register auxiliary generated alpha to original RGB; no artwork synthesis."""
import hashlib
import io
import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageChops,ImageFilter

HERE=Path(__file__).resolve().parent
PRIOR=HERE.parents[1]/'approved-tg1-20261029-v1'


def mask(points):
    out=Image.new('L',(800,374));ImageDraw.Draw(out).polygon([tuple(p)for p in points],fill=255)
    return out.filter(ImageFilter.MaxFilter(11))


def main():
    with Image.open(PRIOR/'approved-full-native.png')as image:original=image.convert('RGBA')
    with Image.open(HERE/'provider-cutout.png')as image:reference=image.convert('RGBA').resize((800,374),Image.Resampling.LANCZOS)
    original_array=np.asarray(original,dtype=np.int16)[:,:,:3]
    reference_array=np.asarray(reference,dtype=np.int16)[:,:,:3]
    alpha=reference.getchannel('A').point(lambda v:255 if v>=128 else 0)
    score_alpha=alpha.filter(ImageFilter.MinFilter(5))
    source=np.asarray(score_alpha)>0
    plan=json.loads((PRIOR/'site-plan-v1.json').read_bytes())
    records=[];combined=Image.new('L',(800,374))
    for site in plan['sites']:
        budget=mask(site['whole_form_polygon']);usable=source&(np.asarray(budget)>0)
        ys,xs=np.nonzero(usable)
        # Subsample evenly in row order. The same immutable pixels always give
        # the same registration; no hand-picked favorable score witnesses.
        step=max(1,len(xs)//1800);xs=xs[::step];ys=ys[::step]
        scores=[]
        for dy in range(-10,11):
            for dx in range(-10,11):
                tx,ty=xs+dx,ys+dy;keep=(tx>=0)&(tx<800)&(ty>=0)&(ty<374)
                delta=np.abs(original_array[ty[keep],tx[keep]]-reference_array[ys[keep],xs[keep]])
                score=float(np.mean(np.minimum(delta,80)))
                scores.append((score,abs(dx)+abs(dy),dy,dx))
        score,_,dy,dx=min(scores)
        shifted=Image.new('L',(800,374));shifted.paste(alpha,(dx,dy))
        # The original manual maximum is only a bounded semantic search window,
        # never an assertion that all its ground pixels are actual architecture.
        body=ImageChops.multiply(shifted.filter(ImageFilter.MaxFilter(5)),budget)
        body.save(HERE/(site['id']+'-registered-alpha.png'),compress_level=9)
        combined=ImageChops.lighter(combined,body)
        records.append({'site':site['id'],'translation':[dx,dy],'score':score,
                        'pixels_sampled':len(xs),'body_pixels':sum(v>0 for v in body.tobytes())})
    combined.save(HERE/'registered-union.png',compress_level=9)
    with Image.open(PRIOR/'empty-recovery-native.png')as image:empty=image.convert('RGBA')
    Image.composite(empty,original,combined).save(HERE/'registered-empty-diagnostic.png',compress_level=9)
    (HERE/'registration.json').write_text(json.dumps({'status':'authored configuration','auxiliary_only':True,
       'approved_RGB_resampled':False,'method':'Bounded per-site integer translation, immutable interior RGB score, 2px alpha registration tolerance; original approved RGB never transformed.',
       'producer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'records':records},indent=2)+'\n')
    print(json.dumps(records))


if __name__=='__main__':main()
