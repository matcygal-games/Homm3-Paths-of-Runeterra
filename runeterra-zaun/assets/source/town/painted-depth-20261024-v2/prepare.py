"""Recompose existing painted Zaun masters at theatrical HoMM3 depth.

Technical crop/scale/composition only. Historical masters and selected V1
sources remain read-only. No stage, runtime or acceptance gate is written.
"""
from pathlib import Path
import hashlib, json, sys, copy, shutil
from PIL import Image, ImageOps, ImageChops, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
REPORT = ROOT / 'build/reports/town-depth-20261024-v2'
OLD = ROOT / 'assets/source/town/painted-community-20261024-v1'
RECTS = {
    'foundryHall': [198, 14, 108, 99],
    'sumpRampart': [14, 20, 110, 94],
    'shimmerInstitute': [359, 42, 80, 111],
    'dwellingThug': [0, 235, 157, 137],
    'dwellingRavager': [166, 243, 148, 126],
    'dwellingConstruct': [535, 277, 112, 87],
    'dwellingEnforcer': [23, 129, 119, 96],
    'dwellingAgent': [678, 152, 115, 96],
    'dwellingVeteran': [532, 139, 128, 105],
    'dwellingPredator': [654, 30, 128, 105],
    'grog': [320, 264, 132, 106],
    'scrapExchange': [302, 223, 108, 62],
    'ammoFoundry': [622, 237, 95, 65],
    'shimmerFactory': [506, 72, 90, 91],
    'shipyard': [712, 278, 88, 96],
    'codeOfProgress': [602, 118, 40, 28],
    'augmentationWorkshop': [162, 120, 111, 84],
    'augmentationClinic': [279, 156, 93, 70],
    'theSump': [386, 161, 104, 95],
    'fightingPit': [444, 253, 90, 87],
}

