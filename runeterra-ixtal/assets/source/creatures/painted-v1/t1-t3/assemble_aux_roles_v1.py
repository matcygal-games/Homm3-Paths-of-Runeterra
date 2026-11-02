"""Compile genuine painted adventure/portrait sources into own candidate roles."""
from pathlib import Path
import hashlib
import io
import json
import sys
import numpy as np
from PIL import Image,ImageDraw
from components import components

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5];PROJECT=ROOT/'runeterra-ixtal'
REPORT=ROOT/'build/reports/ixtal-implementation-20261026-v1/creature-art-t1-t3'
VERSION=sys.argv[1]if len(sys.argv)>1 else'v1'
if not VERSION.isalnum():raise ValueError('Invalid own version')
OUT=HERE/('aux-'+VERSION);DATA=json.loads((HERE/'aux_registration.json').read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def ref(path):return{'path':path.relative_to(PROJECT).as_posix(),'sha256':sha(path)}
def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True);raw=(json.dumps(data,indent=2)+'\n').encode()
    if path.exists()and path.read_bytes()!=raw:raise ValueError('Immutable source output differs: '+str(path))
    path.write_bytes(raw)
def save(path,image):
    path.parent.mkdir(parents=True,exist_ok=True);b=io.BytesIO();image.save(b,format='PNG');raw=b.getvalue()
    if path.exists()and path.read_bytes()!=raw:raise ValueError('Immutable image differs: '+str(path))
    path.write_bytes(raw)
def generation(master):
    record=json.loads(master.with_suffix('.generation.json').read_text())
    return{'image_generation_used':True,'provider':record['provider'],'model':record['model'],'prompt':record['prompt'],
           'painted_master':master.relative_to(PROJECT).as_posix(),'painted_master_sha256':sha(master),
           'method':'Genuine painted2D dedicated source poses/scenic portrait, technical isolation and fixed uniform registration only; no3D, bbox fitting or body warps.'}
def source_image(image,part):
    rgba=np.asarray(image).copy();mask=np.zeros(image.width*image.height,dtype=np.bool_);mask[part['pixels']]=True
    rgba[~mask.reshape(image.height,image.width)]=0
    return Image.fromarray(rgba).crop(tuple(part['box']))
def place(crop,box,root,scale,canvas,target):
    size=tuple(round(v*scale)for v in crop.size);sx,sy=size[0]/crop.width,size[1]/crop.height
    paste=[round(target[0]-(root[0]-box[0])*sx),round(target[1]-(root[1]-box[1])*sy)]
    scaled=crop.resize(size,Image.Resampling.LANCZOS);bounds=scaled.getbbox()
    translated=[paste[0]+bounds[0],paste[1]+bounds[1],paste[0]+bounds[2],paste[1]+bounds[3]]
    if translated[0]<0 or translated[1]<0 or translated[2]>canvas[0]or translated[3]>canvas[1]:
        raise ValueError('Painted subject would be clipped; correct source/calibration, never bbox-fit: '+str(translated))
    native=Image.new('RGBA',tuple(canvas));native.alpha_composite(scaled,tuple(paste))
    return native,{'source_root':root,'nominal_scale':scale,'pixel_grid_scale':[sx,sy],'paste':paste,'native_root':target,'native_bbox':translated}
def raster(identifier,role,path,generation_record,inputs,dimensions,extra=None):
    data={'recipe_type':'raster','canvas':dimensions,'fit':'exact','source':path.relative_to(PROJECT).as_posix(),
          'source_sha256':sha(path),'source_canvas':dimensions,'output_path':f'Content/Sprites/runeterra/ixtal/creatures/{identifier}/{role}.png',
          'generation':generation_record,'production_inputs':inputs,'production_status':'painted-master-complete-unapproved',
          'acceptance':'authored configuration; independent/native/pixels/rights pending'}
    if extra:data.update(extra)
    target=OUT/identifier/'recipes'/f'{identifier}-{role}.json';write(target,data);return ref(target)
