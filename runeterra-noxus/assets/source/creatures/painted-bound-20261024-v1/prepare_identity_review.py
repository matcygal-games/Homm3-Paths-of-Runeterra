"""Technical native scale/crop review of genuine painted identity masters only."""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
REPORT=ROOT/'build/reports/painted-bound-manifestations-20261024-v1'
UNITS={'boundRuinManifestation':'identity-v2.png','greaterRuinManifestation':'identity-v1.png'}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    board=Image.new('RGB',(640,310),(43,40,36))
    draw=ImageDraw.Draw(board)
    pins={}
    for index,(unit,master_name) in enumerate(UNITS.items()):
        path=HERE/unit/master_name
        im=Image.open(path).convert('RGBA')
        bbox=im.getchannel('A').point(lambda value:255 if value>=8 else 0).getbbox()
        figure=im.crop(bbox)
        height=98
        scaled=figure.resize((round(figure.width*height/figure.height),height),Image.Resampling.LANCZOS)
        native=Image.new('RGBA',(450,400))
        native.alpha_composite(scaled,(218-scaled.width//2,266-height))
        out=HERE/unit/'identity-native-candidate.png'
        native.save(out)
        # Large unobstructed gameplay crop and exact two stock widget sizes.
        x=index*320
        body=native.crop((138,146,298,286))
        board.paste(body,(x+10,24),body)
        for j,h in enumerate((120,130)):
            crop=native.crop((170,155,270,155+h))
            box=Image.new('RGBA',(100,h),(116,105,86,255));box.alpha_composite(crop)
            board.paste(box.convert('RGB'),(x+10+j*110,170))
        draw.text((x+10,5),unit,fill='white')
        pins[unit]={'master':path.relative_to(ROOT).as_posix(),'master_sha256':sha(path),
            'source_bbox':bbox,'native':out.relative_to(ROOT).as_posix(),'native_sha256':sha(out),
            'native_body_root':[218,266],'height':height,'scaled_size':scaled.size,
            'scope':'Identity review only; not an action set or accepted final art.'}
    board.save(REPORT/'identity-pair-native.png')
    (REPORT/'identity-pair-native.json').write_text(json.dumps(pins,indent=2)+'\n')
    print(json.dumps(pins,indent=2))

if __name__=='__main__':main()
