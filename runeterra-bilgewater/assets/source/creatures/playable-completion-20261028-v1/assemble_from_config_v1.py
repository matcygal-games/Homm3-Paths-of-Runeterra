"""Technical assembler for explicitly annotated original painted2D source keys.

No generative drawing, limb interpolation or automatic bounding-box fitting.
Actual faction compiler is replayed twice; root owns canonical selection/staging.
"""
from pathlib import Path
import copy, json, sys, argparse
import numpy as np
from PIL import Image,ImageOps,ImageDraw
import assemble_candidate as h
from split_painted_islands import islands
SOURCE=Path(__file__).resolve().parent;PROJECT=SOURCE.parents[3]
def main(config_path):
    config_path=config_path.resolve();cfg=json.loads(config_path.read_text());unit=cfg['unit'];version=cfg.get('version',1)
    if not unit.isalnum()or not config_path.is_relative_to(SOURCE):raise ValueError('Own unit/config required')
    REPORT=PROJECT/f'build/reports/painted-creature-completion-20261028-v1/{unit}/candidate-v{version}'
    OUT=SOURCE/unit/f'native-v{version}';RECIPES=SOURCE/f'proposed-recipes-v{version}'/unit
    root=tuple(cfg.get('battle_root',[197,266]));canvas=tuple(cfg.get('battle_canvas',[450,400]))
    poses={};records={};masters={};source_images={};deps=[config_path,Path(__file__),SOURCE/'assemble_candidate.py',SOURCE/'split_painted_islands.py']
    for plate_name,plate in cfg['plates'].items():
        path=(SOURCE/plate['source']).resolve()
        if not path.is_relative_to(SOURCE):raise ValueError('Source escapes owned art root')
        im=Image.open(path).convert('RGBA');items=islands(im)
        if len(items)!=plate['expected_islands']:raise ValueError('Inspected source-island cohort changed: '+plate_name)
        if plate.get('source_sha256')!=h.sha(path.read_bytes()):raise ValueError('Source master pin changed')
        deps.append(path);prompt=path.with_name(path.name.replace('-raw.png','-prompt.txt'))
        if not prompt.is_file():raise ValueError('Exact prompt missing: '+str(prompt))
        deps.append(prompt);masters[plate_name]=path
        for label,annotation in plate['poses'].items():
            if label in poses:raise ValueError('Duplicate source pose')
            item=items[annotation['island']];arr=np.array(im);mask=np.zeros((im.height,im.width),dtype=np.uint8)
            for y,s,e in item['lines']:mask[y,s:e]=1
            arr[:,:,3]*=mask;key=Image.fromarray(arr);scale=plate['scale'];src_root=annotation['root']
            poses[label]=h.transform(key,src_root,scale,canvas,root);source_images[label]=key
            records[label]={'source':h.rel(path),'source_sha256':h.sha(path.read_bytes()),'source_canvas':list(im.size),'source_island_index':annotation['island'],'source_island_box':item['box'],'source_anatomical_root':src_root,'plate_pixel_scale':scale,'per_frame_bounds_fit':False,'native_root':list(root)}
    groups=[];frames=[];native={}
    for groupstr,labels in cfg['groups'].items():
        group=int(groupstr);seq=[];native[group]=[]
        for frame,label in enumerate(labels):
            im=poses[label];path=OUT/'right'/f'g{group:02d}-f{frame:03d}.png';h.save(path,im);h.save(OUT/'reverse'/path.name,ImageOps.mirror(im));seq.append(h.descriptor(path));native[group].append(im)
            frames.append({'group':group,'frame':frame,'pose':label,**records[label],'native_frame':h.descriptor(path),'native_alpha128_box':h.opaque_box(im)})
        groups.append({'group':group,'frames':seq});h.gif(REPORT/f'g{group:02d}.gif',native[group])
    companion=cfg['companions'];actor=source_images[companion['pose']];aroot=records[companion['pose']]['source_anatomical_root'];scale=companion['scale']
    bgpath=(SOURCE/'portrait-background-v1-raw.png');bg=Image.open(bgpath).convert('RGBA');deps.extend([bgpath,SOURCE/'portrait-background-v1-prompt.txt'])
    extra={'map':h.transform(actor,aroot,scale,(96,64),tuple(companion.get('map_root',[76,60]))),'attackLeft':h.transform(actor,aroot,scale,(64,64),tuple(companion.get('encounter_root',[44,60])))}
    extra['attackRight']=h.mirror_root(extra['attackLeft'],companion.get('encounter_root',[44,60])[0])
    close=actor.crop(tuple(companion['portrait_crop']))
    for role,size in [('large',(64,64)),('small',(32,32))]:
        im=bg.resize(size,Image.Resampling.LANCZOS);im.alpha_composite(close.resize(size,Image.Resampling.LANCZOS));extra[role]=im
    for role,im in extra.items():h.save(OUT/'companions'/f'{role}.png',im)
    deps=sorted(set(deps));pins=[{'path':h.rel(p),'sha256':h.sha(p.read_bytes())}for p in deps]
    ledger=SOURCE/unit/f'cohort-candidate-v{version}.json'
    h.record(ledger,{'status':'authored configuration','selected':False,'unit':unit,'frames':frames,'production_inputs':pins,'native_execution':'not_run','release_accepted':False,'unresolved':cfg['unresolved'],'excluded_source_keys':cfg.get('excluded_source_keys',[]),'source_measured_projectiles':cfg.get('muzzle_measurements')})
    first=masters[next(iter(masters))]
    generation={'image_generation_used':True,'provider':'OpenAI built-in imagegen','model':'not exposed by built-in tool','prompt':'Exact pinned per-source prompts and original painted2D masters are listed in production_inputs. All selected poses are genuine independent painted silhouettes; only technical island separation, explicit plate camera/root registration and conversion are applied. No3D or retired render producers.','painted_master':h.rel(first),'painted_master_sha256':h.sha(first.read_bytes()),'provenance':h.rel(ledger),'provenance_sha256':h.sha(ledger.read_bytes()),'production_inputs':pins}
    common={'production_status':'painted-master-complete-unapproved','unit':unit,'generation':generation,'status':'authored configuration','acceptance':'Isolated unselected painted candidate; motion/root/crest/native/rights review remains pending','credits':{'author':'Project-directed OpenAI built-in imagegen; technical2D assembly','license':None,'redistribution':'unresolved; release prohibited'}}
    prefix=f'Content/Sprites/runeterra/bilgewater/creatures/{unit}/'
    h.record(RECIPES/'battle.json',{**common,'recipe_type':'vcmi_animation','output_path':prefix+'battle.json','canvas':list(canvas),'pivot':{'x':root[0],'y':root[1]},'generateShadow':1,'generateOverlay':1,'groups':groups})
    for role,im in extra.items():
        p=OUT/'companions'/f'{role}.png'
        if role=='map':r={**common,'recipe_type':'vcmi_animation','output_path':prefix+'map.json','canvas':[96,64],'pivot':dict(zip(('x','y'),companion.get('map_root',[76,60]))),'generateShadow':1,'generateOverlay':0,'groups':[{'group':0,'frames':[h.descriptor(p)]}]}
        else:r={**common,'recipe_type':'raster','output_path':prefix+role+'.png','size':list(im.size),'fit':'exact',**h.descriptor(p)}
        h.record(RECIPES/f'{role}.json',r)
    if cfg.get('projectile'):
        pinfo=cfg['projectile'];p=(SOURCE/pinfo['source']).resolve();im=Image.open(p).convert('RGBA');items=islands(im)
        if h.sha(p.read_bytes())!=pinfo['source_sha256']or len(items)!=pinfo['expected_islands']:raise ValueError('Painted projectile source changed')
        seq=[]
        for frame,key in enumerate(pinfo['frames']):
            item=items[key['island']];a=np.array(im);mask=np.zeros((im.height,im.width),dtype=np.uint8)
            for y,s,e in item['lines']:mask[y,s:e]=1
            a[:,:,3]*=mask;out=h.transform(Image.fromarray(a),key['root'],pinfo['scale'],(40,40),(20,20));path=OUT/'projectile'/f'angle-{frame}.png';h.save(path,out);seq.append(h.descriptor(path))
        pg={**generation,'painted_master':h.rel(p),'painted_master_sha256':h.sha(p.read_bytes()),'production_inputs':pins+[{'path':h.rel(p),'sha256':h.sha(p.read_bytes())},{'path':h.rel(p.with_name(p.name.replace('-raw.png','-prompt.txt'))),'sha256':h.sha(p.with_name(p.name.replace('-raw.png','-prompt.txt')).read_bytes())}]}
        h.record(RECIPES/'projectile.json',{**common,'generation':pg,'recipe_type':'vcmi_animation','output_path':f'Content/Sprites/runeterra/bilgewater/projectiles/{unit}.json','canvas':[40,40],'pivot':{'x':20,'y':20},'generateShadow':0,'generateOverlay':0,'groups':[{'group':0,'frames':seq}]})
    sys.path.insert(0,str(PROJECT.parent/'scripts'));import faction_art_compile
    compiler=faction_art_compile.create_compiler('bilgewater');allhashes=[];receipts=[]
    for replay in (1,2):
        hashes={}
        for recipe in sorted(RECIPES.glob('*.json')):
            outputs,receipt=compiler.plan(PROJECT,recipe)
            for name,data in outputs.items():h.put(REPORT/f'compile-pass-{replay}'/name,data);hashes[name]=h.sha(data)
            receipts.append({'pass':replay,**receipt})
        allhashes.append(hashes)
    if allhashes[0]!=allhashes[1]:raise ValueError('Compiler replay changed bytes')
    h.record(REPORT/'actual-compiler-replay-v1.json',{'status':'authored configuration','deterministic':True,'outputs_per_pass':len(allhashes[0]),'output_hashes':allhashes[0],'receipts':receipts,'native_execution':False,'visual_approval_granted':False})
    width=max(len(images)for images in native.values());sheetout=Image.new('RGB',(width*160,len(native)*150),(84,90,80));d=ImageDraw.Draw(sheetout)
    for row,(group,images)in enumerate(native.items()):
        for col,im in enumerate(images):crop=h.preview(im);sheetout.paste(crop,(col*160,row*150),crop);d.text((col*160+3,row*150+130),f'g{group:02d} f{col}',fill='white')
    h.save(REPORT/'native-contact-sheet-v1.png',sheetout)
    # Guarded proposal only: preserve exact current entry/recipe expectations.
    manifest=PROJECT/'assets/manifest.json';rows=json.loads(manifest.read_text())['assets'];changes=[]
    for recipe in sorted(RECIPES.glob('*.json')):
        r=json.loads(recipe.read_text());entry=next((e for e in rows if e.get('output_path')==r['output_path']),None)
        changes.append({'output_path':r['output_path'],'expected_manifest_entry_sha256':h.sha(h.encoded(entry))if entry else None,'proposed_recipe':h.rel(recipe),'proposed_recipe_sha256':h.sha(recipe.read_bytes()),'compiled_sha256':allhashes[0][r['output_path']],'dimensions':r.get('canvas',r.get('size')),'groups':{str(g['group']):len(g['frames'])for g in r.get('groups',[])},'current_recipe':entry.get('source',{}).get('recipe')if entry else None})
    h.record(REPORT/'root-integration-proposal-v1.json',{'status':'authored configuration','apply_automatically':False,'selected':False,'unit':unit,'expected_manifest_sha256':h.sha(manifest.read_bytes()),'changes':changes,'graphics_offset_proposal':cfg.get('muzzle_measurements'),'native_execution':False,'remaining':cfg['unresolved']})
    h.put(REPORT/'index.html',('<html><head><meta charset="utf-8"><title>'+unit+' painted candidate</title></head><body style="background:#202923;color:#eee;font-family:system-ui"><h1>'+unit+' — unselected painted source candidate</h1><p>Actual two-pass compiler replay, source action sheets and deterministic native PNG/JSON. Native motion, appearance, root and crest review remain pending.</p><img src="native-contact-sheet-v1.png" style="max-width:100%"><p>'+''.join(f'<a href="g{g:02d}.gif">g{g:02d} motion</a> 'for g in native)+'</p><a href="root-integration-proposal-v1.json">Guarded integration proposal</a> · <a href="actual-compiler-replay-v1.json">Actual compiler receipts</a></body></html>').encode())
    print(json.dumps({'unit':unit,'frames':len(frames),'recipes':len(list(RECIPES.glob('*.json'))),'outputs_per_pass':len(allhashes[0]),'deterministic':True,'selected':False,'report':str(REPORT/'index.html')}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('config',type=Path);main(p.parse_args().config)
