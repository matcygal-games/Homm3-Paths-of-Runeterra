"""Portable technical conversion only: fixed canvas/root, no body fitting/art."""
from pathlib import Path
from PIL import Image
import argparse
CANVAS=(450,400);SCALE=.074;SOURCE_ROOT=(640,1070);ROOT=(193,266)
def prepare(image):
 image=image.convert('RGBA')
 if image.size==(1331,1182):
  assert image.getchannel('A').crop((1330,0,1331,1182)).getextrema()==(0,0)
  image=image.crop((0,0,1330,1182))
 assert image.size==(1330,1182),'No resize, recenter or body-fit fallback'
 return image
def native(image):
 return prepare(image).transform(CANVAS,Image.Transform.AFFINE,
  (1/SCALE,0,SOURCE_ROOT[0]-ROOT[0]/SCALE,0,1/SCALE,SOURCE_ROOT[1]-ROOT[1]/SCALE),Image.Resampling.BICUBIC)
def mirror(image):
 out=Image.new('RGBA',CANVAS);out.paste(image.transpose(Image.Transpose.FLIP_LEFT_RIGHT),(-63,0));return out
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--raw',type=Path,required=True);parser.add_argument('--output-stem',type=Path,required=True);args=parser.parse_args()
 im=prepare(Image.open(args.raw));n=native(im)
 for suffix,pixels in [('.png',im),('-native.png',n),('-native-left.png',mirror(n))]:
  path=args.output_stem.with_name(args.output_stem.name+suffix)
  assert not path.exists(),'Preserve previous candidate'
  pixels.save(path,compress_level=9)
if __name__=='__main__':main()
