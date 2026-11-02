"""Recompose existing painted masters; no painting, source selection or stage writes."""
from pathlib import Path
from copy import deepcopy
import hashlib
import importlib.util
import itertools
import json
import sys
from PIL import Image, ImageChops, ImageDraw

sys.dont_write_bytecode = True
SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parents[3]
REPORT = ROOT / 'build/reports/town-depth-20261024-v2/v2'
spec = importlib.util.spec_from_file_location('freljord_depth_art', ROOT/'scripts/prepare_town_art.py')
art = importlib.util.module_from_spec(spec)
spec.loader.exec_module(art)

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def rel(path): return path.relative_to(ROOT).as_posix()
def put(path, data):
    if path.exists() and path.read_bytes() != data:
        raise ValueError('Immutable candidate differs: '+rel(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists(): path.write_bytes(data)
def jput(path, data): put(path, art.encoded(data))

def prepare():
    original = art.read(ROOT/'design/building-layout.json')
    layout = deepcopy(original)
    layout.update(status='authored configuration',
        background='Existing painted inhabited fjord terrain; fixed shore and roads. Theatrical low frontal depth: close services frame the bottom corners; distant monuments recede in apparent scale.',
        camera='Low frontal three-quarter painted oblique view, elevated horizon, visible doors and roof tiers; forced apparent scaling rather than physical camera distortion.',
        scope='Candidate complete36state theatrical depth successor. No gameplay, site-count, shoreline or master changes.')
    planned = {
        'dwelling-tier-7':[15,70,100,78],
        'civic-hall':[260,72,134,96],
        'fortifications':[592,77,156,86],
        'mage-guild':[449,114,97,91],
        'dwelling-tier-1':[0,266,139,104],
        'tavern-hall':[145,266,157,104],
        'market':[311,285,105,80],
        'dwelling-tier-6':[430,271,155,100],
        'dwelling-tier-2':[613,270,180,101],
        'dwelling-tier-4':[383,196,127,66],
        'dwelling-tier-5':[243,181,116,85],
        'forge':[516,205,66,50],
        'anivia-shrine':[142,199,80,65],
    }
    for site in layout['sites']:
        if site['id'] not in planned: continue
        old = site['rect']; new = planned[site['id']]
        site['rect'] = new
        # Preserve every state relative to its shared plot, including ornament.
        for state, rect in site.get('state_rects',{}).items():
            site['state_rects'][state] = [
                round(new[0]+(rect[0]-old[0])*new[2]/old[2]),
                round(new[1]+(rect[1]-old[1])*new[3]/old[3]),
                max(1,round(rect[2]*new[2]/old[2])),
                max(1,round(rect[3]*new[3]/old[3]))]
        site['ground_contact_rect']=[new[0]+5,new[1]+new[3]-9,new[2]-10,9]
        site['state_geometry_note']='Uniform whole-master contain. Large close framing versus smaller distant monuments; unchanged painting, no per-part warp.'
    layout_path=SOURCE/'layout-v2.json'; jput(layout_path,layout)
    common={'status':'authored configuration','production_status':'painted-master-complete-unapproved',
        'visual_approval_granted':False,'require_alpha':True,'canvas':[800,374],
        'credits':{'author':'Project-directed OpenAI built-in imagegen; existing painted masters with deterministic technical composition','license':None,'redistribution':'unresolved; release prohibited'},
        'acceptance':'Theatrical depth candidate; native visual/click and external approval pending.',
        'inputs':[{'path':rel(p),'sha256':sha(p)} for p in (layout_path,ROOT/'scripts/prepare_town_art.py',Path(__file__).resolve())]}
    buildings=art.read(ROOT/'content/factions.json')['freljord']['town']['buildings']
    layers={}; recipes={}; receipts=[]
    for state in buildings:
        old_recipe=art.read(ROOT/f'assets/recipes/town/structures/{state}-animation.json')
        master=ROOT/old_recipe['generation']['painted_master']
        site=next(s for s in layout['sites'] if state in s['states'])
        rect=site.get('state_rects',{}).get(state,site['rect'])
        image=art.load_rgba(master); layer, conversion=art.place(image,rect); area,border=art.masks(layer)
        dest=SOURCE/'prepared-v2'/state
        paths={role:dest/(role+'.png') for role in ('layer','area','border','icon')}
        for role,im in [('layer',layer),('area',area),('border',border),('icon',art.icon(image))]: put(paths[role],art.png(im))
        gen=art.generation(ROOT,master.parent,master,art.read(master.parent/'generation.json'),conversion)
        gen['technical_producer']={'path':rel(Path(__file__).resolve()),'sha256':sha(Path(__file__).resolve())}
        recipe={**common,'generation':gen,'recipe_type':'vcmi_animation','pivot':{'x':0,'y':0},
            'output_path':art.PREFIX+f'town/structures/{state}.json',
            'groups':[{'group':0,'generateShadow':0,'generateOverlay':0,'frames':[{'source':rel(paths['layer']),'source_sha256':sha(paths['layer']),'sha256':sha(paths['layer']),'source_canvas':[800,374]}]}]}
        selected={f'assets/recipes/town/structures/{state}-animation.json':recipe}
        for role in ('area','border'):
            selected[f'assets/recipes/town/structures/{state}-{role}.json']={**common,'recipe_type':'raster','fit':'exact',
                'source':rel(paths[role]),'source_sha256':sha(paths[role]),'source_canvas':[800,374],
                'output_path':art.PREFIX+f'town/structures/{state}_{role}.png',
                'generation':{'image_generation_used':False,'method':'Existing alpha128 silhouette or 1px outer edge','painted_source_provenance':gen,
                    'references':[{'path':rel(paths['layer']),'sha256':sha(paths['layer'])}]}}
        for selected_name,value in selected.items():
            path=REPORT/'recipe-payload'/Path(selected_name).relative_to('assets/recipes/town'); jput(path,value);recipes[path]=value
        receipt={'state':state,'site':site['id'],'master':rel(master),'master_sha256':sha(master),
            'native_layer':rel(paths['layer']),'native_layer_sha256':sha(paths['layer']),
            'conversion':conversion,'native_alpha128_bbox':list(area.getchannel('A').getbbox()),
            'recipes':{key:hashlib.sha256(art.encoded(value)).hexdigest() for key,value in selected.items()}}
        jput(dest/'preparation.json',receipt);receipts.append(receipt);layers[state]=layer
    bg_recipe=art.read(ROOT/'assets/recipes/town/background.json')
    background=Image.open(ROOT/bg_recipe['source']).convert('RGBA')
    for label,upgraded,coast in [('empty',None,False),('early',False,False),('base',False,False),('upgraded',True,False),('coastal',True,True)]:
        canvas=background.copy();chosen=[]
        if label!='empty':
            for site in layout['sites']:
                if not site['land'] and not coast:continue
                opts=[s for s in site['states'] if s!='grail'];state=opts[-1] if upgraded else opts[0]
                if label=='early' and state not in ('villageHall','tavern','dwellingLvl1'):continue
                chosen.append((site['z'],state))
            for z,state in sorted(chosen):canvas.alpha_composite(layers[state])
        put(REPORT/(label+'-native.png'),art.png(canvas))
    # Actual cross-site alpha128 intersects, including every replacement state.
    overlaps=[]
    opaque={s:im.getchannel('A').point(lambda a:255 if a>=128 else 0) for s,im in layers.items()}
    for a,b in itertools.combinations(layout['sites'],2):
        for sa,sb in itertools.product(a['states'],b['states']):
            hit=ImageChops.multiply(opaque[sa],opaque[sb]);count=sum(hit.histogram()[1:])
            if count:overlaps.append({'first':sa,'second':sb,'pixels':count,'bbox':hit.getbbox()})
    water=Image.new('L',(800,374));ImageDraw.Draw(water).polygon(layout['water_polygon'],fill=255)
    footing=[]
    for state,im in layers.items():
        site=next(s for s in layout['sites'] if state in s['states'])
        if not site['land'] or state=='grail':continue
        box=opaque[state].getbbox();mask=Image.new('L',(800,374));mask.paste(opaque[state].crop((0,box[3]-7,800,box[3])),(0,box[3]-7))
        count=sum(ImageChops.multiply(mask,water).histogram()[1:])
        footing.append({'state':state,'water_pixels':count})
    jput(REPORT/'geometry.json',{'status':'authored configuration','site_count':len(layout['sites']),'land_sites':sum(s['land'] for s in layout['sites']),'states':len(layers),'overlaps':overlaps,'footing':footing,'native_visual_verified':False})
    jput(REPORT/'candidate.json',{'status':'authored configuration','layout':rel(layout_path),'layout_sha256':sha(layout_path),'states':receipts,'recipes':{rel(p):sha(p) for p in recipes},'background_unchanged':{'path':bg_recipe['source'],'sha256':sha(ROOT/bg_recipe['source'])},'selected_for_build':False})
    print(json.dumps({'states':len(layers),'recipes':len(recipes),'overlaps':len(overlaps),'water_errors':sum(bool(i['water_pixels']) for i in footing)}))

if __name__=='__main__':prepare()
