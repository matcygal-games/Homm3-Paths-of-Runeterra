"""Crop/scale/composite genuine town paintings into real native resources.

Technical derivatives only: no invented buildings, drawing or new artwork.
The independent master paintings and registration remain editable source.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageChops, ImageFilter

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
WORKSPACE = PROJECT.parent
PREFIX = 'Content/Sprites/runeterra/targon/'
SOURCE = HERE.relative_to(PROJECT).as_posix()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='\n')


def save(image, relative):
    path = HERE / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    image.convert('RGBA').save(path)
    return path


def contain(image, canvas, padding=2):
    image = image.convert('RGBA')
    box = image.getchannel('A').point(lambda p: 255 if p >= 8 else 0).getbbox()
    image = image.crop(box)
    ratio = min((canvas[0]-padding*2)/image.width, (canvas[1]-padding*2)/image.height)
    size = (max(1,round(image.width*ratio)), max(1,round(image.height*ratio)))
    image = image.resize(size, Image.Resampling.LANCZOS)
    layer = Image.new('RGBA', canvas)
    layer.alpha_composite(image, ((canvas[0]-image.width)//2, canvas[1]-padding-image.height))
    return layer


def generation():
    result={'image_generation_used': True, 'workflow': 'image-based-painted-2d', 'derived_from_blender': False,
            'provider': 'OpenAI built-in image_gen', 'model': 'Not exposed by built-in tool',
            'method': 'Genuine painted complete composition and isolated complete state masters; deterministic native registration, source-alpha silhouettes, proportional icon derivatives and puzzle slicing. No geometric artwork or rendered paintovers.',
            'source_generation_ledger': SOURCE+'/source-generation-ledger-v1.json'}
    ledger=HERE/'source-generation-ledger-v1.json'
    if ledger.is_file():result['source_generation_ledger_sha256']=sha(ledger)
    return result


def raster(source, output, role):
    image = Image.open(source)
    return {'recipe_type':'raster', 'production_status':'delivered', 'output_path':output, 'role':role,
            'canvas':list(image.size), 'size':list(image.size), 'source_canvas':list(image.size), 'fit':'stretch',
            'source':source.relative_to(PROJECT).as_posix(), 'source_sha256':sha(source),
            'generation':generation(), 'visual_approval_granted':False,
            'credits':{'author':'Project-directed original painted2D via OpenAI image_gen; technical source preparation', 'license':None, 'redistribution':'Unresolved; release prohibited'}}


def main():
    guide=json.loads((HERE/'site-plan-v1.json').read_text(encoding='utf-8'))
    schema=json.loads((HERE/'native-resource-schema-v1.json').read_text(encoding='utf-8'))['recipes']
    prepared={}
    for site, row in guide['sites'].items():
        for state in row['keys']:
            frame=Image.open(HERE/'native-v4'/(state+'.png')).convert('RGBA')
            body=frame.getchannel('A').point(lambda p:255 if p>=128 else 0)
            area=Image.new('RGBA',frame.size,(0,0,0,0));area.putalpha(body)
            border=Image.new('RGBA',frame.size,(225,190,80,0));border.putalpha(ImageChops.subtract(body.filter(ImageFilter.MaxFilter(3)),body.filter(ImageFilter.MinFilter(3))))
            prepared[state+'_area']=save(area,'derived-v1/structures/'+state+'_area.png')
            prepared[state+'_border']=save(border,'derived-v1/structures/'+state+'_border.png')
            prepared[state+'_campaign']=save(contain(frame,(58,64)),'derived-v1/structures/'+state+'_campaign.png')
            prepared[state+'_construction']=save(contain(frame,(150,70)),'derived-v1/construction/'+state+'.png')
    # Native map illustrations are separate genuine overhead paintings, never a
    # stretched low frontal townscreen or geometric proxy.
    for state in ('village','fort','citadel','castle','capitol'):
        raw=HERE/'ancillary'/state/('master-v2-raw.png' if state=='village' else 'master-v1-raw.png')
        mapimage=Image.open(raw).convert('RGBA')
        native=contain(mapimage,(192,160),padding=7)
        prepared['map_'+state]=save(native,'derived-v1/map/'+state+'.png')
    for relative,old in sorted(schema.items()):
        if old['role']!='town-state-icon':continue
        name=Path(relative).stem
        source=prepared['map_castle' if name.startswith('fort') else 'map_village']
        icon=contain(Image.open(source),tuple(old['canvas']))
        if '_built_' in name:
            # Match actual HoMM3 already-built-this-turn semantics with an
            # original genuine painted red-X glyph, never a missing state cue.
            glyph=Image.open(HERE/'ancillary/built-status/master-v1-raw.png').convert('RGBA')
            glyph=contain(glyph,(10,12) if name.endswith('large') else (8,10),padding=0)
            icon.alpha_composite(glyph,(icon.width-glyph.width,icon.height-glyph.height))
        prepared[name]=save(icon,'derived-v1/icons/'+name+'.png')
    raw=Image.open(HERE/'ancillary/creature-background/master-v1-raw.png').convert('RGBA')
    # One genuine portrait landscape supports both actual native recruitment
    # heights. Crops retain the open foreground needed by creature overlays.
    tall=raw.resize((100,130),Image.Resampling.LANCZOS)
    prepared['creatureBackground130']=save(tall,'derived-v1/ui/creatureBackground130.png')
    prepared['creatureBackground120']=save(tall.crop((0,10,100,130)),'derived-v1/ui/creatureBackground120.png')
    guild=Image.open(HERE/'ancillary/guild-window/master-v1-raw.png').convert('RGBA').resize((141,217),Image.Resampling.LANCZOS)
    prepared['guildWindow']=save(guild,'derived-v1/ui/guildWindow.png')
    puzzle=Image.open(HERE/'ancillary/puzzle/master-v1-raw.png').convert('RGBA').resize((592,546),Image.Resampling.LANCZOS)
    prepared['puzzle-master']=save(puzzle,'derived-v1/puzzle/master.png')
    for relative,old in sorted(schema.items()):
        if old['role']!='puzzle-piece':continue
        name=Path(relative).stem;box=old['derivation']['crop']
        prepared[name]=save(puzzle.crop(tuple(box)),'derived-v1/puzzle/'+name+'.png')
    newroot=HERE/'proposed/recipes'
    recipes={}
    guards=[]
    for relative,old in sorted(schema.items()):
        role=old['role'];name=Path(relative).stem
        if old.get('recipe_type')=='indexed_animation':
            atlas={k:v for k,v in old.items() if k in ('recipe_type','output_path','canvas','role')}
            atlas.update(production_status='delivered',generation=generation(),visual_approval_granted=False,credits=raster(prepared['map_castle'],'','')['credits'],frames=[],depends_on=[])
            for oldframe in old['frames']:
                state=oldframe['building'];source=prepared[state+'_construction']
                out=PREFIX+'town/construction/'+state+'.png'
                producer='assets/recipes/town/construction/'+state+'.json'
                recipe=raster(source,out,'town-construction-icon')
                recipes[producer]=recipe
                payload=json.dumps(recipe,indent=2,sort_keys=True)+'\n'
                atlas['depends_on'].append(producer)
                atlas['frames'].append({'building':state,'frame':oldframe['frame'],'source':'assets/generated/'+out,'sha256':sha(source),'source_canvas':[150,70],
                                        'generated_by':producer,'producer_sha256':hashlib.sha256(payload.encode()).hexdigest()})
            recipes[relative]=atlas
        elif old.get('recipe_type')=='vcmi_animation':
            state=name
            source=prepared['map_'+state] if role=='town-adventure' else HERE/'native-v4'/(state+'.png')
            recipe={k:v for k,v in old.items() if k in ('recipe_type','output_path','canvas','role','generateOverlay','generateShadow')}
            recipe.update(production_status='delivered',generation=generation(),visual_approval_granted=False,credits=raster(source,'','')['credits'],pivot={'x':0,'y':0,'basis':'Actual full native canvas; registration resides in source pixels'},
                          groups=[{'group':0,'frames':[{'source':source.relative_to(PROJECT).as_posix(),'sha256':sha(source),'source_canvas':list(Image.open(source).size)}]}])
            recipes[relative]=recipe
        else:
            if role=='town-background':source=HERE/'background-selected-native-v9.png'
            elif role=='town-structure-area' or role=='town-structure-border' or role=='town-structure-campaign':source=prepared[name]
            elif role=='town-interface' or role=='town-state-icon' or role=='puzzle-piece':source=prepared[name]
            else:raise ValueError('Unowned or unknown native town resource: '+relative+' '+role)
            recipes[relative]=raster(source,old['output_path'],role)
        guards.append({'target':relative,'before_sha256':old['before_sha256'],'payload':'proposed/recipes/'+relative,'output_path':old['output_path']})
    for relative,recipe in sorted(recipes.items()):
        write(newroot/relative,recipe)
    write(HERE/'recipe-guards-v1.json',{'status':'design proposal','canonical_edited':False,'replace_existing':guards,
          'new_auxiliary_producers':[name for name in recipes if name not in {x['target'] for x in guards}],
          'logical_native_resources':len(guards),'actual_recipes_including_required_construction_producers':len(recipes)})
    write(HERE/'derived-source-inventory-v1.json',{key:{'path':path.relative_to(PROJECT).as_posix(),'sha256':sha(path),'canvas':list(Image.open(path).size)} for key,path in prepared.items()})
    print(json.dumps({'logical_native_resources':len(guards),'actual_recipes':len(recipes),'prepared_derivatives':len(prepared)}))


if __name__=='__main__':main()
