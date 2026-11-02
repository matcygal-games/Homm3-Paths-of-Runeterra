"""Source-only Ionia painted sprite assembly. Never edits live selections/stages.

This program only isolates delivered painted RGBA, applies one camera calibration
per entire atlas, registers a fixed root and assembles native consumer resources.
No anatomy, action, heraldry or effects are drawn or synthesized by this code.
"""
from pathlib import Path
import argparse, copy, hashlib, io, json
from collections import deque
import numpy as np
from PIL import Image, ImageFilter, ImageOps

SELF=Path(__file__).resolve(); S=SELF.parent; P=SELF.parents[4]
OLD=P/'assets/source/creatures/painted-20261025-revision-v1'
ROOT=[197,266]
UNITS={'ionianDisciple':80,'enlightenedWarrior':84,'kinkouInitiate':83,'kinkouAdept':86,
       'kashuriArmsbearer':86,'kashuriMarksman':89,'resistanceBlade':90,'resistanceVeteran':96}
SHOOTERS={'kashuriArmsbearer','kashuriMarksman'}
SCENE=P/'assets/source/town/landscape-v2/master.png'
ISOLATION_CACHE={}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def encoded(v): return (json.dumps(v,sort_keys=True,indent=2,ensure_ascii=False)+'\n').encode()
def png(im):
    f=io.BytesIO(); im.save(f,format='PNG'); return f.getvalue()
def rel(p): return p.relative_to(P).as_posix()
def pin(p): return {'path':rel(p),'sha256':sha(p)}
def frame_descriptor(p,raw,size):
    h=hashlib.sha256(raw).hexdigest()
    return {'source':rel(p),'source_sha256':h,'sha256':h,'source_canvas':list(size)}

def native_first_turn_r(image,double_wide=False):
    """Counter the ACTUAL native flip/origin shift, not an assumed root mirror.

    Full450px M(x)=449-x. getStackPositionAtHex shifts the same-hex world
    origin by-58 one-hex/-14 two-hex on right->left. Pre-reflect and translate
    the first TURN_R source by that exact delta, so its displayed pixels join
    the last TURN_L frame in either starting facing without interpolation.
    """
    delta=-14 if double_wide else -58
    out=Image.new('RGBA',image.size);out.alpha_composite(ImageOps.mirror(image),(delta,0))
    return out

def isolate(image,box):
    """Discard provider's low-alpha background haze; preserve original actor RGBA.

    Strong-alpha original paint plus a two-pixel antialias margin is the mask.
    There are no per-frame fits, rotations, warps, limb draws or color filters.
    """
    key=(id(image),tuple(box))
    if key in ISOLATION_CACHE:return ISOLATION_CACHE[key].copy()
    tile=image.crop(tuple(box)).convert('RGBA'); a=np.asarray(tile.getchannel('A'))
    core=a>=180; seen=np.zeros(core.shape,dtype=bool); largest=[]; components=[]
    h,w=core.shape
    for sy,sx in zip(*np.nonzero(core)):
        if seen[sy,sx]:continue
        todo=deque([(int(sy),int(sx))]);seen[sy,sx]=True;component=[]
        while todo:
            y,x=todo.popleft();component.append((y,x))
            for yy in range(max(0,y-1),min(h,y+2)):
                for xx in range(max(0,x-1),min(w,x+2)):
                    if core[yy,xx]and not seen[yy,xx]:seen[yy,xx]=True;todo.append((yy,xx))
        components.append(component)
        if len(component)>len(largest):largest=component
    assert largest,'Empty painted cell'
    ys,xs=zip(*largest); region=np.zeros(core.shape,dtype=bool)
    # Retain the complete connected actor and nearby disconnected painted
    # contact shadow/dropped weapon. Exclude fragments of a neighbouring row.
    region[max(0,min(ys)-12):min(h,max(ys)+13),max(0,min(xs)-12):min(w,max(xs)+13)]=True
    selected=np.zeros(core.shape,dtype=bool)
    for component in components:
        cy,cx=zip(*component)
        touches=min(cy)==0 or max(cy)==h-1 or min(cx)==0 or max(cx)==w-1
        if component is largest or (not touches and any(region[y,x]for y,x in component)):
            for y,x in component:selected[y,x]=True
    keep=Image.fromarray(np.where(selected,255,0).astype('uint8')).filter(ImageFilter.MaxFilter(5))
    rgba=np.array(tile); rgba[:,:,3]=np.where(np.asarray(keep)>0,rgba[:,:,3],0)
    result=Image.fromarray(rgba);ISOLATION_CACHE[key]=result;return result.copy()

