"""Technical urban site annotation only; never selected game artwork."""
from pathlib import Path
import json
from PIL import Image,ImageOps,ImageDraw
import prepare
HERE=Path(__file__).resolve().parent
im=ImageOps.fit(Image.open(HERE/"concept-master.png").convert("RGB"),(800,374),method=Image.Resampling.LANCZOS)
draw=ImageDraw.Draw(im)
for i,(site,(rect,states)) in enumerate(prepare.SITES.items(),1):
    x,y,w,h=rect;draw.rectangle((x,y,x+w-1,y+h-1),outline=(60,220,240),width=1)
    draw.text((x+2,y+2),str(i),fill="white",stroke_width=1,stroke_fill="black")
    draw.line((x,y+h-1,x+w-1,y+h-1),fill=(255,200,50),width=2)
im.save(HERE/"urban-site-study-native.png")
prepare.write(HERE/"planned-sites-before-plate.json",{"status":"design proposal","canvas":[800,374],"sites":prepare.SITES,"semantics":"Cyan envelopes reserve full functional architectural silhouettes; gold baseline is connected dry street-front foundation. Incidental urban fabric stays outside plots; no drawn labels enter final plate."})
