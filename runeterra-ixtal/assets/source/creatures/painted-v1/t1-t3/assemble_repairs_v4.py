"""Build bounded new action overrides; never alter old cohorts or canonical recipes."""
from pathlib import Path
import copy,hashlib,io,json,sys
import numpy as np
from PIL import Image,ImageDraw
from components import components
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5];PROJECT=ROOT/'runeterra-ixtal'
REPORT=ROOT/'build/reports/ixtal-implementation-20261026-v1/creature-art-t1-t3'
OUT=HERE/'native-v4';CAL=HERE/'repair_registration_v4.json';DATA=json.loads(CAL.read_text())
PREVIEW='--preview' in sys.argv
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def ref(path):return {'path':path.relative_to(PROJECT).as_posix(),'sha256':sha(path)}
def put(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists()and path.read_bytes()!=raw:raise ValueError('Immutable v4 output changed: '+str(path))
    path.write_bytes(raw)
def dump(path,data):put(path,(json.dumps(data,indent=2)+'\n').encode())
def png(image):buf=io.BytesIO();image.save(buf,format='PNG');return buf.getvalue()
def poses(identifier,settings,file='strict-motion-repair-v4.png'):
    path=HERE/identifier/file;image=Image.open(path).convert('RGBA');parts=[p for p in components(image.getchannel('A'),128)if p['area']>1500]
    if len(parts)!=settings['count']:raise ValueError(f'{identifier}/{file}: genuine component count {len(parts)}')
    rows=[[]for _ in range(settings['rows'])]
    for part in parts:rows[min(len(rows)-1,int((part['box'][1]+part['box'][3])/2*len(rows)/image.height))].append(part)
    ordered=[p for row in rows for p in sorted(row,key=lambda p:p['box'][0])]
    pixels=np.asarray(image);result=[];columns=settings.get('columns',4)
    for index,part in enumerate(ordered):
        row,col=divmod(index,columns);mask=np.zeros(image.width*image.height,dtype=np.bool_);mask[part['pixels']]=True
        rgba=pixels.copy();rgba[~mask.reshape(image.height,image.width)]=0;box=part['box'];crop=Image.fromarray(rgba).crop(tuple(box))
        size=tuple(round(v*settings['scale'])for v in crop.size);sx,sy=size[0]/crop.width,size[1]/crop.height
        root=settings.get('root_overrides',{}).get(str(index),[settings['root_x'][col],settings['ground_y'][row]])
        paste=[round(197-(root[0]-box[0])*sx),round(266-(root[1]-box[1])*sy)]
        native=Image.new('RGBA',(450,400));native.alpha_composite(crop.resize(size,Image.Resampling.LANCZOS),tuple(paste))
        label='tracker-four'if file!='strict-motion-repair-v4.png'else'repair'
        source=OUT/identifier/'isolated'/f'{label}-{index:02}.png';target=OUT/identifier/'poses'/f'{label}-{index:02}.png'
        record={'source_master':ref(path),'source_box':box,'source_root':root,'nominal_scale':settings['scale'],'pixel_grid_scale':[sx,sy],'native_paste':paste,'native_root':[197,266],'alpha_threshold':128,'source_index':index}
        if not PREVIEW:put(source,png(crop));put(target,png(native));record.update(source_frame=ref(source),native_frame=ref(target))
        result.append((native,record))
    return result
def frame(pair,index):
    record=pair[1]['native_frame'];return {'frame':index,'source':record['path'],'sha256':record['sha256'],'source_canvas':[450,400]}
def main():
    selections=[];sheet=Image.new('RGB',(1200,1200),(50,48,43));draw=ImageDraw.Draw(sheet)
    for row,(identifier,settings)in enumerate(DATA['units'].items()):
        new=poses(identifier,settings);oldpath=HERE/'native-v3'/identifier/'recipes'/f'{identifier}-battle.json';old=json.loads(oldpath.read_text());recipe=copy.deepcopy(old)
        oldgroups={g['group']:g for g in old['groups']};groups={g['group']:g for g in recipe['groups']}
        four=poses(identifier,DATA['tracker_four'],DATA['tracker_four']['file'])if identifier=='canopyTracker'else None
        if identifier=='canopyGuide':walk=[new[i]for i in(0,1,4,2,3,5)];fidgets=range(6,11);hit=11;turn=(12,13,14,15)
        elif four:walk=[four[0],new[0],four[1],four[2],four[3],new[1]];fidgets=range(2,7);hit=7;turn=(8,9,10,11)
        else:
            walk=[]
            for pos in(0,1):walk.append((Image.open(PROJECT/oldgroups[0]['frames'][pos]['source']).convert('RGBA'),{'old_frame':oldgroups[0]['frames'][pos]}))
            walk.append(new[0])
            for pos in(2,3):walk.append((Image.open(PROJECT/oldgroups[0]['frames'][pos]['source']).convert('RGBA'),{'old_frame':oldgroups[0]['frames'][pos]}))
            walk.append(new[1]);fidgets=range(2,7);hit=7;turn=(8,9,10,4 if identifier=='pakaaGuardian' else 11)
        group_poses={0:walk,1:[None,None]+[new[i]for i in fidgets],3:[new[hit],None],7:[new[turn[i]]for i in(0,1,2)],8:[new[turn[i]]for i in(2,3,0)]}
        if identifier.startswith('pakaa'):group_poses[2]=[new[12],new[13]]
        for group,cohort in group_poses.items():
            if not PREVIEW:
                frames=[]
                for index,pair in enumerate(cohort):
                    if pair is None:
                        oldindex=index if group==1 else 0;entry=copy.deepcopy(oldgroups[group]['frames'][oldindex])
                    elif 'old_frame'in pair[1]:entry=copy.deepcopy(pair[1]['old_frame'])
                    else:entry=frame(pair,index)
                    entry['frame']=index;frames.append(entry)
                groups[group]['frames']=frames
        show=[walk[0],walk[2],walk[3],walk[4],new[hit],new[turn[2]],new[12]if identifier.startswith('pakaa')else new[turn[1]],new[13]if identifier.startswith('pakaa')else new[turn[3]]]
        for col,(im,_)in enumerate(show):
            tile=im.crop((125,165,275,285));sheet.paste(tile,(col*150,row*200+35),tile)
            draw.text((col*150+3,row*200+15),identifier if col==0 else str(col),fill=(240,230,210))
            if identifier.startswith('pakaa')and col>=6:draw.rectangle((col*150+45,row*200+25,col*150+145,row*200+145),outline=(170,140,75))
        if not PREVIEW:
            registration=OUT/identifier/'repair-registration.json';dump(registration,{'status':'authored configuration; motion/native review pending','producer':ref(Path(__file__)),'calibration':ref(CAL),'poses':[v[1]for v in new],'tracker_four':[v[1]for v in four]if four else[]})
            extra=[ref(Path(__file__)),ref(CAL),ref(registration),ref(HERE/identifier/'strict-motion-repair-v4.png'),ref(HERE/identifier/'strict-motion-repair-v4.generation.json')]
            if four:extra.extend((ref(HERE/identifier/DATA['tracker_four']['file']),ref((HERE/identifier/DATA['tracker_four']['file']).with_suffix('.generation.json'))))
            recipe['production_inputs']+=extra;recipe['generation']['prompt']+='\n\n'+json.loads((HERE/identifier/'strict-motion-repair-v4.generation.json').read_text())['prompt']
            recipe['generation']['method']+=' Strict-manifest v4 override: real additional fidget/recoil/turn phases; unchanged good groups and all quill shooting sources. Native turn7/flip/8 uses coherent shared phase endpoints.'
            recipe['repair_scope']={'baseline_recipe':ref(oldpath),'changed_groups':sorted(group_poses),'unchanged_groups':sorted(set(groups)-set(group_poses)),'native_approval':False}
            path=OUT/identifier/'recipes'/f'{identifier}-battle.json';dump(path,recipe)
            selections.append({'id':identifier,'battle_recipe':ref(path),'registration':ref(registration),'changed_groups':sorted(group_poses),'group_counts':{str(g):len(v['frames'])for g,v in groups.items()}})
    path=REPORT/('repair-v4-preview-initial.png'if PREVIEW else'repair-v4-native-review.png');put(path,png(sheet))
    if not PREVIEW:dump(REPORT/'candidate-selection-v4.json',{'status':'authored configuration','production_accepted':False,'units':selections,'remaining':['Independent pixel/biomechanical gait review','Actual native facing/turn7-flip-8 and motion cadence','Native gameplay, audio and redistribution acceptance']})
    print(json.dumps({'preview':str(path),'candidate_count':len(selections),'canonical_writes':False}))
if __name__=='__main__':main()
