"""Technical fixed-family affine PNG conversion. No painting/warping/body fitting."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw
SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[4]
REPORT=PROJECT/'build/reports/painted-poros-actions-20261024-v1'/SOURCE.name
SCALE=.064
SOURCE_ROOT=(640,1070)
ROOT=(193,266)
CANVAS=(450,400)
ROI=(135,180,260,285)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def native(im,canvas=CANVAS,root=ROOT,scale=SCALE):
    return im.transform(canvas,Image.Transform.AFFINE,(1/scale,0,SOURCE_ROOT[0]-root[0]/scale,0,1/scale,SOURCE_ROOT[1]-root[1]/scale),Image.Resampling.BICUBIC)
def mirror(im,root=ROOT):
    return im.transform(im.size,Image.Transform.AFFINE,(-1,0,2*root[0]+1,0,1,0),Image.Resampling.NEAREST)
def checker(size):
    im=Image.new('RGBA',size,(105,105,105,255));d=ImageDraw.Draw(im)
    for y in range(0,size[1],8):
        for x in range(0,size[0],8):
            if(x//8+y//8)%2:d.rectangle((x,y,x+7,y+7),fill=(145,145,145,255))
    return im
def border(im):
    a=im.getchannel('A');w,h=im.size
    return max(a.crop(b).getextrema()[1] for b in [(0,0,w,1),(0,h-1,w,h),(0,0,1,h),(w-1,0,w,h)])
def main():
    folder=SOURCE/'native';folder.mkdir(exist_ok=True);REPORT.mkdir(parents=True,exist_ok=True);records=[]
    for f in sorted(SOURCE.glob('*-v*.png')):
        if 'native' in f.stem or 'reference' in f.stem:continue
        im=Image.open(f).convert('RGBA');out=native(im);p=folder/f.name;out.save(p,compress_level=9);mirror(out).save(folder/(f.stem+'-left.png'),compress_level=9)
        a=out.getchannel('A')
        records.append({'name':f.stem,'source':f.relative_to(PROJECT).as_posix(),'source_sha256':sha(f),'source_canvas':list(im.size),'source_canvas_contract_ok':abs(im.width-1330)<=1 and abs(im.height-1182)<=1,'native':p.relative_to(PROJECT).as_posix(),'native_sha256':sha(p),'native_bbox':out.getbbox(),'native_alpha8_bbox':a.point(lambda x:255 if x>=8 else 0).getbbox(),'native_alpha128_bbox':a.point(lambda x:255 if x>=128 else 0).getbbox(),'native_border_alpha_max':border(out),'fixed_transform':{'scale':SCALE,'source_root':SOURCE_ROOT,'native_root':ROOT,'canvas':CANVAS,'per_frame_fit':False,'actor_alpha_threshold':False}})
    w=ROI[2]-ROI[0];h=ROI[3]-ROI[1];board=Image.new('RGBA',(2*w+12,(h+20)*len(records)),(35,35,35,255));d=ImageDraw.Draw(board)
    for i,r in enumerate(records):
        im=Image.open(PROJECT/r['native']).convert('RGBA')
        for j,frame in enumerate([im,mirror(im)]):
            crop=frame.crop(ROI);bg=checker(crop.size);bg.alpha_composite(crop);board.paste(bg,(j*(w+12),i*(h+20)+18))
        d.text((2,i*(h+20)+2),r['name'],fill='white')
    board.save(REPORT/'all-keys-both-facings-native1x.png',compress_level=9)
    (REPORT/'native-key-inventory.json').write_text(json.dumps(records,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'unit':SOURCE.name,'keys':len(records),'source_canvas_refusals':[r['name'] for r in records if not r['source_canvas_contract_ok']],'transparent_native_borders':all(r['native_border_alpha_max']==0 for r in records),'root':ROOT,'scale':SCALE}))
if __name__=='__main__':main()
