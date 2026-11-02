"""Existing painted-Nomad fixed-transform method, adapted only to beast registration.

Whole-canvas resolution normalization is not per-pose body fitting. All current
sources share the logical2048x1152 reference; up to two raw pixels of tool canvas rounding are tolerated.
"""
from pathlib import Path
from PIL import Image,ImageDraw
import argparse,hashlib,json
SOURCE=Path(__file__).resolve().parent;PROJECT=SOURCE.parents[4]
REPORT=PROJECT/'build/reports/painted-rockbear-actions-20261023-v1'
NOMINAL=(2048,1152);SOURCE_ROOT=(1037,992);ROOT=(218,266);SCALE=.075;CANVAS=(450,400)
ROI=(120,170,320,285)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def native(picture,canvas=CANVAS,root=ROOT,scale=SCALE):
 # Tool outputs normalize complete canvases to1.57MP. One single width-based
 # factor is used for BOTH axes; no per-body fit or anisotropic normalization.
 factor=picture.width/NOMINAL[0]
 if abs(picture.height-NOMINAL[1]*factor)>2.0:raise ValueError('Wrong full-canvas aspect; refuse pose without fitting')
 return picture.transform(canvas,Image.Transform.AFFINE,
   (factor/scale,0,factor*(SOURCE_ROOT[0]-root[0]/scale),0,factor/scale,factor*(SOURCE_ROOT[1]-root[1]/scale)),Image.Resampling.BICUBIC)
def mirror(picture,root=ROOT):
 out=Image.new('RGBA',picture.size);out.paste(picture.transpose(Image.Transpose.FLIP_LEFT_RIGHT),(2*root[0]-(picture.width-1),0));return out
def alpha_edge(picture):
 a=picture.getchannel('A');w,h=picture.size
 return max(a.crop(box).getextrema()[1] for box in ((0,0,w,1),(0,h-1,w,h),(0,0,1,h),(w-1,0,w,h)))
def checker(size):
 out=Image.new('RGBA',size,(105,105,105,255));draw=ImageDraw.Draw(out)
 for y in range(0,size[1],8):
  for x in range(0,size[0],8):
   if (x//8+y//8)%2:draw.rectangle((x,y,x+7,y+7),fill=(145,145,145,255))
 return out
def main():
 parser=argparse.ArgumentParser();parser.add_argument('unit',choices=('rockbear','elderRockbear'));parser.add_argument('--label',required=True);parser.add_argument('keys',nargs='+');args=parser.parse_args()
 directory=SOURCE.parent/args.unit;destination=directory/'native';destination.mkdir(exist_ok=True)
 board=Image.new('RGBA',(412,135*len(args.keys)),(35,35,35,255));draw=ImageDraw.Draw(board);rows=[];motion=[]
 for index,key in enumerate(args.keys):
  path=directory/(key+'.png');picture=Image.open(path).convert('RGBA');image=native(picture);left=mirror(image)
  target=destination/(key+'.png');image.save(target,compress_level=9)
  left_path=destination/(key+'-left.png');left.save(left_path,compress_level=9)
  assert alpha_edge(image)==alpha_edge(left)==0
  for column,view in enumerate((image,left)):
   crop=view.crop(ROI);bg=checker(crop.size);bg.alpha_composite(crop);board.paste(bg,(column*212,index*135+18))
  draw.text((2,index*135+2),key,fill='white')
  frame=checker((412,115));frame.alpha_composite(image.crop(ROI),(0,0));frame.alpha_composite(left.crop(ROI),(212,0));motion.append(frame.convert('RGB'))
  rows.append({'key':key,'source':path.relative_to(PROJECT).as_posix(),'source_sha256':sha(path),'source_size':list(picture.size),'whole_canvas_uniform_factor':picture.width/NOMINAL[0],'native':target.relative_to(PROJECT).as_posix(),'native_sha256':sha(target),'native_body_bounds':image.getchannel('A').point(lambda a:255 if a>=32 else 0).getbbox(),'native_alpha_bounds':image.getbbox(),'native_root':ROOT,'logical_source_root':SOURCE_ROOT,'uniform_cohort_scale':SCALE,'native_canvas':CANVAS,'border_alpha_max':0,'per_frame_body_fit':False})
 prefix=REPORT/(args.unit+'-'+args.label)
 board.save(prefix.with_suffix('.png'))
 motion[0].save(prefix.with_suffix('.gif'),save_all=True,append_images=motion[1:],duration=130,loop=0)
 prefix.with_suffix('.json').write_text(json.dumps({'status':'authored configuration','native_execution':False,'visual_approval_granted':False,'source_only_technical_preview':True,'rows':rows},indent=2,sort_keys=True)+'\n',encoding='utf-8')
 print(json.dumps({'unit':args.unit,'keys':len(rows),'all_border_alpha_zero':True,'native_roots_identical':True,'all_full_canvas_aspects_valid':True,'preview':prefix.with_suffix('.png').name,'native_body_bounds':[r['native_body_bounds'] for r in rows]}))
if __name__=='__main__':main()
