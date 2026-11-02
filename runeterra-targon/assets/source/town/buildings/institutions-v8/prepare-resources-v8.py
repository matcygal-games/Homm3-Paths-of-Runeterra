"""Derive only the two institution candidates and their actual native consumers.

Run in project Python. No staging/conversion/publication writes. Repeated runs
preserve all unrelated source and recipe bytes and reconstruct identical files.
"""
from pathlib import Path
import hashlib
import importlib.util
import copy
import json
import sys
from PIL import Image, ImageChops, ImageFilter, ImageDraw, ImageOps

ROOT=Path(__file__).resolve().parents[5]
WORKSPACE=ROOT.parent
FOLDER=Path(__file__).resolve().parent
REVIEW=ROOT/'assets/reviews/town/institutions-v8'
REPORT=ROOT/'build/reports/town-institutions-repair-20261023-v1'
KEYS=('special1','mageGuild4')
digest=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
rel=lambda p:Path(p).relative_to(ROOT).as_posix()
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def save(image,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    image.convert('RGBA').save(path)
    return path
def thumbnail(image,size):
    alpha=image.getchannel('A').point(lambda x:255 if x>=128 else 0)
    crop=image.crop(alpha.getbbox())
    crop.thumbnail((size[0]-4,size[1]-4),Image.Resampling.LANCZOS)
    result=Image.new('RGBA',size)
    result.alpha_composite(crop,((size[0]-crop.width)//2,size[1]-crop.height-2))
    return result

baseline=json.loads((FOLDER/'selection-baseline.json').read_text())
ledger=copy.deepcopy(baseline['ledger'])
original_rows={row['output_path']:copy.deepcopy(row) for row in ledger['outputs']}
render=json.loads((FOLDER/'render-receipt.json').read_text())
scene=ROOT/render['scene']
assert digest(scene)==render['scene_sha256']
assert digest(ROOT/'scripts/targon_town_art.py')==baseline['producer']
assert digest(ROOT/'design/town-layout.json')==baseline['layout_sha256']
generation={'image_generation_used':False,
            'method':'Own editable geometry repair in unchanged v6 camera/light/ground roots. Only Solari Temple and Guild IV crown. Original frames and textures remain preserved.',
            'producer':render['producer'],'producer_sha256':render['producer_sha256'],
            'geometry_source':render['scene'],'geometry_sha256':render['scene_sha256'],
            'preparation':{'producer':rel(__file__),'producer_sha256':digest(__file__)}}
changed_recipes=[]
preparations=[]
for key in KEYS:
    entry=next(row for row in render['states'] if row['key']==key)
    raw=ROOT/entry['source']
    assert digest(raw)==entry['source_sha256']
    image=Image.open(raw).convert('RGBA')
    alpha=image.getchannel('A').point(lambda value:value if value>=8 else 0)
    image.putalpha(alpha)
    image=Image.composite(image,Image.new('RGBA',image.size),alpha.point(lambda value:255 if value else 0))
    prepared=save(image,FOLDER/'prepared'/(key+'.png'))
    preparations.append({'key':key,'raw':rel(raw),'raw_sha256':digest(raw),'prepared':rel(prepared),'prepared_sha256':digest(prepared),'registration':'Unchanged800x374 canvas; no crop, fit, translation or scale','clear_shadow_alpha_below':8})
    animation_path=ROOT/'assets/recipes/town/structures'/(key+'.json')
    animation=json.loads(animation_path.read_text())
    animation['groups'][0]['frames'][0].update(source=rel(prepared),sha256=digest(prepared))
    animation['generation']=generation
    write(animation_path,animation);changed_recipes.append(animation_path)
    mask=image.getchannel('A').point(lambda value:255 if value>=128 else 0)
    area=Image.new('RGBA',image.size,(255,255,255,0));area.putalpha(mask)
    outline=ImageChops.subtract(mask.filter(ImageFilter.MaxFilter(3)),mask)
    border=Image.new('RGBA',image.size,(225,190,80,0));border.putalpha(outline)
    for kind,value in [('area',area),('border',border),('campaign',thumbnail(image,(58,64)))]:
        path=save(value,FOLDER/(key+'_'+kind+'.png'))
        recipe_path=ROOT/'assets/recipes/town/structures'/(key+'_'+kind+'.json')
        recipe=json.loads(recipe_path.read_text())
        recipe.update(source=rel(path),source_sha256=digest(path),generation=generation)
        if 'derivation' in recipe: recipe['derivation'].update(source=rel(prepared),source_sha256=digest(prepared))
        write(recipe_path,recipe);changed_recipes.append(recipe_path)
    save(thumbnail(image,(150,70)),FOLDER/(key+'_construction.png'))
icons_path=ROOT/'assets/recipes/town/buildingIcons.json'
icons=json.loads(icons_path.read_text())
icons['generation']=generation
for descriptor in icons['frames']:
    if descriptor['building'] in KEYS:
        source=FOLDER/(descriptor['building']+'_construction.png')
        descriptor.update(source=rel(source),sha256=digest(source))
write(icons_path,icons);changed_recipes.append(icons_path)

# Ask the existing compiler for bytes without writing its assets/generated outputs.
sys.path.insert(0,str(WORKSPACE/'scripts'))
import faction_art_compile
compiler=faction_art_compile.create_compiler('targon')
plans={}
physical={}
for path in changed_recipes:
    outputs,result=compiler.plan(ROOT,path)
    plans[rel(path)]={'recipe_sha256':digest(path),'outputs':{name:hashlib.sha256(data).hexdigest() for name,data in outputs.items()}}
    physical.update({name:hashlib.sha256(data).hexdigest() for name,data in outputs.items()})
    recipe=json.loads(path.read_text())
    row=next(row for row in ledger['outputs'] if row['recipe']==rel(path))
    row.update(recipe_sha256=digest(path),planned_sha256=hashlib.sha256(outputs[recipe['output_path']]).hexdigest())
    if recipe['recipe_type']=='vcmi_animation':
        desc=recipe['groups'][0]['frames'][0]
        row.update(source=desc['source'],source_sha256=desc['sha256'])
    elif recipe['recipe_type']=='raster':
        row.update(source=recipe['source'],source_sha256=recipe['source_sha256'])
changed_set={rel(path) for path in changed_recipes}
for name,checksum in baseline['recipe_hashes'].items():
    if name not in changed_set: assert digest(ROOT/name)==checksum,name
unchanged_rows=[row for row in ledger['outputs'] if row['recipe'] not in changed_set]
assert all(row==original_rows[row['output_path']] for row in unchanged_rows)
ledger['institution_override_receipt']=rel(FOLDER/'render-receipt.json')
ledger['institution_override_receipt_sha256']=digest(FOLDER/'render-receipt.json')
ledger['institution_preparation_record']=rel(FOLDER/'preparation-record.json')
ledger['source_scenes'].append({'source':rel(scene),'source_sha256':digest(scene)})
ledger['remaining_visual_findings']=[finding for finding in ledger['remaining_visual_findings'] if finding!='Solari/Lunari institutions and crescent are subtle at1x']
ledger['remaining_visual_findings'].append('Two public institutions revised for source review; native clicks, motion, full final human art and rights acceptance remain pending. Lunari crescent remains a discreet identity detail.')
write(FOLDER/'preparation-record.json',{'status':'authored configuration','producer':rel(__file__),'producer_sha256':digest(__file__),'frames':preparations,'plans':plans})
ledger['institution_preparation_record_sha256']=digest(FOLDER/'preparation-record.json')
write(ROOT/'assets/production/town-art.json',ledger)

# Actual registered source pixels, not per-building fitting, produce both compositions.
before_layers={}
for row in baseline['ledger']['outputs']:
    if row['role']=='town-structure-animation': before_layers[Path(row['recipe']).stem]=Image.open(ROOT/row['source']).convert('RGBA')
after_layers={**before_layers,**{key:Image.open(FOLDER/'prepared'/(key+'.png')).convert('RGBA') for key in KEYS}}
faction=json.loads((ROOT/'content/factions.json').read_text())['targon']
layout=json.loads((ROOT/'design/town-layout.json').read_text())
selected=[site['keys'][-1] for site in layout['sites'].values()]+[annex['key'] for site in layout['sites'].values() for annex in site.get('annexes',{}).values()]+['grail']
selected=sorted(selected,key=lambda key:faction['town']['structures'][key]['z'])
plate=ImageOps.fit(Image.open(ROOT/'assets/source/town/terrain-v1.png').convert('RGBA'),(800,374),method=Image.Resampling.LANCZOS)
exposures={}
for label,layers in [('before',before_layers),('candidate',after_layers)]:
    composite=plate.copy()
    for key in selected: composite=Image.alpha_composite(composite,layers[key])
    save(composite,REVIEW/(label+'-full-town-native.png'))
    covered=Image.new('L',(800,374));exposures[label]={}
    for key in reversed(selected):
        mask=layers[key].getchannel('A').point(lambda value:255 if value>=128 else 0)
        exposed=ImageChops.subtract(mask,covered)
        exposures[label][key]={'exposed_click_pixels':sum(exposed.histogram()[128:]),'exposed_bounds':exposed.getbbox()}
        covered=ImageChops.lighter(covered,mask)
sheet=Image.new('RGBA',(600,230),(48,44,37,255));draw=ImageDraw.Draw(sheet)
for i,key in enumerate(KEYS):
    for j,(label,layers) in enumerate([('before',before_layers),('candidate',after_layers)]):
        image=layers[key];box=image.getchannel('A').point(lambda v:255 if v>=128 else 0).getbbox()
        sheet.alpha_composite(image.crop(box),(i*300+j*140+10,35))
        draw.text((i*300+j*140+10,8),key+' '+label,fill='white')
save(sheet,REVIEW/'two-institutions-native1x.png')
hall=Image.new('RGBA',(600,155),(48,44,37,255));draw=ImageDraw.Draw(hall)
for i,key in enumerate(KEYS):
    before_source=next(row['source'] for row in baseline['ledger']['outputs'] if row['recipe'].endswith('/'+key+'.json'))
    for j,(label,source) in enumerate([('before',Path(before_source).parent.parent/(key+'_construction.png')),('candidate',Path(rel(FOLDER/(key+'_construction.png'))))]):
        hall.alpha_composite(Image.open(ROOT/source).convert('RGBA'),(i*300+j*150,35))
        draw.text((i*300+j*150,10),key+' '+label,fill='white')
save(hall,REVIEW/'two-hall-icons-native1x.png')
write(REVIEW/'click-exposures.json',{'status':'authored configuration','native_clicks_observed':False,'compositions':exposures})
write(REPORT/'candidate-source-checks.json',{'status':'authored configuration','changed_building_states':list(KEYS),'unchanged_building_states':33,'changed_recipe_count':len(changed_recipes),'unchanged_recipes':len(baseline['recipe_hashes'])-len(changed_recipes),'unchanged_ledger_output_records':len(unchanged_rows),'plans':plans,'physical_output_hashes':physical,'source_scenes':[{'source':rel(scene),'sha256':digest(scene)}],'layout_unchanged':True,'shared_producer_unchanged':True,'staging_or_generated_written':False,'native_visual_approval':False,'review_files':{rel(p):digest(p) for p in REVIEW.glob('*') if p.is_file()}})
print(json.dumps({'changed_recipes':len(changed_recipes),'unchanged_records':len(unchanged_rows),'scene_sha256':digest(scene),'ledger_sha256':digest(ROOT/'assets/production/town-art.json'),'review':str(REVIEW)},indent=2))
