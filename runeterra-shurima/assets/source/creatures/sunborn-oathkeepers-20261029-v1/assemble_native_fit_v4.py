"""Technical slicing/registration of painted Oathkeeper candidates only.

No canonical recipe, generated asset, manifest, gameplay source or stage is
written. Source silhouettes are never redrawn. Near-transparent generation
matte pixels are removed by the explicit alpha threshold, then connected
painted actors are isolated and uniformly scaled onto native canvases.
"""
import hashlib
import io
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageOps

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
WORKSPACE=PROJECT.parent
REPORT=WORKSPACE/'reports/shurima-sunborn-revision-20261029-v1/art-t7-native-fit-v4'
sys.path.insert(0,str(WORKSPACE/'scripts'))
from faction_art_compile import create_compiler

COHORT=SOURCE.relative_to(PROJECT).as_posix()
UNITS={
    'sunbornOathkeeper':{'locomotion':'locomotion-v3.png','combat':'combat-v2.png','reactions':'reactions-v2.png','walk':'walk-v1.png'},
    'exaltedOathkeeper':{'locomotion':'locomotion-v2.png','combat':'combat-v1.png','reactions':'reactions-v1.png','walk':'walk-v1.png'},
}
GROUPS={0:('walk',list(range(6))),1:('locomotion',[6,7]),2:('locomotion',[6]),
        3:('reactions',[2,3]),4:('reactions',[0,1]),5:('reactions',[4,5,6,7]),
        7:('locomotion',[8,9,10]),8:('locomotion',[10,9,8]),
        11:('combat',[4,5,6,7]),12:('combat',[0,1,2,3]),13:('combat',[8,9,10,11]),
        22:('reactions',[7])}
LABELS={0:'Walking',1:'Idle',2:'Standing',3:'Wince',4:'Defend',5:'Death',7:'Turn toward camera',
        8:'Turn return',11:'Strike upward',12:'Strike straight',13:'Strike downward',22:'Corpse'}
ALPHA_THRESHOLD=16

