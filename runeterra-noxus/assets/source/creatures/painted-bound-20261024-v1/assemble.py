"""Own painted bound-manifestation candidate assembly, never active selection.

Art comes exclusively from preserved built-in imagegen masters. This helper
only partitions alpha ownership, uniformly scales whole cohorts, registers
native roots, crops portraits and exercises the actual Noxus compiler twice.
"""
from pathlib import Path
import hashlib
import json
import sys
from PIL import Image, ImageDraw, ImageOps

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
REPORT=ROOT/'build/reports/painted-bound-manifestations-20261024-v1'
CANDIDATE=ROOT/'assets/candidates/painted-bound-20261024-v1/recipes'
sys.path.insert(0,str(ROOT/'scripts'))
from art_human_legion import separate_subjects
import art_compile

UNITS={'boundRuinManifestation':'identity-v2','greaterRuinManifestation':'identity-v1'}
STEMS={'flight':('flight-v3-under-review',6,[2,2,2]),'support':('support-v1',12,[2]*6),
       'death':('death-v1',6,[2,2,2]),'turn':('turn-v1',4,[2,2]),
       'transition':('transition-v1',6,[2,2,2]),'front':('attack-front-v1',6,[2,2,2]),
       'up':('attack-up-v1',6,[2,2,2]),'down':('attack-down-v1',6,[2,2,2]),
       'icons':('attack-icons-v1',2,[2])}
UPGRADE_SUPPORT={key:('support-'+key+'-v2',4,[2,2]) for key in ('fidget','hit','guard')}

def stem_spec(unit,key):
    if key in UPGRADE_SUPPORT:return UPGRADE_SUPPORT[key]
    stem,count,rows=STEMS[key]
    if unit=='greaterRuinManifestation' and key=='flight':stem='flight-v1'
    return stem,count,rows
ACTIONS={0:'six genuine compact magical-hover flight poses',1:'occasional four-pose binding/hand fidget',
         2:'quiet single-frame low-hover holding',3:'four-pose hit recoil',4:'four-pose compact claw guard',
         5:'six-pose anatomical collapse',7:'RIGHT toward FRONT half-turn',8:'FRONT toward RIGHT half-turn after native facing flip',
         11:'single claw strike up-right',12:'single claw strike right',13:'single claw strike down-right',
         20:'three genuine takeoff phases',21:'three genuine descent/settle phases',22:'exact terminal collapsed corpse'}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def rel(path):return path.relative_to(ROOT).as_posix()
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def save(path,image):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(art_compile.png_bytes(image))
def bounds(image,cut=128):return image.getchannel('A').point(lambda a:255 if a>=cut else 0).getbbox()
def generation(path):
    provenance=path.with_suffix('.generation.json')
    value=json.loads(provenance.read_text(encoding='utf-8'))
    return {'image_generation_used':True,'provider':'OpenAI built-in imagegen','model':'not exposed by built-in tool',
            'model_id_exposed':False,'prompt':value['prompt'],'painted_master':rel(path),
            'provenance':rel(provenance),'provenance_sha256':sha(provenance),
            'rights':'unresolved; release prohibited'}
def descriptor(path):return {'source':rel(path),'source_sha256':sha(path),'sha256':sha(path),'source_canvas':list(Image.open(path).size)}

