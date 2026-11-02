"""Reproduce candidate-only Bandle town composition from pinned painted masters.

No source/design selections, publication, staging or desktop actions are performed.
The complete painted town was reviewed first; matching terrain and all-state slices
are derived afterward. Existing compatible painted master silhouettes are retained.
"""
from pathlib import Path
from copy import deepcopy
import hashlib
import itertools
import json
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = ROOT / 'build/reports/complete-town-20261027-v2'
SIZE = (800, 374)
RECTS = {'hall': [151, 4, 163, 119], 'fortification': [325, 3, 205, 124], 'guild': [14, 4, 115, 112], 'tavernAcademy': [150, 267, 145, 103], 'market': [299, 279, 117, 83], 'engineering': [421, 256, 156, 117], 'portal': [504, 137, 97, 83], 'garden': [396, 184, 98, 63], 'fountain': [307, 164, 74, 83], 'dwelling1': [0, 265, 142, 108], 'dwelling2': [161, 154, 126, 95], 'dwelling3': [697, 196, 103, 101], 'dwelling4': [587, 281, 113, 91], 'dwelling5': [608, 169, 108, 105], 'dwelling6': [0, 136, 150, 109], 'dwelling7': [649, 17, 145, 128], 'coast': [704, 314, 96, 60], 'grailOrnament': [421, 49, 31, 34]}
# Manually read front-door/steps from each actual painted upgraded facade.
# These are projected ground/approach annotation points, not automatic alpha centres.
DOORS = {'hall': [231, 122], 'fortification': [427, 126], 'guild': [71, 115], 'tavernAcademy': [225, 369], 'market': [358, 361], 'engineering': [499, 373], 'portal': [553, 219], 'garden': [445, 246], 'fountain': [344, 246], 'dwelling1': [70, 373], 'dwelling2': [225, 248], 'dwelling3': [748, 296], 'dwelling4': [642, 371], 'dwelling5': [663, 273], 'dwelling6': [64, 244], 'dwelling7': [723, 144], 'coast': [730, 353]}
# Roads are a terrain-painting placement guide. The final painted pixels must be
# inspected; a technical annotation is not represented as native traversability.
ROADS = []  # Streets come from the reviewed COMPLETE painted design, not geometric road generation.
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
rel = lambda p: Path(p).relative_to(ROOT).as_posix()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True)+'\n', encoding='utf-8')


def save(path, image):
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, compress_level=9, optimize=False)