def pin(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def encoded(value):return (json.dumps(value,sort_keys=True,indent=2)+'\n').encode('utf-8')
def store(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() and path.read_bytes()!=raw:
        raise ValueError('Candidate output already differs; preserve version: '+str(path))
    if not path.exists():path.write_bytes(raw)
def png(image):
    stream=io.BytesIO();image.save(stream,format='PNG');return stream.getvalue()

def extract(path,rows,columns=4):
    """Eight-connected run labeling avoids cutting weapons at nominal cells."""
    image=Image.open(path).convert('RGBA');array=np.array(image);mask=array[:,:,3]>ALPHA_THRESHOLD
    parents=[];runs=[];previous=[]
    def root(index):
        while parents[index]!=index:
            parents[index]=parents[parents[index]];index=parents[index]
        return index
    for y,row in enumerate(mask):
        edge=np.diff(np.r_[False,row,False].astype(np.int8))
        starts=np.where(edge==1)[0].tolist();ends=np.where(edge==-1)[0].tolist();current=[];j=0
        for left,right in zip(starts,ends):
            ident=len(parents);parents.append(ident)
            while j<len(previous) and previous[j][1]<left:j+=1
            k=j
            while k<len(previous) and previous[k][0]<=right:
                p,q=root(ident),root(previous[k][2])
                if p!=q:parents[p]=q
                k+=1
            runs.append((ident,y,left,right));current.append((left,right,ident))
        previous=current
    components={}
    for ident,y,left,right in runs:
        components.setdefault(root(ident),[]).append((y,left,right))
    major=[];discarded=0
    for component in components.values():
        area=sum(right-left for _,left,right in component)
        if area<1000:
            discarded+=area;continue
        box=[min(left for _,left,_ in component),min(y for y,_,_ in component),
             max(right for _,_,right in component),max(y for y,_,_ in component)+1]
        if box[0]<=0 or box[1]<=0 or box[2]>=image.width or box[3]>=image.height:
            raise ValueError('Painted actor touches source boundary: '+str(path))
        major.append({'runs':component,'box':box,'area':area})
    if len(major)!=columns*rows:raise ValueError('Wrong isolated actor count in '+str(path))
    major.sort(key=lambda item:(item['box'][1]+item['box'][3])/2)
    ordered=[]
    for row in range(rows):ordered.extend(sorted(major[row*columns:row*columns+columns],key=lambda item:item['box'][0]+item['box'][2]))
    result=[]
    for item in ordered:
        left,top,right,bottom=item['box'];cut=array[top:bottom,left:right].copy();owned=np.zeros(cut.shape[:2],dtype=bool)
        for y,x0,x1 in item['runs']:owned[y-top,x0-left:x1-left]=True
        cut[~owned]=[0,0,0,0]
        result.append((Image.fromarray(cut),item['box'],item['area']))
    return result,{'source':path.relative_to(PROJECT).as_posix(),'sha256':pin(path),'size':list(image.size),
                   'major_actors':len(ordered),'discarded_detached_alpha_pixels':discarded,
                   'alpha_threshold':ALPHA_THRESHOLD,'boxes':[item['box'] for item in ordered]}

def native_frame(cut,box,sheet,index):
    scale=.20 if sheet=='walk' else .30 if sheet=='reactions' else .32 if sheet=='locomotion' else .33
    alpha=np.array(cut.getchannel('A'))
    if sheet=='walk':
        root_x=((index%3+.5)*1536/3)-box[0]
    elif sheet=='reactions' and index>=4:
        # Falling actors keep the sheet's physical center rather than recenter
        # around an extended polearm. Corpse baseline remains on the ground.
        root_x=((index-4+.5)*1774/4)-box[0]
    else:
        ys,xs=np.where(alpha[-min(12,cut.height):]>96)
        if not len(xs):raise ValueError('Missing visible ground contact')
        root_x=(int(xs.min())+int(xs.max())+1)/2
    root_y=cut.height
    resized=cut.resize((round(cut.width*scale),round(cut.height*scale)),Image.Resampling.LANCZOS)
    location=(round(214-root_x*scale),round(266-root_y*scale))
    if location[0]<0 or location[1]<0 or location[0]+resized.width>450 or location[1]+resized.height>400:
        raise ValueError('Native frame clipping')
    native=Image.new('RGBA',(450,400));native.alpha_composite(resized,location)
    return native,{'source_box':box,'source_root':[root_x+box[0],box[3]],'scale':scale,
                   'native_pivot':[214,266],'paste':list(location),'native_bounds':list(native.getbbox())}

def small_body(native,size,root,target_scale):
    # Exact affine canvas registration, not a newly painted or morphed action.
    factor=target_scale
    resized=native.resize((round(native.width*factor),round(native.height*factor)),Image.Resampling.LANCZOS)
    offset=(round(root[0]-214*factor),round(root[1]-266*factor))
    result=Image.new('RGBA',size);result.alpha_composite(resized,offset)
    return result

def raster(unit,role,image,master):
    path=SOURCE/unit/'resources-v4'/f'{role}.png';store(path,png(image))
    return base_recipe(unit,role,master)|{'recipe_type':'raster','size':list(image.size),'canvas':list(image.size),
             'source':path.relative_to(PROJECT).as_posix(),'source_sha256':pin(path),'source_canvas':list(image.size)}

def base_recipe(unit,role,master):
    suffix='json' if role in ('battle','map') else 'png'
    return {'unit':unit,'status':'authored configuration','production_status':'painted-master-complete-unapproved',
            'output_path':f'Content/Sprites/runeterra/shurima/creatures/{unit}/{role}.{suffix}',
            'producer_source':Path(__file__).relative_to(PROJECT).as_posix(),'producer_source_sha256':pin(Path(__file__)),
            'generation':{'image_generation_used':True,'provider':'OpenAI built-in imagegen',
               'model':'not exposed by built-in tool','prompt':master.with_suffix('.prompt.txt').relative_to(PROJECT).as_posix(),
               'painted_master':master.relative_to(PROJECT).as_posix(),'painted_master_sha256':pin(master),
               'method':'New original painted2D poses; technical connected-silhouette slicing and fixed native registration only'},
            'credits':{'author':'Project-directed OpenAI built-in imagegen paintings; Codex technical assembly',
                       'license':None,'redistribution':'unresolved; no release acceptance'},
            'acceptance':'Unselected candidate only. Native appearance, action contact, visual acceptance and rights remain pending.'}

def descriptor(path,frame):
    with Image.open(path) as image:size=list(image.size)
    return {'frame':frame,'source':path.relative_to(PROJECT).as_posix(),'source_sha256':pin(path),
            'source_canvas':size}

def main():
    compiler=create_compiler('shurima');summary={'status':'authored configuration','selected':False,
       'native_game_launched':False,'visual_approval_granted':False,'release_accepted':False,
       'assembly_source_sha256':pin(Path(__file__)),'units':{},'raw_sheet_inspection':{},'compiler_receipts':[]}
    for unit,sheets in UNITS.items():
        poses={};registration={}
        for sheet,filename in sheets.items():
            actors,info=extract(SOURCE/unit/filename,2 if sheet in ('reactions','walk') else 3,3 if sheet=='walk' else 4)
            summary['raw_sheet_inspection'][unit+'/'+sheet]=info
            poses[sheet]=[]
            for index,(cut,box,_) in enumerate(actors):
                image,record=native_frame(cut,box,sheet,index)
                path=SOURCE/unit/'native-v4'/f'{sheet}-{index:02}.png';store(path,png(image))
                poses[sheet].append((image,path));registration[sheet+f'-{index:02}']=record
        recipes=[];battle=base_recipe(unit,'battle',SOURCE/unit/sheets['locomotion'])
        battle.update({'recipe_type':'vcmi_animation','canvas':[450,400],'pivot':{'x':214,'y':266},
                       'generateShadow':1,'generateOverlay':1,
                       'required_groups':{str(g):len(indices) for g,(_,indices) in GROUPS.items()},'groups':[]})
        for group,(sheet,indices) in GROUPS.items():
            battle['groups'].append({'group':group,'frames':[descriptor(poses[sheet][index][1],frame) for frame,index in enumerate(indices)]})
        battle['generation']['supplemental_masters']=[{'path':(SOURCE/unit/sheets[s]).relative_to(PROJECT).as_posix(),
                                                     'sha256':pin(SOURCE/unit/sheets[s])} for s in ('combat','reactions','walk')]
        recipes.append(('battle',battle))
        animation=base_recipe(unit,'map',SOURCE/unit/sheets['locomotion'])
        map_paths=[]
        for index in range(6):
            image=small_body(poses['walk'][index][0],(96,64),(64,58),.45)
            bounds=image.getbbox()
            if not bounds or bounds[0]<32 or bounds[1]<0 or bounds[2]>96 or bounds[3]>64:
                raise ValueError('Adventure art escapes native visible two-column mask')
            path=SOURCE/unit/'resources-v4'/f'map-{index:02}.png';store(path,png(image));map_paths.append(path)
        animation.update({'recipe_type':'vcmi_animation','canvas':[96,64],'pivot':{'x':64,'y':58},
                          'generateShadow':1,'generateOverlay':0,'required_groups':{'0':6},
                          'groups':[{'group':0,'frames':[descriptor(p,i) for i,p in enumerate(map_paths)]}]})
        recipes.append(('map',animation))
        portrait=Image.open(SOURCE/unit/'portrait-v1.png').convert('RGBA')
        recipes.append(('large',raster(unit,'large',ImageOps.fit(portrait,(58,64),Image.Resampling.LANCZOS),SOURCE/unit/'portrait-v1.png')))
        recipes.append(('small',raster(unit,'small',ImageOps.fit(portrait,(32,32),Image.Resampling.LANCZOS,centering=(.5,.28)),SOURCE/unit/'portrait-v1.png')))
        attack=poses['combat'][2][0];cut=attack.crop(attack.getbbox())
        cut.thumbnail((56,56),Image.Resampling.LANCZOS)
        encounter=Image.new('RGBA',(64,64));encounter.alpha_composite(cut,((64-cut.width)//2,60-cut.height))
        recipes.append(('attackRight',raster(unit,'attackRight',encounter,SOURCE/unit/sheets['combat'])))
        recipes.append(('attackLeft',raster(unit,'attackLeft',ImageOps.mirror(encounter),SOURCE/unit/sheets['combat'])))
        counts={}
        for role,recipe in recipes:
            path=SOURCE/'recipes-v4'/unit/f'{role}.json';store(path,encoded(recipe))
            outputs,receipt=compiler.plan(PROJECT,path)
            for name,raw in outputs.items():store(REPORT/'runtime'/name,raw)
            summary['compiler_receipts'].append(receipt);counts[role]=len(outputs)
        summary['units'][unit]={'native_groups':battle['required_groups'],'runtime_output_counts':counts,
                                'native_registration':registration,'canonical_selected':False}
        for group,(sheet,indices) in GROUPS.items():
            images=[]
            for index in indices:
                frame=Image.new('RGB',(450,400),(39,34,28));frame.paste(poses[sheet][index][0],mask=poses[sheet][index][0].getchannel('A'))
                images.append(frame)
            target=REPORT/'playback'/unit/f'g{group:02}.gif';target.parent.mkdir(parents=True,exist_ok=True)
            data=io.BytesIO();images[0].save(data,format='GIF',save_all=True,append_images=images[1:],duration=140 if group!=5 else 240,loop=0,disposal=2)
            store(target,data.getvalue())
    store(SOURCE/'registration-v4.json',encoded(summary))
    store(REPORT/'assembly.json',encoded(summary))
    inventory={p.relative_to(PROJECT).as_posix():pin(p) for p in SOURCE.rglob('*') if p.is_file()}
    store(REPORT/'source-pins.json',encoded(inventory))
    runtime={p.relative_to(REPORT/'runtime').as_posix():pin(p) for p in (REPORT/'runtime').rglob('*') if p.is_file()}
    store(REPORT/'runtime-pins.json',encoded(runtime))
    html=['<!doctype html><html lang="en"><meta charset="utf-8"><title>Shurima Oathkeeper T7 candidates</title>',
          '<style>body{background:#1d1b18;color:#eee;font:16px system-ui;margin:24px}article{display:inline-block;vertical-align:top;margin:8px}img{image-rendering:auto}figure{margin:0}details{margin:12px 0}summary{cursor:pointer}a{color:#f4cb77}.pair{display:flex;flex-wrap:wrap;gap:12px}</style>',
          '<h1>Sunborn Oathkeeper / Exalted Oathkeeper</h1><p><strong>Unselected painted2D candidates.</strong> Project-fiction living Shuriman oathbound warriors. Source playback is not native gameplay or release acceptance. No canonical manifest or game stage was changed.</p>',
          '<p><a href="assembly.json">Assembly/registration</a> · <a href="source-pins.json">Source hashes</a> · <a href="runtime-pins.json">Candidate runtime hashes</a></p><div class="pair">']
    for unit in UNITS:
        base=f'runtime/Content/Sprites/runeterra/shurima/creatures/{unit}'
        html.extend([f'<article><h2>{unit}</h2><img src="{base}/large.png" width="58" height="64"><img src="{base}/small.png" width="32" height="32">',
                     f'<figure><img src="playback/{unit}/g00.gif" width="450" height="400"><figcaption>Walking at native450x400; upper-left light; root214,266</figcaption></figure>'])
        for group in GROUPS:
            if group==0:continue
            html.append(f'<details><summary>{LABELS[group]} — group{group}, {len(GROUPS[group][1])} frames</summary><img src="playback/{unit}/g{group:02}.gif" width="450" height="400"></details>')
        html.append('</article>')
    html.append('</div><p>Review limits: crest likeness, anatomy/weapon continuity, stock-window crop, native action contact and shadow/facing behavior still require independent and in-game inspection. Source groups7/8 intentionally reuse true turn poses in reverse order; group22 is the final death pose.</p></html>')
    store(REPORT/'index.html','\n'.join(html).encode('utf-8'))
    print(json.dumps({'units':{u:v['runtime_output_counts'] for u,v in summary['units'].items()},'runtime_files':len(runtime),'canonical_selected':False},indent=2))

if __name__=='__main__':main()