def extract(unit,key):
    stem,count,rows=stem_spec(unit,key)
    path=HERE/unit/(stem+'.png')
    cache=HERE/unit/'isolated'/stem/'ownership-v2.json'
    if cache.is_file():
        record=json.loads(cache.read_text())
        if record['master_sha256']!=sha(path):raise ValueError('Preserve source revision before changing '+str(path))
        return [(Image.open(ROOT/r['isolated']).convert('RGBA'),r) for r in record['poses']]
    master=Image.open(path).convert('RGBA')
    poses=separate_subjects(master,count)
    poses.sort(key=lambda p:(p[1][1]+p[1][3])/2)
    ordered=[];cursor=0
    for n in rows:
        row=poses[cursor:cursor+n];row.sort(key=lambda p:(p[1][0]+p[1][2])/2)
        ordered.extend(row);cursor+=n
    if len(ordered)!=count:raise ValueError('Wrong actual pose count')
    out=[]
    for index,(figure,box) in enumerate(ordered):
        opaque=bounds(figure)
        if not opaque:raise ValueError('Empty subject')
        # Actual solid contact with an image border is refused; disconnected
        # transparent RGB/haze is never treated as a painted extra limb.
        global_box=[box[0]+opaque[0],box[1]+opaque[1],box[0]+opaque[2],box[1]+opaque[3]]
        clipped=global_box[0]<=0 or global_box[1]<=0 or global_box[2]>=master.width or global_box[3]>=master.height
        if clipped and not(key=='support' and index==11):
            raise ValueError('Painted subject touches source image edge: '+unit+' '+key+' '+str(index))
        target=HERE/unit/'isolated'/stem/f'pose-{index:03d}.png'
        alpha=target.with_name(f'pose-{index:03d}-alpha.png')
        save(target,figure);figure.getchannel('A').save(alpha)
        record={'index':index,'master':rel(path),'master_sha256':sha(path),'source_bbox':box,
                'isolated':rel(target),'isolated_sha256':sha(target),'ownership_alpha':rel(alpha),
                'ownership_alpha_sha256':sha(alpha),'size':list(figure.size),
                'selected':not(key=='support' and index==11),'source_edge_clipped':clipped}
        out.append((figure,record))
    write(cache,{'master':rel(path),'master_sha256':sha(path),'poses':[r for _,r in out],
        'method':'Existing connected alpha island partition; original source pixels retained, no color key, paint, affine warp or per-pose fit.'})
    return out

def native(figure,scale,canvas,root,ground):
    width=max(1,round(figure.width*scale));height=max(1,round(figure.height*scale))
    placed=figure.resize((width,height),Image.Resampling.LANCZOS)
    x=root[0]-width//2;y=ground-height
    if x<0 or y<0 or x+width>canvas[0] or y+height>canvas[1]:
        raise ValueError('Native canvas clips source figure')
    result=Image.new('RGBA',canvas);result.alpha_composite(placed,(x,y))
    return result,{'uniform_scale':scale,'paste_origin':[x,y],'scaled_size':[width,height],'root':list(root),'ground':ground}

