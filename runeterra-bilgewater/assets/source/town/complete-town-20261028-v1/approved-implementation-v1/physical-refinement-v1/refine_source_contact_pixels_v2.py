"""Measure actual source pixels within frozen hand-observed basal trace bands.

This writer never loads terrain or validation errors. It preserves complete
authored component spans and reports any source gap it cannot resolve locally.
The raised Roost has genuine separate stilt shoes, not a solid plinth contour.
"""
from pathlib import Path
import json
import hashlib
import importlib.util
from PIL import Image, ImageDraw, ImageChops

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[5]
OUT = HERE / 'structural-contacts-v2'
OUT.mkdir(exist_ok=False)
spec = importlib.util.spec_from_file_location('binder',HERE / 'bind_contract.py')
binder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(binder)
source = HERE / 'structural-contacts-v1/annotations.json'
annotation = json.loads(source.read_text())
index = json.loads((HERE / 'lower-roost-registration-v1/states.json').read_text())
# Five actual load-bearing pairs, all visible in the actor alpha/RGB atlas.
# Between these shoes are genuine open gaps and the raised platform underside.
annotation['states']['dwellingUpLvl5']['foundation'] = {'lines':[
    {'points':[[643,111],[644,111]],'width':1},
    {'points':[[650,111],[651,111]],'width':1},
    {'points':[[660,111],[661,111]],'width':1},
    {'points':[[669,111],[670,111]],'width':1}], 'pixels':[[689,111]]}
annotation['states']['dwellingUpLvl5']['contact_interpretation'] = 'All five actual separate timber stilt shoes at nativey111, including the detached eastern single-pixel shoe. The raised beam underside between posts is open air and is not a ground contact. These literal source coordinates are preserved independently of terrain.'
diagnostics = {}
for key,row in annotation['states'].items():
    frame = Image.open(PROJECT / index['states'][key]['frame']).convert('RGBA')
    alpha = frame.getchannel('A')
    raw = binder.trace(row['foundation'])
    box = raw.getbbox()
    actual = Image.new('L',frame.size)
    draw = ImageDraw.Draw(actual)
    unresolved = []
    moved = []
    for y in range(box[1],box[3]):
        for x in range(box[0],box[2]):
            if not raw.getpixel((x,y)):
                continue
            if alpha.getpixel((x,y)) >= 128:
                chosen = y
            else:
                # One native-column measurement inside the manually authored
                # three-pixel source-edge uncertainty band, never near terrain.
                candidates = [yy for yy in range(max(0,y-3),min(374,y+4)) if alpha.getpixel((x,yy)) >= 128]
                if not candidates:
                    unresolved.append([x,y])
                    continue
                chosen = min(candidates,key=lambda yy:(abs(yy-y),yy))
                moved.append({'from':[x,y],'to':[x,chosen]})
            draw.point((x,chosen),fill=255)
    actual.save(OUT / (key+'-actual-source-contacts.png'))
    pixels = [[x,y] for y in range(374) for x in range(800) if actual.getpixel((x,y))]
    row['foundation'] = {'pixels':pixels}
    if key != 'dwellingUpLvl5':
        row['contact_interpretation'] += ' Final native source-edge measurement is constrained to the frozen three-pixel hand-observed basal band, independent of all terrain/support masks; all unresolved spans remain explicit rather than being silently clipped.'
    diagnostics[key] = {'raw_component_trace_pixels':sum(bool(v) for v in raw.get_flattened_data()),
        'actual_opaque_contact_pixels':len(pixels),'source_edge_pixel_measurements':moved,
        'unresolved_native_source_contact_pixels':unresolved,'complete_source_trace_admitted':not unresolved}
annotation['structural_contact_ancestry'] = {'path':source.relative_to(PROJECT).as_posix(),'sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
(OUT / 'annotations.json').write_text(json.dumps(annotation,indent=2,sort_keys=True)+'\n',encoding='utf-8')
(OUT / 'source-pixel-diagnostics.json').write_text(json.dumps({'status':'design proposal','terrain_loaded':False,'states':diagnostics},indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({key:{'actual':row['actual_opaque_contact_pixels'],'unresolved':len(row['unresolved_native_source_contact_pixels'])} for key,row in diagnostics.items()},indent=2))
