"""Physical 2D attachment proof using genuinely painted regional pigment layers.

This transforms only a painted marking. No body/art pose, original frame alpha,
camera/root, gear or gameplay datum is generated or transformed by this helper.
"""
from pathlib import Path
import hashlib,io,json
import numpy as np
from PIL import Image,ImageDraw

S=Path(__file__).resolve().parent;P=S.parents[2];W=P.parent
R=W/'build/reports/regional-crests-20261025-v1/zaun-material-proof'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def enc(v):return(json.dumps(v,indent=2,sort_keys=True)+'\n').encode()
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists() and p.read_bytes()!=b:raise ValueError('Frozen proof differs; make a new version: '+str(p))
 p.write_bytes(b)
def png(p,im):
 b=io.BytesIO();im.save(b,format='PNG',compress_level=9,optimize=False);put(p,b.getvalue())
def relative(p):return p.relative_to(P).as_posix()

master=S/'material-marks/master-v3.png';im=Image.open(master).convert('RGBA');assert im.size==(1536,1024)
variants=[]
for row in range(2):
 for col in range(4):
  cell=im.crop((col*384,row*512,(col+1)*384,(row+1)*512));box=cell.getchannel('A').point(lambda v:255 if v>=16 else 0).getbbox()
  if not box or min(box[0],box[1],384-box[2],512-box[3])<3:raise ValueError('Whole painted mark not separated from cell edge: '+str((row,col,box)))
  box=[max(0,box[0]-2),max(0,box[1]-2),min(384,box[2]+2),min(512,box[3]+2)];tile=cell.crop(box)
  path=S/'material-marks/variants-v3'/f'r{row}-c{col}.png';png(path,tile);variants.append({'row':row,'col':col,'path':relative(path),'sha256':sha(path),'cell_crop':[col*384,row*512,(col+1)*384,(row+1)*512],'alpha16_bounds_inside_cell':box,'whole_mark_separated':True})
put(S/'material-marks/variants-v3.json',enc({'painted_master':relative(master),'painted_master_sha256':sha(master),'variants':variants,'scope':'Genuine painted pigment/engraving variants, not officialPNG/icon pixels or a code-drawn glyph'}))

def layer_for(variant,quad,canvas):
 glyph=Image.open(P/variant['path']).convert('RGBA');scale=4
 target=[(x*scale,y*scale) for x,y in quad];source=[(0,0),(glyph.width,0),(glyph.width,glyph.height),(0,glyph.height)];a=[];b=[]
 for (x,y),(u,v) in zip(target,source):
  a.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]]);b.extend([u,v])
 coeff=np.linalg.solve(np.asarray(a,float),np.asarray(b,float))
 high=glyph.transform((canvas[0]*scale,canvas[1]*scale),Image.Transform.PERSPECTIVE,tuple(coeff),Image.Resampling.BICUBIC)
 return high.resize(tuple(canvas),Image.Resampling.LANCZOS)

attachments=json.loads((S/'chemJack-first-physical-attachments-v2.json').read_text());prep=json.loads((P/'assets/source/regional-crests-20261025-v2/chemJack/preparation-v2.json').read_text());variant=next(x for x in variants if x['row']==0 and x['col']==1);records=[];pairboard=Image.new('RGBA',(700,280),(43,45,42,255));draw=ImageDraw.Draw(pairboard)
for i,attachment in enumerate(attachments['records']):
 group=attachment['group'];frame=attachment['frame'];entry=next(x for x in prep['entries'] if any(z['role']=='battle' and z['group']==group and z['frame']==frame for z in x['slots']));slot=next(z for z in entry['slots'] if z['role']=='battle' and z['group']==group and z['frame']==frame);source=P/slot['source'];assert sha(source)==slot['source_sha256']
 old=Image.open(source).convert('RGBA');before=np.array(old);layer=np.array(layer_for(variant,attachment['surface_quad'],old.size));ink=layer[:,:,3]>0;material=before[:,:,3]>=248
 # Physical clipping is explicit: no pigment can create an outer unit pixel.
 host_coverage=float((ink&material).sum()/max(1,ink.sum()));assert host_coverage>.96,('Paint outside physical garment',group,frame,host_coverage)
 mask=ink&material;after=before.copy();amount=layer[:,:,3:4].astype(float)/255.;mixed=np.rint(layer[:,:,:3]*amount+before[:,:,:3]*(1-amount)).astype(np.uint8);after[mask,:3]=mixed[mask,:3]
 assert np.array_equal(after[:,:,3],before[:,:,3]) and np.array_equal(after[~mask],before[~mask])
 path=S/'native-proof-v2/chemJack'/f'g{group:02d}-f{frame:03d}.png';png(path,Image.fromarray(after));maskpath=path.with_name(path.stem+'-paint-mask.png');png(maskpath,Image.fromarray(mask.astype(np.uint8)*255))
 # A deliberate remote boot change must fail the outside-mark guarantee.
 y,x=np.argwhere((before[:,:,3]>=248)&~mask)[-1];bad=after.copy();bad[y,x,0]^=1;assert np.any(np.any(bad!=before,axis=2)&~mask)
 records.append({**attachment,'source':slot['source'],'source_sha256':sha(source),'painted_variant':variant,'candidate':relative(path),'candidate_sha256':sha(path),'mask':relative(maskpath),'mask_sha256':sha(maskpath),'host_coverage':host_coverage,'changed_pixels':int(np.any(after!=before,axis=2).sum()),'all_original_alpha_exact':True,'all_outside_mark_RGBA_exact':True,'outside_mark_boot_mutation_rejected':True})
 box=(163,180,240,276);a=old.crop(box);b=Image.fromarray(after).crop(box);x=i*170;draw.text((x+3,3),f'g{group:02d}/f{frame:02d} old / new1x',fill='white');pairboard.alpha_composite(a,(x+3,25));pairboard.alpha_composite(b,(x+88,25));draw.text((x+3,128),'new2x detail',fill='white');pairboard.alpha_composite(b.resize((154,192),Image.Resampling.NEAREST).crop((0,0,154,132)),(x+3,146))
png(R/'chemJack-four-pose-physical-proof-v2.png',pairboard)
put(R/'physical-proof-v2.json',enc({'status':'authored configuration','scope':'Four-frame physical marking proof only, not wholecohort or selectedsource','painted_master':relative(master),'painted_master_sha256':sha(master),'records':records,'no_body_warp':True,'genuine_painted_layers_only':True,'selected_or_staged':False,'native_visual_verified':False,'release_accepted':False}));print(json.dumps({'proof_frames':len(records),'unchanged_all_original_alpha':True,'outside_mark_RGBA_exact':True,'host_coverage':[x['host_coverage'] for x in records]}))
