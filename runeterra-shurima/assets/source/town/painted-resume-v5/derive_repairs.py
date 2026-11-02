"""Two painted progression repairs; direct strict planning, no publication.

Candidate recipe payloads deliberately stay outside active recipe enumeration:
the coordinator must replace the corresponding v4 producer on integration.
Only full generated canvases are resampled, at the inherited chain scale.
"""
from pathlib import Path
import hashlib, importlib.util, json, sys
from PIL import Image, ImageChops, ImageDraw
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
WORKSPACE = PROJECT.parent
REPORT = PROJECT/'build/reports/town-painted-resume-20261024-v5'
HELPER = PROJECT/'assets/source/town/painted-resume-v2/derive_states.py'
HELPER_SHA = '9244b8e0109d40de74eab4b9716d43ac7cb170f6aaebdda3daa96b045d4eb56f'
PREFIX = 'Content/Sprites/runeterra/shurima/town/structures/'
KEYS = ('dwellingUpLvl3', 'dwellingUpLvl7')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_bytes())
def put(p, raw):
    assert any(p.resolve().is_relative_to(r) for r in (HERE, REPORT))
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as f: f.write(raw)
def write(p, value): put(p, (json.dumps(value, sort_keys=True, indent=2)+'\n').encode())
def helper():
    assert sha(HELPER) == HELPER_SHA
    spec=importlib.util.spec_from_file_location('painted_v2_pure', HELPER)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
def contact(im): return im.getchannel('A').point(lambda a: 255 if a >= 32 else 0).getbbox()[3]
def register(im, job):
    assert im.mode == 'RGBA' and list(im.size) == job['source_canvas']
    piece=im.resize(tuple(job['resampled_size']), Image.Resampling.LANCZOS)
    assert job['placement'][1] + contact(piece) == job['foundation_alpha32_contact']
    x,y=job['placement']; box=piece.getchannel('A').getbbox()
    assert 0 <= x+box[0] < x+box[2] <= 800 and 0 <= y+box[1] < y+box[3] <= 374, 'No viewport clipping permitted'
    frame=Image.new('RGBA',(800,374)); frame.alpha_composite(piece,(x,y)); return frame
