"""Isolated genuine painted-source candidate assembly, never canonical publication.

Source sheet camera calibration is explicit per plate and never per-pose bounds
fitting. Every selected pose is a whole painted alpha island. No limbs, equipment
or creative pixels are drawn, warped, interpolated or attached by this code.
"""
from pathlib import Path
import hashlib, io, json, sys
import numpy as np
from PIL import Image, ImageDraw, ImageOps
from split_painted_islands import islands

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
WORKSPACE=PROJECT.parent
REPORT=PROJECT/'build/reports/painted-creature-completion-20261028-v1'
UNIT='bilgeRat'
CANVAS=(450,400); ROOT=(197,266)
def encoded(v):return (json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def sha(data):return hashlib.sha256(data).hexdigest()
def rel(p):return p.relative_to(PROJECT).as_posix()
def put(p,data):
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists() and p.read_bytes()!=data:raise RuntimeError('Preserve existing changed candidate: '+str(p))
    if not p.exists():p.write_bytes(data)
def record(p,v):put(p,encoded(v))
def png(im):
    f=io.BytesIO();im.save(f,format='PNG',compress_level=9,optimize=False);return f.getvalue()
def save(p,im):put(p,png(im))
def descriptor(p):return {'source':rel(p),'source_sha256':sha(p.read_bytes()),'source_canvas':list(Image.open(p).size)}
def plate(name,rows,columns):
    path=SOURCE/UNIT/name;im=Image.open(path).convert('RGBA');components=islands(im)
    if len(components)!=rows*columns:raise RuntimeError('Unexpected painted-island count: '+name)
    # Observed source poses have separate connected silhouettes. Assign rows by
    # baseline, not an assumed equal grid that could cut off a painted sword.
    ordered=[]
    for offset in range(0,len(components),columns):
        pass
    # Every upright/reaction/death row occupies a separate horizontal band.
    by_y=sorted(components,key=lambda q:q['box'][3])
    for row in range(rows):
        ordered.extend(sorted(by_y[row*columns:(row+1)*columns],key=lambda q:q['box'][0]))
    images=[]
    for q in ordered:
        a=np.array(im);mask=np.zeros((im.height,im.width),dtype=np.uint8)
        for y,s,e in q['lines']:mask[y,s:e]=1
        a[:,:,3]*=mask
        # This retains original source coordinates; no crop-fitting/root inference.
        images.append(Image.fromarray(a))
    return path,images,[q['box']for q in ordered]
def transform(im,source_root,scale,canvas=CANVAS,root=ROOT):
    factor=4;tx=root[0]-source_root[0]*scale;ty=root[1]-source_root[1]*scale
    inverse=(1/(scale*factor),0,-tx/scale,0,1/(scale*factor),-ty/scale)
    return im.transform((canvas[0]*factor,canvas[1]*factor),Image.Transform.AFFINE,inverse,Image.Resampling.BICUBIC).resize(canvas,Image.Resampling.LANCZOS)
def mirror_root(im,x):
    out=Image.new('RGBA',im.size);out.paste(ImageOps.mirror(im),(round(2*x-(im.width-1)),0));return out
def opaque_box(im):return im.getchannel('A').point(lambda v:255 if v>=128 else 0).getbbox()
def preview(im):return im.crop((121,158,281,286))
def gif(path,frames):
    frames=[preview(im) for im in frames];render=[]
    for im in frames:
        bg=Image.new('RGB',im.size,(84,90,80));bg.paste(im,(0,0),im);render.append(bg)
    b=io.BytesIO();render[0].save(b,format='GIF',save_all=True,append_images=render[1:],duration=160,loop=0,optimize=False,disposal=2);put(path,b.getvalue())
def main():
    REPORT.mkdir(parents=True,exist_ok=True)
    ap,attack,ab=plate('attacks-v2-raw.png',3,4)
    rp,reaction,rb=plate('reactions-v2-raw.png',3,4)
    wp,walk,wb=plate('walk-v3-raw.png',2,2)
    # Fixed manual anatomical/projected-root coordinates from full source pixel
    # inspection. Plate-wide scale normalizes independently generated sheet
    # camera magnification; all poses on a sheet use exactly the same scale.
    attack_roots=[(165,376),(525,377),(905,377),(1300,379),(190,703),(530,703),(905,704),(1300,704),(170,1045),(525,1042),(905,1042),(1300,1048)]
    reaction_roots=[(166,421),(495,421),(825,420),(1165,421),(170,818),(500,818),(835,818),(1165,816),(170,1109),(495,1116),(825,1113),(1135,1120)]
    walk_roots=[(410,586),(1000,586),(410,1117),(1000,1117)]
    sources={}
    for name,path,images,boxes,roots,scale in [('attack',ap,attack,ab,attack_roots,.25),('reaction',rp,reaction,rb,reaction_roots,.25),('walk',wp,walk,wb,walk_roots,.17)]:
        for index,(im,box,root) in enumerate(zip(images,boxes,roots)):
            native=transform(im,root,scale)
            sources[(name,index)]=(native,{'master':rel(path),'master_sha256':sha(path.read_bytes()),'island':index,'source_island_box':box,'source_anatomical_root':list(root),'plate_pixel_scale':scale,'per_frame_bounds_fit':False,'native_root':list(ROOT)})
    keys={0:[('walk',i)for i in range(4)],1:[('attack',3),('reaction',0)],2:[('attack',3)],3:[('reaction',2),('reaction',3),('attack',3)],4:[('reaction',1),('attack',3)],5:[('reaction',i)for i in range(8,12)],7:[('reaction',i)for i in range(4,8)],8:[('reaction',i)for i in range(7,3,-1)],11:[('attack',i)for i in range(4)],12:[('attack',i)for i in range(4,8)],13:[('attack',i)for i in range(8,12)],20:[('attack',3),('walk',1)],21:[('walk',3),('attack',3)],22:[('reaction',11)]}
    groups=[];all_records=[];native={}
    out=SOURCE/UNIT/'native-candidate-v1'
    for group,items in keys.items():
        seq=[];native[group]=[]
        for frame,key in enumerate(items):
            im,entry=sources[key];p=out/'right'/f'g{group:02d}-f{frame:03d}.png';save(p,im)
            save(out/'reverse'/p.name,ImageOps.mirror(im));seq.append(descriptor(p));native[group].append(im)
            all_records.append({'group':group,'frame':frame,**entry,'native_frame':descriptor(p),'native_alpha128_box':opaque_box(im)})
        groups.append({'group':group,'frames':seq})
        gif(REPORT/UNIT/f'g{group:02d}.gif',native[group])
    painted=SOURCE/UNIT/'cohort-candidate-v1.json'
    ledger={'status':'authored configuration','selected':False,'unit':UNIT,'frames':all_records,'technical_assembler':rel(Path(__file__)),'assembler_sha256':sha(Path(__file__).read_bytes()),'native_execution':'not_run','release_accepted':False,'unresolved':['Opposite-support gait is not visually established','Plate-camera normalization and anatomical root continuity require complete playback review','Canonical selection and source-policy admission have not run','Both native facings and stock creature-window body crops require observation']}
    record(painted,ledger)
    generation={'image_generation_used':True,'provider':'OpenAI built-in imagegen','model':'not exposed by built-in tool','prompt':'Exact prompts preserved beside each original source sheet. Painted2D sources only; explicit plate calibration and whole-pose technical registration, no limb deformation. Candidate is unselected and motion review remains pending.','painted_master':rel(ap),'painted_master_sha256':sha(ap.read_bytes()),'provenance':rel(painted),'provenance_sha256':sha(painted.read_bytes()),'technical_producer':rel(Path(__file__)),'technical_producer_sha256':sha(Path(__file__).read_bytes())}
    common={'production_status':'painted-master-complete-unapproved','unit':UNIT,'generation':generation,'status':'authored configuration','acceptance':'Isolated technical candidate only. Opposite-support gait/root consistency, native visual/gameplay and rights remain pending. No canonical or release acceptance.','credits':{'author':'Project-directed OpenAI built-in imagegen; deterministic technical painted2D assembly','license':None,'redistribution':'unresolved; release prohibited'}}
    prefix=f'Content/Sprites/runeterra/bilgewater/creatures/{UNIT}/'
    recipes=SOURCE/'proposed-recipes'/UNIT
    battle={**common,'recipe_type':'vcmi_animation','output_path':prefix+'battle.json','canvas':list(CANVAS),'pivot':{'x':ROOT[0],'y':ROOT[1]},'generateShadow':1,'generateOverlay':1,'groups':groups}
    record(recipes/'battle.json',battle)
    # Independent role registration: the rightmost64px map-mask columns stay
    # occupied; encounter64 and walking96 roots differ exactly32px.
    actor=reaction[0];source_root=reaction_roots[0]
    mapim=transform(actor,source_root,.135,(96,64),(76,60))
    encounter=transform(actor,source_root,.135,(64,64),(44,60))
    extra={'map':mapim,'attackLeft':encounter,'attackRight':mirror_root(encounter,44)}
    bg=Image.open(SOURCE/'portrait-background-v1-raw.png').convert('RGBA')
    close=actor.crop((90,96,262,270))
    for role,size in [('large',(64,64)),('small',(32,32))]:
        image=bg.resize(size,Image.Resampling.LANCZOS);crop=close.resize(size,Image.Resampling.LANCZOS);image.alpha_composite(crop);extra[role]=image
    for role,im in extra.items():
        p=out/'companions'/f'{role}.png';save(p,im)
        if role=='map':
            recipe={**common,'recipe_type':'vcmi_animation','output_path':prefix+'map.json','canvas':[96,64],'pivot':{'x':76,'y':60},'generateShadow':1,'generateOverlay':0,'groups':[{'group':0,'frames':[descriptor(p)]}]}
        else:recipe={**common,'recipe_type':'raster','output_path':prefix+role+'.png','size':list(im.size),'fit':'exact',**descriptor(p)}
        record(recipes/(role+'.json'),recipe)
    sheet=Image.new('RGB',(4*160,14*150),(84,90,80));d=ImageDraw.Draw(sheet)
    for row,(group,images) in enumerate(native.items()):
        for col,im in enumerate(images):
            crop=preview(im);sheet.paste(crop,(col*160,row*150),crop);d.text((col*160+3,row*150+130),f'g{group:02d} f{col}',fill='white')
    save(REPORT/UNIT/'native-contact-sheet-v1.png',sheet)
    # Run the existing actual compiler planner twice. It performs source pins,
    # dimensions and native PNG/animation conversion; writes stay isolated here.
    sys.path.insert(0,str(WORKSPACE/'scripts'))
    import faction_art_compile
    compiler=faction_art_compile.create_compiler('bilgewater');receipts=[];pass_hashes=[]
    for replay in (1,2):
        hashes={}
        for recipe in sorted(recipes.glob('*.json')):
            outputs,receipt=compiler.plan(PROJECT,recipe)
            for name,data in outputs.items():put(REPORT/UNIT/f'compile-pass-{replay}'/name,data);hashes[name]=sha(data)
            receipts.append({'pass':replay,**receipt})
        pass_hashes.append(hashes)
    if pass_hashes[0]!=pass_hashes[1]:raise RuntimeError('Actual compiler replay changed bytes')
    record(REPORT/UNIT/'actual-compiler-replay-v1.json',{'status':'authored configuration','deterministic':True,'outputs_per_pass':len(pass_hashes[0]),'output_hashes':pass_hashes[0],'receipts':receipts,'native_execution':False,'visual_approval_granted':False})
    html='<html><head><meta charset="utf-8"><title>Bilgewater painted creature candidates</title></head><body style="background:#202923;color:#eee;font-family:system-ui"><h1>Bilge Rat — unselected painted source candidate</h1><p>Actual compiler replay is technical evidence only. Opposite-support gait and root/camera continuity remain unresolved. No native or release acceptance.</p><img src="native-contact-sheet-v1.png" style="max-width:100%"><p>'
    for group in native:html+=f'<a href="g{group:02d}.gif">g{group:02d} motion</a> '
    html+='</p><a href="actual-compiler-replay-v1.json">Actual conversion receipts</a></body></html>'
    put(REPORT/UNIT/'index.html',html.encode())
    print(json.dumps({'unit':UNIT,'recipe_count':len(list(recipes.glob('*.json'))),'native_frame_count':len(all_records),'compiled_outputs_per_pass':len(pass_hashes[0]),'deterministic':True,'selected':False,'report':str(REPORT/UNIT/'index.html')}))
if __name__=='__main__':main()