def load(p):
    return json.loads(p.read_text(encoding='utf-8'))

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def write(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')

def rel(p):
    return p.relative_to(ROOT).as_posix()

def save(p, image):
    p.parent.mkdir(parents=True, exist_ok=True)
    image.save(p, compress_level=9, optimize=False)

def fit(image, rect):
    x,y,w,h = rect
    image = ImageOps.contain(image, (w-4,h-4), Image.Resampling.LANCZOS)
    canvas = Image.new('RGBA', (800,374))
    canvas.alpha_composite(image, (x+(w-image.width)//2,y+h-2-image.height))
    return canvas

def inputs():
    old = load(OLD / 'coordinator-handoff.json')
    entries = {}
    for row in old['states']:
        master = ROOT / row['master']
        if sha(master) != row['master_sha256']:
            raise ValueError('Painted source changed: '+str(master))
        entries[row['state']] = {
            'row':row,
            'image':Image.open(master).convert('RGBA').crop(row['source_crop']),
        }
    return old, entries

def preview():
    old, entries = inputs()
    layers = {}
    for site in old['sites']:
        for state in site['buildings']:
            layers[state] = fit(entries[state]['image'], RECTS[site['id']])
            if state == 'ship':
                boat = fit(entries[state]['image'], [738,330,58,38])
                layers[state] = layers['shipyard'].copy()
                layers[state].alpha_composite(boat)
    REPORT.mkdir(parents=True,exist_ok=True)
    for variant in ['base','upgraded','coastal','moored','grail']:
        canvas = Image.open(OLD / 'background/native-v3.png').convert('RGBA')
        for site in sorted(old['sites'],key=lambda s: RECTS[s['id']][1]+RECTS[s['id']][3]):
            if site['id']=='shipyard':
                state = 'ship' if variant in ['moored','grail'] else 'shipyard' if variant=='coastal' else None
            elif site['id']=='codeOfProgress':
                state = 'grail' if variant=='grail' else None
            else:
                state=site['buildings'][0 if variant=='base' else -1]
            if state: canvas.alpha_composite(layers[state])
        save(REPORT/(variant+'-native.png'),canvas)
    masks = {s:im.getchannel('A').point(lambda a:255 if a>=128 else 0) for s,im in layers.items()}
    sites = {r['state']:r['site'] for r in old['states']}
    overlap=[]
    names=sorted(layers)
    for i,a in enumerate(names):
        for b in names[i+1:]:
            if sites[a] != sites[b]:
                pixels=sum(ImageChops.multiply(masks[a],masks[b]).histogram()[128:])
                if pixels:overlap.append({'states':[a,b],'pixels':pixels})
    write(REPORT/'preview-geometry.json',{'overlap':overlap,'rectangles':RECTS})
    print(json.dumps({'overlaps':overlap,'report':str(REPORT)}))
    return old, layers

def build():
    """Prepare canonical candidate recipes and replay the actual converter twice."""
    sys.path.insert(0,str(ROOT.parent/'scripts'))
    sys.path.insert(0,str(ROOT/'scripts'))
    import faction_artifacts as converter
    import zaun_coastal_state_v1 as coastal
    old,layers=preview()
    sites=copy.deepcopy(old['sites'])
    rows=[];bindings=[];recipes=[]
    oldby={r['state']:r for r in old['states']}
    for site in sites:
        rect=RECTS[site['id']]
        site['composition_rectangle']=rect
        site['native_z']=rect[1]+rect[3]
        site['source_states']={}
        for state in site['buildings']:
            row=copy.deepcopy(oldby[state])
            folder=HERE/'structures'/state
            surfaces=coastal.surfaces(layers[state])
            for kind,im in surfaces.items():save(folder/(kind+'.png'),im)
            if state=='ship':
                _,entries=inputs()
                save(folder/'boat-only.png',fit(entries[state]['image'],[738,330,58,38]))
            row.update(composition_rectangle=rect,native_z=site['native_z'],native_layer=rel(folder/'layer.png'),
                       native_layer_sha256=sha(folder/'layer.png'),click_bbox=surfaces['area'].getchannel('A').getbbox(),
                       click_pixels=sum(surfaces['area'].getchannel('A').histogram()[128:]),
                       visual_approval_granted=False)
            rows.append(row);site['source_states'][state]=row
            for kind in ['animation','area','border','construction']:
                active=f'assets/recipes/town/construction/{state}.json' if kind=='construction' else f'assets/recipes/town/structures/{state}-{kind}.json'
                recipe=load(ROOT/active)
                src=folder/('layer.png' if kind=='animation' else kind+'.png')
                recipe['source_sha256']=sha(src)
                recipe['visual_approval_granted']=False
                recipe['native_visual_review']='pending'
                recipe['identity_review']=rel(REPORT/'source-pixel-review.json')
                recipe['dependencies']=[d for d in recipe.get('dependencies',[]) if d['path']!=rel(HERE/'prepare.py')]
                recipe['dependencies'].append({'path':rel(HERE/'prepare.py'),'sha256':sha(HERE/'prepare.py')})
                recipe['generation']['conversion']={'method':'Existing genuine painted source, uniform contain and full-canvas placement; alpha-derived masks. No new painting or camera projection.',
                    'revision':HERE.name,'source_crop':row['source_crop'],'composition_rectangle':rect,'native_z':site['native_z'],
                    'depth_direction':'Larger apparent foreground framing; smaller distant monuments; staggered connected dry terraces.'}
                if state=='ship':
                    recipe['generation']['technical_assembly']={'method':'Native Zaun ship replaces shipyard; exact new dock plus original painted boat',
                        'contains_base_shipyard':True,'dock_source':rel(HERE/'structures/shipyard/layer.png'),
                        'dock_sha256':sha(HERE/'structures/shipyard/layer.png'),'boat_source':rel(folder/'boat-only.png'),'boat_sha256':sha(folder/'boat-only.png')}
                    recipe['dependencies']=[d for d in recipe['dependencies'] if not d['path'].endswith('/structures/shipyard/layer.png')]
                    recipe['dependencies'].append({'path':rel(HERE/'structures/shipyard/layer.png'),'sha256':sha(HERE/'structures/shipyard/layer.png')})
                if kind=='animation':
                    recipe['groups'][0]['frames']=[{'source':rel(src),'sha256':sha(src)}]
                    recipe['building_contract']['full_canvas_placement']={'x':0,'y':0,'z':site['native_z']}
                    recipe['building_contract']['native_ground_contact']=rect
                else:
                    recipe['source']=rel(src)
                target=HERE/'recipes'/Path(active).relative_to('assets/recipes')
                write(target,recipe);recipes.append(target)
                bindings.append({'active':active,'candidate':rel(target),'sha256':sha(target)})
    data={'status':'authored configuration','revision':HERE.name,'siteCount':20,'stateCount':36,'canvas':[800,374],
          'sites':sites,'states':rows,'terrain':old['terrain'],'recipe_bindings':bindings,
          'coast_semantics':old['coast_semantics'],'visual_approval_granted':False,'runtime_verified':False,'release_accepted':False}
    outputs=[]
    for run in (1,2):
        scratch=REPORT/f'compiler-run-{run}/runeterra-zaun'
        inventory={};receipts=[];construction={}
        for recipepath in recipes:
            recipe=load(recipepath)
            recipe_dest=scratch/'assets/recipes'/recipepath.relative_to(HERE/'recipes')
            recipe_dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(recipepath,recipe_dest)
            source=recipe.get('source') or recipe['groups'][0]['frames'][0]['source']
            dest=scratch/source;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/source,dest)
            receipt=converter.CONVERTERS[recipe['recipe_type']](scratch,recipe,'Content/Sprites/runeterra/zaun/',False,{},check=False)
            receipts.append(receipt)
            if '/construction/' in rel(recipepath):construction[recipe['building']]=receipt['sha256']
        index=load(ROOT/'assets/recipes/town/buildingIcons.json')
        for frame in index['frames']:
            frame['sha256']=construction[frame['building']]
            frame['producer_sha256']=sha(HERE/'recipes/town/construction'/f"{frame['building']}.json")
        index['identity_review']=rel(REPORT/'source-pixel-review.json')
        indexpath=HERE/'recipes/town/buildingIcons.json';write(indexpath,index)
        receipts.append(converter.convert_indexed(scratch,index,'Content/Sprites/runeterra/zaun/',False,{},check=False))
        for path in sorted((scratch/'assets/generated').rglob('*')):
            if path.is_file():inventory[path.relative_to(scratch/'assets/generated').as_posix()]=sha(path)
        outputs.append(inventory);write(REPORT/f'compiler-run-{run}-receipts.json',receipts)
    bindings.append({'active':'assets/recipes/town/buildingIcons.json','candidate':rel(indexpath),'sha256':sha(indexpath)})
    write(HERE/'layout.json',data)
    write(HERE/'selection.json',{'status':'authored configuration','revision':HERE.name,
          'candidate_design':rel(HERE/'layout.json'),'candidate_design_sha256':sha(HERE/'layout.json'),
          'technical_helper':rel(HERE/'prepare.py'),'technical_helper_sha256':sha(HERE/'prepare.py'),
          'previous_selection':rel(OLD/'selection.json'),'previous_selection_sha256':sha(OLD/'selection.json'),
          'artistic_change':'Existing genuine painted masters and terrain retained; only technical uniform scale and composition changed.',
          'visual_approval_granted':False,'runtime_verified':False,'release_accepted':False})
    write(REPORT/'compiler-determinism.json',{'ok':outputs[0]==outputs[1],'recipe_count':len(bindings),'physical_outputs':len(outputs[0]),'outputs':outputs[0],
          'converter':'scripts/faction_artifacts.py existing DELIVERED converter','runs':2,'byte_identical':outputs[0]==outputs[1]})
    if outputs[0]!=outputs[1]:raise ValueError('Candidate conversion is not deterministic')
    return data

if __name__=='__main__':
    build() if '--build' in sys.argv else preview()