def crop(image):
    box = image.getchannel('A').point(lambda v: 255 if v >= 8 else 0).getbbox()
    if box is None:
        raise ValueError('Empty painted master')
    box = [max(0, box[0]-8), max(0, box[1]-8), min(image.width, box[2]+8), min(image.height, box[3]+8)]
    return image.crop(box), box


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    baseline_path = HERE / 'inputs/current-town-visuals.json'
    if not baseline_path.is_file():
        write(baseline_path, json.loads((ROOT/'design/town-visuals.json').read_text()))
    old = json.loads(baseline_path.read_text())
    design = deepcopy(old)
    design.pop('selected_sources', None)
    design['layout_note'] = ('COMPLETE-TOWN-FIRST V2: reviewed assembled painted city precedes terrain/layer extraction; broad level civic landing supports every rear root/foundation/shadow; '
                            'larger rear civic/fortified/Mirror institutions, organic root-grown shared '
                            'foundations and clear front-facing entrances; actual all-state alpha silhouettes '
                            'planned before the independently painted empty landscape. Painted buildings are retained.')
    recipes, layers, masks, rows, bindings = [], {}, {}, [], []
    files = {baseline_path, Path(__file__)}
    terrain_master, terrain_native = HERE/'background/master.png', HERE/'background/native.png'
    # Keep the optional small inlet below the land site's nearest actual footing.
    # Final source observation: provider placed the inlet slightly farther up
    # the right edge than its requested polygon. Reserve that observed water,
    # and raise the workshop's complete master onto the visibly dry quay.
    water_polygon = [[704, 355], [721, 343], [745, 329], [769, 318], [798, 306], [799, 373], [704, 373]]
    water = Image.new('L', SIZE)
    ImageDraw.Draw(water).polygon([tuple(p) for p in water_polygon], fill=255)
    for site in design['sites']:
        x, y, width, height = RECTS[site['id']]
        z = 128 if site['id']=='grailOrnament' else 374 if site['id']=='coast' else y+height
        site.update(composition_rectangle=[x, y, width, height], center=[x+width//2, y+height//2], native_z=z,
                    layer_origin=[0, 0], selected_state_art={})
        for state in site['states']:
            input_dir = HERE/'inputs/recipes'
            for role in ['animation', 'area', 'border', 'campaign']:
                frozen = input_dir/f'{state}-{role}.json'
                if not frozen.is_file():
                    frozen.parent.mkdir(parents=True, exist_ok=True)
                    frozen.write_bytes((ROOT/f'assets/recipes/town/structures/{state}-{role}.json').read_bytes())
                files.add(frozen)
            source_recipe = json.loads((input_dir/f'{state}-animation.json').read_text())
            original_master = ROOT/source_recipe['generation']['painted_master']
            # Preserve exactly the currently selected crest-bearing pixels in
            # this town-only sealed closure; don't fall back to pre-crest art.
            master = HERE/'retained-masters'/state/'master.png'
            if not master.is_file():
                master.parent.mkdir(parents=True, exist_ok=True)
                master.write_bytes(original_master.read_bytes())
            if sha(master)!=source_recipe['generation']['painted_master_sha256']:
                raise ValueError('Retained current master does not match frozen input: '+state)
            lineage = dict(original_path=rel(original_master), original_sha256=sha(original_master),
                           retained_sha256=sha(master), production='Byte-identical retained current painted2D building master.')
            write(master.parent/'lineage.json',lineage)
            files.add(master.parent/'lineage.json')
            raw = Image.open(master).convert('RGBA')
            image, crop_box = crop(raw)
            fitted = ImageOps.contain(image, (width, height), Image.Resampling.LANCZOS)
            layer = Image.new('RGBA', SIZE)
            layer.alpha_composite(fitted, (x+(width-fitted.width)//2, y+height-fitted.height))
            dest = HERE/'structures'/state
            save(dest/'layer.png', layer)
            mask = layer.getchannel('A').point(lambda v: 255 if v >= 128 else 0)
            for role, channel in [('area', mask), ('border', ImageChops.subtract(mask.filter(ImageFilter.MaxFilter(5)), mask))]:
                technical = Image.new('RGBA', SIZE, (255, 235, 32, 0))
                technical.putalpha(channel)
                save(dest/(role+'.png'), technical)
            for role, size in [('hall-icon', (150,70)), ('campaign', (58,64))]:
                icon = ImageOps.contain(image, size, Image.Resampling.LANCZOS)
                canvas = Image.new('RGBA', size)
                canvas.alpha_composite(icon, ((size[0]-icon.width)//2, size[1]-icon.height))
                save(dest/(role+'.png'), canvas)
            state_z = 375 if state=='ship' else z
            foot = mask.copy()
            box = mask.getbbox()
            foot.paste(0, (0,0,800,max(0,box[3]-10)))
            wet = sum(ImageChops.multiply(foot, water).histogram()[128:])
            row = dict(state=state, site=site['id'], master=rel(master), master_sha256=sha(master),
                       source_crop_xyxy=crop_box, fit_size=list(fitted.size), native_layer=rel(dest/'layer.png'),
                       native_layer_sha256=sha(dest/'layer.png'), native_z=state_z,
                       composition_rectangle=[x,y,width,height], click_bbox=list(box),
                       click_pixels=sum(mask.histogram()[128:]), footing_water_pixels=wet,
                       visual_approval_granted=False)
            site['source'][state] = rel(master)
            site['sha256'][state] = sha(master)
            site['selected_state_art'][state] = row
            if state_z!=z: site.setdefault('native_state_z', {})[state] = state_z
            rows.append(row);layers[state]=layer;masks[state]=mask
            for role in ['animation', 'area', 'border', 'campaign']:
                active = f'assets/recipes/town/structures/{state}-{role}.json'
                recipe = json.loads((input_dir/f'{state}-{role}.json').read_text())
                source = dest/('layer.png' if role=='animation' else role+'.png')
                desc = dict(source=rel(source), source_sha256=sha(source), source_canvas=list(Image.open(source).size))
                if role=='animation': recipe['groups'][0]['frames']=[desc]
                else: recipe.update(desc)
                recipe['generation']['painted_master']=rel(master)
                recipe['generation']['painted_master_sha256']=sha(master)
                recipe['generation']['retained_master_lineage']=rel(master.parent/'lineage.json')
                recipe['generation']['conversion'] = dict(revision=HERE.name, source_crop_xyxy=crop_box,
                    fit_size=list(fitted.size), composition_rectangle=[x,y,width,height], native_z=state_z,
                    method='Uniform LANCZOS technical scale/place of current selected painted2D master; no warp, recolour or new architecture.')
                target=HERE/'recipes/structures'/f'{state}-{role}.json'
                write(target,recipe);recipes.append(rel(target));files.add(target)
                bindings.append(dict(candidate=rel(target), active=active, sha256=sha(target)))
            for name in ['layer.png','area.png','border.png','hall-icon.png','campaign.png']: files.add(dest/name)
            files.add(master)
            for name in ['generation.json','prompt.txt','provenance.json','prompt-v2.txt']:
                if (master.parent/name).is_file(): files.add(master.parent/name)
    # Freeze the all-state complete silhouette plan BEFORE generating background.
    union_sites = {}
    for site in design['sites']:
        union=Image.new('L', SIZE)
        for state in site['states']: union=ImageChops.lighter(union,masks[state])
        save(HERE/'silhouette-envelopes'/(site['id']+'.png'),union)
        union_sites[site['id']] = dict(alpha128_bbox=list(union.getbbox()), states=site['states'],
                                     ground_approach=DOORS.get(site['id']), silhouette_sha256=sha(HERE/'silhouette-envelopes'/(site['id']+'.png')))
    plan = dict(status='authored configuration', canvas=list(SIZE), sites=union_sites,
                rectangles=RECTS, proposed_road_guides=ROADS, water_polygon=water_polygon,
                rule_quotes=['Before repainting a background, make a complete placement plan using the selected buildings\' actual full silhouettes, roofs, towers, stairs, foundations and contact shadows.',
                             'The terrain plate must not contain completed functional architecture.'],
                masters={r['master']:r['master_sha256'] for r in rows}, no_procedural_art=True)
    plan['complete_town_first']={'master':'assets/source/town/complete-town-20261027-v2/complete-design/master.png','master_sha256':sha(HERE/'complete-design/master.png'),'native':'assets/source/town/complete-town-20261027-v2/complete-design/native.png','native_sha256':sha(HERE/'complete-design/native.png'),'reviewed_by':'root coordinator before extraction; source pixel scope only'}
    write(HERE/'placement-plan.json',plan)
    guide=Image.new('RGBA',SIZE,(104,109,80,255));draw=ImageDraw.Draw(guide)
    for road in ROADS: draw.line([tuple(p) for p in road],fill=(223,186,111),width=9)
    for site in design['sites']:
        if site['id'] not in {'coast','grailOrnament'}: guide.alpha_composite(layers[site['states'][-1]])
    save(OUT/'placement-guide.png',guide)
    for row in rows:
        if row['site'] not in {'coast','grailOrnament'} and row['footing_water_pixels']: raise ValueError('Wet land footing '+row['state'])
    overlaps=[]
    for a,b in itertools.combinations(rows,2):
        if a['site']==b['site'] or 'grailOrnament' in (a['site'],b['site']):continue
        overlap=ImageChops.multiply(masks[a['state']],masks[b['state']]);n=sum(overlap.histogram()[128:])
        if n: overlaps.append(dict(a=a['state'],b=b['state'],sites=[a['site'],b['site']],pixels=n,bbox=overlap.getbbox()))
    write(OUT/'geometry.json',dict(rows=rows,cross_site_opaque_overlaps=overlaps,wet_land=[]))
    if not terrain_master.is_file():
        print(json.dumps(dict(plan_created=True, overlaps=len(overlaps), background_pending=True)));return
    save(terrain_native,ImageOps.fit(Image.open(terrain_master).convert('RGBA'),SIZE,Image.Resampling.LANCZOS))
    save(HERE/'background/water-annotation.png',water)
    terrain=dict(master=rel(terrain_master),master_sha256=sha(terrain_master),native=rel(terrain_native),
                 native_sha256=sha(terrain_native),water_polygon=water_polygon,
                 annotation='Small optional inlet at bottom-right; land footings measured against the planned shoreline and visually inspected source.')
    design['terrain']=terrain
    for name in ['background','buildingIcons']:
        active=f'assets/recipes/town/{name}.json';recipe=json.loads((ROOT/active).read_text())
        if name=='buildingIcons':
            for frame in recipe['frames']:
                source=HERE/'structures'/frame['building']/'hall-icon.png'
                frame.update(source=rel(source),source_sha256=sha(source))
        else:
            recipe.update(source=rel(terrain_native),source_sha256=sha(terrain_native))
            recipe['generation']=json.loads((HERE/'background/generation.json').read_text())
        target=HERE/'recipes'/f'{name}.json';write(target,recipe);recipes.append(rel(target));files.add(target)
        bindings.append(dict(candidate=rel(target),active=active,sha256=sha(target)))
    from support_annotations import prepare as prepare_support
    support, support_files = prepare_support(design, layers)
    files.update(support_files)
    if not support['ok']:
        raise ValueError('Actual full foundation profile does not match level/stair/cliff annotations: '+str([row for row in support['states'] if row['errors']]))
    # Bind the complete master, level/stair/contact annotations and their real
    # producer into the normal backend's source-input walk, not only this report.
    # All edges stay inside this town's own assets/source subtree.
    background_recipe_path=HERE/'recipes/background.json'
    background_recipe=json.loads(background_recipe_path.read_text())
    background_recipe['generation']['complete_design_dependencies']={
        'complete_painted_master':rel(HERE/'complete-design/master.png'),
        'complete_native_master':rel(HERE/'complete-design/native.png'),
        'complete_prompt':rel(HERE/'complete-design/prompt.txt'),
        'complete_generation':rel(HERE/'complete-design/generation.json'),
        'complete_root_review':rel(HERE/'complete-design/review-checkpoint.json'),
        'support_helper':rel(HERE/'support_annotations.py'),
        'preparation_helper':rel(Path(__file__)),
        'support_annotations':rel(HERE/'support/foundation-annotations.json'),
        'terrain_stairs':rel(HERE/'support/terrain-stair-exclusion.png'),
        'terrain_bank_faces':rel(HERE/'support/terrain-cliff-exclusion.png'),
        'level_landings':{name:rel(HERE/'support'/('level-landing-'+name+'.png')) for name in ['guild','hall','fortification','dwelling7']},
        'actual_state_contact_profiles':{row['state']:rel(HERE/row['profile']) for row in support['states']}}
    write(background_recipe_path,background_recipe)
    for binding in bindings:
        if binding['candidate']==rel(background_recipe_path):binding['sha256']=sha(background_recipe_path)
    files.update(p for folder in [HERE/'complete-design', HERE/'background', HERE/'initial-full-silhouette-plan'] for p in folder.rglob('*') if p.is_file())
    files.update([terrain_master,terrain_native,HERE/'placement-plan.json',HERE/'background/generation.json',HERE/'background/prompt.txt',HERE/'background/water-annotation.png',HERE/'complete-design/native.png'])
    design['recipe_paths']=recipes
    selection=dict(schema_version=1,revision=HERE.name,status='authored configuration',visual_approval_granted=False,
                   sites=design['sites'],terrain=terrain,recipe_bindings=bindings,
                   files={rel(p):sha(p) for p in sorted(files)},
                   preparation_policy='Candidate only. Validate exact source closure before coordinator integration; no active writes.')
    write(HERE/'selection.json',selection)
    design['selected_sources']=dict(path=rel(HERE/'selection.json'),sha256=sha(HERE/'selection.json'),
         terrain_master=rel(terrain_master),terrain_master_sha256=sha(terrain_master),
         terrain_native=rel(terrain_native),terrain_native_sha256=sha(terrain_native))
    write(HERE/'town-visuals.candidate.json',design)
    faction=json.loads((ROOT/'content/factions.json').read_text())
    for site in design['sites']:
        for state in site['states']:
            faction['bandlecity']['town']['structures'][state].update(x=0,y=0,z=site.get('native_state_z',{}).get(state,site['native_z']))
    write(HERE/'factions.candidate.json',faction)
    for variant in ['empty','early','base','upgraded','coastal','grail']:
        canvas=Image.open(terrain_native).convert('RGBA');chosen=[]
        if variant=='early':chosen=['villageHall','tavern','dwellingLvl1','dwellingLvl2']
        elif variant!='empty':
            for site in design['sites']:
                if site['id']=='coast':
                    if variant in ['coastal','grail']:chosen+=site['states']
                elif site['id']=='grailOrnament':
                    if variant=='grail':chosen+=site['states']
                else:chosen.append(site['states'][0 if variant=='base' else -1])
        for state in sorted(chosen,key=lambda s:next(r['native_z'] for r in rows if r['state']==s)):canvas.alpha_composite(layers[state])
        save(OUT/(variant+'-native.png'),canvas)
    print(json.dumps(dict(states=len(rows),recipes=len(bindings),overlaps=len(overlaps),candidate=rel(HERE/'town-visuals.candidate.json'))))


if __name__=='__main__':main()
