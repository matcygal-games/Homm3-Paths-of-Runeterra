"""Derive scenic UI portraits from selected painted TG1, never map miniatures.

Only deterministic crop, proportional reduction and the existing painted native
built-today glyph are used. No stage, sealed profile or canonical recipe writes.
"""
from pathlib import Path
import hashlib, io, json
from PIL import Image

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
WORKSPACE=PROJECT.parent
MASTER='assets/source/town/approved-tg1-implementation-20261030-v19/fully-built.png'
GLYPH='assets/source/town/playable-completion-20261028-v1/ancillary/built-status/master-v1-raw.png'
SIZES={'large':(58,64),'small':(48,32)}
# Keep whole gate pylons and mountains in fortified portraits; ordinary inhabited
# lower terraces supply the village subject. Boxes preserve native slot aspect.
CROPS={('fort','large'):(555,0,765,232),('fort','small'):(520,0,800,187),
       ('village','large'):(0,154,199,374),('village','small'):(0,174,300,374)}

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
def save_png(path,image):
    path.parent.mkdir(parents=True,exist_ok=True)
    out=io.BytesIO();image.save(out,format='PNG',compress_level=9,optimize=False)
    path.write_bytes(out.getvalue())
def contain_glyph(image,canvas):
    alpha=image.getchannel('A').point(lambda p:255 if p>=8 else 0)
    image=image.crop(alpha.getbbox())
    ratio=min(canvas[0]/image.width,canvas[1]/image.height)
    image=image.resize((max(1,round(image.width*ratio)),max(1,round(image.height*ratio))),Image.Resampling.LANCZOS)
    result=Image.new('RGBA',canvas);result.alpha_composite(image,((canvas[0]-image.width)//2,canvas[1]-image.height));return result
def main():
    master=Image.open(PROJECT/MASTER).convert('RGBA')
    glyph=Image.open(PROJECT/GLYPH).convert('RGBA')
    records={}
    for form in ('fort','village'):
        for size,canvas in SIZES.items():
            portrait=master.crop(CROPS[form,size]).resize(canvas,Image.Resampling.LANCZOS)
            if portrait.getchannel('A').getextrema()!=(255,255):raise ValueError('Portrait must fill its scene slot')
            for status in ('normal','built'):
                name=f'{form}_{status}_{size}'
                image=portrait.copy()
                if status=='built':
                    marker=contain_glyph(glyph,(10,12)if size=='large'else(8,10))
                    image.alpha_composite(marker,(canvas[0]-marker.width,canvas[1]-marker.height))
                source=HERE/'portraits'/(name+'.png');save_png(source,image)
                previous=HERE/'templates-before'/(name+'.json')
                recipe=json.loads(previous.read_bytes())
                recipe.update(source=source.relative_to(PROJECT).as_posix(),source_sha256=digest(source),
                              production_status='painted-master-complete-unapproved')
                recipe['generation']=json.loads((HERE/'templates-before/background.json').read_bytes())['generation']
                recipe['generation']['method']='Scenic portrait crop and proportional reduction from selected painted TG1 composition; existing painted built-today marker. No map sprite or new generated painting.'
                recipe['production_inputs']=[{'path':path,'sha256':digest(PROJECT/path)}for path in (MASTER,GLYPH,(HERE/'derive_portraits.py').relative_to(PROJECT).as_posix())]
                save_json(HERE/'candidate-recipes'/(name+'.json'),recipe)
                records[name]={'canvas':list(canvas),'crop':list(CROPS[form,size]),'source':source.relative_to(PROJECT).as_posix(),
                    'source_sha256':digest(source),'canonical_recipe_before_sha256':digest(previous),
                    'candidate_recipe_sha256':digest(HERE/'candidate-recipes'/(name+'.json'))}
    save_json(HERE/'derivation.json',{'status':'authored configuration','master':{'path':MASTER,'sha256':digest(PROJECT/MASTER)},
        'built_today_glyph':{'path':GLYPH,'sha256':digest(PROJECT/GLYPH)},'portraits':records,'canonical_or_stage_changed':False})
    print(json.dumps({'portraits':len(records),'all_opaque':True,'canonical_or_stage_changed':False}))
if __name__=='__main__':main()