def main():
    REPORT.mkdir(parents=True,exist_ok=True);summaries=[];board=Image.new('RGB',(640,600),(54,51,46));draw=ImageDraw.Draw(board)
    for unit_index,(identifier,settings)in enumerate(DATA['units'].items()):
        master=HERE/identifier/settings['adventure_master'];image=Image.open(master).convert('RGBA')
        parts=[v for v in components(image.getchannel('A'),DATA['alpha_threshold'])if v['area']>1500]
        if len(parts)!=8:raise ValueError(f'{identifier}: expected eight real dedicated poses, got{len(parts)}')
        rows=[[],[]]
        for p in parts:rows[min(1,int((p['box'][1]+p['box'][3])/2*2/image.height))].append(p)
        if any(len(row)!=4 for row in rows):raise ValueError('Actual adventure pose layout is not2x4')
        parts=[p for row in rows for p in sorted(row,key=lambda p:p['box'][0])]
        records=[];maps=[];encounters={}
        for index,part in enumerate(parts):
            row,col=divmod(index,4);crop=source_image(image,part)
            isolated=OUT/identifier/'isolated'/f'adventure-{index:02}.png';save(isolated,crop)
            root=[settings['root_x'][col],settings['ground_y'][row]]
            canvas=[96,64]if row==0 else[64,64];target=settings['map_root']if row==0 else settings['encounter_root']
            frame,placement=place(crop,part['box'],root,settings['scale'],canvas,target)
            path=OUT/identifier/('map'if row==0 else'encounters')/f'pose-{index:02}.png';save(path,frame)
            if row==0:
                if frame.crop((0,0,32,64)).getbbox():raise ValueError('Map actor enters unmasked leftmost32pixels')
                maps.append(path)
            elif index in(4,5):encounters['attackLeft'if index==4 else'attackRight']=path
            records.append({'index':index,'source_frame':ref(isolated),'source_box':part['box'],'native_frame':ref(path),
                            'visual_facing':'left'if index in(5,7)else'right',**placement})
        portrait=HERE/identifier/'portrait-master-v1.png';portrait_image=Image.open(portrait).convert('RGBA')
        ratio=58/64;crop_width=min(portrait_image.width,round(portrait_image.height*ratio));x=(portrait_image.width-crop_width)//2
        large=portrait_image.crop((x,0,x+crop_width,portrait_image.height)).resize((58,64),Image.Resampling.LANCZOS)
        small_box=settings['small_crop']
        if small_box[2]>portrait_image.width or small_box[3]>portrait_image.height:raise ValueError('Authored portrait crop escapes real source')
        small=portrait_image.crop(tuple(small_box)).resize((32,32),Image.Resampling.LANCZOS)
        large_path=OUT/identifier/'portraits'/'large.png';small_path=OUT/identifier/'portraits'/'small.png';save(large_path,large);save(small_path,small)
        placement_path=OUT/identifier/'role-placement.json'
        write(placement_path,{'producer':ref(Path(__file__)),'components_helper':ref(HERE/'components.py'),
            'calibration':ref(HERE/'aux_registration.json'),'source_master':ref(master),'poses':records,
            'portrait_master':ref(portrait),'portrait_large_crop':[x,0,x+crop_width,portrait_image.height],'portrait_small_crop':small_box,
            'world_registration':{'map_root':settings['map_root'],'encounter_root':settings['encounter_root'],
                                  'same_world_root':settings['map_root'][0]-96==settings['encounter_root'][0]-64}})
        inputs=[ref(Path(__file__)),ref(HERE/'components.py'),ref(HERE/'aux_registration.json'),ref(placement_path),
                ref(master),ref(master.with_suffix('.generation.json')),ref(portrait),ref(portrait.with_suffix('.generation.json'))]
        map_recipe={'recipe_type':'vcmi_animation','canvas':[96,64],'pivot':dict(zip(('x','y'),settings['map_root'])),
            'generateShadow':1,'generateOverlay':0,'output_path':f'Content/Sprites/runeterra/ixtal/creatures/{identifier}/map.json',
            'groups':[{'group':0,'frames':[{'frame':i,'source':p.relative_to(PROJECT).as_posix(),'sha256':sha(p),'source_canvas':[96,64]}for i,p in enumerate(maps)]}],
            'generation':generation(master),'production_inputs':inputs,'production_status':'painted-master-complete-unapproved',
            'acceptance':'authored configuration; independent/native/fidget cadence/pixels/rights pending'}
        map_path=OUT/identifier/'recipes'/f'{identifier}-map.json';write(map_path,map_recipe)
        recipes=[ref(map_path),raster(identifier,'large',large_path,generation(portrait),inputs,[58,64]),raster(identifier,'small',small_path,generation(portrait),inputs,[32,32])]
        for role,path in encounters.items():recipes.append(raster(identifier,role,path,generation(master),inputs,[64,64],{'visual_facing':'right'if role=='attackLeft'else'left'}))
        summaries.append({'id':identifier,'recipes':recipes,'placement':ref(placement_path),'actual_adventure_poses':8,
                          'native_visual_status':'pending actual game observation and independent approval'})
        y=unit_index*100;draw.text((5,y+5),identifier,fill=(236,225,200))
        for path,pos in [(large_path,(170,y+15)),(small_path,(240,y+30)),(maps[0],(290,y+25)),(encounters['attackLeft'],(405,y+25)),(encounters['attackRight'],(490,y+25))]:
            pic=Image.open(path);board.paste(pic,pos,pic)
    write(REPORT/f'aux-selection-{VERSION}.json',{'status':'authored configuration','production_accepted':False,'units':summaries,
        'projectile_note':'Root owns active projectiles. Own extra quill master remains unselected candidate history; no duplicate projectile producer.',
        'remaining':['Actual native map/encounter binding/mask/visit/root/fidget review','Native-size UI and crest acceptance','Independent art/motion/rights acceptance']})
    save(REPORT/f'aux-native-role-preview-{VERSION}.png',board)
    print(json.dumps({'units':len(summaries),'recipes':sum(len(u['recipes'])for u in summaries),'preview':str(REPORT.relative_to(ROOT)/f'aux-native-role-preview-{VERSION}.png'),
        'source_bytes':sum(p.stat().st_size for p in HERE.rglob('*')if p.is_file())},indent=2))
if __name__=='__main__':main()