def cell(image,row,col,rows,cols=6):
    w,h=image.size
    return [round(col*w/cols),round(row*h/rows),round((col+1)*w/cols),round((row+1)*h/rows)]

def project(image,pivot,scale,mirrored=False,canvas=(96,64),anchor=(80,60)):
    sx=-scale if mirrored else scale
    return image.convert('RGBA').transform(canvas,Image.Transform.AFFINE,
        (1/sx,0,pivot[0]-anchor[0]/sx,0,1/scale,pivot[1]-anchor[1]/scale),Image.Resampling.BICUBIC)

def atlas_camera(image,rows,holdrow,target_height,cols=6,holdcol=0):
    # This one holding-pose measurement calibrates the WHOLE atlas camera once.
    # Every action retains this same scale/root, including collapse and attacks.
    box=cell(image,holdrow,holdcol,rows,cols); tile=isolate(image,box)
    bounds=tile.getchannel('A').point(lambda x:255 if x>=180 else 0).getbbox()
    assert bounds, 'Missing delivered holding actor'
    scale=target_height/(bounds[3]-bounds[1])
    # Registered physical floor and pelvis corridor, frozen for the entire atlas.
    root=[tile.width*.55,bounds[3]]
    return {'scale':scale,'source_root_in_cell':root,'holding_bounds':list(bounds),'grid':[cols,rows]}

def render(image,row,col,rows,camera,ground_y=None):
    box=cell(image,row,col,rows,camera['grid'][0]); tile=isolate(image,box); scale=camera['scale']
    root=list(camera['source_root_in_cell'])
    if ground_y is not None:root[1]=ground_y
    sz=[round(tile.width*scale),round(tile.height*scale)]
    reduced=tile.resize(sz,Image.Resampling.LANCZOS)
    out=Image.new('RGBA',(450,400)); origin=[ROOT[0]-round(root[0]*scale),ROOT[1]-round(root[1]*scale)]
    out.alpha_composite(reduced,tuple(origin))
    return out,{'source_crop':box,'source_root':[box[0]+root[0],box[1]+root[1]],
                'scale':scale,'native_pivot':ROOT,'native_origin':origin}

