"""Technical source inventory/contact sheets; no authored pixel content."""
from pathlib import Path
from PIL import Image, ImageDraw
import hashlib, json
ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[3]
REPORT=PROJECT/'build/reports/playable-creatures-20261028-v1'
REPORT.mkdir(parents=True,exist_ok=True)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def checker(size):
 out=Image.new('RGBA',size,(105,105,105,255));d=ImageDraw.Draw(out)
 for y in range(0,size[1],8):
  for x in range(0,size[0],8):
   if (x//8+y//8)%2:d.rectangle((x,y,x+7,y+7),fill=(145,145,145,255))
 return out
def fixed(im,scale=.11,source_root=(590,833),canvas=(450,400),root=(218,266)):
 return im.transform(canvas,Image.Transform.AFFINE,(1/scale,0,source_root[0]-root[0]/scale,0,1/scale,source_root[1]-root[1]/scale),Image.Resampling.BICUBIC)
def main():
 files=sorted((ROOT/'awakenedSunforged').glob('*-raw.png'));rows=[]
 board=Image.new('RGBA',(430,130*len(files)),(32,32,32,255));draw=ImageDraw.Draw(board)
 for i,p in enumerate(files):
  im=Image.open(p).convert('RGBA');a=im.getchannel('A');native=fixed(im)
  view=native.crop((130,170,340,285));bg=checker(view.size);bg.alpha_composite(view)
  board.paste(bg,(0,i*130+15));board.paste(bg.resize((210,115)),(220,i*130+15))
  draw.text((2,i*130),p.stem,fill='white')
  hist=a.histogram();rows.append({'path':p.relative_to(PROJECT).as_posix(),'sha256':sha(p),'size':im.size,'alpha0':hist[0],'alpha255':hist[255],'alpha_partial':sum(hist[1:255]),'alpha8_bbox':a.point(lambda x:255 if x>=8 else 0).getbbox(),'alpha128_bbox':a.point(lambda x:255 if x>=128 else 0).getbbox(),'native_bbox':native.getbbox()})
 board.save(REPORT/'sunforged-new-six-native1x.png')
 (REPORT/'sunforged-new-six-inventory.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(rows))
if __name__=='__main__':main()