def assemble(unit):
    folder=HERE/unit
    master=folder/(UNITS[unit]+'.png')
    identity=Image.open(master).convert('RGBA');identity_box=identity.getchannel('A').point(lambda a:255 if a>=8 else 0).getbbox()
    identity=identity.crop(identity_box)
    keys=list(STEMS)
    if unit=='greaterRuinManifestation':keys.remove('support');keys+=list(UPGRADE_SUPPORT)
    poses={key:extract(unit,key) for key in keys}
    scale={key:98/frames[0][0].height for key,frames in poses.items()}
    # The actual compact flight cohort is calibrated once, with native pixel
    # limits, not shrunk independently per frame. Other action cameras retain
    # their first ready-body scale and long attacks may overhang stock widgets.
    scale['flight']=min(96/max(im.width for im,_ in poses['flight']),98/max(im.height for im,_ in poses['flight']))
    id_scale=98/identity.height
    groups={};lineage=[]
    mapping={0:('flight',list(range(6))),1:('support',list(range(4))),
             3:('support',list(range(4,8))),4:('support',list(range(8,11))),5:('death',list(range(6))),
             7:('turn',list(range(4))),8:('turn',[3,2,1,0]),
             11:('up',list(range(6))),12:('front',list(range(6))),13:('down',list(range(6))),
             20:('transition',[0,1,2]),21:('transition',[3,4,5])}
    if unit=='greaterRuinManifestation':
        mapping.update({1:('fidget',list(range(4))),3:('hit',list(range(4))),4:('guard',list(range(4)))})
    for group,(key,indices) in mapping.items():
        frames=[]
        for index,source_index in enumerate(indices):
            figure,source=poses[key][source_index]
            ground=254 if group==0 else 266
            if group==20:ground=(266,260,254)[index]
            if group==21:ground=(254,260,266)[index]
            if group==5:ground=(255,257,260,263,265,266)[index]
            im,transform=native(figure,scale[key],(450,400),(218,266),ground)
            path=folder/'native-v1'/f'g{group:02d}'/f'g{group:02d}-f{index:03d}.png'
            save(path,im);frames.append(path)
            lineage.append({'group':group,'frame':index,'pose':source,**transform,
                            'output':rel(path),'output_sha256':sha(path)})
        groups[group]=frames
    idle,_=native(identity,id_scale,(450,400),(218,266),266)
    idle_path=folder/'native-v1/g02/g02-f000.png';save(idle_path,idle);groups[2]=[idle_path]
    lineage.append({'group':2,'frame':0,'master':rel(master),'master_sha256':sha(master),
                    'source_bbox':identity_box,'uniform_scale':id_scale,'output':rel(idle_path),'output_sha256':sha(idle_path)})
    if unit=='boundRuinManifestation':
        guard_recovery=folder/'native-v1/g04/g04-f003.png';save(guard_recovery,idle);groups[4].append(guard_recovery)
        lineage.append({'group':4,'frame':3,'master':rel(master),'master_sha256':sha(master),
            'source_bbox':identity_box,'uniform_scale':id_scale,'output':rel(guard_recovery),'output_sha256':sha(guard_recovery),
            'meaning':'Exact canonical ready pose after three genuine guards; clipped atlas recovery is unselected.'})
    corpse=folder/'native-v1/g22/g22-f000.png';save(corpse,Image.open(groups[5][-1]).convert('RGBA'));groups[22]=[corpse]
    if corpse.read_bytes()!=groups[5][-1].read_bytes():raise ValueError('DEAD is not exact terminal DEATH')
    map_frames=[]
    for index,(figure,source) in enumerate(poses['flight']):
        im,transform=native(figure,44/poses['flight'][0][0].height,(96,64),(64,63),63)
        path=folder/'native-v1/map'/f'map-f{index:03d}.png';save(path,im);map_frames.append(path)
        lineage.append({'role':'map','frame':index,'pose':source,**transform,'output':rel(path),'output_sha256':sha(path)})
    icons={}
    for index,role in enumerate(('attackLeft','attackRight')):
        figure,source=poses['icons'][index]
        path=folder/'native-v1'/f'{role}-isolated.png';save(path,figure);icons[role]=path
        lineage.append({'role':role,'pose':source,'oppositely_painted_direction':True,'mirroring_used':False,'output':rel(path),'output_sha256':sha(path)})
    cohort=folder/'native-v1/cohort.json'
    write(cohort,{'status':'authored configuration','unit':unit,'frames':lineage,'cohort_uniform_scales':scale,
        'native_battle_canvas':[450,400],'body_root':[218,266],'front_root':[240,266],'map_root':[64,63],
        'source_generation':[generation(folder/(stem_spec(unit,key)[0]+'.png')) for key in keys],
        'native_semantics':'g7 RIGHT to FRONT; g8 reversed genuine same half, native facing flip between halves. Quiet g2 single frame. Six actual g0 flight poses; genuine g20/21 departure/settling poses + twelve-pixel registration trajectory. Corpse exact terminal collapse.',
        'artistic_acceptance':False,'native_motion_verified':False,'rights':'unresolved; release prohibited'})
    # Noxus's selected-input collector scans declared recipe paths rather than
    # implicitly traversing arbitrary provenance JSON. Expose the actual live
    # authoring closure explicitly so changing a selected atlas, sidecar or
    # ownership mask invalidates the production signature as well as review.
    dependency_paths={cohort,master,master.with_suffix('.generation.json'),Path(__file__)}
    for key in keys:
        source=folder/(stem_spec(unit,key)[0]+'.png')
        dependency_paths.update((source,source.with_suffix('.generation.json')))
    for row in lineage:
        pose=row.get('pose')
        if pose:
            dependency_paths.update(ROOT/pose[field] for field in ('isolated','ownership_alpha'))
    # Preserve the genuine prior paint input used for the head correction and
    # identity upgrade, without reselecting its rejected crown as game artwork.
    base=HERE/'boundRuinManifestation'
    for name in ('identity-v1','identity-v2'):
        dependency_paths.update((base/(name+'.png'),base/(name+'.generation.json')))
    if unit=='greaterRuinManifestation':
        for key in UPGRADE_SUPPORT:
            reference=REPORT/('base-'+key+'-reference.png')
            copy=folder/'references'/reference.name
            copy.parent.mkdir(parents=True,exist_ok=True)
            copy.write_bytes(reference.read_bytes())
            dependency_paths.add(copy)
    dependencies=[{'path':rel(path),'sha256':sha(path)} for path in sorted(dependency_paths)]
    common={'unit':unit,'art_contract_revision':'painted-bound-manifestations-20261024-v1',
        'production_status':'painted-master-complete-unapproved','status':'built-unreviewed','visual_approval_granted':False,
        'generation':generation(master),'painted_cohort_manifest':rel(cohort),'painted_cohort_manifest_sha256':sha(cohort),
        'dependencies':dependencies,
        'credits':{'author':'OpenAI built-in imagegen; original project designs and exact prompts retained','license':None,'redistribution':'unresolved; release prohibited'},
        'acceptance':'Technical painted candidate only; actual pixels/motion/native behavior and redistribution remain unaccepted.',
        'lore':{'classification':'Project-fiction bound manifestations inspired by unique Atakhan, not a canonical plural species or Atakhan copy.',
                'flight':'Wingless magical hovering is explicit project gameplay/art adaptation; native physical FLYING, no teleport.',
                'nature':'Native NON_LIVING; no universal magic/healing immunity inferred.',
                'mark':'Small invented Black Rose binding ward, not an official regional crest.'}}
    prefix=f'Content/Sprites/runeterra/noxus/creatures/{unit}/'
    recipes=[]
    for role in ('battle','map','large','small','attackLeft','attackRight'):
        recipe=dict(common);recipe['output_path']=prefix+role+('.json' if role in ('battle','map') else '.png')
        if role in ('battle','map'):
            recipe.update(recipe_type='vcmi_animation',canvas=[450,400] if role=='battle' else [96,64],
                          pivot={'x':240,'y':266} if role=='battle' else {'x':64,'y':63},
                          generateShadow=1 if role=='battle' else 2,generateOverlay=1)
            selected=groups if role=='battle' else {0:map_frames}
            recipe['groups']=[{'group':group,'action':ACTIONS.get(group,'genuine native flight phases'),
                              'frames':[descriptor(path) for path in frames]} for group,frames in sorted(selected.items())]
            if role=='battle':
                recipe['turn_semantics']='RIGHT -> FRONT; native mirror; FRONT -> RIGHT using reverse genuine half.'
                recipe['movement']='physical FLYING, g0 six compact poses, g20 takeoff, g21 settle; no teleport'
                recipe['attack_semantics']='One ordinary single-target claw strike, ordinary retaliation; no shot/breath/cleave/free spell.'
                recipe['footprint']={'doubleWide':True,'battle':{'body_center':[218,266],'front_center':[240,266],
                                       'rear_center':[196,266],'hex_width':44,'hex_height':42}}
        else:
            path=master if role in ('large','small') else icons[role]
            recipe.update(recipe_type='raster',canvas={'large':[58,64],'small':[32,32],'attackLeft':[64,64],'attackRight':[64,64]}[role],
                          source=rel(path),source_sha256=sha(path),source_canvas=list(Image.open(path).size),require_alpha=True,fit='contain')
            if role=='large':recipe.update(crop=[670,65,1050,485],fit='cover')
        path=CANDIDATE/(unit+'-'+role+'.json');write(path,recipe);recipes.append(path)
    make_reviews(unit,groups,map_frames,icons)
    return recipes

