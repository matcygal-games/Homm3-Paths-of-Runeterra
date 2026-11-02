"""Review-only native town candidate. No production files or active selectors written."""
import hashlib
import json
import sys
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw, ImageFilter, ImageChops

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
REPORT = ROOT / 'build/reports/painted-town-community-20261024-v1'
DESIGN = ROOT / 'design/town-visuals-painted-community-20261024-v1.candidate.json'
RECTS = {
    'hall':[155,22,150,142], 'fortification':[308,4,202,132],
    'guild':[18,20,112,145], 'tavernAcademy':[133,266,126,93],
    'market':[271,288,116,73], 'engineering':[406,258,141,103],
    'portal':[490,80,102,100], 'garden':[465,190,90,60],
    'fountain':[352,190,77,86], 'dwelling1':[16,265,111,92],
    'dwelling2':[152,160,118,99], 'dwelling3':[681,182,118,104],
    'dwelling4':[555,252,104,84], 'dwelling5':[581,148,112,112],
    'dwelling6':[4,154,139,103], 'dwelling7':[618,12,164,158],
    'coast':[689,312,111,62], 'grailOrnament':[389,55,40,45],
}
NEW_STATES = ['dwellingLvl2','dwellingUpLvl2','dwellingLvl5','dwellingUpLvl5','dwellingLvl7','dwellingUpLvl7']
# Conservatively annotated by observing generated native.png. Bank margins included.
WATER_POLYGON = [[600,373],[650,353],[689,341],[726,328],[760,314],[799,298],[799,373]]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8')

def rel(path):
    return path.relative_to(ROOT).as_posix()