def main():
    h=helper(); baseline=read(REPORT/'input-baseline.json')
    assert all(sha(PROJECT/p)==pin for p,pin in baseline['preserved'].items()), 'Preserved input drift'
    old=read(PROJECT/'build/reports/town-painted-resume-20261023-v4/conversion-final.json')
    lookup={k:PROJECT/v['source'] for k,v in old['all35_frame_sources'].items()}
    bases={v['key']:v for v in read(PROJECT/'assets/source/town/painted-resume-v1/provenance.json')['states']}
    prior={v['key']:v for v in read(PROJECT/'assets/source/town/painted-resume-v4/registration.json')['states']}
    faction=read(PROJECT/'content/factions.json')['shurima']['town']
    visuals=read(PROJECT/'design/town-visuals.json'); records=[]; outputs_all={}; receipts=[]
    active={}
    for path in (PROJECT/'assets/recipes').rglob('*.json'):
        r=read(path)
        for name in [r.get('output_path'),*r.get('output_paths',[])]:
            if name: active.setdefault(name,[]).append(path.relative_to(PROJECT).as_posix())
    targets=[PREFIX+k+s for k in KEYS for s in ('.json','_area.png','_border.png','_campaign.png')]
    collisions={name:active[name] for name in targets if name in active}
    assert len(collisions)==8 and all(len(p)==1 and '/painted-resume-v4/' in p[0] for p in collisions.values())
    collision_record={'existing_producers':collisions,'decision':'Preserve v4; candidate JSON only in report recipe-payload. Root must select exactly one producer per resource.','active_recipe_writes':False}
    collision_path=REPORT/'producer-collisions.json'
    if collision_path.exists(): assert read(collision_path)==collision_record
    else: write(collision_path,collision_record)
    sys.path.insert(0,str(WORKSPACE/'scripts')); import faction_art_compile
    compiler=faction_art_compile.create_compiler('shurima')
    for key in KEYS:
        master=HERE/key/'master.png'; meta=read(HERE/key/'master-generation.json')
        assert sha(master)==meta['master_sha256'] and sha(HERE/key/'prompt.txt')==meta['prompt_sha256']
        assert all(sha(PROJECT/v['path'])==v['sha256'] for v in meta['inputs'])
        parent='special2' if key.endswith('3') else 'special4'; base=bases[prior[key]['base_site']]
        assert faction['buildings'][key]['upgrades']==parent
        with Image.open(master) as src: src.load(); image=src.copy()
        scale=base['uniform_scale']; size=[round(image.width*scale),round(image.height*scale)]
        with Image.open(lookup[parent]) as p: ground=contact(p)
        piece=image.resize(tuple(size),Image.Resampling.LANCZOS)
        job={'key':key,'parent':parent,'source_canvas':list(image.size),'source_crop':[0,0,*image.size],
             'resampled_size':size,'uniform_chain_scale':scale,
             'placement':[base['placement'][0]+(base['resampled_size'][0]-size[0])//2,ground-contact(piece)],
             'foundation_alpha32_contact':ground,'native_site_box':prior[key]['native_site_box'],
             'registration':'Complete generated canvas at original base source-pixel scale; same horizontal source center, parent alpha32 foundation contact. No opaque bbox fit, clipping or artistic cleanup.'}
        frame=register(image,job); surfaces=h.surfaces(frame,image); sources={}
        for role,im in surfaces.items():
            path=HERE/key/(role+'.png'); put(path,h.png(im)); sources[role]={'path':path.relative_to(PROJECT).as_posix(),'sha256':sha(path)}
        common={'status':'painted-candidate','production_status':'painted-master-complete-unapproved','visual_approval_granted':False,
                'generation':{'image_generation_used':True,'provider':'builtin image_gen','model':'not exposed by built-in tool','painted_master':master.relative_to(PROJECT).as_posix(),'painted_master_sha256':sha(master),'prompt':(HERE/key/'prompt.txt').read_text(),'prompt_file':(HERE/key/'prompt.txt').relative_to(PROJECT).as_posix()},
                'credits':{'author':'Project-directed builtin image generation; deterministic technical conversion','license':None,'redistribution':'unresolved; no release approval'}}
        mappings=[]
        for role,recipe in h.recipe_set(key,sources,common,job).items():
            path=REPORT/'recipe-payload'/(key+'-'+role+'.json'); write(path,recipe)
            outputs,receipt=compiler.plan(PROJECT,path); receipts.append(receipt)
            for name,raw in outputs.items():
                assert name not in outputs_all; put(REPORT/'compiled'/name,raw)
                outputs_all[name]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'recipe_path':path.relative_to(PROJECT).as_posix(),'recipe_sha256':sha(path)}
            mappings.append({'output_path':recipe['output_path'],'recipe_path':path.relative_to(PROJECT).as_posix(),'recipe_sha256':sha(path)})
        records.append({'key':key,'registration':job,'master_sha256':sha(master),'derived_sources':sources,'outputs':mappings,'native_alpha_bbox':frame.getchannel('A').getbbox()})
        lookup[key]=HERE/key/'frame.png'
    with Image.open(PROJECT/'assets/source/town/landscape-v1/native-rgba.png') as src: terrain=src.convert('RGBA')
    def scene(keys, new=True):
        im=terrain.copy()
        for k in sorted(keys,key=lambda k:faction['structures'][k]['z']):
            p=lookup[k] if new else PROJECT/old['all35_frame_sources'][k]['source']
            with Image.open(p) as layer: im.alpha_composite(layer)
        return im
    exposures={}; intersections={}
    for name,keys in old['variants'].items():
        put(REPORT/(name+'-800x374.png'),h.png(scene(keys)))
        covered=Image.new('L',(800,374)); rows={}
        for k in sorted(keys,key=lambda k:faction['structures'][k]['z'],reverse=True):
            with Image.open(lookup[k]) as im: mask=im.getchannel('A').point(lambda a:255 if a>=128 else 0)
            count=mask.histogram()[255]; exposed=ImageChops.subtract(mask,covered).histogram()[255]
            rows[k]={'click_pixels':count,'exposed_click_pixels':exposed,'covered_click_pixels':count-exposed}
            covered=ImageChops.lighter(mask,covered)
        exposures[name]=rows
        if name=='all-upgraded':
            for k in KEYS:
                with Image.open(lookup[k]) as im: mask=im.getchannel('A').point(lambda a:255 if a>=128 else 0)
                overlaps={}
                for other in keys:
                    if other==k: continue
                    with Image.open(lookup[other]) as im: othermask=im.getchannel('A').point(lambda a:255 if a>=128 else 0)
                    count=ImageChops.darker(mask,othermask).histogram()[255]
                    if count: overlaps[other]=count
                intersections[k]=overlaps
    keys=old['variants']['all-upgraded']; before=scene(keys,False); after=scene(keys)
    pair=Image.new('RGBA',(1600,374)); pair.alpha_composite(before); pair.alpha_composite(after,(800,0)); put(REPORT/'town-before-after-1600x374.png',h.png(pair))
    for n,key in enumerate(KEYS):
        parent='special2' if n==0 else 'special4'; base='dwellingLvl3' if n==0 else 'dwellingLvl7'
        crop=(0,175,190,298) if n==0 else (0,25,195,158)
        cohort=Image.new('RGBA',((crop[2]-crop[0])*4,crop[3]-crop[1]+20),(40,40,40,255)); draw=ImageDraw.Draw(cohort)
        for i,k in enumerate((base,parent,key,key)):
            layer=PROJECT/old['all35_frame_sources'][k]['source'] if i==2 else lookup[k]
            im=terrain.copy()
            with Image.open(layer) as raw: im.alpha_composite(raw)
            cohort.alpha_composite(im.crop(crop),(i*(crop[2]-crop[0]),20)); draw.text((i*(crop[2]-crop[0])+2,3),('base','intermediate','old final','v5 final')[i],fill='white')
        put(REPORT/(key+'-cohort-native.png'),h.png(cohort))
    assert all(sha(PROJECT/p)==pin for p,pin in baseline['preserved'].items()), 'Input drift during conversion'
    write(HERE/'provenance.json',{'producer':Path(__file__).relative_to(PROJECT).as_posix(),'producer_sha256':sha(Path(__file__)),'helper_sha256':HELPER_SHA,'states':records,'native_execution':False,'visual_approval_granted':False})
    write(REPORT/'conversion.json',{'states':records,'results':receipts,'compiled_outputs':outputs_all,'exposure':exposures,'assigned_solid_alpha_intersections':intersections,'actual_converter_sha256':sha(WORKSPACE/'scripts/faction_art_compile.py'),'native_execution':False,'active_recipe_writes':False,'global_generated_written':False,'manifest_modified':False,'visual_approval_granted':False})
    print(json.dumps({'states':len(records),'recipes':len(receipts),'compiled_resources':len(outputs_all),'native_execution':False}))
if __name__=='__main__': main()