def build():
    inputs=json.loads((S/'inputs.json').read_text())
    ground=json.loads((S/'death-ground-registration.json').read_text())
    for n,h in inputs['input_sha256'].items(): assert sha(P/n)==h,'Missing/stale source: '+n
    deps=[pin(SELF),pin(S/'inputs.json')]+[{'path':n,'sha256':h}for n,h in sorted(inputs['input_sha256'].items())]
    outputs={}; recipes={}; coverage={}; lineage=[]
    def save(path,image):
        raw=png(image); outputs[path]=raw; return frame_descriptor(path,raw,image.size)
    def emit(name,value):
        path=S/'recipes'/name; outputs[path]=encoded(value); recipes[value['output_path']]={'path':rel(path),'sha256':hashlib.sha256(outputs[path]).hexdigest()}
    for unit,height in UNITS.items():
        ISOLATION_CACHE.clear()
        motionpath=S/unit/('motion-master-v2-public.png'if unit=='resistanceVeteran'else'motion-master-v1-public.png')
        combatpath=S/unit/('combat-master-v2-public.png'if unit=='ionianDisciple'else'combat-master-v1-public.png')
        nearpath=S/unit/'near-walk-master-v1-public.png';farpath=S/unit/'far-walk-master-v1-public.png'
        adventurepath=S/unit/('adventure-master-v3-public.png'if unit=='enlightenedWarrior'else('adventure-master-v2-public.png'if unit=='resistanceVeteran'else'adventure-master-v1-public.png'))
        motion=Image.open(motionpath).convert('RGBA'); combat=Image.open(combatpath).convert('RGBA')
        near=Image.open(nearpath).convert('RGBA');far=Image.open(farpath).convert('RGBA');adventure=Image.open(adventurepath).convert('RGBA')
        cr=6 if unit in SHOOTERS else 4
        cameras={'motion':atlas_camera(motion,6,1,height),'combat':atlas_camera(combat,cr,0,height),
                 'near':atlas_camera(near,1,0,height,3),'far':atlas_camera(far,1,0,height,3),
                 'adventure':atlas_camera(adventure,2,1,height,4,2)}
        # Uniform atlas-level body calibration: upright carried weapons exceed
        # the anatomical head landmark. Keep body scale consistent with utility
        # holding rather than normalizing the actor to the weapon's opaque tip.
        if unit in ['resistanceBlade','resistanceVeteran']:
            for key in ['near','far']:
                cameras[key]['scale']*=1.08;cameras[key]['body_landmark_calibration']=1.08
        if unit in ['ionianDisciple','enlightenedWarrior']:
            cameras['adventure']['scale']*=1.18;cameras['adventure']['body_landmark_calibration']=1.18
        sheets={'motion':motion,'combat':combat,'near':near,'far':far,'adventure':adventure}; paths={'motion':motionpath,'combat':combatpath,'near':nearpath,'far':farpath,'adventure':adventurepath}
        # Slots reference genuinely delivered painted poses. Returns to ready are
        # intentional and are not counted as additional unique action poses.
        poses={0:[(half,0,c)for half in ['near','far']for c in range(3)],
               1:[('motion',1,c)for c in [0,1,2,1,0]],
               2:[('motion',1,0)]*2,
               3:[('motion',1,c)for c in [3,4,5]],
               4:[('motion',2,c)for c in [0,1,2]],
               5:[('motion',3,c)for c in range(6)]}
        if unit in ['resistanceBlade','resistanceVeteran']:
            poses[2]=[('adventure',1,2)]*2
        if unit in SHOOTERS:
            half=[('motion',1,0),('motion',2,3),('motion',2,4)]
        else: half=[('combat',3,c)for c in [0,1,2]]
        poses[7]=half; poses[8]=list(reversed(half))
        for g in [11,12,13]: poses[g]=[('combat',g-11+(3 if unit in SHOOTERS else 0),c)for c in range(6)]
        if unit in SHOOTERS:
            for g in [14,15,16]: poses[g]=[('combat',g-14,c)for c in range(6)]
        poses[22]=[('motion',3,5)]
        native={}; desc={}; unitline=[]
        for g,items in sorted(poses.items()):
            for f,(sheet,row,col)in enumerate(items):
                ground_y=ground['units'][unit]['source_ground_in_cell'][col]if g in [5,22]else None
                rows=6 if sheet=='motion'else(cr if sheet=='combat'else(2 if sheet=='adventure'else 1))
                image,e=render(sheets[sheet],row,col,rows,cameras[sheet],ground_y)
                path=S/unit/'native'/f'g{g:02d}-f{f:03d}.png'; d=save(path,image)
                native[g,f]=image; desc[g,f]=d
                unitline.append({'unit':unit,'group':g,'frame':f,'painted_master':rel(paths[sheet]),
                    'painted_master_sha256':sha(paths[sheet]),'cell':[row,col],**e,'native':d})
        # Exact native display joins, while preserving the genuine intermediate
        # half-turn poses and ordinary HOLDING body/ground registration.
        last7=len(poses[7])-1;last8=len(poses[8])-1
        replacements={(7,0):native[2,0].copy(),(8,last8):native[2,0].copy(),
                      (8,0):native_first_turn_r(native[7,last7])}
        for key,image in replacements.items():
            g,f=key;native[key]=image;path=S/unit/'native'/f'g{g:02d}-f{f:03d}.png';desc[key]=save(path,image)
            unitline=[e for e in unitline if (e['group'],e['frame'])!=key]
            parentkey=(7,last7)if key==(8,0)else(2,0)
            unitline.append({'unit':unit,'group':g,'frame':f,'painted_parent_native':desc[parentkey],
                'technical_transform':'full-canvas horizontal reflection then translation(-58,0)'if key==(8,0)else'exact HOLDING source copy',
                'native_consumer_world_shift':-58 if key==(8,0)else 0,'native':desc[key]})
        assert png(native[5,5])==png(native[22,0]),'Settled corpse continuity'
        lineage+=unitline
        gen={'image_generation_used':True,'provider':'OpenAI built-in imagegen','model':'not exposed by built-in tool',
             'painted_master':rel(motionpath),'painted_master_sha256':sha(motionpath),
             'painted_action_masters':[pin(motionpath),pin(combatpath),pin(nearpath),pin(farpath),pin(adventurepath)],
             'prompt':'\n\n'.join((S/unit/name).read_text()for name in [('motion-v2-prompt.txt'if unit=='resistanceVeteran'else'motion-prompt.txt'),('combat-v2-prompt.txt'if unit=='ionianDisciple'else'combat-prompt.txt'),'near-walk-prompt.txt','far-walk-prompt.txt',('adventure-v3-prompt.txt'if unit=='enlightenedWarrior'else('adventure-v2-prompt.txt'if unit=='resistanceVeteran'else'adventure-prompt.txt'))]),
             'method':'Original delivered painted2D action cohorts; original RGBA strong-alpha isolation with2px edge margin; one fixed camera calibration/root per whole atlas, no per-frame fit or anatomy synthesis.',
             'native_playback':'not_run','release_accepted':False}
        common={'unit':unit,'production_status':'painted-master-complete-unapproved','status':'built-unreviewed',
            'visual_approval_granted':False,'acceptance':'authored configuration; independent pixel review/native playback/rights pending',
            'credits':{'author':'Project-directed OpenAI built-in imagegen; deterministic technical assembly','license':None,'redistribution':'unresolved'},
            'generation':gen,'dependencies':deps}
        emit(unit+'-battle.json',{**common,'recipe_type':'vcmi_animation','canvas':[450,400],
            'pivot':dict(zip(['x','y'],ROOT)),'generateShadow':1,'generateOverlay':1,
            'output_path':f'Content/Sprites/runeterra/ionia/creatures/{unit}/battle.json',
            'groups':[{'group':g,'frames':[desc[g,f]for f in range(len(items))]}for g,items in sorted(poses.items())]})
        maps=[];adventureparents={};adventuredesc={};adventure_scale=.45
        # Separate compact painted carrying poses preserve a native-size actor
        # instead of shrinking long battle weapon swings to fit the map tile.
        reaction_pose=4 if unit=='resistanceVeteran'else 7
        for i in sorted({0,1,2,3,4,5,reaction_pose}):
            row,col=divmod(i,4);image,e=render(adventure,row,col,2,cameras['adventure'])
            adventureparents[i]=image;adventuredesc[i]=save(S/unit/'adventure-parent'/f'f{i:03d}.png',image)
            lineage.append({'unit':unit,'role':'compact adventure parent','pose':i,'painted_master':rel(adventurepath),'painted_master_sha256':sha(adventurepath),**e,'native':adventuredesc[i]})
        for f,i in enumerate([4,0,1,5,2,3]):
            image=project(adventureparents[i],ROOT,adventure_scale); d=save(S/unit/'adventure'/f'map-{f:03d}.png',image)
            d['projection_contract']={'source':adventuredesc[i]['source'],'source_sha256':adventuredesc[i]['source_sha256'],'pivot':ROOT,'scale':adventure_scale,'mirrored':False,'anchor':[80,60],'canvas':[96,64]}; maps.append(d)
        emit(unit+'-map.json',{**common,'recipe_type':'vcmi_animation','canvas':[96,64],'pivot':{'x':80,'y':60},
            'generateShadow':0,'generateOverlay':0,'output_path':f'Content/Sprites/runeterra/ionia/creatures/{unit}/map.json','groups':[{'group':0,'frames':maps}]})
        for role,mirror in [('attackLeft',True),('attackRight',False)]:
            image=project(adventureparents[reaction_pose],ROOT,adventure_scale,mirror,(96,64),(80,60)); d=save(S/unit/'adventure'/(role+'.png'),image)
            emit(unit+'-'+role+'.json',{**common,'recipe_type':'raster','size':[96,64],'fit':'exact','require_alpha':True,
                'output_path':f'Content/Sprites/runeterra/ionia/creatures/{unit}/{role}.png',**d,
                'projection_contract':{'source':adventuredesc[reaction_pose]['source'],'source_sha256':adventuredesc[reaction_pose]['source_sha256'],'pivot':ROOT,'scale':adventure_scale,'mirrored':mirror,'anchor':[80,60],'canvas':[96,64],'source_facing':'right'}})
        # Close head/upper torso portraits from genuine high-resolution combat
        # source, composited over this project's verified own painted scene.
        box=cell(near,0,0,1,3); tile=isolate(near,box); b=tile.getchannel('A').point(lambda x:255 if x>=180 else 0).getbbox()
        head=[b[0]+(b[2]-b[0])*.34,b[1],b[0]+(b[2]-b[0])*.79,b[1]+(b[3]-b[1])*.48]
        for role,size in [('large',(58,64)),('small',(32,32))]:
            back=Image.open(SCENE).convert('RGBA').crop((250,80,850,700)); back=ImageOps.fit(back,size,Image.Resampling.LANCZOS)
            face=ImageOps.fit(tile.crop(tuple(round(x)for x in head)),size,Image.Resampling.LANCZOS); back.alpha_composite(face)
            d=save(S/unit/'portraits'/(role+'.png'),back.convert('RGB').convert('RGBA'))
            emit(unit+'-'+role+'.json',{**common,'recipe_type':'raster','size':list(size),'fit':'exact','require_alpha':False,
                'output_path':f'Content/Sprites/runeterra/ionia/creatures/{unit}/{role}.png',**d,
                'portrait_background':pin(SCENE),'portrait_composition':{'source':rel(nearpath),'source_cell':box,'crop_in_cell':head,'scene_crop':[250,80,850,700]}})
        coverage[unit]={'status':'authored configuration','groups':{str(g):len(v)for g,v in poses.items()},'cameras':cameras,
            'source_sha256':{rel(p):sha(p)for p in [motionpath,combatpath,nearpath,farpath,adventurepath]},'native_playback':False,
            'art_review':'Native-size candidate review and independent final acceptance remain pending. Explicit near/far passing states are visibly articulated; contact-leg opposition under baggy trousers remains a precise review limitation. No artistic acceptance inferred from conversion.'}
    # Preserve all six existing genuinely painted cohorts byte for byte.
    for folder in [OLD/'t3/candidates',OLD/'t5-t7/recipes-v2']:
        for rp in sorted(folder.glob('*.json')):
            r=json.loads(rp.read_text()); role=rp.stem.split('-')[-1]
            if role=='battle':
                bygroup={g['group']:g for g in r['groups']}
                bygroup[7]['frames'][0]=copy.deepcopy(bygroup[2]['frames'][0])
                bygroup[8]['frames']=list(reversed(copy.deepcopy(bygroup[7]['frames'])))
                unit=r['unit'];wide=r['pivot']['x']==218
                front=bygroup[7]['frames'][-1];image=Image.open(P/front['source']).convert('RGBA')
                path=S/unit/'turn-native/g08-f000.png';bygroup[8]['frames'][0]=save(path,native_first_turn_r(image,wide))
                r['turn_consumer_contract']={'consumer':'g7 half-turn, native flip/reposition, g8 genuine reverse-half remainder, holding',
                    'source_reuse':'G7 first/G8 last exact HOLDING. FirstG8 is full450px mirror of lastG7 translated by native world-origin delta; laterG8 uses genuine reverse half-turn. Old back-turn studies preserved unselected.',
                    'first_turn_r_world_shift':-14 if wide else -58,
                    'native_playback':'pending; asymmetric tail/weapon boundary still needs observation'}
                r.setdefault('dependencies',[]).extend([pin(SELF),pin(S/'inputs.json'),pin(rp)])
            emit(rp.name,r)
    # A new ordinary painted musket pellet, reduced/rotated technically only.
    ISOLATION_CACHE.clear()
    shotpath=S/'projectile/painted-master-public.png'; shot=Image.open(shotpath).convert('RGBA')
    mask=shot.getchannel('A').point(lambda x:255 if x>=180 else 0); b=mask.getbbox(); shot=isolate(shot,b)
    ratio=14/shot.width; shot=shot.resize((14,max(1,round(shot.height*ratio))),Image.Resampling.LANCZOS)
    tile=Image.new('RGBA',(40,40));tile.alpha_composite(shot,((40-shot.width)//2,(40-shot.height)//2))
    for unit in sorted(SHOOTERS):
        frames=[]
        for f,angle in enumerate([90,45,0,-45,-90]): frames.append(save(S/unit/'projectile'/f'f{f:03d}.png',tile.rotate(angle,resample=Image.Resampling.BICUBIC)))
        emit(unit+'-projectile.json',{'unit':unit,'recipe_type':'vcmi_animation','canvas':[40,40],
            'pivot':{'x':20,'y':20},'generateShadow':0,'generateOverlay':0,'production_status':'painted-master-complete-unapproved','status':'built-unreviewed',
            'credits':{'author':'OpenAI built-in imagegen; technical reduction/rotations','license':None,'redistribution':'unresolved'},
            'generation':{'image_generation_used':True,'provider':'OpenAI built-in imagegen','model':'not exposed by built-in tool','painted_master':rel(shotpath),'painted_master_sha256':sha(shotpath),'method':'Actual original painted physical pellet, one uniform reduction then native angle rotations only','prompt':(S/'projectile/prompt.txt').read_text()},
            'dependencies':deps,'output_path':f'Content/Sprites/runeterra/ionia/projectiles/{unit}.json','groups':[{'group':0,'frames':frames}]})
    outputs[S/'frame-lineage.json']=encoded({'status':'authored configuration','frames':lineage})
    outputs[S/'coverage.json']=encoded({'status':'authored configuration','new_variants':coverage,'reused_variants':['vastayanScout','vastayanWarrior','jeweledProtector','crestboundProtector','empyrean','elderEmpyrean'],'selected_native_execution':False,'final_art_accepted':False})
    outputs[S/'candidate-selection.json']=encoded({'status':'authored configuration','candidate_only':True,'outputs':recipes,'coordinator_only_integration':True})
    return outputs

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args();out=build()
    for p,raw in out.items():
        if args.check: assert p.read_bytes()==raw,'Stale derived source: '+rel(p)
        else: p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    print(json.dumps({'exact_check':args.check,'source_artifacts':len(out),'candidate_recipes':sum(p.parent.name=='recipes'for p in out),'native_execution':False}))
if __name__=='__main__':main()
