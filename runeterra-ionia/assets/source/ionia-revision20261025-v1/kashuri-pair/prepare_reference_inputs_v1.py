"""Rebuild own painted pose-function contact sheets, never creature artwork."""
from pathlib import Path
from PIL import Image,ImageDraw
import sys,io
S=Path(__file__).resolve().parent;sys.path.insert(0,str(S))
from pose_tools import png,put

def main():
    out=Image.new('RGBA',(1400,1050));draw=ImageDraw.Draw(out)
    for j,(name,box) in enumerate([('walk-contacts-v1.png',(0,0,820,1024)),('walk-contactB-v2.png',None)]):
        im=Image.open(S/'kashuriArmsbearer'/name).convert('RGBA');im=im.crop(box) if box else im
        b=im.getchannel('A').point(lambda v:255 if v>=16 else 0).getbbox();im=im.crop(b);factor=850/im.height
        im=im.resize((round(im.width*factor),850),Image.Resampling.LANCZOS);out.alpha_composite(im,(j*700+(700-im.width)//2,980-im.height))
        draw.text((j*700+8,5),'ContactA: near2-buckle FRONT' if j==0 else 'ContactB: near2-buckle BACK,far1-buckle FRONT',fill='white')
    png(S/'reference-inputs/own-painted-opposed-contacts-v1.png',out)
    im=Image.open(S/'kashuriMarksman/melee-v1.png').crop((470,680,1080,1010))
    raw=io.BytesIO();im.save(raw,format='PNG');put(S/'reference-inputs/marksman-downstrike-merged-function-v1.png',raw.getvalue())

if __name__=='__main__':main()
