"""Reproducible NX1 completion. Writes only this versioned source/report cohort."""
from pathlib import Path
from copy import deepcopy
import hashlib,html,importlib.util,json,sys
from PIL import Image,ImageChops,ImageDraw,ImageFilter,ImageOps
from finish_plan import HERE,PRIOR,SIZE,SITES,ROUTES,COAST

ROOT=HERE.parents[3];WORKSPACE=ROOT.parent
REPORT=ROOT/'build/reports/approved-nx1-finish-20261030-v1'
CANDIDATE=HERE/'candidate'
spec=importlib.util.spec_from_file_location('nx1_prior_derivation',PRIOR/'derive_candidate.py')
old=importlib.util.module_from_spec(spec);sys.path.insert(0,str(PRIOR));spec.loader.exec_module(old)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel(p):return Path(p).relative_to(ROOT).as_posix()
def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
def write(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n',encoding='utf8')
def save(p,im):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
def mask(points):
 im=Image.new('L',SIZE);ImageDraw.Draw(im).polygon(points,fill=255);return im
def binary(im,t=128):return im.getchannel('A').point(lambda a:255 if a>=t else 0)
def count(im):return im.histogram()[255]
def fit_master(path,box):
 im=Image.open(path).convert('RGBA');a=im.getchannel('A').point(lambda a:0 if a<16 else (255 if a>=220 else a));im.putalpha(a);im=im.crop(a.getbbox())
 fitted=ImageOps.contain(im,(box[2],box[3]),Image.Resampling.LANCZOS);layer=Image.new('RGBA',SIZE);layer.alpha_composite(fitted,(box[0]+(box[2]-fitted.width)//2,box[1]+box[3]-fitted.height));return layer
def prompt_for(source):
 p=source.with_name(source.stem+'.prompt.txt')
 return p.read_text(encoding='utf8').strip() if p.is_file() else read(source.with_name('generation.json'))['prompt']
def default_route(entrance,solid):
 x,y=entrance;end=y
 while end<373 and solid.getpixel((x,end)):end+=1
 return [tuple(entrance),(x,min(373,end+3))]
def compose(states,layers,bg):
 im=bg.convert('RGBA')
 for s in sorted(states,key=lambda s:rows_by_state[s]['native_z']):im.alpha_composite(layers[s])
 return im

def main():
 global rows_by_state
 REPORT.mkdir(parents=True,exist_ok=True)
 frozen={rel(p):sha(p) for p in [ROOT/'content/factions.json',ROOT/'design/town-visuals.json',ROOT/'assets/manifest.json',*(ROOT/'assets/recipes/town').rglob('*.json')]}
 write(HERE/'canonical-before.json',frozen)
 approved=Image.open(PRIOR/'approved-native.png').convert('RGBA')
 plate=Image.open(PRIOR/'empty-plate-v1/native.png').convert('RGBA')
 masks={site:ImageChops.lighter(mask(v['poly']),mask(v['foot'])) for site,v in SITES.items()}
 contexts={};union=Image.new('L',SIZE)
 for site,body in masks.items():
  context=body.filter(ImageFilter.MaxFilter(7));others=Image.new('L',SIZE)
  for other,other_body in masks.items():
   if other!=site:others=ImageChops.lighter(others,ImageChops.subtract(other_body,body))
  context=ImageChops.subtract(context,others);contexts[site]=context;union=ImageChops.lighter(union,context)
 background=Image.composite(plate,approved,union)
 save(HERE/'terrain/background.png',background);save(HERE/'terrain/removal-contours.png',union);save(HERE/'terrain/water-mask.png',Image.new('L',SIZE))
 old_rows={r['state']:r for r in read(PRIOR/'candidate/selection.json')['states']}
 recipes={};layers={};rows=[];structures={};coastal_source=HERE/'coastal-complete-master.png'
 for site,info in SITES.items():
  for state in info['states']:
   folder=HERE/'structures'/state
   if state==info['top']:
    layer=approved.copy();layer.putalpha(contexts[site]);solid=masks[site];source=PRIOR/'approved-master.png';entrance=list(info['door'])
    # The knife guild's completed left wall is visible only with barracks absent.
    # The patch occupies real barracks-owned silhouette and is underneath it at z248.
    if state=='dwellingUpLvl3':
     end=fit_master(HERE/'knife-complete-master.png',(227,182,110,66))
     end_mask=ImageChops.multiply(masks['dwellingLegion'],mask([(227,190),(237,186),(240,246),(228,247)]))
     patch=end.copy();patch.putalpha(ImageChops.multiply(end.getchannel('A'),end_mask));layer.alpha_composite(patch);solid=ImageChops.lighter(solid,ImageChops.multiply(binary(end),end_mask))
    foundation=ImageChops.multiply(mask(info['foot']),solid)
   else:
    row=old_rows[state];layer=Image.open(ROOT/row['native_layer']).convert('RGBA');solid=binary(layer);source=ROOT/row['painted_master'];entrance=row['entrance'];foundation=old.own_bottom(solid,5)
    offset=-8 if state in ('mageGuild1','mageGuild2','mageGuild3') else -10 if state=='dwellingLvl6' else 0
    if offset:
     moved=Image.new('RGBA',SIZE);moved.alpha_composite(layer,(0,offset));layer=moved;solid=binary(layer);entrance=[entrance[0],entrance[1]+offset];foundation=old.own_bottom(solid,5)
   alpha=layer.getchannel('A');layer.putalpha(Image.composite(Image.new('L',SIZE,255),alpha,solid.filter(ImageFilter.MinFilter(3))))
   door=Image.new('L',SIZE);ImageDraw.Draw(door).rectangle((entrance[0]-2,entrance[1]-2,entrance[0]+2,entrance[1]+2),fill=255)
   arch=state in ('fort','citadel')
   if not arch:door=ImageChops.multiply(door,solid)
   route=Image.new('L',SIZE);points=[tuple(entrance),*ROUTES[site][1:]] if site in ROUTES else default_route(entrance,solid)
   ImageDraw.Draw(route).line(points,fill=255,width=3)
   area=Image.new('RGBA',SIZE,(255,255,255,0));area.putalpha(solid)
   border=Image.new('RGBA',SIZE,(255,224,90,0));border.putalpha(ImageChops.subtract(solid.filter(ImageFilter.MaxFilter(3)),solid))
   for name,im in [('layer',layer),('area',area),('border',border),('silhouette',solid),('foundation',foundation),('door',door),('entry-route',route)]:save(folder/(name+'.png'),im)
   row={'state':state,'site':site,'native_z':info['z'],'native_layer':rel(folder/'layer.png'),'native_layer_sha256':sha(folder/'layer.png'),'painted_master':rel(source),'painted_master_sha256':sha(source),'entrance':entrance,'entry_kind':'open_arch' if arch else 'front_threshold','route_points':points,'whole_composition_approved':True,'visual_approval_granted':False,'geometry':{n:{'path':rel(folder/(n+'.png')),'sha256':sha(folder/(n+'.png'))} for n in ('silhouette','foundation','door','entry-route')}}
   rows.append(row);layers[state]=layer;structures[state]={'x':0,'y':0,'z':info['z']}
 # Native Noxus coast family: ship upgrades shipyard and must carry the quay too.
 coast_native=Image.open(coastal_source).convert('RGBA').resize(SIZE,Image.Resampling.LANCZOS)
 quaymask=mask([(365,334),(489,334),(491,373),(365,373)])
 for ordinary in masks.values():quaymask=ImageChops.subtract(quaymask,ordinary)
 quay=Image.new('RGBA',SIZE);quay.paste(coast_native,(0,0),quaymask)
 subject,_=old.atlas_cut(PRIOR/'coast-stages-v1/master.png',0,0,cols=2,rows=1)
 dock,_,_=old.make_layer(subject,COAST['box']);quay.alpha_composite(dock)
 boat=fit_master(HERE/'boat-master.png',COAST['boat_box']);save(HERE/'structures/ship/boat-only-control.png',boat);moored=quay.copy();moored.alpha_composite(boat)
 docksolid=ImageChops.multiply(binary(dock),mask([(390,319),(401,318),(410,330),(430,334),(438,345),(457,349),(463,360),(453,368),(398,357),(385,350),(385,337)]))
 for state,layer in [('shipyard',quay),('ship',moored)]:
  folder=HERE/'structures'/state;solid=docksolid if state=='shipyard' else ImageChops.lighter(docksolid,binary(boat))
  alpha=layer.getchannel('A');layer.putalpha(Image.composite(Image.new('L',SIZE,255),alpha,solid.filter(ImageFilter.MinFilter(3))))
  area=Image.new('RGBA',SIZE,(255,255,255,0));area.putalpha(solid);border=Image.new('RGBA',SIZE,(255,224,90,0));border.putalpha(ImageChops.subtract(solid.filter(ImageFilter.MaxFilter(3)),solid))
  foot=ImageChops.multiply(docksolid,mask([(397,343),(412,343),(419,350),(398,351)]));door=Image.new('L',SIZE);ImageDraw.Draw(door).ellipse((COAST['landing'][0]-2,COAST['landing'][1]-2,COAST['landing'][0]+2,COAST['landing'][1]+2),fill=255)
  for name,im in [('layer',layer),('area',area),('border',border),('silhouette',solid),('foundation',foot),('door',door),('entry-route',Image.new('L',SIZE))]:save(folder/(name+'.png'),im)
  source=coastal_source if state=='shipyard' else HERE/'boat-master.png'
  rows.append({'state':state,'site':'coast','native_z':COAST['z'],'native_layer':rel(folder/'layer.png'),'native_layer_sha256':sha(folder/'layer.png'),'painted_master':rel(source),'painted_master_sha256':sha(source),'entrance':list(COAST['landing']),'entry_kind':'native_optional_coastal_overlay','visual_approval_granted':False,'whole_composition_approved':False,'coastal_adaptation':COAST['description'],'geometry':{n:{'path':rel(folder/(n+'.png')),'sha256':sha(folder/(n+'.png'))} for n in ('silhouette','foundation','door','entry-route')}});layers[state]=layer;structures[state]={'x':0,'y':0,'z':COAST['z']}
 save(HERE/'terrain/coastal-water-mask.png',mask(COAST['water']))
 rows_by_state={r['state']:r for r in rows}
 templates={p.relative_to(ROOT).as_posix():read(p) for p in (ROOT/'assets/recipes/town').rglob('*.json')}
 for row in rows:
  state=row['state'];folder=HERE/'structures'/state
  for role in ('animation','area','border'):
   key=f'assets/recipes/town/structures/{state}-{role}.json';recipe=deepcopy(templates[key]);p=folder/('layer.png' if role=='animation' else role+'.png')
   recipe.update(source_sha256=sha(p),sha256=sha(p),source_canvas=list(SIZE),fit='exact',production_status='painted-master-complete' if role=='animation' else 'derived-technical-mask-complete',status='candidate-unselected',visual_approval_granted=False)
   recipe['building_contract'].update(full_canvas_placement=structures[state],native_ground_contact=list(Image.open(folder/'foundation.png').getbbox()))
   recipe['generation']={'image_generation_used':role=='animation','provider':'OpenAI built-in image_gen' if role=='animation' else None,'model':'Not exposed by built-in tool','prompt':prompt_for(ROOT/row['painted_master']) if role=='animation' else None,'method':'Painted2D master with exact approved pixels; technical contour isolation and native registration. Hidden wall patches and coast derive from separately preserved imagegen paintings.','painted_master':row['painted_master'],'painted_master_sha256':row['painted_master_sha256'],'source_ledger':rel(HERE/'source-ledger.json'),'source_ledger_sha256':sha(HERE/'source-ledger.json'),'assembly_script':rel(Path(__file__)),'assembly_script_sha256':sha(Path(__file__)),'candidate_only':True}
   if role=='animation':recipe['groups'][0]['frames'][0].update(source=rel(p),source_sha256=sha(p),sha256=sha(p))
   else:recipe['source']=rel(p)
   recipes[key]=recipe
 key='assets/recipes/town/background.json';recipe=deepcopy(templates[key]);p=HERE/'terrain/background.png';recipe.update(source=rel(p),source_sha256=sha(p),sha256=sha(p),source_canvas=list(SIZE),fit='exact',production_status='painted-master-complete',status='candidate-unselected',visual_approval_granted=False);recipe['generation']={'image_generation_used':True,'provider':'OpenAI built-in image_gen','model':'Not exposed by built-in tool','prompt':prompt_for(PRIOR/'empty-plate-v1/master.png'),'painted_master':rel(PRIOR/'empty-plate-v1/master.png'),'painted_master_sha256':sha(PRIOR/'empty-plate-v1/master.png'),'method':'Existing genuinely painted empty terrain through corrected whole architectural removal contours; exact approved scenery elsewhere.','assembly_script':rel(Path(__file__)),'assembly_script_sha256':sha(Path(__file__))};recipes[key]=recipe
 key='assets/recipes/town/buildingIcons.json';recipe=deepcopy(templates[key])
 for frame in recipe['frames']:
  state=frame['building'];im=layers[state];bb=binary(im,8).getbbox();thumb=ImageOps.contain(im.crop(bb),(146,66),Image.Resampling.LANCZOS);icon=Image.new('RGBA',(150,70));icon.alpha_composite(thumb,((150-thumb.width)//2,68-thumb.height));p=HERE/'construction'/f'{state}.png';save(p,icon);frame.update(source=rel(p),source_sha256=sha(p),sha256=sha(p))
 recipe.update(status='candidate-unselected',visual_approval_granted=False);recipe['generation']={'image_generation_used':False,'method':'Technical native icon crop from selected36 candidate layers','assembly_script':rel(Path(__file__)),'assembly_script_sha256':sha(Path(__file__))};recipes[key]=recipe
 for key,value in recipes.items():write(CANDIDATE/'recipes'/key,value)
 complete=[v['top'] for v in SITES.values()];modes={'full-with-grail':complete,'full':[v['top'] for k,v in SITES.items() if k!='grail'],'empty':[],'base':[v['states'][0] for k,v in SITES.items() if k!='grail'],'early':['villageHall','fort','dwellingLvl1','tavern'],'barracks-only':['dwellingUpLvl1'],'knife-guild-only':['dwellingUpLvl3'],'coastal-full':complete+['shipyard'],'coastal-full-with-boat':complete+['ship']}
 for name,states in modes.items():save(REPORT/(name+'.png'),compose(states,layers,background))
 selection={'status':'authored configuration','candidate_only':True,'integration_ready':False,'canvas':list(SIZE),'ordinary_land_sites':17,'optional_coastal_sites':1,'grail_sites':1,'states':rows,'structures':structures,'background':{'path':rel(HERE/'terrain/background.png'),'sha256':sha(HERE/'terrain/background.png')},'recipes':{k:sha(CANDIDATE/'recipes'/k) for k in recipes},'coastal_plan':COAST,'occlusion_budget':{'path':rel(CANDIDATE/'occlusion-budget.json'),'sha256':sha(CANDIDATE/'occlusion-budget.json')},'runtime_verified':False,'release_accepted':False,'remaining':['Independent native-size visual/geometry review before coordinator selection','Native town rendering/all-state clicks/coast and service verification','External final human art and rights acceptance']}
 write(CANDIDATE/'selection.json',selection);write(CANDIDATE/'town-structures.patch.json',{'structures':structures,'source_factions_sha256':frozen['content/factions.json'],'scope':'Only full-canvas placement/depth fields; other structure resources/functions unchanged'})
 cards=''.join(f'<figure><img src="{name}.png" width="800" height="374"><figcaption>{html.escape(name)}</figcaption></figure>' for name in modes)
 (REPORT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Noxus approved NX1 completion</title><style>body{background:#211a1a;color:#eee;font:16px system-ui;margin:24px}img{max-width:100%;height:auto}figure{margin:24px 0}a{color:#edc783}</style><h1>Noxus NX1 completion candidate</h1><p>Authored configuration. Approved full inland view is preserved. Optional coast is a conditional project adaptation. Native gameplay and final art/rights acceptance remain separate.</p>'+cards,encoding='utf8')
 assert {k:sha(ROOT/k) for k in frozen}==frozen,'Canonical source changed during candidate assembly'
 print(json.dumps({'states':len(rows),'recipes':len(recipes),'canonical_changed':False}))
if __name__=='__main__':main()
