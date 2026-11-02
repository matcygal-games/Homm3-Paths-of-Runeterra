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
OUT = HERE / 'structural-contacts-v3'
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
revised = {
 'capitol': [[[310,109],[330,116],[352,122],[374,126],[393,128],[413,123],[424,114]],[[386,128],[396,128]]],
 'dwellingLvl3': [[[209,180],[227,184],[251,187],[278,189],[300,186],[311,179],[314,175]],[[307,184],[310,182]]],
 'dwellingLvl4': [[[598,200],[612,206],[635,211],[658,213],[681,211],[699,196]],[[626,212],[638,212]]],
 'dwellingLvl5': [[[620,105],[621,105]],[[626,107],[633,107],[640,109],[646,110],[653,111],[660,112],[676,112],[681,110],[688,109]],[[698,111],[699,111]]],
 'dwellingUpLvl1': [[[70,246],[83,249],[101,252],[123,252],[143,244]],[[135,251],[140,248]]],
 'dwellingUpLvl2': [[[266,280],[285,287],[308,291],[332,289],[348,284]],[[333,288],[344,287]]],
 'mageGuild1': [[[470,121],[482,131],[493,133],[507,133],[520,132],[531,128]],[[499,133],[508,133]]],
 'mageGuild3': [[[485,124],[493,130],[505,131],[518,122],[519,120]],[[500,131],[506,131]]],
 'special1': [[[600,202],[615,208],[637,212],[659,213],[682,210],[698,197]],[[647,213],[657,213]]],
 'tavern': [[[516,262],[538,277],[557,284],[579,289],[599,293],[621,291],[634,285]],[[619,292],[632,289]]],
}
for key,parts in revised.items():
    annotation['states'][key]['foundation'] = {'lines':[{'points':part,'width':1} for part in parts]}
annotation['states']['dwellingLvl5']['contact_interpretation'] = 'Complete low Roost masonry-front sole, the separate left bearing shoe and detached eastern flagstaff foot. The raised rear/side wall and suspended flag cloth are not invented ground contacts.'
annotation['states']['dwellingUpLvl2']['contact_interpretation'] = 'Complete actual front bearing plinth and entry sole. The high cantilevered stern/side hull at251,262 is not a foot; the old draft contour below that hull crossed transparent air. No source anatomy was removed or altered.'
annotation['states']['mageGuild3']['contact_interpretation'] = 'Complete actual clock-tower plinth and entry sole. The detached high flag/pole pixels at482,64 and520,57 are not ground-level pedestal feet; the previous draft misread hidden RGB beyond the actual alpha.'
for key in ('shipyard','ship'):
    frame = Image.open(PROJECT / index['states'][key]['frame']).convert('RGBA')
    alpha = frame.getchannel('A')
    wet_points = []
    # Actual visible submerged pier contact contour. The functional ship frame
    # replaces the jetty and occludes/rearranges some pier details; never clone
    # the base state's footer coordinates into the ship state.
    for x in range(634,776):
        candidates = [y for y in range(314,328) if alpha.getpixel((x,y))>=128]
        if candidates:
            wet_points.append([x,max(candidates)])
    if key == 'ship':
        for x in range(621,725):
            candidates = [y for y in range(329,355) if alpha.getpixel((x,y))>=128]
            if candidates:
                wet_points.append([x,max(candidates)])
    annotation['states'][key]['foundation'] = {'pixels':wet_points}
    annotation['states'][key]['contact_interpretation'] = 'Entire actual visible wet pier/deck-contact contour, measured separately in this exact native state; the ship also retains its complete submerged lower hull contour. Source-alpha geometry is restricted to the explicit below-deck/marine contact zones, never arbitrary surrounding water or copied base-state piers.'
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
