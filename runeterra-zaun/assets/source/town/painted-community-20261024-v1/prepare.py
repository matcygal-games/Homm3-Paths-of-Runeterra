"""Review-only Zaun town source candidate using existing painted/convert helpers.

No active content, recipes, manifests, generated assets or stage is written.
"""
from pathlib import Path
import hashlib,json,sys,shutil
from PIL import Image,ImageOps,ImageChops,ImageFilter,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
REPORT=ROOT/'build/reports/painted-town-community-20261024-v1'
DESIGN=ROOT/'design/town-visuals-painted-community-20261024-v1.candidate.json'
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT.parent/'scripts'))
import zaun_painted_town as painted
import zaun_coastal_state_v1 as coastal
import faction_artifacts as converter
PREFIX='Content/Sprites/runeterra/zaun/'
RECTS={
 'foundryHall':[164,4,151,122], 'sumpRampart':[3,4,151,114],
 'shimmerInstitute':[324,0,112,157], 'dwellingThug':[4,247,115,94],
 'dwellingRavager':[128,233,111,94], 'dwellingConstruct':[485,286,108,83],
 'dwellingEnforcer':[7,125,113,91], 'dwellingAgent':[699,158,98,89],
 'dwellingVeteran':[565,153,125,103], 'dwellingPredator':[605,0,186,146],
 'grog':[246,268,108,84], 'scrapExchange':[363,286,111,71],
 'ammoFoundry':[596,265,104,65], 'shimmerFactory':[455,84,105,95],
 'shipyard':[712,278,88,96], 'codeOfProgress':[365,252,47,30],
 'augmentationWorkshop':[129,133,113,82], 'augmentationClinic':[251,164,100,70],
 'theSump':[354,167,84,83], 'fightingPit':[442,190,113,88],
}
NEW=['dwellingLvl2','dwellingUpLvl2','dwellingLvl6','dwellingUpLvl6','dwellingLvl7','dwellingUpLvl7']
NAMES={'dwellingLvl2':'Chem-Jack Yard','dwellingUpLvl2':'Reinforced Chem-Jack Yard','dwellingLvl6':'Sump Reclaimer Depot','dwellingUpLvl6':'Hydraulic Reclaimer Depot','dwellingLvl7':'Chem-Golem Foundry','dwellingUpLvl7':'Pressure Colossus Foundry'}
WATER=[[618,373],[650,360],[681,347],[713,329],[748,305],[778,275],[799,252],[799,373]]
FLOOR=[[0,48],[150,69],[300,94],[430,112],[510,135],[570,115],[660,100],[799,88],
 [799,250],[777,273],[746,303],[711,327],[679,345],[648,358],[616,373],[0,373]]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()
