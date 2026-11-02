"""Technical earlier watchtower fitting; preserves original tool master."""
from pathlib import Path
import argparse
import hashlib
import json
from PIL import Image

R=Path(__file__).resolve().parent
BOX=(573,140,28,65)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(out):
    record=json.loads((R/'selection.json').read_text(encoding='utf-8'))
    for key in ('master','prompt','approved_reference'):
        ref=record[key];path=R/ref['path']
        if path.is_symlink() or not path.resolve().is_relative_to(R.resolve()) or sha(path)!=ref['sha256']:
            raise ValueError('Source dependency missing or changed')
    if out.exists():raise ValueError('Fresh output required')
    out.mkdir(parents=True)
    image=Image.open(R/record['master']['path']).convert('RGBA')
    alpha=image.getchannel('A');bound=alpha.point(lambda a:255 if a>=8 else 0).getbbox()
    crop=(max(0,bound[0]-8),max(0,bound[1]-8),min(image.width,bound[2]+8),min(image.height,bound[3]+8))
    tile=image.crop(crop)
    tile.putalpha(tile.getchannel('A').point(lambda a:255 if a>=128 else (0 if a<8 else a)))
    x,y,w,h=BOX;scale=min(w/tile.width,h/tile.height)
    fitted=tile.resize((max(1,round(tile.width*scale)),max(1,round(tile.height*scale))),Image.Resampling.LANCZOS)
    fitted.putalpha(fitted.getchannel('A').point(lambda a:255 if a>=128 else (0 if a<8 else a)))
    left=x+(w-fitted.width)//2;top=y+h-fitted.height
    result=Image.new('RGBA',(800,374));result.alpha_composite(fitted,(left,top))
    mask=result.getchannel('A').point(lambda a:255 if a>=128 else 0)
    result.save(out/'frame.png',compress_level=9);mask.save(out/'architecture-mask.png',compress_level=9)
    box=result.getchannel('A').getbbox()
    view=Image.new('RGBA',(150,210),(55,60,62,255));cut=result.crop(box).resize(((box[2]-box[0])*3,(box[3]-box[1])*3),Image.Resampling.NEAREST)
    view.alpha_composite(cut,((150-cut.width)//2,210-cut.height));view.save(out/'native-3x.png')
    receipt={'status':'authored configuration candidate','runtime_selected':False,'box_xywh':list(BOX),
             'source_crop_xyxy':list(crop),'scale':scale,'paste_xy':[left,top],
             'source_master_sha256':record['master']['sha256'],
             'selection_sha256':sha(R/'selection.json'),'producer_sha256':sha(Path(__file__)),
             'frame_sha256':sha(out/'frame.png'),'mask_sha256':sha(out/'architecture-mask.png'),
             'alpha128_bounds':list(mask.getbbox()),'alpha_body_policy':'a>=128->255; a<8->0'}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    print(json.dumps(run(a.output),indent=2))
