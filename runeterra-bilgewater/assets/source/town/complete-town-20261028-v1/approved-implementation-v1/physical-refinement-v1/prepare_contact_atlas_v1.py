from pathlib import Path
import json
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[5]
OUT = HERE / 'contact-atlas-v1'
OUT.mkdir(exist_ok=False)
index = json.loads((HERE / 'lower-roost-registration-v1/states.json').read_text())
rows = []
for key,row in index['states'].items():
    frame = Image.open(PROJECT / row['frame']).convert('RGBA')
    bbox = frame.getchannel('A').point(lambda p:255 if p>=8 else 0).getbbox()
    crop = [max(0,bbox[0]-2),max(0,bbox[3]-32),min(800,bbox[2]+2),min(374,bbox[3]+3)]
    composite = Image.alpha_composite(Image.new('RGBA',frame.size,(155,15,90,255)),frame).convert('RGB')
    native = composite.crop(crop)
    zoom = native.resize((native.width*6,native.height*6),Image.Resampling.NEAREST)
    draw = ImageDraw.Draw(zoom,'RGBA')
    for x in range(((crop[0]+9)//10)*10,crop[2],10):
        xx = (x-crop[0])*6
        draw.line((xx,0,xx,zoom.height),fill=(255,255,255,100))
        draw.text((xx+2,2),str(x),fill=(255,255,255,255))
    for y in range(((crop[1]+4)//5)*5,crop[3],5):
        yy = (y-crop[1])*6
        draw.line((0,yy,zoom.width,yy),fill=(255,255,255,100))
        draw.text((2,yy+1),str(y),fill=(255,255,255,255))
    name = key+'-native-contact.png'
    zoom.save(OUT / name)
    rows.append({'state':key,'native_crop':crop,'image':name})
(OUT / 'index.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
(OUT / 'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Bilgewater actual structural contact atlas</title><style>body{background:#17151a;color:#eee;font:16px system-ui}img{display:block;image-rendering:pixelated;max-width:none}section{margin:30px 0}</style><h1>Actual selected native actor pixels, all35states</h1><p>Magenta is transparent source, never terrain. Native6×nearest technical inspection; this is not a physical pass.</p>'+''.join('<section><h2>'+r['state']+'</h2><p>Native crop '+str(r['native_crop'])+'</p><img src="'+r['image']+'"></section>' for r in rows),encoding='utf-8')
print('35 actual source actor contact crops prepared')
