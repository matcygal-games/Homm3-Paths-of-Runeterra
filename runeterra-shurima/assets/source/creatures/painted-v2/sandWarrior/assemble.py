"""Technical painted PNG conversion only; no art generation or per-frame fitting."""
from pathlib import Path
import json, hashlib
from PIL import Image, ImageDraw

SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[4]
REPORT = PROJECT / 'build/reports/painted-sandwarrior-actions-20261023-v1'
SCALE = .074
SOURCE_ROOT = (640,1070)
ROOT = (193,266)
CANVAS = (450,400)
ROI = (130,170,265,285)

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def native(im, canvas=CANVAS, root=ROOT, scale=SCALE):
    return im.transform(canvas, Image.Transform.AFFINE,
        (1/scale,0,SOURCE_ROOT[0]-root[0]/scale,
         0,1/scale,SOURCE_ROOT[1]-root[1]/scale), Image.Resampling.BICUBIC)

def mirror(im, root=ROOT):
    out=Image.new('RGBA',im.size)
    out.paste(im.transpose(Image.Transpose.FLIP_LEFT_RIGHT),(2*root[0]-(im.width-1),0))
    return out

def checker(size):
    out=Image.new('RGBA',size,(105,105,105,255));d=ImageDraw.Draw(out)
    for y in range(0,size[1],8):
        for x in range(0,size[0],8):
            if (x//8+y//8)%2:d.rectangle((x,y,x+7,y+7), fill=(145,145,145,255))
    return out

def main():
    folder=SOURCE/'native';folder.mkdir(exist_ok=True);REPORT.mkdir(exist_ok=True)
    records=[]
    for f in sorted(SOURCE.glob('*-v*.png')):
        if 'reference' in f.stem:continue
        im=Image.open(f).convert('RGBA');out=native(im);dest=folder/f.name;out.save(dest,compress_level=9)
        left=mirror(out);left.save(folder/(f.stem+'-left.png'),compress_level=9)
        alpha=out.getchannel('A');border=max(alpha.crop((0,0,450,1)).getextrema()[1],alpha.crop((0,399,450,400)).getextrema()[1],alpha.crop((0,0,1,400)).getextrema()[1],alpha.crop((449,0,450,400)).getextrema()[1])
        records.append({'name':f.stem,'source':f.relative_to(PROJECT).as_posix(),'source_sha256':sha(f),'source_size':list(im.size),'canvas_contract_ok':im.size in [(1330,1182),(1331,1182),(1330,1183),(1331,1183)],'native':dest.relative_to(PROJECT).as_posix(),'native_sha256':sha(dest),'native_bbox':out.getbbox(),'border_alpha_max':border,'transform':{'scale':SCALE,'source_root':SOURCE_ROOT,'native_root':ROOT,'canvas':CANVAS,'per_frame_body_fit':False}})
    width=2*(ROI[2]-ROI[0])+12;cell_h=ROI[3]-ROI[1]+20
    board=Image.new('RGBA',(width,cell_h*len(records)),(35,35,35,255));draw=ImageDraw.Draw(board)
    for i,r in enumerate(records):
        out=Image.open(PROJECT/r['native']).convert('RGBA')
        for col,img in enumerate([out,mirror(out)]):
            crop=img.crop(ROI);bg=checker(crop.size);bg.alpha_composite(crop);board.paste(bg,(col*(crop.width+12),i*cell_h+18))
        draw.text((2,i*cell_h+2),r['name'],fill='white')
    board.save(REPORT/'all-keys-both-facings-native1x.png',compress_level=9)
    (REPORT/'native-key-inventory.json').write_text(json.dumps(records,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'keys':len(records),'source_canvas_refusals':[r['name'] for r in records if not r['canvas_contract_ok']],'transparent_native_borders':all(r['border_alpha_max']==0 for r in records),'native_root':ROOT,'fixed_scale':SCALE}))

if __name__=='__main__':main()
