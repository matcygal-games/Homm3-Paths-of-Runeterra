"""Technical assembly of genuinely painted badgerbear actors. Never paints poses."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from PIL import Image, ImageOps

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[4]
UNITS=('loyalBadgerbear','veteranBadgerbear')

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,value):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def rel(p):return Path(p).relative_to(PROJECT).as_posix()
def checked(record):
    p=(PROJECT/record['source']).resolve()
    if not p.is_relative_to((PROJECT/'assets/source').resolve()):raise ValueError('source escapes own artwork')
    if not p.is_file() or digest(p)!=record['sha256']:raise ValueError('source pin drift '+str(p))
    return p

def actor(plan,name):
    r=plan['poses'][name];im=Image.open(checked(r)).convert('RGBA').crop(r['crop'])
    # Threshold is technical transparent-background cleanup, never a drawing/filter.
    a=im.getchannel('A');matte=Image.open(checked(r['matte'])).convert('L')
    if matte.size!=im.size:raise ValueError('whole-actor matte/crop mismatch')
    im.putalpha(Image.composite(a,Image.new('L',im.size),matte))
    scale=r['scale'];root=[r['root'][0]-r['crop'][0],r['root'][1]-r['crop'][1]]
    size=(round(im.width*scale),round(im.height*scale))
    im=im.resize(size,Image.Resampling.LANCZOS)
    out=Image.new('RGBA',(450,400))
    out.alpha_composite(im,(round(197-root[0]*scale),round(266-root[1]*scale)))
    return out

def project(im,mirror=False,scale=.3):
    # One affine root transform, matching the native bottom-right tile anchor.
    sign=-1 if mirror else 1
    return im.transform((96,64),Image.Transform.AFFINE,
        (sign/scale,0,197-sign*80/scale,0,1/scale,266-60/scale),
        Image.Resampling.BICUBIC)

def descriptor(p,**extra):return {'source':rel(p),'sha256':digest(p),**extra}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--report',type=Path);args=parser.parse_args()
    plan_path=HERE/'assembly-plan-v1.json';plan=json.loads(plan_path.read_text())
    for r in plan['poses'].values():checked(r);checked(r['matte'])
    groups={
        0:['walk0','walk1','walk2','walk3','walk4','walk5'],
        1:['hold','fidget1','fidget1','fidget2','fidget2','fidget3','fidget3'],
        2:['hold'],3:['hit0','hit1','hold'],4:['defend0','defend1','hold'],
        5:['die0','die1','die2','dead'],
        7:['turn0','turn1','front'],8:['front','turn1','turn0'],
        11:['level0','level1','level2','level3','hold'],
        12:['up0','up1','up2','up3','hold'],
        13:['down0','down1','down2','down3','hold'],22:['dead']}
    paths=[];selection={};reports={}
    for unit in UNITS:
        native=HERE/'native'/unit;native.mkdir(parents=True,exist_ok=True)
        allframes={};animation=[]
        for group,names in groups.items():
            frames=[]
            for i,name in enumerate(names):
                im=actor(plan,unit+'/'+name);p=native/f'g{group:02d}-f{i:03d}.png';im.save(p)
                frames.append(descriptor(p));allframes[f'{group}/{i}']=digest(p)
            animation.append({'group':group,'frames':frames})
        corpse=Image.open(native/'g05-f003.png').convert('RGBA')
        assert corpse.tobytes()==Image.open(native/'g22-f000.png').convert('RGBA').tobytes()
        assert corpse.tobytes()!=Image.open(native/'g02-f000.png').convert('RGBA').tobytes()
        output=f'Content/Sprites/runeterra/demacia/creatures/{unit}/'
        provenance={'image_generation_used':True,'provider':'OpenAI built-in imagegen','model':'not exposed',
            'method':'Original painted2D identity/actions; whole-pose crop, uniform source-sheet density calibration and root transform only; no3D, body warp or procedural actor',
            'painted_master':rel(HERE/f'{unit}-master-v1-public.png'),
            'painted_master_sha256':digest(HERE/f'{unit}-master-v1-public.png'),
            'native_playback':'not_run','release_accepted':False}
        inputs=[{'path':rel(p),'sha256':digest(p)} for p in sorted([*HERE.glob('*'),*HERE.glob('mattes/*.png')]) if p.is_file() and (p.parent.name=='mattes' or p.name.endswith('-public.png') or p.suffix in ('.py','.txt') or p.name in ('assembly-plan-v1.json','generation-provenance-v1.json','identity-prompts-v1.json','action-prompts-v1.json'))]
        common={'generation':provenance,'producer_inputs':inputs,'acceptance':'authored configuration; source pixels only; native motion/final art/rights pending',
            'credits':'Project-directed built-in imagegen original painted2D artwork. Official/installed images used privately for reference only; redistribution approval unresolved.',
            'unit':unit,'status':'built-unreviewed','visual_approval_granted':False}
        recipes={}
        recipes['battle']={**common,'recipe_type':'vcmi_animation','output_path':output+'battle.json','canvas':[450,400],'pivot':{'x':197,'y':266},'generateShadow':1,'generateOverlay':1,'groups':animation}
        mf=[]
        for i,name in enumerate(['hold','fidget1','turn0','turn1','sniff','settle']):
            parent=native/f'map-parent-f{i:03d}.png';actor(plan,unit+'/'+name).save(parent)
            im=project(Image.open(parent).convert('RGBA'),True);p=native/f'map-f{i:03d}.png';im.save(p)
            mf.append(descriptor(p,projection_contract={'source':rel(parent),'source_sha256':digest(parent),'pivot':[197,266],'anchor':[80,60],'canvas':[96,64],'scale':.3,'mirrored':True}))
        recipes['map']={**common,'recipe_type':'vcmi_animation','output_path':output+'map.json','canvas':[96,64],'pivot':{'x':80,'y':60},'generateShadow':2,'generateOverlay':0,'groups':[{'group':0,'frames':mf}]}
        for role,mirror in [('attackLeft',True),('attackRight',False)]:
            parent=native/(role+'-parent.png');actor(plan,unit+'/turn1').save(parent)
            p=native/(role+'.png');project(Image.open(parent).convert('RGBA'),mirror).save(p)
            recipes[role]={**common,'recipe_type':'raster','output_path':output+role+'.png',
                'source':rel(p),'source_sha256':digest(p),'size':[96,64],'fit':'contain','require_alpha':True,
                'projection_contract':{'source':rel(parent),'source_sha256':digest(parent),'pivot':[197,266],'anchor':[80,60],'canvas':[96,64],'scale':.3,'mirrored':mirror,'source_facing':'right'}}
        portrait=PROJECT/'assets/source/creatures'/unit/'scenic-portrait-master-v1.png'
        portrait.parent.mkdir(parents=True,exist_ok=True)
        Image.open(HERE/f'{unit}-portrait-v1-public.png').convert('RGBA').save(portrait)
        for role,size in [('large',[58,64]),('small',[32,32])]:
            # Two explicit crops of the SAME genuine own painted scenic portrait.
            im=Image.open(portrait);ratio=size[0]/size[1]
            h=im.height;w=round(h*ratio)
            if w>im.width:w=im.width;h=round(w/ratio)
            x=(im.width-w)//2;y=0
            recipes[role]={**common,'recipe_type':'raster','output_path':output+role+'.png','source':rel(portrait),
                'source_sha256':digest(portrait),'size':size,'crop':[x,y,x+w,y+h],'fit':'contain','require_alpha':False}
        for role,r in recipes.items():
            p=HERE/'candidates'/f'{unit}-{role}.json';dump(p,r);selection[r['output_path']]=rel(p);paths.append(p)
        reports[unit]={'battle_frame_count':sum(len(v) for v in groups.values()),'groups':{str(g):len(v) for g,v in groups.items()},'frame_sha256':allframes,
            'corpse_exact_final_death':True,'native_verified':False,'release_accepted':False,'pivot':[197,266],
            'fidget_ticks':7,'fidget_probability':'unchanged source content0.1, native timing unobserved',
            'turn_contract':'g7 side-to-front, engine flips facing, g8 reverses same genuine half-turn to source-side; no back-view snap'}
    selected={'status':'authored configuration; unselected source candidates','candidates':selection,'recipe_sha256':{rel(p):digest(p) for p in paths},'units':reports}
    dump(HERE/'candidate-selection-v1.json',selected)
    if args.report:dump(args.report,selected)
    print(json.dumps({'ok':True,'recipes':len(paths),'units':{k:v['battle_frame_count'] for k,v in reports.items()},'selection_sha256':digest(HERE/'candidate-selection-v1.json')}))

if __name__=='__main__':main()
