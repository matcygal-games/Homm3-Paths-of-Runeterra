"""Register genuine painted terrace caps and access stairs in the full design.

Only deterministic proportional scale, native translation and source-mask
composition. All stone, ground, cliff faces and stair artwork are imagegen
paintings, not code art. Protected historical source plates stay unchanged.
"""
from pathlib import Path
import json
import hashlib
from PIL import Image, ImageDraw, ImageFilter, ImageChops

HERE=Path(__file__).resolve().parent
PARTS=HERE/'terrain-repair-v9'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def poly(points):
    im=Image.new('L',(800,374));ImageDraw.Draw(im).polygon(points,fill=255)
    return im


def main():
    bg=Image.open(HERE/'background-selected-native-v3.png').convert('RGBA')
    annotations=json.loads((HERE/'physical-annotations-v2.json').read_text())
    stairs=Image.new('L',bg.size)
    for points in annotations['public_stair_polygons']:stairs=ImageChops.lighter(stairs,poly([tuple(p) for p in points]))
    records=[]
    # Whole genuine paintings are scaled uniformly and their painted front edge
    # registered against the actual complete-foot line of the selected town.
    specs=[
        ('upper',486,(152,25),[(153,137),(274,132),(479,132),(637,143),(637,197),(602,200),(500,198),(408,205),(336,201),(281,195),(218,187),(153,181)],True),
        ('middle',636,(164,48),[(164,214),(298,209),(450,209),(620,216),(791,228),(799,239),(799,279),(650,279),(620,282),(451,282),(299,274),(164,267)],True),
        ('foreground',800,(0,34),[(0,318),(170,313),(300,315),(450,314),(630,319),(799,317),(799,373),(0,373)],False),
        ('upper',155,(0,169),[(8,198),(152,198),(153,223),(8,223)],False),
        ('upper',164,(0,46),[(8,77),(160,77),(162,107),(8,107)],False),
        ('upper',184,(604,47),[(604,81),(790,81),(790,113),(604,113)],False)
    ]
    for index,(name,width,origin,points,preserve_stairs) in enumerate(specs):
        path=PARTS/(name+'-raw.png');raw=Image.open(path).convert('RGBA')
        size=(width,round(raw.height*width/raw.width));source=raw.resize(size,Image.Resampling.LANCZOS)
        layer=Image.new('RGBA',bg.size);layer.alpha_composite(source,origin)
        mask=poly(points)
        if preserve_stairs:mask=ImageChops.subtract(mask,stairs.filter(ImageFilter.MaxFilter(5)))
        mask=mask.filter(ImageFilter.GaussianBlur(2))
        # Limit every transition to the preauthored terrain repair region.
        bg.paste(layer,(0,0),mask)
        mask.convert('RGBA').save(PARTS/('cap-'+str(index)+'-selection.png'))
        records.append({'kind':'genuine-painted-terrace-cap','source':path.name,'source_sha256':sha(path),'uniform_size':list(size),'origin':list(origin),
                        'selection_mask':'cap-'+str(index)+'-selection.png','preserved_original_stair_corridors':preserve_stairs})
    raw=Image.open(PARTS/'stair-raw.png').convert('RGBA');box=raw.getchannel('A').point(lambda p:255 if p>=8 else 0).getbbox();stair=raw.crop(box)
    for name,height,origin in [('aerie-access',78,(125,100)),('bastion-access',80,(616,104)),('eastern-alley',59,(672,267)),('western-alley',55,(156,267))]:
        width=round(stair.width*height/stair.height);picture=stair.resize((width,height),Image.Resampling.LANCZOS)
        layer=Image.new('RGBA',bg.size);layer.alpha_composite(picture,origin);layer.save(PARTS/(name+'-native.png'))
        bg=Image.alpha_composite(bg,layer)
        records.append({'kind':'genuine-painted-stair','source':'stair-raw.png','source_sha256':sha(PARTS/'stair-raw.png'),'transparent_margin_crop':list(box),
                        'uniform_size':[width,height],'origin':list(origin),'native_layer':name+'-native.png'})
    output=HERE/'background-selected-native-v9.png';bg.save(output)
    (PARTS/'terrain-assembly-v9.json').write_text(json.dumps({'status':'authored configuration','method':'Genuine painted2D whole-scene local terrace/support repair, preserving recognizable terrain depth and original steps; no invented rendered/code art.',
            'base':{'path':'background-selected-native-v3.png','sha256':sha(HERE/'background-selected-native-v3.png')},'parts':records,'output':{'path':output.name,'sha256':sha(output)}},indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
