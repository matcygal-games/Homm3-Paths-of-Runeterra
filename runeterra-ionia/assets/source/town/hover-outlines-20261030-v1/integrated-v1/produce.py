"""Reproduce the reviewed Ionia architecture masks and hover borders.

Only interaction graphics are derived. Painted art and click ownership are
external pinned read-only inputs. This does not stage or publish a mod.
"""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw,ImageChops,ImageFilter

FOLDER=Path(__file__).resolve().parent
PROJECT=FOLDER.parents[4]
GOLD=(225,190,80,255)
SHADOW=(38,29,15,208)

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def reproduce():
    traces=json.loads((FOLDER/'architecture-traces.json').read_text())
    outputs={}
    for name,row in sorted(traces['states'].items()):
        source=PROJECT/row['selected_layer']['path']
        if not source.resolve().is_relative_to(PROJECT) or digest(source)!=row['selected_layer']['sha256']:
            raise ValueError('Selected painting missing/changed: '+name)
        with Image.open(source) as layer:
            if layer.mode!='RGBA' or layer.size!=(800,374):raise ValueError('Expected native RGBA painting')
            alpha=layer.getchannel('A').point(lambda value:255 if value>=128 else 0)
        envelope=Image.new('L',(800,374));draw=ImageDraw.Draw(envelope)
        x0,y0,_,_=row['native_crop']
        for polygon in row['polygons_native_crop_local']:
            draw.polygon([(x0+x,y0+y) for x,y in polygon],fill=255)
        mask=ImageChops.multiply(envelope,alpha)
        near=mask.filter(ImageFilter.MaxFilter(3));far=mask.filter(ImageFilter.MaxFilter(5))
        edge=ImageChops.subtract(near,mask);support=ImageChops.subtract(far,near)
        border=Image.new('RGBA',(800,374));dark=Image.new('RGBA',(800,374),SHADOW)
        dark.putalpha(support.point(lambda value:208 if value else 0));border.alpha_composite(dark)
        line=Image.new('RGBA',(800,374),GOLD);line.putalpha(edge);border.alpha_composite(line)
        for suffix,image in (('architecture-mask',mask),('border',border)):
            path=FOLDER/(name+'-'+suffix+'.png');image.save(path)
            outputs[path.name]=digest(path)
    return outputs

if __name__=='__main__':print(json.dumps({'outputs':reproduce(),'status':'authored configuration','native_observed':False},sort_keys=True))
