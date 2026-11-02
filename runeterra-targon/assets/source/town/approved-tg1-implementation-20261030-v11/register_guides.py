"""Register generated matte assistance to genuine RGB; never transform master RGB."""
from collections import deque
import hashlib,io,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageChops,ImageFilter

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3];ORIGINAL=HERE.parent/'approved-tg1-20261029-v1'
BASE=HERE.parent/'approved-tg1-implementation-20261030-v5'
REPORT=PROJECT.parent/'reports/targon-tg1-implementation-20261030-v11'
GROUPS=[('sunhawks',['sunhawks']),('civic-relic',['civic','reliquary']),
 ('guild-temple',['guild','solariTemple']),('fortifications',['fortifications']),
 ('trailguard',['trailguard']),('archers',['archers']),('ibex',['ibex']),('stellacorns',['stellacorns']),
 ('sunforgers',['sunforgers']),('lunari',['lunari']),('silo-market',['silo','marketplace']),
 ('blacksmith',['blacksmith']),('tavern-monastery',['tavern','monastery']),('starforge',['starforge']),
 ('lunariShrine',['lunariShrine']),('grail',['grail'])]

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def im(p):
    with Image.open(p)as opened:opened.load();return opened.convert('RGBA')
def write(p,raw):
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists()and p.read_bytes()!=raw:raise ValueError('Preserve old guide registration: '+str(p))
    if not p.exists():p.write_bytes(raw)
def save(p,image):
    out=io.BytesIO();image.save(out,format='PNG',compress_level=9);write(p,out.getvalue())
def dump(p,obj):write(p,(json.dumps(obj,sort_keys=True,indent=2)+'\n').encode())

def transform(image,scale,dx,dy,center):
    cx,cy=center
    return image.transform((800,374),Image.Transform.AFFINE,
      (1/scale,0,cx-(cx+dx)/scale,0,1/scale,cy-(cy+dy)/scale),Image.Resampling.BILINEAR)

def fit(reference,original,budget,*,scales,dxs,dys):
    # Fixed deterministic interior sample, not manually selected favorable points.
    usable=ImageChops.multiply(reference.getchannel('A').point(lambda v:255 if v>=192 else 0).filter(ImageFilter.MinFilter(3)),budget)
    ys,xs=np.nonzero(np.asarray(usable)>0)
    if len(xs)<40:raise ValueError('Insufficient actual guide body for registration')
    step=max(1,len(xs)//1400);xs=xs[::step];ys=ys[::step]
    box=budget.getbbox();center=((box[0]+box[2])/2,(box[1]+box[3])/2)
    orig=np.asarray(original,dtype=np.int16)[:,:,:3];ref=np.asarray(reference,dtype=np.int16)[:,:,:3]
    samples=ref[ys,xs];scores=[]
    for scale in scales:
        sx=np.rint((xs-center[0])*scale+center[0]).astype(int)
        sy=np.rint((ys-center[1])*scale+center[1]).astype(int)
        for dy in dys:
            for dx in dxs:
                tx,ty=sx+dx,sy+dy;keep=(tx>=0)&(tx<800)&(ty>=0)&(ty<374)
                delta=np.abs(orig[ty[keep],tx[keep]]-samples[keep]);score=float(np.mean(np.minimum(delta,80)))
                scores.append((score,abs(scale-1),abs(dx)+abs(dy),scale,int(dx),int(dy)))
    best=min(scores);return best,center,len(xs)

def main():
    index=read(BASE/'candidate-frames.json');plan=read(ORIGINAL/'site-plan-v1.json')
    sites={s['id']:s for s in plan['sites']};REPORT.mkdir(parents=True,exist_ok=True)
    summaries=[]
    for tag in ('approved','early','middle'):
        original=im(ORIGINAL/('approved-full-native.png'if tag=='approved'else tag+'-states-native.png'))
        reference=im(HERE/'guides'/(tag+'-guide.png')).resize((800,374),Image.Resampling.LANCZOS)
        for name,members in GROUPS:
            matching=[s for s,r in index['states'].items()if r['site']in members and r['source_tag']==tag]
            if not matching:continue
            budget=Image.new('L',(800,374));draw=ImageDraw.Draw(budget)
            for member in members:draw.polygon([tuple(p)for p in sites[member]['whole_form_polygon']],fill=255)
            # Guides are deliberately untrusted. Search window is an expanded
            # semantic parcel, not a selected final mask or a source approval.
            budget=budget.filter(ImageFilter.MaxFilter(31))
            coarse,center,n=fit(reference,original,budget,scales=np.arange(.85,1.151,.025),dxs=range(-16,17,2),dys=range(-16,17,2))
            _,_,_,s,dx,dy=coarse
            fine,center,n=fit(reference,original,budget,scales=np.arange(s-.02,s+.0201,.005),dxs=range(dx-2,dx+3),dys=range(dy-2,dy+3))
            score,_,_,s,dx,dy=fine
            shifted=transform(reference,float(s),dx,dy,center)
            alpha=ImageChops.multiply(shifted.getchannel('A').point(lambda v:255 if v>=64 else 0),budget)
            save(HERE/'registered'/(tag+'--'+name+'.png'),alpha.convert('RGB'))
            comparison=original.copy();tint=Image.new('RGBA',(800,374),(255,40,50,0));tint.putalpha(alpha.point(lambda v:80 if v else 0));comparison.alpha_composite(tint)
            box=budget.getbbox();crop=comparison.crop(box).resize(((box[2]-box[0])*3,(box[3]-box[1])*3),Image.Resampling.NEAREST)
            save(REPORT/(tag+'--'+name+'-overlay.png'),crop)
            summaries.append({'tag':tag,'group':name,'sites':members,'scale':float(s),'translation':[dx,dy],
              'center':center,'mean_clipped_RGB_error':score,'samples':n,'alpha_pixels':alpha.histogram()[255],
              'bounds':alpha.getbbox(),'mask':str((HERE/'registered'/(tag+'--'+name+'.png')).relative_to(PROJECT)).replace('\\','/')})
    dump(HERE/'registration.json',{'status':'authored configuration','auxiliary_only':True,
      'approved_RGB_transformed':False,'producer_sha256':sha(Path(__file__)),
      'inputs':{p.name:sha(p)for p in (HERE/'guides').glob('*.png')},'records':summaries})
    print(json.dumps(summaries))

if __name__=='__main__':main()
