"""BC1 completion: deterministic registration of genuinely painted states.

Candidate source producer only. No canonical content/manifest/stage is changed.
"""
from pathlib import Path
import hashlib, io, json, sys
import numpy as np
from PIL import Image, ImageChops, ImageFilter

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
WORKSPACE=PROJECT.parent
OLD=SOURCE.parent/'approved-BC1-20261029-v1'
REPORT=WORKSPACE/'reports/bandle-BC1-completion-20261030-v2'
sys.path.insert(0,str(WORKSPACE/'scripts'))
from faction_art_compile import create_compiler

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def encoded(value):return (json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
def write(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() and path.read_bytes()!=raw:raise ValueError('Immutable candidate differs: '+str(path))
    if not path.exists():path.write_bytes(raw)
def png(image):
    out=io.BytesIO();image.save(out,format='PNG');return out.getvalue()
def read(path):return json.loads(Path(path).read_bytes())

# Painted asset bounds and exact doorway thresholds measured on raw atlases.
CIVIC=[
 ('villageHall',(0,0,365,500),(205,462),(.58,.55)),
 ('townHall',(365,0,775,500),(526,461),(.70,.65)),
 ('cityHall',(775,0,1180,500),(955,462),(.86,.80)),
 ('fort',(1180,0,1536,500),(1336,460),(.82,.67)),
 ('citadel',(0,500,455,1024),(232,947),(.95,.82)),
 ('mageGuild1',(455,500,790,1024),(636,940),(.65,.54)),
 ('mageGuild2',(790,500,1140,1024),(994,940),(.82,.80)),
 ('tavern',(1140,500,1536,1024),(1365,943),(.72,.83)),
]
DWELLINGS=[
 ('blacksmith',(0,0,418,520),(215,473),(.82,.83)),
 ('dwellingLvl1',(418,0,790,520),(611,478),(.84,.85)),
 ('dwellingLvl2',(790,0,1135,520),(962,476),(.86,.86)),
 ('dwellingLvl3',(1135,0,1536,520),(1310,466),(.86,.87)),
 ('dwellingLvl4',(0,520,406,1024),(222,904),(.86,.87)),
 ('dwellingLvl5',(406,520,760,1024),(596,903),(.83,.88)),
 ('dwellingLvl6',(760,520,1135,1024),(967,900),(.85,.84)),
 ('dwellingLvl7',(1135,520,1536,1024),(1270,904),(.85,.87)),
]

def clean(image):
    """Remove generation matte noise and make painted architecture opaque."""
    arr=np.array(image.convert('RGBA'));alpha=arr[:,:,3]
    alpha[alpha<=16]=0;alpha[alpha>=192]=255
    arr[:,:,3]=alpha;arr[alpha==0,:3]=0
    return Image.fromarray(arr)

def registered(raw,box,door,target,target_size):
    cell=clean(raw.crop(box));bounds=cell.getbbox()
    if not bounds:raise ValueError('Empty painted source')
    # Source sheet edges must not clip substantial painted architecture.
    opaque=cell.getchannel('A').point(lambda x:255 if x>=192 else 0)
    ob=opaque.getbbox()
    if ob[0]==0 or ob[1]==0 or ob[2]==cell.width or ob[3]==cell.height:
        raise ValueError('Painted body touches assigned extraction boundary '+str(box))
    cut=cell.crop(bounds);scale=min(target_size[0]/cut.width,target_size[1]/cut.height)
    im=cut.resize((round(cut.width*scale),round(cut.height*scale)),Image.Resampling.LANCZOS)
    # Reassert only almost-opaque interiors after antialias downsampling.
    im=clean(im)
    root=((door[0]-box[0]-bounds[0])*scale,(door[1]-box[1]-bounds[1])*scale)
    loc=(round(target[0]-root[0]),round(target[1]-root[1]))
    if loc[0]<0 or loc[1]<0 or loc[0]+im.width>800 or loc[1]+im.height>374:
        raise ValueError('Registered state escapes native scene')
    native=Image.new('RGBA',(800,374));native.alpha_composite(im,loc)
    return native,{'sheet_crop':list(box),'painted_bounds':list(bounds),'source_door':list(door),
                   'scale':scale,'target_door':list(target),'location':list(loc),'size':list(im.size)}

def recipe(path,output,*,animation=False,canvas=(800,374),master=None):
    rel=path.relative_to(PROJECT).as_posix()
    value={'recipe_type':'vcmi_animation' if animation else 'raster','production_status':'painted-master-complete-unapproved',
      'canvas':list(canvas),'output_path':'Content/Sprites/runeterra/bandlecity/town/'+output,
      'status':'authored configuration','visual_approval_granted':False,
      'acceptance':'Approved BC1 full composition; individual construction/hit/native review remains separate.',
      'credits':{'author':'Project-directed OpenAI built-in imagegen; deterministic painted sprite registration','license':None,'redistribution':'unresolved'},
      'generation':{'image_generation_used':True,'provider':'OpenAI built-in imagegen','model':'not exposed by tool',
       'painted_master':(master or path).relative_to(PROJECT).as_posix(),'painted_master_sha256':sha(master or path),
       'prompt':'Approved BC1 complete-town reference; original painted simpler timber/teal/gold predecessor buildings in isolated atlas cells with visible front doors and transparent alpha; deterministic registration only.',
       'technical_producer':Path(__file__).relative_to(WORKSPACE).as_posix(),
       'method':'Exact approved final pixels; painted earlier-state atlas; technical alpha cleanup, uniform scale and fixed threshold registration only; no 3D'},}
    frame={'source':rel,'source_sha256':sha(path),'source_canvas':list(canvas)}
    if animation:value.update(pivot={'x':0,'y':0},generateOverlay=0,generateShadow=0,groups=[{'group':0,'frames':[frame]}])
    else:value.update(frame,fit='exact')
    return value

def main():
    plan=read(OLD/'decomposition-plan.json');sites=plan['sites']
    contract=read(PROJECT/'design/town-visuals.json')['sites']
    by_state=({state:data['id'] for data in contract for state in data['states']} if isinstance(contract,list)
              else {state:site for site,data in contract.items() for state in data['keys']})
    by_site={s['site']:s for s in sites};layers={};registration={}
    # The exact visible approved maxima are preserved at their original positions.
    for site in sites:
        state=site['extracted_state'];layers[state]=Image.open(OLD/'sites'/site['site']/'maximum-state.png').convert('RGBA')
        registration[state]={'approved_visible_maximum':True,'door':site['door']}
    for filename,rows in [('civic-states-v1.png',CIVIC),('dwelling-states-v1.png',DWELLINGS)]:
        raw=Image.open(SOURCE/filename).convert('RGBA')
        for state,box,door,fraction in rows:
            site=by_site[by_state[state]];maximum=layers[site['extracted_state']]
            b=maximum.getbbox();size=((b[2]-b[0])*fraction[0],(b[3]-b[1])*fraction[1])
            layers[state],registration[state]=registered(raw,box,door,site['door'],size)
            registration[state]['painted_master']=filename
    optional=Image.open(SOURCE/'optional-sites-v1.png').convert('RGBA')
    for state,box,door,target,size in [
      ('shipyard',(0,0,1130,724),(715,485),(776,354),(48,42)),
      ('ship',(1130,0,1700,724),(1428,611),(786,360),(13,16)),
      ('grail',(1700,0,2172,724),(1937,676),(325,294),(26,55))]:
        layers[state],registration[state]=registered(optional,box,door,target,size)
        registration[state]['painted_master']='optional-sites-v1.png'
    recipes=[];compiler=create_compiler('bandlecity');runtime={}
    background=SOURCE/'background-v2.png';write(background,(OLD/'background.png').read_bytes())
    recipes.append(('background',recipe(background,'background.png',master=OLD/'empty-provider-v1.png')))
    structure_patch={};state_records={}
    # Stable approved occlusion order: thresholds define background-to-front depth.
    order={s['site']:i for i,s in enumerate(sorted(sites,key=lambda s:(s['door'][1],s['door'][0])))}
    for state,image in layers.items():
        folder=SOURCE/'states-v2'/state;layer=folder/'layer.png';write(layer,png(image))
        mask=image.getchannel('A').point(lambda a:255 if a>=192 else 0)
        area=Image.new('RGBA',(800,374),(255,255,255,0));area.putalpha(mask);write(folder/'area.png',png(area))
        ring=ImageChops.subtract(mask.filter(ImageFilter.MaxFilter(3)),mask)
        border=Image.new('RGBA',(800,374),(255,223,96,0));border.putalpha(ring);write(folder/'border.png',png(border))
        cut=image.crop(image.getbbox());cut.thumbnail((144,64),Image.Resampling.LANCZOS)
        icon=Image.new('RGBA',(150,70));icon.alpha_composite(cut,((150-cut.width)//2,(70-cut.height)//2));write(folder/'hall.png',png(icon))
        master=SOURCE/registration[state]['painted_master'] if 'painted_master' in registration[state] else OLD/'approved-native.png'
        for role,source,out,anim,canvas in [('animation',layer,state+'.json',True,(800,374)),
          ('area',folder/'area.png',state+'_area.png',False,(800,374)),
          ('border',folder/'border.png',state+'_border.png',False,(800,374)),
          ('campaign',folder/'hall.png',state+'_campaign.png',False,(150,70))]:
            recipes.append((state+'-'+role,recipe(source,'structures/'+out,animation=anim,canvas=canvas,master=master)))
        site=by_state[state];z=20+order[site] if site in order else 18 if state=='shipyard' else 19 if state=='ship' else 60
        structure_patch[state]={'x':0,'y':0,'z':z}
        state_records[state]={'site':site,'bounds':list(image.getbbox()),'opaque_pixels':mask.histogram()[255],
            'layer':layer.relative_to(PROJECT).as_posix(),'sha256':sha(layer),'registration':registration[state]}
    for name,value in recipes:
        path=SOURCE/'recipes-v3'/f'{name}.json';write(path,encoded(value));outputs,receipt=compiler.plan(PROJECT,path)
        for output,raw in outputs.items():
            if output in runtime and runtime[output]!=hashlib.sha256(raw).hexdigest():raise ValueError('Duplicate output')
            runtime[output]=hashlib.sha256(raw).hexdigest();write(REPORT/'runtime'/output,raw)
    native=Image.open(OLD/'approved-native.png').convert('RGBA');full=Image.open(background).convert('RGBA')
    for site in sorted(sites,key=lambda s:(s['door'][1],s['door'][0])):full.alpha_composite(layers[site['extracted_state']])
    if ImageChops.difference(full,native).getbbox() is not None:raise ValueError('Approved full pixels changed')
    write(REPORT/'fully-built.png',png(full));write(REPORT/'empty.png',background.read_bytes())
    for title,selection in [('early',['villageHall','fort','mageGuild1','tavern','blacksmith','marketplace','dwellingLvl1','dwellingLvl2']),
                            ('base',[s for s in layers if s not in ('grail','shipyard','ship') and not s.startswith('dwellingUp') and s not in ('townHall','cityHall','capitol','citadel','castle','mageGuild2','mageGuild3','special3','resourceSilo')]),
                            ('coast-full',[s['extracted_state'] for s in sites]+['shipyard','ship']),
                            ('grail-full',[s['extracted_state'] for s in sites]+['grail'])]:
        canvas=Image.open(background).convert('RGBA')
        for state in sorted(selection,key=lambda s:structure_patch[s]['z']):canvas.alpha_composite(layers[state])
        write(REPORT/(title+'.png'),png(canvas))
    write(REPORT/'structure-position-patch.json',encoded(structure_patch))
    write(REPORT/'states.json',encoded(state_records))
    write(REPORT/'runtime-inventory.json',encoded(runtime))
    write(REPORT/'candidate.json',encoded({'status':'authored configuration','selected':False,'runtime_verified':False,
      'approved_fully_built_pixel_difference':0,'states':len(layers),'recipes':len(recipes),'runtime_files':len(runtime),
      'source':SOURCE.relative_to(PROJECT).as_posix(),'mandatory_land_sites':16,'optional_coast_sites':1,
      'notes':['Guild is left tower of civic cluster; fortification is separate right timber wardhouse. Shared visual terrace is intentional.',
       'Optional dock includes its own foreground water inlet and shoreline; only enabled for coastal town. Grail is separate path lantern.',
       'Maximum-state clipped faces remain the approved visible composition; individual absent-neighbor native review still required.']}))
    print(json.dumps({'states':len(layers),'recipes':len(recipes),'runtime_files':len(runtime),'full_pixel_difference':0}))
if __name__=='__main__':main()
