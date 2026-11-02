"""Technical-only extraction/registration of independent spherical Fluft poses.

Does not paint, deform, rotate, synthesize or publish a stage. Candidates and
actual production-compiler outputs are isolated until coordinator selection.
"""
from pathlib import Path
from statistics import median
from copy import deepcopy
import hashlib
import io
import json
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageOps

S = Path(__file__).resolve().parent
P = S.parents[3]
W = P.parent
O = P / 'build/reports/round-fluft-ten-20261029-v1'
sys.path.insert(0, str(P / 'scripts'))
sys.path.insert(0, str(W / 'scripts'))
from creature_atlas import components, assign_rows, ownership, subject
from faction_art_compile import create_compiler


def sha(raw): return hashlib.sha256(raw).hexdigest()
def rel(path): return path.relative_to(P).as_posix()
def write(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
def js(path, value): write(path, (json.dumps(value, indent=2, sort_keys=True)+'\n').encode())
def png(im, path):
    data=io.BytesIO(); im.save(data, format='PNG',compress_level=9,optimize=False)
    write(path,data.getvalue())
    return {'source':rel(path),'source_canvas':list(im.size),'source_sha256':sha(data.getvalue())}


def extract(cohort, counts, target_height=70):
    master=S/cohort/'master.png'
    im=Image.open(master).convert('RGBA')
    labels,found=components(im)
    rows,extra=assign_rows(found,counts,minimum_area=600)
    mains=sum(rows,[]); own=ownership(labels,mains,extra)
    # One fixed camera scale per sheet; never fit a pose individually.
    reference=(rows[0][0].bbox[3]-rows[0][0].bbox[1] if cohort.startswith('special')
               else median(x.bbox[3]-x.bbox[1] for x in rows[0 if cohort.startswith('melee') else 1]))
    scale=target_height/reference
    data={}; records=[]
    for row,bodies in enumerate(rows):
        centers=[x.centroid[0] for x in bodies]
        spacing=median(b-a for a,b in zip(centers,centers[1:]))
        offset=median(x.centroid[0]-col*spacing for col,x in enumerate(bodies))
        for col,body in enumerate(bodies):
            part,e=subject(im,labels,body,extra,mains,cell_ownership=own)
            bounds=e['source_bbox']; root=offset+col*spacing
            ground=266
            if cohort=='general-v2' and row==0: ground=(264,258,253,258,264,260)[col]
            if cohort=='special-v1' and row==1: ground=(266,263,252,252,266,266)[col]
            native=Image.new('RGBA',(450,400))
            actor=part.resize((round(part.width*scale),round(part.height*scale)),Image.Resampling.LANCZOS)
            origin=(193+round((bounds[0]-root)*scale),ground-round((body.bbox[3]-bounds[1])*scale))
            native.alpha_composite(actor,origin)
            if np.count_nonzero(np.asarray(native)[:,:,3]) != np.count_nonzero(np.asarray(actor)[:,:,3]):
                raise ValueError('Native canvas clips complete subject')
            desc=png(native,S/'native-v1'/cohort/f'r{row}-c{col}.png')
            data[row,col]=desc
            retained=np.count_nonzero((own==body.identifier)&(labels==body.identifier))
            foreign=np.count_nonzero((own==body.identifier)&(labels!=0)&np.isin(labels,[x.identifier for x in mains if x!=body]))
            if retained!=body.area or foreign: raise ValueError('Incomplete/contaminated actor')
            records.append({'row':row,'col':col,'source_bbox':bounds,'source_opaque_bbox':list(body.bbox),
                            'retained_opaque_pixels':int(retained),'foreign_body_pixels':int(foreign),
                            'native_origin':origin,'native_support_y':ground,'descriptor':desc,**e})
    edges=[im.getchannel('A').crop(b).getextrema()[1] for b in [(0,0,im.width,1),(0,im.height-1,im.width,im.height),(0,0,1,im.height),(im.width-1,0,im.width,im.height)]]
    if max(edges)>=128: raise ValueError('Master body clips edge')
    registration={'master':rel(master),'master_sha256':sha(master.read_bytes()),'canvas':list(im.size),
                  'row_counts':counts,'scale':scale,'per_frame_scaling':False,'fixed_pivot':[193,266],
                  'edge_max_alpha':edges,'frames':records,'native_execution':False,'art_accepted':False}
    js(S/cohort/'registration.json',registration)
    return data


def auxiliary(hold, attack):
    resources={}
    for role,size,diameter in [('large',(58,64),53),('small',(32,32),29),('map',(64,64),39),('attackRight',(64,64),39),('attackLeft',(64,64),39)]:
        src=attack if role.startswith('attack') else hold
        actor=Image.open(P/src['source']).convert('RGBA')
        alpha=actor.getchannel('A'); box=alpha.point(lambda a:255 if a>=16 else 0).getbbox()
        actor=actor.crop(box); scale=diameter/max(actor.size)
        actor=actor.resize((round(actor.width*scale),round(actor.height*scale)),Image.Resampling.LANCZOS)
        out=Image.new('RGBA',size)
        if role in ('map','attackLeft','attackRight'):
            origin=(44-actor.width//2,59-actor.height)
        else: origin=((size[0]-actor.width)//2,size[1]-actor.height-2)
        out.alpha_composite(actor,origin)
        if role=='attackLeft': out=ImageOps.mirror(out)
        resources[role]=png(out,S/'native-v1/resources'/f'{role}.png')
    return resources


def assemble():
    general=extract('general-v2',[6]*4)
    melee=extract('melee-v2',[6]*3)
    special=extract('special-v1',[6]*2)
    h=general[1,0]
    groups={0:[general[0,c] for c in range(6)],1:[general[1,c] for c in range(6)],2:[h],
            3:[h]+[general[2,c] for c in range(3)],4:[h]+[general[2,c] for c in range(3,6)],
            5:[h]+[special[0,c] for c in range(6)]+[special[0,5]],
            7:[general[3,c] for c in range(3)],8:[general[3,3],general[3,4],general[2,5]],
            11:[h]+[melee[0,c] for c in range(6)],12:[h]+[melee[1,c] for c in range(6)],
            13:[h]+[melee[2,c] for c in range(6)],20:[h]+[special[1,c] for c in range(3)],
            21:[special[1,c] for c in range(3,6)]+[h]}
    resources=auxiliary(general[3,0],melee[1,3])
    selected_files=[S/'assemble.py']
    # Include selected masters and their actual painted edit lineage, excluding
    # the unrelated superseded 36-pose ten-Poro study.
    for cohort in ('identity-v1','general-v2','melee-v1','melee-v2','special-v1'):
        selected_files += [path for path in (S/cohort).iterdir() if path.is_file() and path.name in ('master.png','prompt.txt','generation.json','registration.json')]
    selected_files += [P/'assets/source/creatures/painted-20261024/fluftOfPoros/holding-v1.png',
                      P/'assets/source/regional-crests-20261025-v1/creatures/materials/poro-cloth-raw-v2.png']
    inputs=[{'path':rel(path),'sha256':sha(path.read_bytes())} for path in sorted(selected_files)]
    generation={'image_generation_used':True,'provider':'OpenAI built-in imagegen','model':'not exposed by tool',
                'painted_master':rel(S/'general-v2/master.png'),'painted_master_sha256':sha((S/'general-v2/master.png').read_bytes()),
                'supplemental_masters':[{'path':rel(S/cohort/'master.png'),'sha256':sha((S/cohort/'master.png').read_bytes())} for cohort in ('melee-v2','special-v1','identity-v1')],
                'prompt':'Exact versioned prompt.txt and generation.json in selected source cohorts.',
                'method':'About ten living small Poros nest into one spherical Fluft. Independent painted articulated tumble/bounce, six movement phases with an explicit support arc. Irregular alpha ownership extraction and fixed cohort camera scale; no per-frame fitting, no rigid bitmap rotation, no Blender/3D or code-painted artwork.',
                'native_execution':False,'visual_approval_granted':False}
    recipes=[]
    previous=P/'assets/recipes/creatures/painted-20261024/fluftOfPoros'
    for role in ('battle','map','large','small','attackLeft','attackRight'):
        r=json.loads((previous/f'{role}.json').read_text(encoding='utf-8'))
        r.update(generation=deepcopy(generation),inputs=inputs,status='authored configuration',visual_approval_granted=False)
        if role=='battle': r['groups']=[{'group':g,'frames':[{'frame':i,**d} for i,d in enumerate(seq)]} for g,seq in groups.items()]
        elif role=='map': r['groups']=[{'group':0,'frames':[{'frame':0,**resources['map']}]}]
        else: r.update(resources[role])
        path=S/'recipes'/f'{role}.json';js(path,r);recipes.append(path)
    compiler=create_compiler('freljord')
    output_sets=[]
    for passnum in (1,2):
        complete={}; receipts=[]
        for path in recipes:
            outputs,receipt=compiler.plan(P,path);receipts.append(receipt)
            for name,payload in outputs.items():
                if name in complete: raise ValueError('Duplicate export')
                complete[name]=sha(payload)
                write(O/f'pass{passnum}'/name,payload)
        js(O/f'output-hashes-pass{passnum}.json',complete)
        js(O/f'compiler-pass{passnum}.json',receipts);output_sets.append(complete)
    if output_sets[0]!=output_sets[1]: raise ValueError('Real compiler differs twice')
    sheet=Image.new('RGBA',(780,len(groups)*120),(43,48,51,255));draw=ImageDraw.Draw(sheet)
    for row,(group,seq) in enumerate(groups.items()):
        draw.text((3,row*120+3),f'Native group {group}',fill='white')
        for col,d in enumerate(seq): sheet.alpha_composite(Image.open(P/d['source']).crop((145,174,243,284)),(col*97,row*120+12))
        frames=[]
        for d in seq:
            im=Image.new('RGBA',(110,114),(43,48,51,255));im.alpha_composite(Image.open(P/d['source']).crop((140,174,250,288)));frames.append(im.convert('RGB'))
        frames[0].save(O/f'group-{group}.gif',save_all=True,append_images=frames[1:],duration=130,loop=0,disposal=2)
    png(sheet,O/'native-contact.png')
    tests=[]
    for group in (0,2,20,21):
        for d in groups[group]:
            im=Image.open(P/d['source']);crop=im.crop((170,155,270,285));pixels=np.count_nonzero(np.asarray(crop)[:,:,3]>=128)
            if pixels<500: raise ValueError('Native picture body crop too small')
            tests.append({'group':group,'source':d['source'],'opaque_crop_pixels':int(pixels)})
    js(O/'crop-check.json',tests)
    alpha=Image.new('RGBA',(440,114))
    for i,color in enumerate(('white','#132c55','#286839','#786044')):
        part=Image.new('RGBA',(110,114),color);part.alpha_composite(Image.open(P/h['source']).crop((140,174,250,288)));alpha.alpha_composite(part,(i*110,0))
    png(alpha,O/'alpha-backgrounds.png')
    html='<html><meta charset="utf-8"><title>Ten-poro rolling Fluft</title><style>body{background:#202830;color:#eee;font:18px sans-serif}img{image-rendering:pixelated;max-width:100%}figure{display:inline-block}</style><h1>About ten small Poros: bouncy rolling Fluft</h1><p>Authored configuration, painted2D candidate. Native gameplay and release acceptance pending. Nine visible faces in the identity; animated front hemisphere shows6–8faces plus small backs, horns and paw tips, with other animals occluded behind. FLYING retained only as rolling obstacle-clearing hop adaptation. Base single Overgrown Poro untouched. Native canvas450×400 and pivot193,266 retained. Actual alpha on varied backdrops:</p><img src="alpha-backgrounds.png"><p>All action frames at native scale:</p><img src="native-contact.png"><h2>Software motion previews</h2>'
    for g in groups:html+=f'<figure><figcaption>Native group {g}</figcaption><img src="group-{g}.gif"></figure>'
    write(O/'index.html',html.encode())
    js(S/'source-selection.json',{'status':'authored configuration','unit':'fluftOfPoros','candidate_only':True,
        'recipes':[{'path':rel(p),'sha256':sha(p.read_bytes())} for p in recipes],
        'outputs':output_sets[0],'native_execution':False,'visual_approval_granted':False})
    print(json.dumps({'ok':True,'recipes':len(recipes),'outputs':len(output_sets[0]),'crop_checks':len(tests),'two_real_compiler_passes_identical':True}))


if __name__=='__main__': assemble()
