"""Losslessly group reviewed large/small sources into one subject master.

No paint, crop, resampling or alpha blending occurs here. Existing sources are
pasted into disjoint rectangles so the original production crops reproduce
their exact reviewed native output bytes through the unchanged raster converter.
"""
from pathlib import Path
import hashlib,json
from PIL import Image
FOLDER=Path(__file__).resolve().parent
PROJECT=FOLDER.parents[3]

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def reproduce():
    values=json.loads((FOLDER/'inputs.json').read_text());outputs={}
    for unit,row in sorted(values['units'].items()):
        pictures=[]
        for size in ('large','small'):
            source=PROJECT/row[size]['path']
            if not source.resolve().is_relative_to(PROJECT) or digest(source)!=row[size]['sha256']:
                raise ValueError('Reviewed portrait source missing/changed: '+unit+'/'+size)
            with Image.open(source) as image:pictures.append(image.convert('RGBA'))
        large,small=pictures
        if list(large.size)!=row['large']['dimensions'] or list(small.size)!=row['small']['dimensions']:
            raise ValueError('Reviewed source dimensions changed')
        atlas=Image.new('RGBA',tuple(row['canvas']))
        atlas.paste(large,(0,0));atlas.paste(small,tuple(row['small']['offset']))
        path=PROJECT/row['output']
        if not path.resolve().is_relative_to(PROJECT/'assets/source/creatures'/unit):raise ValueError('Wrong portrait subject namespace')
        path.parent.mkdir(parents=True,exist_ok=True);atlas.save(path);outputs[unit]={'path':row['output'],'sha256':digest(path)}
    return outputs

if __name__=='__main__':print(json.dumps({'status':'authored configuration','outputs':reproduce(),'native_pixels_changed':False},sort_keys=True))
