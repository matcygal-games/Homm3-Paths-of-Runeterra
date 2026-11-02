"""Portable technical assembly of genuine painted sources; no artistic drawing.

Run from workspace root with the project Python. Canonical recipes, manifests,
content and generated outputs are never modified. Compilation uses the real
regional compiler's plan() twice and writes only a candidate report tree.
"""
from __future__ import annotations
import argparse,copy,hashlib,io,json,math,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageFilter,ImageOps,ImageDraw
from components import components

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
ROOT=PROJECT.parent
REPORT=ROOT/'reports/targon-creature-completion-20261028-v1'
ORIGINAL=PROJECT/'assets/source/creatures/painted-rebuild-20261027-v1'
HUMANOIDS=['rakkorTrailguard','rakkorPassguard','mountainArcher','peakMarksman','lunariAcolyte','lunariPriestess','solariSunforger','solariDawnforger']
PREFIX='Content/Sprites/runeterra/targon/'
CANVAS=(450,400);ROOT_POINT=(196,267)

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def dump(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def relative(path):return Path(path).relative_to(PROJECT).as_posix()
def png(path,image):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    image.save(path,compress_level=9,optimize=False)
    return {'source':relative(path),'source_sha256':sha(path),'source_canvas':list(image.size)}

def clean_alpha(image):
    """Normalize transparent RGB and nearly opaque generation quantization only."""
    a=np.array(image.convert('RGBA'));a[a[:,:,3]>=250,3]=255;a[a[:,:,3]==0,:3]=0
    return Image.fromarray(a,'RGBA')

def register_settled_ground(image,ground=267):
    """Place the painted physical contact plane at the fixed native root.

    Generated corpse cells use a different row inset from upright controls.
    This is explicit translation registration only: no pose deformation,
    rescaling, redrawing or substitution. The whole canvas/root stays fixed.
    """
    alpha=np.asarray(image.getchannel('A'));yy,xx=np.nonzero(alpha>64)
    if not len(yy):raise ValueError('No visible contact plane')
    delta=ground-(int(yy.max())+1)
    out=Image.new('RGBA',image.size,(0,0,0,0));out.alpha_composite(image,(0,delta))
    return out,delta

def atlas_cells(path,columns,rows,threshold=64):
    """Isolate actual connected painted bodies, allowing weapons past grid lines.

    Equal cells establish spatial registration only. Visible alpha islands give
    the actual nonrectangular silhouettes, so a spear is not sliced at a cell
    edge. Low-alpha edge antialias is preserved by a three-pixel mask expansion.
    Unselected merged bodies are explicitly recorded rather than called valid.
    """
    image=Image.open(path).convert('RGBA');w,h=image.size
    islands=components(image,threshold,300);assigned={};bad=[]
    for island in islands:
        b=island['bbox'];x=(b[0]+b[2])/2;y=(b[1]+b[3])/2
        col=min(columns-1,int(x/(w/columns)));row=min(rows-1,int(y/(h/rows)))
        key=row*columns+col
        if key in assigned:bad.append({'cell':key,'extra':b});continue
        assigned[key]=island
    cells={};records=[]
    for key,island in assigned.items():
        b=island['bbox'];row,col=divmod(key,columns)
        if b[3]-b[1] > h/rows*1.65:
            bad.append({'cell':key,'merged_silhouette':b});continue
        mask=Image.new('L',image.size,0)
        pixels=mask.load()
        for y,x0,x1 in island['runs']:
            for x in range(x0,x1):pixels[x,y]=255
        mask=mask.filter(ImageFilter.MaxFilter(7))
        a=np.minimum(np.array(image.getchannel('A')),np.array(mask))
        selected=image.copy();selected.putalpha(Image.fromarray(a,'L'))
        box=[max(0,b[0]-3),max(0,b[1]-3),min(w,b[2]+3),min(h,b[3]+3)]
        crop=clean_alpha(selected.crop(box))
        cells[key]={'image':crop,'bbox':box,'visible_bbox':b,'row':row,'col':col,
                    'source_cell_origin':[col*w/columns,row*h/rows]}
        records.append({'cell':key,'bbox':box,'visible_bbox':b,'area':island['area'],
                        'source':relative(path),'sha256':sha(path)})
    return cells,{'source':relative(path),'canvas':[w,h],'columns':columns,'rows':rows,'visible_alpha_threshold':threshold,
                  'actual_islands':len(islands),'cells':records,'unusable_or_extra':bad}

def native_pose(cell,scale,source_root,canvas=CANVAS,pivot=ROOT_POINT,mirror=False):
    """One cohort scale; explicit source coordinate root, never fit each pose."""
    im=cell['image'];b=cell['bbox'];size=(max(1,round(im.width*scale)),max(1,round(im.height*scale)))
    im=im.resize(size,Image.Resampling.LANCZOS)
    x=round(pivot[0]+(b[0]-source_root[0])*scale)
    y=round(pivot[1]+(b[1]-source_root[1])*scale)
    out=Image.new('RGBA',canvas,(0,0,0,0));out.alpha_composite(im,(x,y))
    if mirror:
        flipped=ImageOps.mirror(out);shift=2*pivot[0]-(canvas[0]-1)
        out=Image.new('RGBA',canvas,(0,0,0,0));out.alpha_composite(flipped,(shift,0))
    return clean_alpha(out)

def calibrated_roots(cells,columns,rows,width,height):
    # Source grids were requested as constant-root rows. Use upright holding
    # controls for the root/scale, then apply that root to every action cell.
    hold=cells[6];hb=hold['visible_bbox'];origin=hold['source_cell_origin']
    base_height=hb[3]-hb[1]
    source_x=(hb[0]+hb[2])/2-origin[0]
    foot_y=hb[3]-origin[1]
    return source_x,foot_y,base_height

def build_unit(unit,background):
    original=ORIGINAL/(unit+'-atlas-'+('v2' if unit=='rakkorTrailguard' else 'v1')+'.png')
    rows=7 if unit=='solariDawnforger' else 8
    old,old_record=atlas_cells(original,4,rows)
    supplement=HERE/'humanoids'/(unit+'-supplement-v1.png')
    if unit=='rakkorTrailguard':supplement=HERE/'humanoids/rakkorTrailguard-turn-v1.png'
    fresh,new_record=atlas_cells(supplement,4,2)
    ow,oh=old_record['canvas'];nw,nh=new_record['canvas']
    sx,sy,bodyheight=calibrated_roots(old,4,rows,ow,oh)
    target_height=79 if unit not in ['solariSunforger','solariDawnforger'] else 84
    scale=target_height/bodyheight
    # Every new-sheet action uses a common scale fixed from its upright first
    # turn pose, not independently fitted weapon/attack/corpse bounds.
    nb=fresh[0]['visible_bbox'];new_scale=target_height/(nb[3]-nb[1])
    nx=(nb[0]+nb[2])/2;ny=nb[3]
    # The provider's two rows do not always use a perfect 512px pitch.
    # Measure each row's upright control baseline, then keep it fixed for all
    # poses in that row. This fixes registration without fitting each action.
    new_row_baselines={0:ny,1:fresh[7]['visible_bbox'][3]}
    selected=[]
    def o(index):
        c=old[index];r,cx=divmod(index,4)
        sr=(sx+cx*ow/4,sy+r*oh/rows)
        selected.append(('original',index))
        return native_pose(c,scale,sr)
    def n(index):
        c=fresh[index];r,cx=divmod(index,4)
        sr=(nx+cx*nw/4,new_row_baselines[r])
        selected.append(('supplement',index))
        return native_pose(c,new_scale,sr)
    hold=o(6);hold2=o(7)
    if unit in ['solariSunforger','solariDawnforger']:
        # The old painted upright cells omit the polearm head. Use the new
        # complete painted controls so equipment does not vanish during idle.
        hold=n(7);hold2=n(6)
    turn=[n(i) for i in range(4)]
    # VCMI plays TURN_L, toggles facing, then TURN_R. The latter starts
    # with the same painted frontal silhouette reflected about the fixed root,
    # so the engine flip yields an identical visual join. Final holding is real.
    frontal=turn[-1]
    flipped=ImageOps.mirror(frontal);turn_join=Image.new('RGBA',CANVAS,(0,0,0,0))
    turn_join.alpha_composite(flipped,(2*ROOT_POINT[0]-(CANVAS[0]-1),0))
    groups={0:[o(i) for i in range(6)],2:[hold,hold2,hold,hold2],7:turn,8:[turn_join,turn[0],hold]}
    archer=unit in ['mountainArcher','peakMarksman']
    if archer:
        wind=n(4);up=n(5);middle=n(6);down=n(7)
        for g,contact in [(11,up),(12,middle),(13,down)]:groups[g]=[hold,wind,wind,contact,wind,hold]
        for g,inds in [(14,[12,12,13,14]),(15,[8,9,10,11]),(16,[16,16,17,18])]:
            poses=[o(i) for i in inds];groups[g]=[hold,poses[0],poses[1],poses[2],poses[3],hold]
        groups[3]=[hold,o(20),o(21),o(22),hold]
        groups[4]=[hold,o(24),o(25),o(26),hold]
        fidget=[hold,hold2,o(23),hold2]
    else:
        for g,indices in [(11,[12,13,14]),(12,[8,9,10,11]),(13,[16,17,18])]:
            poses=[o(i) for i in indices]
            contact=poses[2] if g==12 else poses[1]
            groups[g]=[hold,poses[0],poses[0],contact,poses[-1],hold]
        if unit in ['solariSunforger','solariDawnforger']:
            groups[3]=[hold,n(5),n(5),hold2,hold]
            groups[4]=[hold,n(4),n(4),hold2,hold]
            fidget=[hold,n(6),hold2,hold]
        elif unit.startswith('lunari'):
            groups[3]=[hold,o(20),o(21),o(22),hold]
            groups[4]=[hold,n(4),n(4),hold2,hold]
            fidget=[hold,n(6),hold2,hold]
            cast=[hold,o(24),o(24),o(25),o(26),hold]
            for g in [17,18,19,30,31,32]:groups[g]=cast
        else:
            groups[3]=[hold,o(20),o(21),o(22),hold]
            groups[4]=[hold,o(24),o(25),o(26),hold]
            fidget=[hold,n(6),hold2,hold]
    groups[1]=fidget
    death_indices=[24,25,26,27] if rows==7 else [28,29,30,31]
    if unit=='solariSunforger':death_indices=[29,30,31]
    groups[5]=[hold]+[o(i) for i in death_indices]
    registered=[register_settled_ground(frame) for frame in groups[5]]
    groups[5]=[frame for frame,offset in registered]
    groups[22]=[groups[5][-1].copy()]
    groups[20]=[hold,groups[0][0],groups[0][1]]
    groups[21]=[groups[0][-2],groups[0][-1],hold]
    root=HERE/'humanoids'/unit
    descriptors={}
    for group,frames in sorted(groups.items()):
        descriptors[group]=[]
        for i,image in enumerate(frames):
            info=png(root/'battle'/f'g{group:02d}-f{i:03d}.png',image);info['frame']=i;descriptors[group].append(info)
    # 64x64 native two-column map: anchor tile is [32,32,64,64], root48,60.
    # Same fixed 0.40 battle transform across all holds and encounter poses.
    def map_image(image,mirror=False):
        cells={'image':image,'bbox':[0,0,*CANVAS]}
        return native_pose(cells,0.40,ROOT_POINT,(64,64),(48,60),mirror)
    maps=[map_image(i) for i in groups[2]]
    map_desc=[]
    for i,image in enumerate(maps):
        info=png(root/'map'/f'hold-{i}.png',image);info['frame']=i;map_desc.append(info)
    # These native map fields are encounter reactions to an approaching hero,
    # so use the genuine compact recoil instead of a long battle thrust that
    # would clip at the right edge of the fixed 64px map canvas.
    reactions={'attackRight':map_image(groups[3][2]),'attackLeft':map_image(groups[3][2],True)}
    reaction_desc={k:png(root/'map'/(k+'.png'),v) for k,v in reactions.items()}
    from map_assembly import make_map_resources
    map_desc,reaction_desc,compact_map,map_dependencies=make_map_resources(unit,root)
    # Dedicated close head/upper-body portrait from the detailed new painting,
    # composited over an independently painted own regional mountain backdrop.
    subject=fresh[3]['image'];vb=subject.getchannel('A').getbbox()
    headheight=round((vb[3]-vb[1])*0.40)
    top=vb[1];cx=(vb[0]+vb[2])/2
    crop=subject.crop((round(cx-headheight*.58),top,round(cx+headheight*.58),top+headheight))
    portrait=background.copy().resize((58,64),Image.Resampling.LANCZOS)
    ratio=min(56/crop.width,63/crop.height);crop=crop.resize((round(crop.width*ratio),round(crop.height*ratio)),Image.Resampling.LANCZOS)
    portrait.alpha_composite(crop,((58-crop.width)//2,64-crop.height))
    large=png(root/'portrait-large.png',clean_alpha(portrait))
    small=png(root/'portrait-small.png',clean_alpha(portrait.resize((32,32),Image.Resampling.LANCZOS)))
    record={'unit':unit,'status':'authored configuration','native_execution':False,
            'battle_canvas':list(CANVAS),'battle_root':list(ROOT_POINT),'cohort_scale':scale,
            'supplement_cohort_scale':new_scale,'target_body_height':target_height,
            'original_map':old_record,'supplement_map':new_record,'selected_cells':sorted(set(selected)),
            'group_frame_counts':{str(g):len(v) for g,v in groups.items()},
            'map_canvas':[64,64],'map_root':[48,60],'map_mask':['VV','VA'],
            'map_scale_from_battle':0.40,'portrait':'Close head/upper-body source crop over own painted regional background; no tiny whole-body stamp',
            'limitations':['Authored candidate; source/native inspection does not grant external art or release acceptance',
                          'Full native recruitment/playback checks remain assigned to coordinator']}
    record['compact_adventure']=compact_map
    record['death_contact_registration']={'ground_y':267,'native_y_offsets':[offset for frame,offset in registered],
              'method':'Explicit measured physical-contact registration of genuinely painted death poses; fixed canvas/root and constant cohort scale preserved'}
    dump(root/'assembly.json',record)
    projectile=None
    if archer:
        arrow_box={'mountainArcher':[866,365,926,372],'peakMarksman':[881,351,939,360]}[unit]
        arrow=clean_alpha(Image.open(original).convert('RGBA').crop(arrow_box))
        arrow=arrow.resize((24,max(2,round(arrow.height*24/arrow.width))),Image.Resampling.LANCZOS)
        projectile=[]
        for i,angle in enumerate([90,45,0,-45,-90]):
            rotated=arrow.rotate(angle,Image.Resampling.BICUBIC,expand=True)
            final=Image.new('RGBA',(32,32),(0,0,0,0));final.alpha_composite(rotated,((32-rotated.width)//2,(32-rotated.height)//2))
            desc=png(root/'projectile'/f'angle-{i}.png',clean_alpha(final));desc['frame']=i;projectile.append(desc)
        record['projectile']={'source_crop':arrow_box,'origin':'Actual detached painted arrow from the same genuine2D action atlas',
                              'frame_angles':[90,45,0,-45,-90],'rotation':'Technical orientation of painted projectile, not code-drawn artwork',
                              'release_frame_one_based':4,'release_frame_zero_based':3,
                              'release_origins':({'upper':[221,205],'middle':[219,221],'lower':[219,232]} if unit=='mountainArcher' else {'upper':[224,208],'middle':[232,222],'lower':[233,245]})}
        dump(root/'assembly.json',record)
    return {'unit':unit,'root':root,'groups':groups,'battle':descriptors,'map':map_desc,'projectile':projectile,
            'reactions':reaction_desc,'large':large,'small':small,'record':record,
            'original':original,'supplement':supplement,'extra_dependencies':map_dependencies,'extra_origins':[map_dependencies[0]]}

def recipe_base(unit,master,ledger,ledger_hash,prompt):
    return {'status':'authored configuration','production_status':'painted-master-complete-unapproved',
            'visual_approval':False,'acceptance':'Technical conversion only; native art, motion, rights and release acceptance remain pending',
            'assembly_method':'Actual painted silhouettes, fixed cohort roots/scales, native action assembly; no artistic code drawing',
            'generation':{'image_generation_used':True,'workflow':'image-based-painted-2d','provider':'OpenAI built-in image_gen',
                          'model':'not exposed','prompt':prompt,'painted_master':relative(master),
                          'source_generation_ledger':relative(ledger),'source_generation_ledger_sha256':ledger_hash},
            'unit':unit}

def make_recipes(data,background_path):
    producer=data.get('producer',Path(__file__))
    files={relative(p):sha(p) for p in data['root'].rglob('*') if p.is_file() and p.suffix in ['.png','.json'] and p.name!='source-generation-ledger.json'}
    for p in [data['original'],data['supplement'],background_path,producer,Path(__file__),HERE/'components.py',HERE/'humanoids/effective-prompts-v1.json',HERE/'generation-receipts-v1.json',ORIGINAL/'effective-prompts-v1.json']+data.get('extra_dependencies',[]):
        files[relative(p)]=sha(p)
    ledger=data['root']/'source-generation-ledger.json'
    origins=[{'kind':'image-generation','path':relative(p),'sha256':sha(p)} for p in [data['original'],data['supplement'],background_path]]
    origins += [{'kind':'image-generation','path':relative(p),'sha256':sha(p)} for p in data.get('extra_origins',[])]
    dump(ledger,{'status':'authored configuration','workflow':'image-based-painted-2d','derived_from_blender':False,
                 'user_rejected':False,'assembly_operations':['fixed-canvas','root-placement','alpha-cleanup','frame-assembly','png-conversion'],
                 'provider':'OpenAI built-in image_gen','model':'not exposed','files_sha256':files,'origins':origins,
                 'producer_source':relative(producer),'producer_sha256':sha(producer),
                 'scope':'Portable candidate source closure; no acceptance implied'})
    base=recipe_base(data['unit'],data['original'],ledger,sha(ledger),
          'Preserve the exact genuine painted Targon actor; use recorded original and supplementary action prompts in effective-prompts-v1.json.')
    unit=data['unit'];out=PREFIX+'creatures/'+unit+'/'
    recipes=[]
    def add(name,props):
        recipe=copy.deepcopy(base);recipe.update(props);path=HERE/'proposed-recipes'/unit/(name+'.json');dump(path,recipe);recipes.append(path)
    bp=data['record'].get('battle_root',[196,267]);mp=data['record'].get('map_root',[48,60]);mc=data['record'].get('map_canvas',[64,64])
    add('battle',{'recipe_type':'vcmi_animation','canvas':list(CANVAS),'pivot':{'x':bp[0],'y':bp[1]},'output_path':out+'battle.json',
                  'groups':[{'group':g,'generateShadow':2,'generateOverlay':0,'frames':frames} for g,frames in sorted(data['battle'].items())]})
    add('map',{'recipe_type':'vcmi_animation','canvas':mc,'pivot':{'x':mp[0],'y':mp[1]},'output_path':out+'map.json',
               'groups':[{'group':0,'generateShadow':2,'generateOverlay':0,'frames':data['map']}],
               'registration':{'mask':['VV','VA'],'anchor_tile':[mc[0]-32,32,mc[0],64],'ground_root':mp}})
    for name,desc in [('large',data['large']),('small',data['small']),*data['reactions'].items()]:
        add(name,{'recipe_type':'raster','canvas':desc['source_canvas'],'fit':'exact','output_path':out+name+'.png',**desc})
    if data.get('projectile'):
        add('projectile',{'recipe_type':'vcmi_animation','canvas':[32,32],'pivot':{'x':16,'y':16},
                          'output_path':PREFIX+'projectiles/'+unit+'.json',
                          'groups':[{'group':0,'generateShadow':0,'generateOverlay':0,'frames':data['projectile']}]})
    return recipes

def review(data):
    unit=data['unit'];groups=data['groups'];out=REPORT/'humanoids'/unit;out.mkdir(parents=True,exist_ok=True)
    crop=(105,155,315,285);rows=[]
    for g in sorted(groups):
        frames=groups[g]
        strip=Image.new('RGBA',(210*max(6,len(frames)),150),(52,49,46,255));d=ImageDraw.Draw(strip)
        d.text((3,3),f'{unit} group {g}',fill='white')
        for i,frame in enumerate(frames):strip.alpha_composite(frame.crop(crop),(i*210,20))
        rows.append(strip)
        if g in [0,5,7,8,11,12,13,15,31]:
            views=[]
            for frame in frames:
                bg=Image.new('RGBA',(210,130),(52,49,46,255));bg.alpha_composite(frame.crop(crop));views.append(bg.convert('RGB'))
            views[0].save(out/f'g{g:02d}.gif',save_all=True,append_images=views[1:],duration=150,loop=0,disposal=2)
    page=Image.new('RGBA',(max(r.width for r in rows),150*len(rows)),(52,49,46,255))
    for i,row in enumerate(rows):page.alpha_composite(row,(0,i*150))
    page.convert('RGB').save(out/'actions-native.png')
    # Correct consumer order including the actual native-facing toggle.
    sequence=groups[7]+[ImageOps.mirror(f) for f in groups[8]]
    frames=[]
    for f in sequence:
        bg=Image.new('RGBA',(450,400),(52,49,46,255));bg.alpha_composite(f);frames.append(bg.crop((110,155,340,285)).convert('RGB'))
    frames[0].save(out/'turn-native-consumer.gif',save_all=True,append_images=frames[1:],duration=180,loop=0,disposal=2)

def compile_candidates(recipes,label='humanoid'):
    sys.path.insert(0,str(ROOT/'scripts'))
    from faction_art_compile import create_compiler
    compiler=create_compiler('targon');receipts=[];patch=[];errors=[]
    for recipe_path in recipes:
        try:
            a,receipt=compiler.plan(PROJECT,recipe_path);b,_=compiler.plan(PROJECT,recipe_path)
            if a!=b:raise AssertionError('Compiler replay differs')
            for name,raw in a.items():
                destination=REPORT/'compiled'/name;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(raw)
            receipts.append(receipt)
            recipe=json.loads(recipe_path.read_text());output=recipe['output_path'];unit=recipe['unit']
            role=('creature-projectile' if '/projectiles/' in output else {'battle.json':'creature-battle-animation','map.json':'creature-adventure-animation','large.png':'creature-large','small.png':'creature-small','attackLeft.png':'creature-adventure-attack-left','attackRight.png':'creature-adventure-attack-right'}[Path(output).name])
            patch.append({'unit':unit,'role':role,'output_path':output,'dimensions':recipe['canvas'],'sha256':hashlib.sha256(a[output]).hexdigest(),
                          'source':{'editable_path':'assets/generated/'+output,'recipe_path':relative(recipe_path),'recipe':relative(recipe_path),
                                    'recipe_present':True,'recipe_sha256':sha(recipe_path)},
                          'status':'built-unreviewed','native_visual_review':'pending','dependencies':[relative(recipe_path)]})
        except Exception as exc:errors.append({'recipe':relative(recipe_path),'error':str(exc)})
    dump(REPORT/(label+'-compiler-double-replay.json'),{'status':'authored configuration','ok':not errors,'recipes':len(recipes),
             'compiled_recipes':len(receipts),'actual_compiler':'scripts/faction_art_compile.py:create_compiler(targon).plan',
             'byte_identical_second_assembly':not errors,'receipts':receipts,'errors':errors,'native_execution':False})
    dump(HERE/('proposed-manifest-'+label+'s.json'),{'status':'authored configuration','assets':patch})
    offsets={}
    for unit in ['mountainArcher','peakMarksman']:
        assembly=HERE/'humanoids'/unit/'assembly.json'
        if not assembly.exists():continue
        record=json.loads(assembly.read_text())
        if 'projectile' not in record:continue
        origins=record['projectile']['release_origins'];offset={}
        for angle,(x,y) in origins.items():offset[angle+'X']=x-196;offset[angle+'Y']=y-267
        offsets[unit]={'graphics':{'missile':{'projectile':'runeterra/targon/projectiles/'+unit+'.json',
                         'frameAngles':[90,45,0,-45,-90],'attackClimaxFrame':4,'offset':offset}}}
    dump(HERE/'proposed-content-graphics-offsets.json',{'status':'authored configuration','units':offsets,
         'basis':'Source-pixel bow-hand origin measurement at actual compiled group14/15/16 zero-based frame3; native flight/impact verification pending'})
    return errors

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--unit',action='append');args=parser.parse_args()
    background_path=HERE/'portrait-background-v1.png';background=Image.open(background_path).convert('RGBA')
    # Use close crops of the same genuine environmental painting; no recolor.
    results=[];recipes=[]
    for unit in args.unit or HUMANOIDS:
        data=build_unit(unit,background);results.append(data['record']);recipes+=make_recipes(data,background_path);review(data)
    errors=compile_candidates(recipes)
    dump(REPORT/'humanoid-assembly-summary.json',{'status':'authored configuration','units':results,'errors':errors,
             'art_acceptance':False,'native_execution':False})
    print(json.dumps({'units':len(results),'recipes':len(recipes),'errors':errors},indent=2))
    return 2 if errors else 0
if __name__=='__main__':raise SystemExit(main())