def make_reviews(unit,groups,map_frames,icons):
    folder=REPORT/unit;folder.mkdir(parents=True,exist_ok=True)
    rows=[];findings=[]
    for group,paths in sorted(groups.items()):
        row=Image.new('RGB',(170*len(paths),160),(180,170,149));draw=ImageDraw.Draw(row);motion=[]
        for index,path in enumerate(paths):
            frame=Image.open(path).convert('RGBA');crop=frame.crop((138,135,308,295))
            row.paste(crop,(170*index,0),crop);draw.text((170*index+3,2),f'g{group} f{index}',fill='black')
            bg=Image.new('RGB',(170,160),(180,170,149));bg.paste(crop,(0,0),crop);motion.append(bg)
            box=bounds(frame)
            outside=0
            if box:
                alpha=frame.getchannel('A');outside=sum(1 for y in range(frame.height) for x in range(frame.width)
                    if alpha.getpixel((x,y))>=128 and not(170<=x<270 and 155<=y<275))
            findings.append({'group':group,'frame':index,'opaque_bbox':box,'stock100x120_outside_pixels':outside,'frame_sha256':sha(path)})
        row.save(folder/f'g{group:02d}-native.png');rows.append(row)
        motion[0].save(folder/f'g{group:02d}-motion.webp',save_all=True,append_images=motion[1:],duration=130 if group in (1,7,8) else 110,loop=0,lossless=True)
    contact=Image.new('RGB',(max(r.width for r in rows),160*len(rows)),(218,211,195))
    for index,row in enumerate(rows):contact.paste(row,(0,index*160))
    contact.save(folder/'all-native-actions.png')
    turn=groups[7]+groups[8]
    turnims=[]
    for i,path in enumerate(turn):
        im=Image.open(path).convert('RGBA')
        if i>=len(groups[7]):im=ImageOps.mirror(im)
        crop=im.crop((100,135,350,295));bg=Image.new('RGB',crop.size,(180,170,149));bg.paste(crop,(0,0),crop);turnims.append(bg)
    turnims[0].save(folder/'native-halfturn-flip-order.webp',save_all=True,append_images=turnims[1:],duration=140,loop=0,lossless=True)
    required=[r for r in findings if r['group'] in (0,2)]
    write(folder/'frame-findings.json',{'frames':findings,'holding_moving_stock_crop_pass':all(r['stock100x120_outside_pixels']==0 for r in required),
        'scope':'Actual source/native static pixels only; hit/defend/attack preview overhang is diagnostic, not native battle clipping or acceptance.'})