def save(image,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    image.save(path,compress_level=9,optimize=False)

def crop_master(path):
    image = Image.open(path).convert('RGBA')
    b = image.getchannel('A').point(lambda p:255 if p>=8 else 0).getbbox()
    crop = [max(0,b[0]-8),max(0,b[1]-8),min(image.width,b[2]+8),min(image.height,b[3]+8)]
    return image.crop(crop),crop

def main():
    REPORT.mkdir(parents=True,exist_ok=True)
    design=json.loads((ROOT/'design/town-visuals.json').read_text())
    rows=[];layers={};recipes=[];sites=[]
    water=Image.new('L',(800,374));ImageDraw.Draw(water).polygon([tuple(p) for p in WATER_POLYGON],fill=255)
    save(water.convert('RGBA'),HERE/'background/water-annotation.png')
    terrain=Image.open(HERE/'background/native.png').convert('RGBA')
    for site in design['sites']:
        rect=RECTS[site['id']];x,y,w,h=rect;z=y+h
        if site['id']=='grailOrnament':z=137
        ns={'id':site['id'],'states':site['states'],'composition_rectangle':rect,
            'center':[x+w//2,y+h//2],'native_z':z,'layer_origin':[0,0],'source':{},'sha256':{},'selected_state_art':{}}
        for state in site['states']:
            master=HERE/state/'master.png' if state in NEW_STATES else ROOT/site['source'][state]
            im,crop=crop_master(master)
            im=ImageOps.contain(im,(w,h),Image.Resampling.LANCZOS)
            layer=Image.new('RGBA',(800,374));layer.alpha_composite(im,(x+(w-im.width)//2,y+h-im.height))
            out=HERE/'structures'/state;save(layer,out/'layer.png')
            mask=layer.getchannel('A').point(lambda p:255 if p>=128 else 0)
            area=Image.new('RGBA',layer.size,(255,255,255,0));area.putalpha(mask);save(area,out/'area.png')
            border=Image.new('RGBA',layer.size,(255,235,32,0));border.putalpha(ImageChops.subtract(mask.filter(ImageFilter.MaxFilter(5)),mask));save(border,out/'border.png')
            raw,_=crop_master(master)
            for name,size in [('hall-icon.png',(150,70)),('campaign.png',(58,64))]:
                thumb=ImageOps.contain(raw,(size[0]-8,size[1]-8),Image.Resampling.LANCZOS)
                icon=Image.new('RGBA',size);icon.alpha_composite(thumb,((size[0]-thumb.width)//2,(size[1]-thumb.height)//2));save(icon,out/name)
            # Ground-contact annotation covers lower opaque 10 pixels, not entire tall silhouette.
            b=mask.getbbox();foot=mask.copy();foot.paste(0,(0,0,800,max(0,b[3]-10)))
            wet=ImageChops.multiply(foot,water)
            row={'state':state,'site':site['id'],'master':rel(master),'master_sha256':sha(master),
                 'source_crop_xyxy':crop,'fit_size':list(im.size),'native_layer':rel(out/'layer.png'),
                 'native_layer_sha256':sha(out/'layer.png'),'native_z':z+(1 if state=='ship' else 0),
                 'composition_rectangle':rect,'click_bbox':b,'click_pixels':sum(mask.histogram()[128:]),
                 'footing_water_pixels':sum(wet.histogram()[128:]),'visual_approval_granted':False}
            rows.append(row);layers[state]=layer
            ns['source'][state]=rel(master);ns['sha256'][state]=sha(master);ns['selected_state_art'][state]=row
            generation=json.loads((master.parent/'generation.json').read_text())
            generation['conversion']={'revision':HERE.name,'crop':crop,'fit_size':list(im.size),'composition_rectangle':rect,
                'native_z':row['native_z'],'method':'Uniform LANCZOS contain; no warp/recolor or artwork generation in code'}
            for suffix in ['animation','area','border']:
                recipe=json.loads((ROOT/f'assets/recipes/town/structures/{state}-{suffix}.json').read_text())
                source=out/('layer.png' if suffix=='animation' else suffix+'.png')
                recipe['generation']=generation
                desc={'source':rel(source),'source_sha256':sha(source),'source_canvas':[800,374]}
                if suffix=='animation':recipe['groups'][0]['frames']=[desc]
                else:recipe.update(desc)
                target=HERE/'recipes/structures'/f'{state}-{suffix}.json';write(target,recipe);recipes.append(rel(target))
            iconrecipe=json.loads((ROOT/f'assets/recipes/town/structures/{state}-campaign.json').read_text())
            iconrecipe.update({'source':rel(out/'campaign.png'),'source_sha256':sha(out/'campaign.png'),'source_canvas':[58,64],'generation':generation})
            target=HERE/'recipes/structures'/f'{state}-campaign.json';write(target,iconrecipe);recipes.append(rel(target))
        if site['id']=='coast':ns['native_state_z']={'shipyard':374,'ship':375}
        sites.append(ns)
    bgrecipe=json.loads((ROOT/'assets/recipes/town/background.json').read_text())
    bgrecipe.update({'source':rel(HERE/'background/native.png'),'source_sha256':sha(HERE/'background/native.png'),
        'generation':json.loads((HERE/'background/generation.json').read_text())})
    target=HERE/'recipes/background.json';write(target,bgrecipe);recipes.append(rel(target))
    index=json.loads((ROOT/'assets/recipes/town/buildingIcons.json').read_text())
    for frame in index['frames']:
        source=HERE/'structures'/frame['building']/'hall-icon.png'
        frame.update({'source':rel(source),'source_sha256':sha(source),'source_canvas':[150,70]})
    index['generation']={'image_generation_used':False,'method':'Indexed technical assembly of separately pinned painted2D town candidate hall icons; see every state generation.json'}
    target=HERE/'recipes/buildingIcons.json';write(target,index);recipes.append(rel(target))
    proposal={'status':'authored configuration','art_status':'built-unreviewed','canvas':[800,374],
        'land_sites':16,'optional_coast_sites':1,'construction_states':35,'sites':sites,
        'terrain':{'master':rel(HERE/'background/master.png'),'master_sha256':sha(HERE/'background/master.png'),
            'native':rel(HERE/'background/native.png'),'native_sha256':sha(HERE/'background/native.png'),
            'water_polygon':WATER_POLYGON,'annotation':'Conservative manually observed creek water; dry land footings measured against annotation'},
        'recipe_paths':recipes,'visual_approval_granted':False,'acceptance':'pending',
        'layout_note':'Larger rear monuments; modest foreground services; irregular rooted community. Sixteen land sites; seven dwelling upgrades in place. Independent transparent states, bare terrain.'}
    write(DESIGN,proposal);write(HERE/'coordinator-handoff.json',proposal)
    # Native composites use real engine replacement semantics. Ship adds over shipyard.
    for variant in ['base','upgraded','coastal','grail']:
        canvas=terrain.copy()
        chosen=[]
        for site in sites:
            if site['id']=='coast':
                if variant in ['coastal','grail']:chosen.extend(['shipyard','ship'])
            elif site['id']=='grailOrnament':
                if variant=='grail':chosen.append('grail')
            else:chosen.append(site['states'][0 if variant=='base' else -1])
        chosen.sort(key=lambda s:next(r['native_z'] for r in rows if r['state']==s))
        for state in chosen:canvas.alpha_composite(layers[state])
        save(canvas,REPORT/f'{variant}-native.png')
    annotated=Image.open(REPORT/'grail-native.png').copy();d=ImageDraw.Draw(annotated)
    for site in sites:
        x,y,w,h=site['composition_rectangle'];d.rectangle((x,y,x+w-1,y+h-1),outline=(245,200,50,255));d.text((x+1,y+1),site['id'],fill=(255,255,230,255),stroke_width=1,stroke_fill=(10,10,10,255))
    d.line([tuple(p) for p in WATER_POLYGON],fill=(80,210,250,255),width=1);save(annotated,REPORT/'annotated-sites-water-native.png')
    sheet=Image.new('RGBA',(800,798),(32,29,24,255))
    old=Image.open(ROOT/'build/reports/art-review/town/recomposition-v2/full-town-native.png').convert('RGBA')
    sheet.alpha_composite(old,(0,14));sheet.alpha_composite(Image.open(REPORT/'grail-native.png'),(0,424))
    d=ImageDraw.Draw(sheet);d.text((3,0),'Previous selected composition (native800x374)',fill='white');d.text((3,408),'Candidate separate layers (native800x374)',fill='white');save(sheet,REPORT/'old-new-native.png')
    contact=Image.new('RGBA',(1000,7*150),(43,39,34,255));d=ImageDraw.Draw(contact)
    for i,row in enumerate(rows):
        im=layers[row['state']];b=im.getchannel('A').point(lambda p:255 if p>=8 else 0).getbbox();im=im.crop(b)
        im=ImageOps.contain(im,(194,124),Image.Resampling.LANCZOS);x=(i%5)*200;y=(i//5)*150
        contact.alpha_composite(im,(x+(200-im.width)//2,y));d.text((x+2,y+128),row['state'],fill='white')
    save(contact,REPORT/'all-35-states-contact.png')
    # Compare original native source pixels without modifying protected references.
    original=ROOT.parent/'runeterra-demacia/references/sheets/building-animation-00.png'
    ref=Image.open(original).convert('RGBA');refparts=[(0,0,330,220),(338,950,660,1190),(1015,1195,1340,1452)]
    comparison=Image.new('RGBA',(1000,500),(43,39,34,255))
    for i,box in enumerate(refparts):comparison.alpha_composite(ref.crop(box),(i*333,0))
    for i,state in enumerate(['blacksmith','capitol','mageGuild3']):
        im=layers[state];im=im.crop(im.getchannel('A').point(lambda p:255 if p>=8 else 0).getbbox());comparison.alpha_composite(im,(i*333+25,290))
    ImageDraw.Draw(comparison).text((5,265),'Original Castle native pixels above / candidate native-scale counterparts below; no aesthetic approval',fill='white')
    save(comparison,REPORT/'original-castle-native-comparison.png')
    # Conservative exposure: all other-site variants above a state, not just chosen upgrades.
    above=Image.new('L',(800,374));exposure=[]
    for site in sorted(sites,key=lambda s:s['native_z'],reverse=True):
        union=Image.new('L',(800,374))
        for state in site['states']:
            mask=layers[state].getchannel('A').point(lambda p:255 if p>=128 else 0)
            exposed=ImageChops.subtract(mask,above)
            if state=='shipyard':
                ship_mask=layers['ship'].getchannel('A').point(lambda p:255 if p>=128 else 0)
                exposed=ImageChops.subtract(exposed,ship_mask)
            exposure.append({'state':state,'site':site['id'],'exposed_click_pixels':sum(exposed.histogram()[128:])})
            union=ImageChops.lighter(union,mask)
        above=ImageChops.lighter(above,union)
    write(REPORT/'source-state-checks.json',{'rows':rows,'conservative_exposure':exposure,
        'native_original_reference':str(original),'native_original_sha256':sha(original),
        'land_states_dry':all(r['footing_water_pixels']==0 for r in rows if r['site']!='coast'),
        'visual_approval_granted':False})
    sys.path.insert(0,str(ROOT.parent/'scripts'));from faction_art_compile import create_compiler
    compiler=create_compiler('bandlecity');runs=[];errors=[]
    for run in range(2):
        outputs={};receipts=[]
        for recipepath in recipes:
            try:
                planned,receipt=compiler.plan(ROOT,ROOT/recipepath);receipts.append(receipt)
                for target,data in planned.items():
                    if target in outputs:raise ValueError('Duplicate producer: '+target)
                    outputs[target]=hashlib.sha256(data).hexdigest()
                    # Candidate payload only, never production generated/stage.
                    p=REPORT/f'compiler-run-{run+1}'/target;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
            except Exception as e:errors.append(recipepath+': '+str(e))
        runs.append(outputs);write(REPORT/f'compiler-run-{run+1}-receipts.json',receipts)
    result={'ok':not errors and runs[0]==runs[1], 'actual_shared_compiler':True,
        'runs':2,'recipe_count':len(recipes),'output_count':len(runs[0]),'identical_bytes':runs[0]==runs[1],
        'outputs':runs[0],'errors':errors,'active_generated_or_stage_written':False,'visual_approval_granted':False}
    write(REPORT/'compiler-determinism.json',result)
    print(json.dumps({k:result[k] for k in ['ok','runs','recipe_count','output_count','identical_bytes','errors']}))
    return 0 if result['ok'] else 2

if __name__=='__main__':raise SystemExit(main())
