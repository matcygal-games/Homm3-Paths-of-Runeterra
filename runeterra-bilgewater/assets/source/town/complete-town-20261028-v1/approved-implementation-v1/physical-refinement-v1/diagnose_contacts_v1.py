"""Native semantic diagnostics; no mask fitting or baseline claim."""
from pathlib import Path
import importlib.util
import json
from PIL import Image, ImageDraw, ImageChops

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[5]
OUT = HERE / 'contact-diagnostics-v1'
OUT.mkdir(exist_ok=False)
spec = importlib.util.spec_from_file_location('binder',HERE / 'bind_contract.py')
binder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(binder)
annotation = json.loads((HERE / 'semantic-candidate-v6/annotations.json').read_text())
index = json.loads((HERE / 'lower-roost-registration-v1/states.json').read_text())
terrain = {role:Image.open(HERE / 'terrain-planes-v1' / (role+'.png')).convert('L') for role in ('land','support','stairs','water')}
background = Image.open(PROJECT / index['background']).convert('RGBA')

def pixels(mask):
    box = mask.getbbox()
    if not box:
        return []
    return [[x,y] for y in range(box[1],box[3]) for x in range(box[0],box[2]) if mask.getpixel((x,y))]

results = {}
for key,row in annotation['states'].items():
    frame = Image.open(PROJECT / index['states'][key]['frame']).convert('RGBA')
    full = frame.getchannel('A').point(lambda p:255 if p>=8 else 0)
    roots = ImageChops.multiply(binder.trace(row['foundation']),full)
    unsupported = ImageChops.subtract(roots,terrain['support'])
    on_stairs = ImageChops.multiply(roots,terrain['stairs'])
    door = binder.trace(row['door'])
    approach = binder.trace(row['approach'])
    off_dry = ImageChops.subtract(ImageChops.lighter(door,approach),terrain['land'])
    off_walk = ImageChops.subtract(approach,ImageChops.lighter(terrain['support'],terrain['stairs']))
    results[key] = {'root_pixels':len(pixels(roots)), 'unsupported_root_pixels':pixels(unsupported),
        'root_on_stairs_pixels':pixels(on_stairs),'access_off_dry_pixels':pixels(off_dry),
        'approach_off_actual_top_or_stair_pixels':pixels(off_walk)}
    scene = Image.alpha_composite(background,frame)
    draw = ImageDraw.Draw(scene)
    for point in pixels(roots):
        draw.point(tuple(point),fill=(255,230,0))
    for point in pixels(unsupported):
        draw.point(tuple(point),fill=(255,40,70))
    for point in pixels(off_walk):
        draw.point(tuple(point),fill=(255,0,255))
    box = full.getbbox()
    box = (max(0,box[0]-8),max(0,box[1]-8),min(800,box[2]+8),min(374,box[3]+12))
    scene.crop(box).resize(((box[2]-box[0])*5,(box[3]-box[1])*5),Image.Resampling.NEAREST).save(OUT / (key+'-native-contact-overlay.png'))
record = {'status':'authored configuration','whole_baseline_passed':False,'results':results}
(OUT / 'diagnostics.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({key:{'roots':row['root_pixels'],'unsupported':len(row['unsupported_root_pixels']),'stairs':len(row['root_on_stairs_pixels']),'access_off_dry':len(row['access_off_dry_pixels']),'approach_off_walk':len(row['approach_off_actual_top_or_stair_pixels'])} for key,row in results.items()},indent=2))
print('Support/stair overlap:',pixels(ImageChops.multiply(terrain['support'],terrain['stairs'])))