def compile_twice(paths):
    all_outputs=[];receipts=[]
    for pass_index in (1,2):
        outputs={};records=[]
        for path in paths:
            planned,receipt=art_compile.plan(ROOT,path)
            if set(outputs)&set(planned):raise ValueError('Duplicate actual compiler output')
            outputs.update(planned);records.append(receipt)
        for name,data in outputs.items():
            target=REPORT/f'compile-pass-{pass_index}'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        all_outputs.append({name:hashlib.sha256(data).hexdigest() for name,data in sorted(outputs.items())});receipts.append(records)
    if all_outputs[0]!=all_outputs[1]:raise ValueError('Actual compiler not deterministic')
    write(REPORT/'compiler-verification.json',{'recipes':len(paths),'physical_outputs_per_pass':len(all_outputs[0]),
        'repeat_exact':True,'compiled_files':all_outputs[0],'recipe_pins':{rel(p):sha(p) for p in paths},'native_or_visual_acceptance':False})
    write(REPORT/'compiler-receipts.json',receipts)
    print(json.dumps({'recipes':len(paths),'physical_outputs':len(all_outputs[0]),'repeat_exact':True}))

def main():
    paths=[]
    for unit in UNITS:paths+=assemble(unit)
    compile_twice(paths)

if __name__=='__main__':main()
