"""Reproduce this hand-traced building hover border; preserves painting/clicks."""
from pathlib import Path
import hashlib,json,sys
from PIL import Image,ImageDraw,ImageChops,ImageFilter
here=Path(__file__).resolve().parent
project=here.parents[4]
v=json.loads((here/"contour.json").read_text())
source=project/v["source"]["path"]
if hashlib.sha256(source.read_bytes()).hexdigest()!=v["source"]["sha256"]:raise ValueError("Selected building layer changed")
im=Image.open(source).convert("RGBA")
mask=Image.new("L",(800,374));ImageDraw.Draw(mask).polygon([tuple(p) for p in v["points_native"]],fill=255)
mask=ImageChops.multiply(mask,im.getchannel("A").point(lambda a:255 if a>=128 else 0))
near=mask.filter(ImageFilter.MaxFilter(3));far=mask.filter(ImageFilter.MaxFilter(5))
gold=ImageChops.subtract(near,mask);shadow=ImageChops.subtract(far,near)
result=Image.new("RGBA",(800,374));support=Image.new("RGBA",(800,374),(38,29,15,0));support.putalpha(shadow.point(lambda a:208 if a else 0));result.alpha_composite(support)
edge=Image.new("RGBA",(800,374),(225,190,80,0));edge.putalpha(gold);result.alpha_composite(edge)
dest=Path(sys.argv[1]);dest.mkdir(parents=True,exist_ok=False)
mask.save(dest/"architecture-mask.png");result.save(dest/"border.png")
