"""Candidate-only Freljord village assembly through existing town helpers.

No active content, recipes, selector, manifest, stage or native process writes.
"""
from pathlib import Path
from copy import deepcopy
import hashlib,importlib.util,itertools,json,sys
from PIL import Image,ImageChops,ImageDraw,ImageOps
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
REPORT=ROOT/'build/reports/northern-village-20261024-v3'
PLAN=REPORT/'plan-v2/placement-plan.json'
PLAN_SHA='48b96c893c8c5087aea221c8c987f1ce72b3764de0f8777f47aedbb965db0b85'
spec=importlib.util.spec_from_file_location('freljord_village_helper',ROOT/'scripts/prepare_town_art.py');art=importlib.util.module_from_spec(spec);spec.loader.exec_module(art)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def rel(p):return p.relative_to(ROOT).as_posix()
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(art.encoded(v))
def png(p,im):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(art.png(im))
def mask(im,t=128):return im.getchannel('A').point(lambda a:255 if a>=t else 0)
def count(im):return sum(im.histogram()[128:])
def main():
 if sha(PLAN)!=PLAN_SHA:raise ValueError('Frozen prepaint plan changed; version and review it')
 plan=load(PLAN);mastermap=load(HERE/'master-selection.json')['states'];oldrows={r['state']:r for r in plan['states']}
 layout=deepcopy(load(ROOT/'design/building-layout.json'));layout.update(sites=deepcopy(plan['sites']),water_polygon=plan['water_polygon'],planned_before_painting=True,status='authored configuration',background='Small inhabited northern Freljord village at pale winter bluehour with aurora, snowpacked winding lanes, warm hearths and connected dry local workyards. Large rear communal hall, lorekeeper lodge and timber stronghold retained in explicitly allocated plots.',camera='OriginalHeroesIII low frontal threequarter painted matte depth/elevatedhorizon; no globalnear-far ratio or camera warp.',scope='New painted background and northernGuild/coherent regionalHallheraldry, uniform whole-master placement,16ordinarylandsites+optionalshore, native service/replacement semantics preserved.')
 if (HERE/'background-adoption.json').is_file():
  adoption=load(HERE/'background-adoption.json');layout.update(prepaint_water_polygon=plan['water_polygon'],water_polygon=adoption['water_polygon'],painted_water_annotation=adoption['water_annotation'],water_annotation_scope=adoption['water_scope'])
 guild=next(s for s in layout['sites'] if s['id']=='mage-guild');guild['state_rects']={}
 guild['subject']='Coherent northern timber-and-basalt lorekeeper lodge family: steep horn-ended gables, real front stairs, scroll/story-panel alcoves and larger sheltered archive chambers in advanced ranks. Project-fiction regional institution, not an Ionian pagoda, church or canonical united priesthood.'
 coast=next(s for s in layout['sites'] if s['id']=='optional-coast');coast['mirror_x']=True
 coast['shore_orientation']='Whole-family mirror: boathouse/stone approach left on dryland; crane/boat hull right over deliberate water. Entire master mirrored, not individual props.'
 x,y,w,h=guild['rect'];bottom=y+h
 for state,width,height in [('mageGuild1',109,96),('mageGuild2',123,110),('mageGuild3',134,123),('mageGuild4',141,132)]:guild['state_rects'][state]=[x+(w-width)//2,bottom-height,width,height]
 save(HERE/'layout-v3.json',layout)
 inputs=[{'path':rel(p),'sha256':sha(p)} for p in (HERE/'layout-v3.json',ROOT/'scripts/prepare_town_art.py',Path(__file__))]
 common={'status':'authored configuration','production_status':'painted-master-complete-unapproved','visual_approval_granted':False,'require_alpha':True,'canvas':[800,374],'credits':{'author':'Project-directed built-in OpenAI imagegen painted sources and deterministic technical assembly','license':None,'redistribution':'unresolved; release prohibited'},'acceptance':'Technical candidate only; current native/art/rights acceptance remains separate.','inputs':inputs}
 names=load(ROOT/'content/factions.json')['freljord']['town']['buildings'];rows=[];layers={};recipes={};preparations=[]
 for state in names:
  selected=mastermap[state];master=ROOT/selected['master'];record=ROOT/selected['generation_record']
  if sha(master)!=selected['master_sha256'] or sha(record)!=selected['generation_record_sha256']:raise ValueError('Selected master/provenance changed '+state)
  site=next(s for s in layout['sites'] if state in s['states']);rect=site.get('state_rects',{}).get(state,site['rect'])
  source=art.load_rgba(master)
  if site.get('mirror_x'):source=ImageOps.mirror(source)
  native,conversion=art.place(source,rect);conversion['mirror_x']=bool(site.get('mirror_x'));conversion['source_coordinate_basis']='after whole-master horizontal mirror' if site.get('mirror_x') else 'original master'
  area,border=art.masks(native);icon=art.icon(source)
  folder=HERE/'prepared'/state;paths={role:folder/(role+'.png') for role in ('layer','area','border','icon')}
  for role,im in [('layer',native),('area',area),('border',border),('icon',icon)]:png(paths[role],im)
  raw=load(record);gen={'image_generation_used':True,'tool':'image_gen.imagegen','provider':'OpenAI built-in imagegen','model':raw.get('model') or 'Not exposed by the built-in tool','model_id_exposed':False,'prompt':raw['prompt'],'painted_master':rel(master),'painted_master_sha256':sha(master),'generation_record':rel(record),'conversion':conversion,'technical_producer':{'path':rel(Path(__file__)),'sha256':sha(Path(__file__))},'visual_approval_granted':False,'references':[{'path':rel(p),'sha256':sha(p)} for p in (master,record)]}
  emitted={}
  emitted[f'assets/recipes/town/structures/{state}-animation.json']={**common,'generation':gen,'recipe_type':'vcmi_animation','pivot':{'x':0,'y':0},'output_path':art.PREFIX+f'town/structures/{state}.json','groups':[{'group':0,'generateShadow':0,'generateOverlay':0,'frames':[{'source':rel(paths['layer']),'source_sha256':sha(paths['layer']),'sha256':sha(paths['layer']),'source_canvas':[800,374]}]}]}
  for role in ('area','border'):
   emitted[f'assets/recipes/town/structures/{state}-{role}.json']={**common,'recipe_type':'raster','fit':'exact','source':rel(paths[role]),'source_sha256':sha(paths[role]),'source_canvas':[800,374],'output_path':art.PREFIX+f'town/structures/{state}_{role}.png','generation':{'image_generation_used':False,'method':'Existing canonical alpha128 silhouette area or one-native-pixel outward MaxFilter3-minus-silhouette border.','painted_source_provenance':gen,'references':[{'path':rel(paths['layer']),'sha256':sha(paths['layer'])}]}}
  previous=oldrows[state];entry=deepcopy(previous['entrance']);ox,oy=conversion['placed_origin'];pw,ph=conversion['placed_size'];body=area.getchannel('A').getbbox()
  # Northern replacement doors are left of centre. Per-state actual source
  # stairs are projected explicitly, rather than inheriting the pagoda's .50.
  if state.startswith('mageGuild'):
   frac={'mageGuild1':.335,'mageGuild2':.335,'mageGuild3':.33,'mageGuild4':.33}[state]
   entry.update(door_point=[ox+round(frac*pw),oy+round(.78*ph)],front_exit_point=[ox+round(.35*pw),body[3]-1],kind='Northern lorekeeper hall front door and low stone steps, left-of-centre')
  elif site['id']=='optional-coast':
   entry.update(door_point=[ox+round(.35*pw),oy+round(.58*ph)],front_exit_point=[ox+round(.08*pw),body[3]-1],kind='Mirrored family: house left, stone landward entry at farleft; boat/hull intentionally right overwater',facing=[-1,0])
  else:
   dx=previous['entrance']['door_point'][0]-previous['conversion']['placed_origin'][0];dy=previous['entrance']['door_point'][1]-previous['conversion']['placed_origin'][1]
   entry['door_point']=[ox+dx,oy+dy];entry['front_exit_point']=[previous['entrance']['front_exit_point'][0],body[3]-1]
  ex,ey=entry['front_exit_point'];entry['front_apron']=[ex-8,ey,16,10]
  entry['scope']='Actual painted source doorway/stair projection plus reserved apron; exact painted-road support reviewed independently. Not native navigation.'
  row={'state':state,'site':site['id'],'land':site['land'],'rect':rect,'z':site['z']+(1 if state=='grail' else 0),'master':rel(master),'master_sha256':sha(master),'generation_record':rel(record),'generation_record_sha256':sha(record),'previous_master':selected['previous_master'],'previous_master_sha256':selected['previous_master_sha256'],'master_changed':selected['master_changed'],'native_layer':rel(paths['layer']),'native_layer_sha256':sha(paths['layer']),'conversion':conversion,'native_alpha128_bbox':list(body),'full_alpha_bbox':list(mask(native,1).getbbox()),'entrance':entry,'prepared_icon':rel(paths['icon']),'icon_sha256':sha(paths['icon']),'recipes':{p:hashlib.sha256(art.encoded(v)).hexdigest() for p,v in emitted.items()}}
  save(folder/'preparation.json',row);rows.append(row);preparations.append(row);layers[state]=native;recipes.update(emitted)
 icons=art.icon_recipe(ROOT,preparations);icons.update(status='authored configuration',selection_record='assets/production/town/community-selection-v2.json');recipes['assets/recipes/town/buildingIcons.json']=icons
 bg_recipe=load(Path(sys.argv[1])) if len(sys.argv)>1 else load(ROOT/'assets/recipes/town/background.json')
 background=Image.open(ROOT/bg_recipe['source']).convert('RGBA')
 if background.size!=(800,374):raise ValueError('Background source must already be exact native800x374')
 recipes['assets/recipes/town/background.json']=bg_recipe
 for key,value in recipes.items():save(HERE/'candidate-recipes'/key,value)
 selected={'status':'authored configuration','schema_version':1,'source_placement_plan':rel(PLAN),'source_placement_sha256':PLAN_SHA,'layout':rel(HERE/'layout-v3.json'),'layout_sha256':sha(HERE/'layout-v3.json'),'canvas':[800,374],'sites':layout['sites'],'states':rows,'water_polygon':layout['water_polygon'],'recipes':{p:sha(HERE/'candidate-recipes'/p) for p in recipes},'background':{'source':bg_recipe['source'],'sha256':sha(ROOT/bg_recipe['source']),'recipe_sha256':sha(HERE/'candidate-recipes/assets/recipes/town/background.json')},'preserved_existing_masters':28,'changed_existing_masters':8,'native_verified':False,'visual_approval_granted':False,'release_accepted':False}
 save(HERE/'candidate-selection.json',selected)
 overlaps=[];apron_hits=[]
 for a,b in itertools.combinations(rows,2):
  if a['site']==b['site']:continue
  for threshold in (1,128):
   n=count(ImageChops.multiply(mask(layers[a['state']],threshold),mask(layers[b['state']],threshold)))
   if n:overlaps.append([a['state'],b['state'],threshold,n])
 for a in rows:
  if a['state']=='grail' or not a['land']:continue
  x,y,w,h=a['entrance']['front_apron'];apron=Image.new('L',(800,374));ImageDraw.Draw(apron).rectangle((x,y,x+w-1,y+h-1),fill=255)
  for b in rows:
   if a['site']==b['site']:continue
   n=count(ImageChops.multiply(apron,mask(layers[b['state']])) )
   if n:apron_hits.append([a['state'],b['state'],n])
 save(REPORT/'candidate-geometry.json',{'status':'authored configuration','cross_site_overlaps':overlaps,'entrance_apron_obstructions':apron_hits,'outside_canvas_aprons':[r['state'] for r in rows if r['state']!='grail' and r['entrance']['front_apron'][1]+10>374],'all_state_count':36,'ordinary_land_sites':16,'coast_sites':1})
 png(REPORT/'empty-native.png',background)
 rowmap={r['state']:r for r in rows}
 for mode in ('early','base','upgraded','coast','moored','grail','grail-villageHall','grail-townHall','grail-cityHall','grail-capitol'):
  chosen=[]
  for site in layout['sites']:
   if not site['land'] and mode not in ('coast','moored'):continue
   opts=[s for s in site['states'] if s!='grail'];state=opts[0] if mode in ('base','early','coast') else opts[-1]
   if site['id']=='optional-coast':state='shipyard' if mode=='coast' else 'ship'
   if mode=='early' and state not in ('villageHall','tavern','dwellingLvl1'):continue
   if mode.startswith('grail-') and site['id']=='civic-hall':state=mode.split('-',1)[1]
   chosen.append(state)
  if mode.startswith('grail'):chosen.append('grail')
  out=background.copy()
  for state in sorted(chosen,key=lambda s:rowmap[s]['z']):out.alpha_composite(layers[state])
  png(REPORT/(mode+'-native.png'),out)
 print(json.dumps({'states':len(rows),'recipes':len(recipes),'overlaps':len(overlaps),'apron_obstructions':len(apron_hits),'selected_source_sha256':sha(HERE/'candidate-selection.json')}))
if __name__=='__main__':main()
