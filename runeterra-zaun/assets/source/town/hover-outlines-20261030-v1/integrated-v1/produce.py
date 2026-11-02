"""Reproduce source-reviewed Zaun architecture-only hover graphics."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageChops,ImageDraw,ImageFilter
FOLDER=Path(__file__).resolve().parent
PROJECT=FOLDER.parents[4]
GOLD=(225,190,80,255);SHADOW=(38,29,15,208)

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def reproduce():
    trace=json.loads((FOLDER/'architecture-traces.json').read_text());outputs={}
    for name,row in sorted(trace['states'].items()):
        source=PROJECT/row['selected_layer']['path']
        if not source.resolve().is_relative_to(PROJECT) or digest(source)!=row['selected_layer']['sha256']:
            raise ValueError('Selected painting missing/changed: '+name)
        with Image.open(source) as layer:
            if layer.mode!='RGBA' or layer.size!=(800,374):raise ValueError('Expected native RGBA source')
            mask=layer.getchannel('A').point(lambda value:255 if value>=128 else 0)
        if row['polygons_native_crop_local']:
            envelope=Image.new('L',(800,374));d=ImageDraw.Draw(envelope);x0,y0,_,_=row['native_crop']
            for polygon in row['polygons_native_crop_local']:d.polygon([(x0+x,y0+y) for x,y in polygon],fill=255)
            mask=ImageChops.multiply(mask,envelope)
        for point in row['removed_component_pixels']:
            if not mask.getpixel(tuple(point)):raise ValueError('Observed fragment changed: '+name)
            mask.putpixel(tuple(point),0)
        near=mask.filter(ImageFilter.MaxFilter(3));far=mask.filter(ImageFilter.MaxFilter(5))
        border=Image.new('RGBA',(800,374));dark=Image.new('RGBA',(800,374),SHADOW)
        dark.putalpha(ImageChops.subtract(far,near).point(lambda value:208 if value else 0));border.alpha_composite(dark)
        edge=Image.new('RGBA',(800,374),GOLD);edge.putalpha(ImageChops.subtract(near,mask));border.alpha_composite(edge)
        for suffix,image in (('architecture-mask',mask),('border',border)):
            path=FOLDER/(name+'-'+suffix+'.png');image.save(path);outputs[path.name]=digest(path)
    return outputs

if __name__=='__main__':print(json.dumps({'outputs':reproduce(),'status':'authored configuration','native_observed':False},sort_keys=True))
