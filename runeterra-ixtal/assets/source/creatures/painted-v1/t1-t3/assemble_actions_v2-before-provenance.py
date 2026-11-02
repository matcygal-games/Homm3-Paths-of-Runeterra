"""Isolate real painted poses; author candidate native frames/recipes, never stage."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np
from PIL import Image,ImageDraw
from components import components

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[5]
PROJECT=ROOT/'runeterra-ixtal'
REPORT=ROOT/'build/reports/ixtal-implementation-20261026-v1/creature-art-t1-t3'
VERSION=sys.argv[1] if len(sys.argv)>1 else 'v2'
if not VERSION.isalnum(): raise ValueError('Version must be a simple own output label')
NATIVE=HERE/('native-'+VERSION)
DATA=json.loads((HERE/'action_registration.json').read_text())

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def ref(path): return {'path':path.relative_to(PROJECT).as_posix(),'sha256':sha(path)}
def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    raw=(json.dumps(data,indent=2)+'\n').encode()
    if path.exists() and path.read_bytes()!=raw: raise ValueError('Existing immutable output differs: '+str(path))
    path.write_bytes(raw)
def save(path,image):
    path.parent.mkdir(parents=True,exist_ok=True)
    import io
    buf=io.BytesIO();image.save(buf,format='PNG');raw=buf.getvalue()
    if path.exists() and path.read_bytes()!=raw: raise ValueError('Existing immutable image differs: '+str(path))
    path.write_bytes(raw)

def atlas(identifier,kind,settings):
    source_path=HERE/identifier/settings['file'];image=Image.open(source_path).convert('RGBA')
    threshold=DATA['alpha_threshold'];parts=[p for p in components(image.getchannel('A'),threshold) if p['area']>1500]
    row_count=4 if kind=='motion' else 3
    if len(parts)!=4*row_count: raise ValueError(f'{identifier}/{kind}: {len(parts)} real painted components')
    rows=[[] for _ in range(row_count)]
    for part in parts: rows[min(row_count-1,int((part['box'][1]+part['box'][3])/2*row_count/image.height))].append(part)
    if any(len(row)!=4 for row in rows): raise ValueError(f'{identifier}/{kind}: wrong actual4-column pose layout')
    ordered=[p for row in rows for p in sorted(row,key=lambda p:p['box'][0])]
    pixels=np.asarray(image);result=[]
    for index,part in enumerate(ordered):
        row,col=divmod(index,4);mask=np.zeros(image.width*image.height,dtype=np.bool_);mask[part['pixels']]=True
        isolated=pixels.copy();isolated[~mask.reshape(image.height,image.width)]=0
        box=part['box'];crop=Image.fromarray(isolated).crop(tuple(box))
        source_frame=NATIVE/identifier/'isolated'/f'{kind}-{index:02}.png';save(source_frame,crop)
        scale=settings['scale'];size=tuple(round(v*scale) for v in crop.size)
        sx,sy=size[0]/crop.width,size[1]/crop.height
        source_root=settings.get('overrides',{}).get(str(index),[settings['root_x'][col],settings['ground_y'][row]])
        paste=[round(197-(source_root[0]-box[0])*sx),round(266-(source_root[1]-box[1])*sy)]
        native=Image.new('RGBA',(450,400));native.alpha_composite(crop.resize(size,Image.Resampling.LANCZOS),tuple(paste))
        native_path=NATIVE/identifier/'poses'/f'{kind}-{index:02}.png';save(native_path,native)
        result.append({'index':index,'kind':kind,'source_frame':ref(source_frame),'source_box':box,'source_root':source_root,
            'nominal_scale':scale,'pixel_grid_scale':[sx,sy],'native_paste':paste,'native_root':[197,266],
            'native_frame':ref(native_path),'source_master':ref(source_path),'alpha_threshold':threshold})
    return result

def battle(identifier,poses,dependencies):
    mapping={0:('motion',[0,1,2,3]),1:('motion',[4,5]),2:('motion',[4,5]),3:('motion',[7]),4:('motion',[6]),
             5:('motion',[12,13,14,15]),7:('motion',[8]),8:('motion',[9]),
             11:('attacks',[0,1,2,3]),12:('attacks',[4,5,6,7]),13:('attacks',[8,9,10,11]),
             20:('motion',[10]),21:('motion',[11]),22:('motion',[15])}
    if 'shooting'in poses: mapping.update({14:('shooting',[0,1,2,3]),15:('shooting',[4,5,6,7]),16:('shooting',[8,9,10,11])})
    groups=[];emissions=[]
    for group,(kind,indices)in sorted(mapping.items()):
        frames=[]
        for frame,index in enumerate(indices):
            pose=poses[kind][index];source=PROJECT/pose['native_frame']['path']
            target=NATIVE/identifier/'battle'/f'g{group}-f{frame:03}.png';save(target,Image.open(source))
            frames.append({'frame':frame,'source':target.relative_to(PROJECT).as_posix(),'sha256':sha(target),'source_canvas':[450,400]})
            if group in(14,15,16)and frame==3:
                row=group-14;tip=DATA['units'][identifier]['shooting']['tips'][row]
                master=PROJECT/pose['source_master']['path'];rgba=Image.open(master).getpixel(tuple(tip))
                if rgba[3]<128:raise ValueError('Quill emission point is not an actual opaque painted pixel')
                box=pose['source_box'];sx,sy=pose['pixel_grid_scale'];px,py=pose['native_paste']
                point=[round(px+(tip[0]-box[0])*sx),round(py+(tip[1]-box[1])*sy)]
                emissions.append({'direction':('upper','middle','lower')[row],'group':group,'release_frame_zero_based':3,
                    'native_tip_pixels':point,'original_tip_pixels':tip,'source_tip_rgba':list(rgba),'source_frame':pose['source_frame'],
                    'native_frame':ref(target),'native_origin_offset':[point[0]-197,point[1]-265],
                    'measurement':'Actual fourth-pose dorsal quill tip; separate physical projectile; source-only calibration, native trajectory/facing pending.'})
        groups.append({'group':group,'frames':frames})
    recipe={'recipe_type':'vcmi_animation','canvas':[450,400],'pivot':{'x':197,'y':266},'generateShadow':1,'generateOverlay':1,
        'output_path':f'Content/Sprites/runeterra/ixtal/creatures/{identifier}/battle.json','groups':groups,
        'production_status':'painted-master-complete-unapproved','acceptance':'authored configuration; independent pixels/native/motion/rights pending',
        'generation':{'image_generation_used':True,'provider':'OpenAI built-in image_gen','model':'not exposed by built-in tool',
                      'method':'Genuine painted2D articulated cohorts; alpha isolation, one density per atlas and authored projected anatomical roots. No3D, body warps or bbox-fit animation.'},
        'production_inputs':dependencies}
    path=NATIVE/identifier/'recipes'/f'{identifier}-battle.json';write(path,recipe)
    return path,emissions

def preview(identifier,poses):
    sheet=Image.new('RGB',(900,440),(54,51,46));d=ImageDraw.Draw(sheet)
    selected=[('hold','motion',4),('walk0','motion',0),('walk1','motion',1),('defend','motion',6),('hit','motion',7),
              ('up','attacks',3),('front','attacks',7),('down','attacks',11),('fall','motion',13),('dead','motion',15)]
    for i,(name,kind,index)in enumerate(selected):
        frame=Image.open(PROJECT/poses[kind][index]['native_frame']['path']).convert('RGBA')
        crop=frame.crop((130,150,280,285));x,y=(i%5)*180,(i//5)*220
        d.text((x+5,y+5),name,fill=(235,224,200));sheet.paste(crop,(x+10,y+25),crop)
    target=REPORT/f'{identifier}-native-action-crops-{VERSION}.png';save(target,sheet)
    for kind,indices in [('walk',[0,1,2,3]),('death',[12,13,14,15])]:
        frames=[]
        for index in indices:
            source=Image.open(PROJECT/poses['motion'][index]['native_frame']['path']).convert('RGBA').crop((130,150,280,285))
            frame=Image.new('RGB',source.size,(54,51,46));frame.paste(source,(0,0),source);frames.append(frame)
        path=REPORT/f'{identifier}-{kind}-{VERSION}.gif'
        frames[0].save(path,save_all=True,append_images=frames[1:],duration=180,loop=0)
    return target

def main():
    REPORT.mkdir(parents=True,exist_ok=True);summary=[]
    for identifier,settings in DATA['units'].items():
        poses={kind:atlas(identifier,kind,s)for kind,s in settings.items()}
        registration=NATIVE/identifier/'frame-registration.json'
        write(registration,{'status':'authored configuration; independent native/motion review pending',
            'producer':ref(Path(__file__)),'components_helper':ref(HERE/'components.py'),'calibration':ref(HERE/'action_registration.json'),
            'canvas':[450,400],'native_root':[197,266],'poses':poses})
        inputs=[ref(Path(__file__)),ref(HERE/'components.py'),ref(HERE/'action_registration.json'),ref(registration)]
        for kind,s in settings.items():
            path=HERE/identifier/s['file'];inputs.extend((ref(path),ref(path.with_suffix('.generation.json'))))
        recipe,emissions=battle(identifier,poses,inputs)
        record={'id':identifier,'battle_recipe':ref(recipe),'registration':ref(registration),'real_painted_pose_count':sum(len(v)for v in poses.values()),
                'native_source_preview':preview(identifier,poses).relative_to(ROOT).as_posix()}
        if emissions:
            path=NATIVE/identifier/f'shot-measurements-{VERSION}.json'
            write(path,{'units':[{'id':identifier,'source_kind':'painted-native','source_master':poses['shooting'][0]['source_master'],
                'source_metadata':ref(registration),'measurements':emissions}],'acceptance':'Technical source geometry only; native projectile/facing/motion/rights pending.'})
            record.update({'measurement':ref(path),'native_points':{row['direction']:row['native_tip_pixels']for row in emissions},
                           'offsets':{row['direction']:row['native_origin_offset']for row in emissions}})
        summary.append(record)
    write(REPORT/f'candidate-selection-{VERSION}.json',{'status':'authored configuration','production_accepted':False,
        'real_painted_poses':sum(v['real_painted_pose_count']for v in summary),'units':summary,
        'remaining':['Actual native movement/turn/attack timing, both facings, crest and root review','Dedicated portrait/scenic and adventure-role derivations','Separate actual quill projectile asset','Independent art/motion/native/audio/rights acceptance']})
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