def write(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.convert('RGBA').save(p,compress_level=9,optimize=False)
def count(im):return sum(im.histogram()[128:])
def mask(im):return im.getchannel('A').point(lambda p:255 if p>=128 else 0)
def fit(image,rect):
 x,y,w,h=rect;fitted=ImageOps.contain(image,(w-4,h-4),Image.Resampling.LANCZOS)
 out=Image.new('RGBA',(800,374));out.alpha_composite(fitted,(x+(w-fitted.width)//2,y+h-2-fitted.height));return out
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def preflight(pins=None):
 seal=HERE/'preflight-selection.json'
 if pins is None:
  if not seal.is_file():return
  pins=load(seal)['inputs']
 for name,expected in pins.items():
  p=ROOT/name
  if not p.is_file() or sha(p)!=expected:raise ValueError('Sealed candidate input changed before any writes: '+name)

def source_plan():
 preflight()
 old=load(ROOT/'assets/source/town/chemtech-v4-buildings/selection.json')
 by={r['building']:r for r in old['states']};design=load(ROOT/'design/town-visuals.json')
 states={s for site in design['sites'] for s in site['buildings']}
 if states!=set(by) or len(states)!=36 or len(design['sites'])!=20:raise ValueError('Current20site/36state contract changed')
 entries={}
 for state in sorted(states):
  if state in NEW:
   master=HERE/state/'master.png';generation=HERE/state/'generation.json';im=Image.open(master).convert('RGBA')
   b=im.getchannel('A').point(lambda p:255 if p>=8 else 0).getbbox()
   crop=[max(0,b[0]-8),max(0,b[1]-8),min(im.width,b[2]+8),min(im.height,b[3]+8)]
   entry={'building':state,'master':rel(master),'master_sha256':sha(master),'crop':crop,'provenance':rel(generation)}
  else:entry=dict(by[state])
  # Existing own helper performs the exact selected-master pin check before reads.
  im=painted.selected_image(entry)
  provenance=load(ROOT/entry['provenance'])
  entries[state]={'entry':entry,'image':im.crop(tuple(entry['crop'])),'generation':provenance}
 terrain=HERE/'background/master-v3.png';native=HERE/'background/native-v3.png'
 if not terrain.is_file() or not native.is_file():raise ValueError('New selected empty terrain missing')
 return design,entries
def build():
 design,entries=source_plan();REPORT.mkdir(parents=True,exist_ok=True)
 terrain=Image.open(HERE/'background/native-v3.png').convert('RGBA');layers={};rows=[];sites=[];recipes=[];bindings=[]
 water=Image.new('L',(800,374));ImageDraw.Draw(water).polygon([tuple(p) for p in WATER],fill=255)
 floor=Image.new('L',(800,374));ImageDraw.Draw(floor).polygon([tuple(p) for p in FLOOR],fill=255)
 save(HERE/'background/water-annotation.png',water);save(HERE/'background/buildable-floor-annotation.png',floor)
 for site in design['sites']:
  site=dict(site);rect=RECTS[site['id']];site['composition_rectangle']=rect;site['native_z']=rect[1]+rect[3];site['source_states']={}
  if site['id']=='dwellingRavager':site.update({'name':'Chem-Jack Yard','visual':'Living protected industrial workers; practical tools and pressure-assisted reinforced yard upgrade.'})
  if site['id']=='dwellingVeteran':site.update({'name':'Sump Reclaimer Depot','visual':'Living salvage workers; extended hydraulic clamp and reinforced gantry upgrade.'})
  if site['id']=='dwellingPredator':site.update({'name':'Chem-Golem Foundry','visual':'Unmanned industrial golem casting institution; rear multi-storey pressure foundry landmark.'})
  for state in site['buildings']:
   data=entries[state];entry=data['entry'];layer=fit(data['image'],rect)
   if state=='ship':
    # Native ship replaces its shipyard family. Preserve a complete dock.
    boat=fit(data['image'],[738,330,58,38]);save(HERE/'structures/ship/boat-only.png',boat)
    layer=coastal.assemble(layers['shipyard'],boat)
   layers[state]=layer
   surfaces=coastal.surfaces(layer);out=HERE/'structures'/state
   for name,im in surfaces.items():save(out/(name+'.png'),im)
   # Optional native58x64 campaign icon source; no unsolicited consumer/producer activation.
   crop=layer.crop(layer.getchannel('A').getbbox());icon=ImageOps.contain(crop,(54,60),Image.Resampling.LANCZOS)
   campaign=Image.new('RGBA',(58,64));campaign.alpha_composite(icon,((58-icon.width)//2,(64-icon.height)//2));save(out/'campaign.png',campaign)
   own=mask(layer);bb=own.getbbox();foot=own.copy();foot.paste(0,(0,0,800,max(0,bb[3]-8)))
   wet=count(ImageChops.multiply(foot,water));unsupported=count(ImageChops.multiply(foot,ImageChops.invert(floor)))
   row={'state':state,'site':site['id'],'composition_rectangle':rect,'native_z':site['native_z'],
    'master':entry['master'],'master_sha256':entry['master_sha256'],'source_crop':entry['crop'],'provenance':entry['provenance'],
    'native_layer':rel(out/'layer.png'),'native_layer_sha256':sha(out/'layer.png'),'click_bbox':bb,'click_pixels':count(own),
    'footing_water_pixels':wet,'footing_outside_buildable_floor_pixels':unsupported,'visual_approval_granted':False}
   rows.append(row);site['source_states'][state]=row
   gen=dict(data['generation']);gen.update({'image_generation_used':True,'painted_master':entry['master'],'painted_master_sha256':entry['master_sha256'],
    'provider':gen.get('provider','OpenAI built-in imagegen'),'model':gen.get('model'),
    'prompt':gen.get('prompt','See exact pinned source provenance'),
    'conversion':{'method':'Original painted2D source crop; uniform contain; full800x374 placement; native alpha-derived area/one-pixel outward border',
      'source_crop':entry['crop'],'composition_rectangle':rect,'native_z':site['native_z'],'revision':HERE.name}})
   if state=='ship':gen['technical_assembly']={'method':'Existing native Zaun dock+boat family replacement helper','contains_base_shipyard':True,'dock_source':rel(HERE/'structures/shipyard/layer.png'),'dock_sha256':sha(HERE/'structures/shipyard/layer.png'),'boat_source':rel(out/'boat-only.png'),'boat_sha256':sha(out/'boat-only.png')}
   deps=[{'path':entry['master'],'sha256':entry['master_sha256']},{'path':entry['provenance'],'sha256':sha(ROOT/entry['provenance'])},{'path':rel(HERE/'prepare.py'),'sha256':sha(HERE/'prepare.py')},{'path':'scripts/zaun_coastal_state_v1.py','sha256':sha(ROOT/'scripts/zaun_coastal_state_v1.py')}]
   if state=='ship':deps.append({'path':rel(HERE/'structures/shipyard/layer.png'),'sha256':sha(HERE/'structures/shipyard/layer.png')})
   for kind in ['animation','area','border']:
    active=f'assets/recipes/town/structures/{state}-{kind}.json';recipe=load(ROOT/active)
    if state in NAMES:recipe['title']=NAMES[state]+' town '+kind
    source=out/('layer.png' if kind=='animation' else kind+'.png');recipe.update({'source_sha256':sha(source),'generation':gen,'dependencies':deps,'visual_approval_granted':False,'native_visual_review':'pending','identity_review':rel(REPORT/'source-pixel-review.json')})
    if kind=='animation':
     if state in NAMES:recipe['building_contract']['name']=NAMES[state];recipe['title']=NAMES[state]+' town layer'
     recipe['groups'][0]['frames']=[{'source':rel(source),'sha256':sha(source)}]
     recipe['building_contract']['full_canvas_placement']={'x':0,'y':0,'z':site['native_z']}
     recipe['building_contract']['native_ground_contact']=rect
    else:recipe.update({'source':rel(source),'size':[800,374],'canvas':[800,374],'content_box':[0,0,800,374],'fit':'contain'})
    target=HERE/'recipes/town/structures'/f'{state}-{kind}.json';write(target,recipe);recipes.append(target);bindings.append({'candidate':rel(target),'active':active,'sha256':sha(target)})
   active=f'assets/recipes/town/construction/{state}.json';recipe=load(ROOT/active);source=out/'construction.png'
   if state in NAMES:recipe['title']=NAMES[state]+' construction icon'
   recipe.update({'source':rel(source),'source_sha256':sha(source),'size':[150,70],'canvas':[150,70],'content_box':[0,0,150,70],'fit':'contain','generation':gen,'dependencies':deps,'identity_review':rel(REPORT/'source-pixel-review.json')})
   target=HERE/'recipes/town/construction'/f'{state}.json';write(target,recipe);recipes.append(target);bindings.append({'candidate':rel(target),'active':active,'sha256':sha(target)})
   optional=dict(recipe);optional.update({'id':'zaun.town.optionalCampaign.'+state,'output_path':PREFIX+'town/structures/'+state+'_campaign.png','source':rel(out/'campaign.png'),'source_sha256':sha(out/'campaign.png'),'size':[58,64],'canvas':[58,64],'content_box':[0,0,58,64],'optional_unselected':True})
   write(HERE/'optional-campaign-recipes'/f'{state}.json',optional)
  sites.append(site)
 bg=load(ROOT/'assets/recipes/town/background.json');native=HERE/'background/native-v3.png'
 bg.update({'source':rel(native),'source_sha256':sha(native),'size':[800,374],'canvas':[800,374],'fit':'contain','content_box':[0,0,800,374],
  'generation':load(HERE/'background/generation-v3.json'),'dependencies':[{'path':rel(HERE/'background'/p),'sha256':sha(HERE/'background'/p)} for p in ['master-v3.png','generation-v3.json','prompt-v3.txt','site-keep-clear-guide.png']],'identity_review':rel(REPORT/'source-pixel-review.json')})
 target=HERE/'recipes/town/background.json';write(target,bg);recipes.append(target);bindings.append({'candidate':rel(target),'active':'assets/recipes/town/background.json','sha256':sha(target)})
 # All converters run against a minimal report-only scratch project. This is
 # the existing DELIVERED Zaun converter, not the different COMPLETE protocol.
 outputs=[];receipts=[];construction_outputs={}
 for run in range(2):
  scratch=REPORT/f'compiler-run-{run+1}/runeterra-zaun';(scratch/'assets/source').mkdir(parents=True,exist_ok=True)
  for path in recipes:
   data=load(path);source=ROOT/data['source'] if 'source' in data else ROOT/data['groups'][0]['frames'][0]['source']
   dst=scratch/source.relative_to(ROOT);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dst)
   active=next(b['active'] for b in bindings if b['candidate']==rel(path));dst=scratch/active;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(path.read_bytes())
  runreceipts=[]
  for path in recipes:
   data=load(path);receipt=converter.CONVERTERS[data['recipe_type']](scratch,data,PREFIX,False,{},check=False);runreceipts.append({'recipe':rel(path),'recipe_sha256':sha(path),'receipt':receipt})
   if '/construction/' in rel(path):construction_outputs[data['building']]=receipt['sha256']
  index=load(ROOT/'assets/recipes/town/buildingIcons.json')
  for frame in index['frames']:
   state=frame['building'];producer=f'assets/recipes/town/construction/{state}.json'
   frame.update({'sha256':construction_outputs[state],'producer_sha256':sha(scratch/producer)})
  index.update({'dependencies':[],'source_sha256':sha(HERE/'background/master-v3.png'),
   'generation':{'image_generation_used':True,'provider':'OpenAI built-in imagegen','model':None,'painted_master':rel(HERE/'background/master-v3.png'),'prompt':'Native-indexed assembly of36 separately pinned own painted2D building icons; see exact candidate state provenance'},'identity_review':rel(REPORT/'source-pixel-review.json')})
  indexpath=HERE/'recipes/town/buildingIcons.json';write(indexpath,index)
  receipt=converter.convert_indexed(scratch,index,PREFIX,False,{},check=False);runreceipts.append({'recipe':rel(indexpath),'recipe_sha256':sha(indexpath),'receipt':receipt})
  inventory={relpath.relative_to(scratch/'assets/generated').as_posix():sha(relpath) for relpath in sorted((scratch/'assets/generated').rglob('*')) if relpath.is_file()}
  outputs.append(inventory);receipts.append(runreceipts);write(REPORT/f'compiler-run-{run+1}-receipts.json',runreceipts)
 recipes.append(indexpath);bindings.append({'candidate':rel(indexpath),'active':'assets/recipes/town/buildingIcons.json','sha256':sha(indexpath)})
 # Every composite uses one native base-family member. Ship already includes dock.
 for variant in ['base','upgraded','coastal','moored','grail']:
  canvas=terrain.copy();selected=[]
  for site in sorted(sites,key=lambda s:s['native_z']):
   if site['id']=='shipyard':state='ship' if variant in ['moored','grail'] else 'shipyard' if variant=='coastal' else None
   elif site['id']=='codeOfProgress':state='grail' if variant=='grail' else None
   else:state=site['buildings'][0 if variant=='base' else -1]
   if state:canvas.alpha_composite(layers[state]);selected.append(state)
  save(REPORT/f'{variant}-native.png',canvas)
 annotated=Image.open(REPORT/'grail-native.png').convert('RGBA');draw=ImageDraw.Draw(annotated)
 for site in sites:
  x,y,w,h=site['composition_rectangle'];draw.rectangle((x,y,x+w-1,y+h-1),outline=(240,195,60,255));draw.text((x+1,y+1),site['id'],fill='white',stroke_width=1,stroke_fill='black')
 draw.line([tuple(p) for p in WATER],fill=(60,190,240,255));draw.line([tuple(p) for p in FLOOR[:8]],fill=(250,130,40,255));save(REPORT/'annotated-sites-native.png',annotated)
 old=Image.open(ROOT/'assets/reviews/town/chemtech-v5-organic/partial-native-composition.png').convert('RGBA')
 board=Image.new('RGBA',(800,784),(35,32,29,255));board.alpha_composite(old,(0,14));board.alpha_composite(Image.open(REPORT/'grail-native.png').convert('RGBA'),(0,410));d=ImageDraw.Draw(board);d.text((2,0),'Previously selected native composition',fill='white');d.text((2,394),'Candidate native800x374 separate states',fill='white');save(REPORT/'before-after-native.png',board)
 sheet=Image.new('RGBA',(1200,6*160),(43,40,35,255));d=ImageDraw.Draw(sheet)
 for i,row in enumerate(rows):
  im=layers[row['state']];im=im.crop(im.getchannel('A').getbbox());im=ImageOps.contain(im,(194,132),Image.Resampling.LANCZOS);x=(i%6)*200;y=(i//6)*160;sheet.alpha_composite(im,(x+(200-im.width)//2,y));d.text((x+2,y+137),row['state'],fill='white')
 save(REPORT/'all36-state-contact.png',sheet)
 proposal={'status':'authored configuration','revision':HERE.name,'siteCount':20,'stateCount':36,'canvas':[800,374],
  'sites':sites,'states':rows,'terrain':{'master':rel(HERE/'background/master-v3.png'),'master_sha256':sha(HERE/'background/master-v3.png'),'native':rel(native),'native_sha256':sha(native),'water_polygon':WATER,'buildable_floor_polygon':FLOOR},
  'recipe_bindings':bindings,'optional_campaign_recipes':'36source58x64icons and recipes prepared but not activated; current Zaun has no campaignBonus fields',
  'coast_semantics':'ship is the native replacement of shipyard and contains dock+boat; hidden click remaps to Shipyard; same z',
  'visual_approval_granted':False,'runtime_verified':False,'release_accepted':False}
 write(DESIGN,proposal);write(HERE/'coordinator-handoff.json',proposal)
 write(REPORT/'compiler-determinism.json',{'ok':outputs[0]==outputs[1],'actual_converter':'scripts/faction_artifacts.py existing Zaun DELIVERED converter',
  'runs':2,'recipe_count':len(recipes),'output_count':len(outputs[0]),'outputs':outputs[0],'byte_identical':outputs[0]==outputs[1],
  'active_generated_or_stage_written':False,'visual_approval_granted':False})
 print(json.dumps({'candidate_states':len(rows),'sites':len(sites),'recipes':len(recipes),'physical_outputs':len(outputs[0]),'deterministic':outputs[0]==outputs[1]}))
 return 0 if outputs[0]==outputs[1] else 2
if __name__=='__main__':raise SystemExit(build())
