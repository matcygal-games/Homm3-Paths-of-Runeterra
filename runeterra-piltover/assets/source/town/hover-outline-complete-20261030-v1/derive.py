"""Reproduce reviewed town hover sources; no painting or click-area changes."""
from pathlib import Path
import hashlib,json,sys
from PIL import Image,ImageDraw,ImageChops,ImageFilter
here=Path(__file__).resolve().parent;project=here.parents[3]
traces=json.loads((here/"traces.json").read_text())
dest=Path(sys.argv[1]);dest.mkdir(parents=True,exist_ok=False)
for name,v in sorted(traces["states"].items()):
 source=project/v["source"]["path"]
 if hashlib.sha256(source.read_bytes()).hexdigest()!=v["source"]["sha256"]:raise ValueError("Selected layer changed: "+name)
 im=Image.open(source).convert("RGBA")
 if im.size!=(800,374):raise ValueError("Native layer required")
 base=im.getchannel("A").point(lambda a:255 if a>=128 else 0)
 points=v.get("points_native")
 if points is None:
  if v.get("mode")!="alpha128-silhouette-for-review":raise ValueError("Missing explicit contour mode")
  mask=base.copy()
 else:
  mask=Image.new("L",(800,374));ImageDraw.Draw(mask).polygon([tuple(p)for p in points],fill=255);mask=ImageChops.multiply(mask,base)
 for x0,y0,x1,y1 in v.get("exclusions_native",[]):ImageDraw.Draw(mask).rectangle((x0,y0,x1-1,y1-1),fill=0)
 if not mask.getbbox()or mask.getextrema()==(255,255):raise ValueError("Nonempty architectural cutout required")
 near=mask.filter(ImageFilter.MaxFilter(3));far=mask.filter(ImageFilter.MaxFilter(5))
 gold=ImageChops.subtract(near,mask);shadow=ImageChops.subtract(far,near)
 result=Image.new("RGBA",(800,374));support=Image.new("RGBA",(800,374),(38,29,15,0));support.putalpha(shadow.point(lambda a:208 if a else 0));result.alpha_composite(support)
 edge=Image.new("RGBA",(800,374),(225,190,80,0));edge.putalpha(gold);result.alpha_composite(edge)
 folder=dest/name;folder.mkdir();mask.save(folder/"architecture-mask.png");result.save(folder/"border.png")
