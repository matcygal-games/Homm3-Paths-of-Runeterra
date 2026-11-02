"""Sea Dog painted2D proposal. The touching source pair is not selected.

Imports the preserved v1 technical primitives and actual native compiler. Only
new source/report/proposed-recipe paths are written; no canonical selection.
"""
from pathlib import Path
import importlib.util, json, sys, hashlib
from PIL import Image, ImageOps, ImageDraw
import numpy as np
import assemble_candidate as h
from split_painted_islands import islands
SOURCE=Path(__file__).resolve().parent;PROJECT=SOURCE.parents[3]
UNIT='seaDog';REPORT=PROJECT/'build/reports/painted-creature-completion-20261028-v1'/UNIT
ROOT=(197,266);CANVAS=(450,400)
def sheet(name):
    p=SOURCE/UNIT/name;im=Image.open(p).convert('RGBA');components=islands(im);out=[]
    for item in components:
        a=np.array(im);m=np.zeros((im.height,im.width),dtype=np.uint8)
        for y,s,e in item['lines']:m[y,s:e]=1
        a[:,:,3]*=m;out.append(Image.fromarray(a))
    return p,out,[q['box']for q in components]
def main():
    REPORT.mkdir(parents=True,exist_ok=True)
    paths={};poses={};records={}
    # Index ordering is fixed by inspected connected source islands, not cells.
    assignments={
      'attacks-v1-raw.png':(.25,[(2,'up0',(170,389)),(0,'up1',(535,389)),(1,'up2',(925,393)),(3,'ready',(1305,395)),(5,'front0',(190,726)),(6,'front1',(535,726)),(7,'front2',(925,731)),(8,'down0',(175,1065))]),
      'reactions-v1-raw.png':(.25,[(0,'idle',(167,423)),(1,'defend',(495,423)),(2,'hurt0',(825,423)),(3,'hurt1',(1165,423)),(7,'turn0',(175,821)),(6,'turn1',(500,821)),(4,'turn2',(835,821)),(5,'turn3',(1165,818)),(8,'death0',(170,1111)),(9,'death1',(495,1118)),(10,'death2',(825,1118)),(11,'death3',(1135,1121))]),
      'walk-v1-raw.png':(.20,[(0,'walk0',(292,479)),(1,'walk1',(785,483)),(2,'walk2',(1285,478)),(3,'walk3',(305,962)),(5,'walk4',(785,952)),(4,'walk5',(1285,958))]),
      'down-repair-v1-raw.png':(.12,[(1,'down1',(510,719)),(0,'down2',(1475,721))])}
    for name,(scale,items)in assignments.items():
        p,images,boxes=sheet(name);paths[name]=p
        for index,label,root in items:
            if index>=len(images):raise RuntimeError('Missing inspected source island: '+name)
            poses[label]=h.transform(images[index],root,scale)
            records[label]={'master':h.rel(p),'master_sha256':h.sha(p.read_bytes()),'source_island_index':index,'source_island_box':boxes[index],'source_anatomical_root':list(root),'plate_pixel_scale':scale,'per_frame_bounds_fit':False,'native_root':list(ROOT)}
    order={0:['walk0','walk1','walk2','walk3','walk4','walk5'],1:['ready','idle'],2:['ready'],3:['hurt0','hurt1','ready'],4:['defend','ready'],5:['death0','death1','death2','death3'],7:['turn0','turn1','turn2','turn3'],8:['turn3','turn2','turn1','turn0'],11:['up0','up1','up2','ready'],12:['front0','front1','front2','ready'],13:['down0','down1','down2','ready'],20:['ready','walk1'],21:['walk4','ready'],22:['death3']}
    out=SOURCE/UNIT/'native-candidate-v1';groups=[];ledger=[];native={}
    for group,labels in order.items():
        seq=[];native[group]=[]
        for frame,label in enumerate(labels):
            im=poses[label];p=out/'right'/f'g{group:02d}-f{frame:03d}.png';h.save(p,im);h.save(out/'reverse'/p.name,ImageOps.mirror(im));seq.append(h.descriptor(p));native[group].append(im)
            ledger.append({'group':group,'frame':frame,'pose':label,**records[label],'native_frame':h.descriptor(p),'native_alpha128_box':h.opaque_box(im)})
        groups.append({'group':group,'frames':seq});h.gif(REPORT/f'g{group:02d}.gif',native[group])
    deps=[]
    for path in sorted([*paths.values(),*(SOURCE/UNIT).glob('*-prompt.txt'),Path(__file__),SOURCE/'assemble_candidate.py',SOURCE/'split_painted_islands.py',SOURCE/'portrait-background-v1-raw.png',SOURCE/'portrait-background-v1-prompt.txt']):
        deps.append({'path':h.rel(path),'sha256':h.sha(path.read_bytes())})
    proof=SOURCE/UNIT/'cohort-candidate-v1.json'
    h.record(proof,{'status':'authored configuration','unit':UNIT,'selected':False,'frames':ledger,'production_inputs':deps,'excluded_source_island':{'master':h.rel(paths['attacks-v1-raw.png']),'index':10,'reason':'Two lower attack silhouettes touched; complete independent painted repair poses replace both'},'native_execution':'not_run','release_accepted':False,'unresolved':['Opposite support and gait continuity need complete motion review','Both facings and stock crops need native observation','Exact crest legibility at native size needs independent visual review']})
    generation={'image_generation_used':True,'provider':'OpenAI built-in imagegen','model':'not exposed by built-in tool','prompt':'Exact per-source prompts are pinned in production_inputs; coherent painted2D upgrade transfers and independent genuine lower-strike repair. No3D producer or previous rendered frames selected.','painted_master':h.rel(paths['attacks-v1-raw.png']),'painted_master_sha256':h.sha(paths['attacks-v1-raw.png'].read_bytes()),'provenance':h.rel(proof),'provenance_sha256':h.sha(proof.read_bytes()),'production_inputs':deps}
    common={'production_status':'painted-master-complete-unapproved','unit':UNIT,'generation':generation,'status':'authored configuration','acceptance':'Unselected technical candidate; complete source motion, native appearance/playability and rights review pending','credits':{'author':'Project-directed OpenAI built-in imagegen; technical2D assembly','license':None,'redistribution':'unresolved; release prohibited'}}
    recipes=SOURCE/'proposed-recipes'/UNIT;prefix=f'Content/Sprites/runeterra/bilgewater/creatures/{UNIT}/'
    h.record(recipes/'battle.json',{**common,'recipe_type':'vcmi_animation','output_path':prefix+'battle.json','canvas':list(CANVAS),'pivot':{'x':ROOT[0],'y':ROOT[1]},'generateShadow':1,'generateOverlay':1,'groups':groups})
    rp,imgs,boxes=sheet('reactions-v1-raw.png');actor=imgs[0];root=(167,423)
    extra={'map':h.transform(actor,root,.13,(96,64),(76,60)),'attackLeft':h.transform(actor,root,.13,(64,64),(44,60))}
    extra['attackRight']=h.mirror_root(extra['attackLeft'],44)
    bg=Image.open(SOURCE/'portrait-background-v1-raw.png').convert('RGBA');close=actor.crop((90,96,265,270))
    for role,size in [('large',(64,64)),('small',(32,32))]:
        im=bg.resize(size,Image.Resampling.LANCZOS);im.alpha_composite(close.resize(size,Image.Resampling.LANCZOS));extra[role]=im
    for role,im in extra.items():
        p=out/'companions'/f'{role}.png';h.save(p,im)
        if role=='map':r={**common,'recipe_type':'vcmi_animation','output_path':prefix+'map.json','canvas':[96,64],'pivot':{'x':76,'y':60},'generateShadow':1,'generateOverlay':0,'groups':[{'group':0,'frames':[h.descriptor(p)]}]}
        else:r={**common,'recipe_type':'raster','output_path':prefix+role+'.png','size':list(im.size),'fit':'exact',**h.descriptor(p)}
        h.record(recipes/f'{role}.json',r)
    sheetout=Image.new('RGB',(6*160,len(native)*150),(84,90,80));d=ImageDraw.Draw(sheetout)
    for row,(group,images)in enumerate(native.items()):
        for col,im in enumerate(images):crop=h.preview(im);sheetout.paste(crop,(col*160,row*150),crop);d.text((col*160+3,row*150+130),f'g{group:02d} f{col}',fill='white')
    h.save(REPORT/'native-contact-sheet-v1.png',sheetout)
    sys.path.insert(0,str(PROJECT.parent/'scripts'));import faction_art_compile
    compiler=faction_art_compile.create_compiler('bilgewater');hashes=[];receipts=[]
    for replay in (1,2):
        pins={}
        for recipe in sorted(recipes.glob('*.json')):
            outputs,receipt=compiler.plan(PROJECT,recipe)
            for name,data in outputs.items():h.put(REPORT/f'compile-pass-{replay}'/name,data);pins[name]=h.sha(data)
            receipts.append({'pass':replay,**receipt})
        hashes.append(pins)
    if hashes[0]!=hashes[1]:raise RuntimeError('Actual compiler replay differs')
    h.record(REPORT/'actual-compiler-replay-v1.json',{'status':'authored configuration','deterministic':True,'outputs_per_pass':len(hashes[0]),'output_hashes':hashes[0],'receipts':receipts,'native_execution':False,'visual_approval_granted':False})
    h.put(REPORT/'index.html',('<html><head><meta charset="utf-8"><title>Sea Dog painted candidate</title></head><body style="background:#202923;color:#eee;font-family:system-ui"><h1>Sea Dog — unselected painted source candidate</h1><p>Real compiler conversion, genuine poses and two lower-strike repairs. Gait, both native facings and crest legibility remain under review.</p><img src="native-contact-sheet-v1.png" style="max-width:100%"><p>'+''.join(f'<a href="g{g:02d}.gif">g{g:02d} motion</a> 'for g in native)+'</p><a href="actual-compiler-replay-v1.json">Actual conversion receipts</a></body></html>').encode())
    print(json.dumps({'unit':UNIT,'frames':len(ledger),'recipes':len(list(recipes.glob('*.json'))),'outputs_per_pass':len(hashes[0]),'deterministic':True,'selected':False,'report':str(REPORT/'index.html')}))
if __name__=='__main__':main()
