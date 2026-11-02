"""Deterministic technical fit of painted state candidates; never selects art.

Preserves tool masters. Canvas placement is provisional and supplied by the
complete-scene geometry owner. Opaque architecture becomes alpha255, as required
by the user's no-floor-through-building correction. No RGB values are painted.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
from PIL import Image, ImageChops, ImageDraw, ImageFilter

R=Path(__file__).resolve().parent
W=R
BOXES={
 'villageHall':[445,88,55,43], 'townHall':[425,60,95,73],
 'cityHall':[392,35,157,100], 'fort':[625,91,155,45],
 'citadel':[616,70,175,68], 'mageGuild1':[283,70,42,45],
 'mageGuild2':[274,44,57,73], 'dwellingLvl1':[184,207,136,47],
 'dwellingLvl2':[13,173,153,61], 'dwellingLvl3':[480,149,73,47],
 'dwellingLvl4':[428,204,154,51], 'dwellingLvl5':[280,125,137,72],
 'special1':[571,129,32,76], 'dwellingLvl6':[562,127,65,79],
 'special4':[210,137,67,42], 'dwellingLvl7':[205,121,75,60],
 'grail':[537,108,20,30],
}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def dump(path,value):path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def native_border(mask):
    near=mask.filter(ImageFilter.MaxFilter(3));far=mask.filter(ImageFilter.MaxFilter(5))
    result=Image.new('RGBA',mask.size)
    for rgb,alpha in (((38,29,15),ImageChops.subtract(far,near).point(lambda a:208 if a else 0)),
                      ((225,190,80),ImageChops.subtract(near,mask))):
        layer=Image.new('RGBA',mask.size,(*rgb,0));layer.putalpha(alpha);result.alpha_composite(layer)
    return result

def run(output):
    if output.exists():raise ValueError('Fresh fit directory required')
    output.mkdir(parents=True)
    plan=json.loads((R/'selection.json').read_text(encoding='utf-8'))
    for record in plan['states']:
        for ref in (record['master'],record['prompt'],record['approved_reference'],record['generation']['edit_input']):
            raw=R/ref['path'];resolved=raw.resolve()
            if not resolved.is_relative_to(R.resolve()) or raw.is_symlink() or not raw.is_file() or sha(raw)!=ref['sha256']:
                raise ValueError('Portable source dependency missing or changed')
        record['path']=record['master']['path'];record['sha256']=record['master']['sha256']
    states=[]
    for row in plan['states']:
        if row['state'] not in BOXES:continue
        source=W/row['path']
        if sha(source)!=row['sha256']:raise ValueError('Painted master changed')
        with Image.open(source) as image:image=image.convert('RGBA')
        alpha=image.getchannel('A')
        bound=alpha.point(lambda a:255 if a>=8 else 0).getbbox()
        if bound is None:raise ValueError('No visible building')
        crop=(max(0,bound[0]-8),max(0,bound[1]-8),min(image.width,bound[2]+8),min(image.height,bound[3]+8))
        tile=image.crop(crop)
        # Normalization is explicit and repeatable; untouched RGBA master remains.
        tile.putalpha(tile.getchannel('A').point(lambda a:255 if a>=128 else (0 if a<8 else a)))
        x,y,w,h=BOXES[row['state']]
        scale=min(w/tile.width,h/tile.height)
        size=(max(1,round(tile.width*scale)),max(1,round(tile.height*scale)))
        fitted=tile.resize(size,Image.Resampling.LANCZOS)
        fitted.putalpha(fitted.getchannel('A').point(lambda a:255 if a>=128 else (0 if a<8 else a)))
        left=x+(w-size[0])//2;top=y+h-size[1]
        canvas=Image.new('RGBA',(800,374));canvas.alpha_composite(fitted,(left,top))
        mask=canvas.getchannel('A').point(lambda a:255 if a>=128 else 0)
        folder=output/row['state'];folder.mkdir()
        canvas.save(folder/'frame.png',compress_level=9)
        mask.save(folder/'architecture-mask.png',compress_level=9)
        native_border(mask).save(folder/'border.png',compress_level=9)
        states.append({'state':row['state'],'source_master':row['path'],
                       'source_master_sha256':row['sha256'],'source_crop_xyxy':list(crop),
                       'target_box_xywh':[x,y,w,h],'scale':scale,
                       'paste_xy':[left,top],'fitted_size':list(size),
                       'architecture_bounds':list(mask.getbbox()),
                       'alpha_policy':'a>=128 becomes255; a<8 becomes0; low-edgealpha8..127 preserved',
                       'frame_sha256':sha(folder/'frame.png'),
                       'mask_sha256':sha(folder/'architecture-mask.png'),
                       'border_sha256':sha(folder/'border.png')})
    dump(output/'receipt.json',{'status':'authored configuration candidates',
         'selected_for_runtime':False,'native_placement_review_pending':True,
         'master_selection_sha256':sha(R/'selection.json'),
         'producer_sha256':sha(Path(__file__)),'states':states})
    # Native scene overlays are provisional review aids. Full upgraded pixels do
    # not change; this sheet shows one earlier state over a dark neutral field.
    sheet=Image.new('RGB',(1000,((len(states)+3)//4)*170),(55,60,62));draw=ImageDraw.Draw(sheet)
    for n,row in enumerate(states):
        im=Image.open(output/row['state']/'frame.png').convert('RGBA')
        box=im.getchannel('A').getbbox();crop=im.crop((max(0,box[0]-3),max(0,box[1]-3),min(800,box[2]+3),min(374,box[3]+3)))
        # 2x nearest is an explicit enlarged review, never a runtime sprite.
        crop=crop.resize((crop.width*2,crop.height*2),Image.Resampling.NEAREST)
        crop.thumbnail((240,140),Image.Resampling.NEAREST)
        px=(n%4)*250+(250-crop.width)//2;py=(n//4)*170+25+(140-crop.height)
        sheet.paste(crop,(px,py),crop)
        draw.text(((n%4)*250+6,(n//4)*170+5),row['state']+' 2x',fill='white')
    sheet.save(output/'native-fit-sheet.png')
    return states

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();rows=run(args.output)
    print('Fitted',len(rows),'native building-state candidates')
