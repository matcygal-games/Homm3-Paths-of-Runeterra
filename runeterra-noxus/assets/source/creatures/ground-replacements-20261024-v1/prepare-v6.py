"""Assigned Noxus source extraction and real converter candidate rehearsal.

Only technical RGBA island extraction, whole-atlas scaling, fixed roots, crops
and native assembly. No figures are painted, warped or synthesized by code.
"""
from pathlib import Path
import hashlib, io, json, statistics, sys, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

SCRIPT=Path(__file__).resolve()
PROJECT=next(p for p in SCRIPT.parents if (p/'content/factions.json').is_file()and(p/'scripts/art_compile.py').is_file())
REPORT=PROJECT/'build/reports/painted-ground-replacements-20261024-v1'
WORKSPACE=PROJECT.parent
CANDIDATES=PROJECT/'assets/candidates/painted-ground-20261024-v1'
SOURCES=PROJECT/'assets/source/creatures/ground-replacements-20261024-v1'
sys.path.insert(0,str(WORKSPACE/'scripts'))
import faction_artifacts as ART
import importlib.util
own_spec=importlib.util.spec_from_file_location('noxus_ground_own_art_compile',PROJECT/'scripts/art_compile.py')
OWN=importlib.util.module_from_spec(own_spec);own_spec.loader.exec_module(OWN)
PREFIX='Content/Sprites/runeterra/noxus/'
ROOT=(197,266)
VERSION='v6'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def enc(v): return (json.dumps(v,indent=2,sort_keys=True)+'\n').encode()
def rel(p): return p.relative_to(PROJECT).as_posix()
def put(p,b):
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists() and p.read_bytes()!=b: raise ValueError('Version changed outputs instead of overwriting: '+str(p))
    p.write_bytes(b)
def png(im):
    stream=io.BytesIO(); im.save(stream,format='PNG',compress_level=9,optimize=False); return stream.getvalue()
def save(im,p):
    put(p,png(im)); return {'source':rel(p),'source_sha256':sha(p),'sha256':sha(p),'source_canvas':list(im.size)}

def islands(array):
    """8-neighbour run-length connected components on actual source alpha."""
    parent=[];runs=[];previous=[]
    def find(i):
        while parent[i]!=i: parent[i]=parent[parent[i]];i=parent[i]
        return i
    for y,row in enumerate(array):
        padded=np.pad(row.astype(np.int8),(1,1));changes=np.flatnonzero(np.diff(padded))
        current=[]
        for x0,x1 in zip(changes[::2],changes[1::2]):
            idx=len(parent);parent.append(idx);runs.append((y,int(x0),int(x1)));current.append(idx)
            for old in previous:
                _,a,b=runs[old]
                if b<int(x0): continue
                if a>int(x1): break
                left,right=find(idx),find(old)
                if left!=right: parent[right]=left
        previous=current
    components={}
    for i,run in enumerate(runs):components.setdefault(find(i),[]).append(run)
    return sorted(components.values(),key=lambda q:sum(b-a for _,a,b in q),reverse=True)

def isolate(label,cols,rows,allowed=None):
    path=SOURCES/(label+'.png');im=Image.open(path).convert('RGBA');a=np.array(im);h,w=a.shape[:2]
    components=islands(a[:,:,3]>30);labels=np.full((h,w),-1,np.int32);cells={};records=[]
    for component in components:
        pixels=sum(b-a for _,a,b in component)
        if pixels<400:continue
        box=[min(a for _,a,b in component),min(y for y,_,_ in component),max(b for _,a,b in component),max(y for y,_,_ in component)+1]
        row=min(rows-1,int((box[1]+box[3])/2/h*rows));col=min(cols-1,int((box[0]+box[2])/2/w*cols));key=(row,col)
        if allowed is not None and key not in allowed:continue
        if key in cells:raise ValueError('Multiple major painted bodies in one cell: '+str((label,key)))
        if box[2]-box[0]>w/cols*1.75 or box[3]-box[1]>h/rows*1.65:raise ValueError('Connected body crosses atlas cells: '+str((label,key,box)))
        mask=np.zeros((h,w),np.uint8)
        for y,x0,x1 in component:mask[y,x0:x1]=255;labels[y,x0:x1]=row*cols+col
        cells[key]={'mask':mask,'bbox':box,'pixels':pixels}
    if len(cells)!=(len(allowed)if allowed is not None else cols*rows):raise ValueError('Source body count differs from specified atlas: '+str((label,len(cells),cols*rows)))
    for key,cell in cells.items():
        row,col=key;box=cell['bbox'];x0,y0=max(0,box[0]-2),max(0,box[1]-2);x1,y1=min(w,box[2]+2),min(h,box[3]+2)
        mask=np.array(Image.fromarray(cell['mask']).filter(ImageFilter.MaxFilter(5)))>0
        foreign=(labels>=0)&(labels!=row*cols+col);mask &= ~foreign
        raw=np.zeros((y1-y0,x1-x0,4),np.uint8);raw[mask[y0:y1,x0:x1]]=a[y0:y1,x0:x1][mask[y0:y1,x0:x1]]
        edge=box[0]==0 or box[1]==0 or box[2]==w or box[3]==h
        cell.update(image=Image.fromarray(raw),crop=[x0,y0,x1,y1],source=rel(path),source_sha256=sha(path),canvas=[w,h],row=row,col=col,touches_edge=edge)
        del cell['mask']
        records.append({k:v for k,v in cell.items() if k!='image'})
    put(REPORT/'measurements'/(label+'.json'),enc(records))
    return cells

def register(unit,label,cols,rows,target_height,allowed=None):
    cells=isolate(label,cols,rows,allowed);ref=cells[0,0];w,h=ref['canvas'];scale=target_height/(ref['bbox'][3]-ref['bbox'][1])
    # A single atlas camera scale and fixed cell-horizontal root. Whole-row
    # whitespace baselines are normalized; each pose is never tightly refitted.
    source_root=(ref['bbox'][0]+ref['bbox'][2])/2
    baselines={r:statistics.median(c['bbox'][3] for (rr,_),c in cells.items() if rr==r) for r in set(rr for rr,_ in cells)}
    out={};records=[]
    for (r,c),cell in cells.items():
        raw=cell['image'];x0,y0,_,_=cell['crop'];fitted=raw.resize((max(1,round(raw.width*scale)),max(1,round(raw.height*scale))),Image.Resampling.LANCZOS)
        camera_x=2 if unit=='broodSentry'else 0
        xy=(round(ROOT[0]+camera_x+(x0-c*w/cols-source_root)*scale),round(ROOT[1]+1+(y0-baselines[r])*scale))
        native=Image.new('RGBA',(450,400));native.alpha_composite(fitted,xy)
        if sum(native.getchannel('A').histogram()[1:])!=sum(fitted.getchannel('A').histogram()[1:]):raise ValueError('Native canvas clipping')
        p=SOURCES/unit/('native-'+VERSION)/f'{label}-r{r}-c{c}.png';desc=save(native,p)
        records.append({k:v for k,v in cell.items() if k!='image'}|{'raw_source_master':cell['source'],'raw_source_master_sha256':cell['source_sha256'],'uniform_atlas_scale':scale,'row_baseline':baselines[r],'whole_cohort_camera_x':camera_x,'native_offset':list(xy),'native_root':list(ROOT),**desc})
        out[r,c]=(native,desc)
    return out,records

def fit(im,size):
    cropped=im.crop(im.getchannel('A').getbbox());sc=ImageOps.contain(cropped,(size[0]-4,size[1]-4),Image.Resampling.LANCZOS)
    out=Image.new('RGBA',size);out.alpha_composite(sc,((size[0]-sc.width)//2,(size[1]-sc.height)//2));return out

def recipe(unit,role,generation,**kwargs):
    return {'id':f'noxus.creature.{unit}.{role}','unit':unit,'title':unit+' '+role,
            'output_path':PREFIX+f'creatures/{unit}/'+role+('.json' if role in ('battle','map') else '.png'),
            'production_status':'painted-master-complete-unapproved','status':'built-unreviewed','visual_approval_granted':False,
            'acceptance':'authored configuration; native motion/human art/rights acceptance pending',
            'credits':{'author':'OpenAI built-in imagegen, project-directed painted2D and technical extraction','license':None,'redistribution':'unresolved; release prohibited'},
            'generation':generation,'depends_on':[],**kwargs}

def main():
    SOURCES.mkdir(parents=True,exist_ok=True)
    producer=SOURCES/('prepare-'+VERSION+'.py');put(producer,SCRIPT.read_bytes())
    for p in CANDIDATES.glob('*.png'):
        dest=SOURCES/p.name
        if not dest.exists():shutil.copy2(p,dest)
    for p in CANDIDATES.glob('*.generation.json'):
        value=json.loads(p.read_text());value['reference']=rel(SOURCES/value['reference'])
        put(SOURCES/p.name,enc(value))
    recipes=[];unit_records=[]
    for unit,stem,human,height in [('guildKnifeThrower','knife-base',True,78),('masterKnifeThrower','knife-up',True,80),('arachnoidSentry','spider-base',False,58),('broodSentry','spider-up',False,60)]:
        motion,mrec=register(unit,stem+'-motion',3,5,height)
        reaction,rrec=register(unit,stem+'-reactions',4,4,height,{(r,c)for r in range(2)for c in range(4)}if stem=='knife-up'else None)
        melee,arec=register(unit,stem+'-melee',6,3,height)
        row=lambda frames,r,columns:[frames[r,c]for c in columns]
        holding=motion[4,2]
        turn=[holding,motion[3,1],motion[4,0],motion[4,1]]
        if stem=='knife-up':
            deaths,drec=register(unit,stem+'-death-v2',3,2,height)
            death=[*row(deaths,0,range(3)),*row(deaths,1,range(3))];rrec+=drec
        else:
            death=[*row(reaction,2,range(4)),*row(reaction,3,[0,1,2,3])]
        groups={0:[*row(motion,0,range(3)),*row(motion,1,range(3))],1:[*row(motion,2,range(3)),motion[3,0]],2:[holding],3:row(reaction,0,range(4)),4:row(reaction,1,range(4)),5:death,7:turn,8:list(reversed(turn)),11:row(melee,0,range(6)),12:row(melee,1,range(6)),13:row(melee,2,range(6)),22:[death[-1]]}
        registrations=mrec+rrec+arec
        if stem=='knife-base':
            walking,wrec=register(unit,stem+'-walk-v3',3,2,height)
            groups[0]=[*row(walking,0,range(3)),*row(walking,1,range(3))]
            registrations=[r for r in registrations if not(r['raw_source_master'].endswith('knife-base-motion.png')and r['row']<2)]+wrec
        if human:
            opposite,orec=register(unit,stem+'-step-opposite-v6',3,1,height)
            groups[0]=groups[0][:3]+row(opposite,0,range(3))
            registrations=[r for r in registrations if not(r['row']==1 and r['raw_source_master'].endswith(('knife-base-walk-v3.png','knife-up-motion.png')))]+orec
        if human:
            shots,srec=register(unit,stem+'-shoot',8,3,height);registrations+=srec
            for r,g in enumerate((14,15,16)):groups[g]=row(shots,r,range(8))
        selected_labels=[stem+'-'+suffix for suffix in ('motion','reactions','melee')]+([stem+'-shoot']if human else [])+([stem+'-death-v2']if stem=='knife-up'else [])
        if stem=='knife-base':selected_labels.append(stem+'-walk-v3')
        if human:selected_labels.append(stem+'-step-opposite-v6')
        generation={'provider':'OpenAI built-in imagegen','image_generation_used':True,'model_id_exposed':False,'status':'authored configuration','release_accepted':False,
            'model':'not exposed by built-in tool','prompt':json.loads((SOURCES/(stem+'-motion.generation.json')).read_text())['prompt'],
            'route':'Genuine painted action atlases; intact alpha-island extraction, uniform atlas camera scale, whole-row whitespace registration, fixed197/266 root; no synthesized pose or3D input',
            'painted_master':rel(SOURCES/(stem+'-motion.png')),'painted_master_sha256':sha(SOURCES/(stem+'-motion.png')),
            'supplementary_painted_sources':[{'painted_master':rel(SOURCES/(label+'.png')),'painted_master_sha256':sha(SOURCES/(label+'.png')),'generation_record':rel(SOURCES/(label+'.generation.json')),'generation_record_sha256':sha(SOURCES/(label+'.generation.json'))}for label in selected_labels]}
        cohort=SOURCES/unit/('cohort-'+VERSION+'.json');put(cohort,enc({'unit':unit,'pivot':list(ROOT),'canvas':[450,400],'source_frames':registrations,'turn_semantics':'g7right3/4→frontal; nativeflip; g8reverse genuinehalfturn→right3/4','status':'authored configuration'}))
        r=recipe(unit,'battle',generation,recipe_type='vcmi_animation',canvas=[450,400],pivot={'x':197,'y':266},source=rel(cohort),source_sha256=sha(cohort),generateOverlay=1,generateShadow=1,groups=[{'group':g,'frames':[desc for _,desc in pairs]}for g,pairs in sorted(groups.items())]);recipes.append(r)
        # Current Noxus map animation convention is one six-frame group0.
        mapframes=[]
        for i,(im,_) in enumerate(groups[0]):
            a=im.getchannel('A').point(lambda x:255 if x>=30 else 0).getbbox();crop=im.crop(a);factor=(46 if human else 33)/height
            sc=crop.resize((max(1,round(crop.width*factor)),max(1,round(crop.height*factor))),Image.Resampling.LANCZOS)
            out=Image.new('RGBA',(96,64));out.alpha_composite(sc,(round(48+(a[0]-197)*factor),round(59+(a[1]-267)*factor)))
            desc=save(out,SOURCES/unit/('native-'+VERSION)/f'map-f{i:03}.png');mapframes.append(desc)
        mapcohort=SOURCES/unit/('map-cohort-'+VERSION+'.json');put(mapcohort,enc({'unit':unit,'frames':mapframes,'pivot':[48,58],'derivation':'Compatible own genuine walking frames at fixed Noxus map48/58 scale/root; no independent elevated camera repaint claimed'}))
        recipes.append(recipe(unit,'map',generation,recipe_type='vcmi_animation',canvas=[96,64],pivot={'x':48,'y':58},source=rel(mapcohort),source_sha256=sha(mapcohort),generateOverlay=0,generateShadow=0,groups=[{'group':0,'frames':mapframes}]))
        for role,size in [('large',(58,64)),('small',(32,32)),('attackLeft',(64,64)),('attackRight',(64,64))]:
            if role.startswith('attack'):
                body=groups[12][3][0]
                if role=='attackLeft':body=ImageOps.mirror(body)
            else:
                body=holding[0]
                if human:
                    box=body.getchannel('A').getbbox();body=body.crop((box[0],box[1],box[2],box[1]+round((box[3]-box[1])*.62)))
            native=fit(body,size);desc=save(native,SOURCES/unit/('native-'+VERSION)/(role+'.png'))
            recipes.append(recipe(unit,role,generation,recipe_type='raster',size=list(size),canvas=list(size),fit='contain',require_alpha=True,**desc))
        board=Image.new('RGBA',(1250,len(groups)*130),(46,44,38,255));draw=ImageDraw.Draw(board);crop_checks=[]
        for rr,(g,pairs) in enumerate(sorted(groups.items())):
            draw.text((2,rr*130+2),'g'+str(g),fill='white')
            for c,(im,_)in enumerate(pairs):
                board.alpha_composite(im.crop((125,150,275,280)),(50+c*150,rr*130))
                if g in (0,1,2):
                    box=im.getchannel('A').point(lambda x:255 if x>=128 else 0).getbbox()
                    crop_checks.append({'group':g,'frame':c,'bbox':box,'stock120_intact':box[0]>=150 and box[1]>=155 and box[2]<=250 and box[3]<=275})
        put(REPORT/(unit+'-actions-native-'+VERSION+'.png'),png(board))
        unit_records.append({'unit':unit,'groups':{g:len(v)for g,v in groups.items()},'stock_crop_checks':crop_checks,'source_registration':rel(cohort),'gait_and_native_motion_acceptance':'pending actual review','attackLeft_mirrors_own_genuine_right_contact_pose':True})
    raw=SOURCES/'throwing-knife-projectile.png';im=Image.open(raw).convert('RGBA');im=im.crop(im.getchannel('A').getbbox());im=ImageOps.contain(im,(24,10),Image.Resampling.LANCZOS)
    projectile_frames=[]
    for i,angle in enumerate((90,45,0,-45,-90)):
        rotated=im.rotate(angle,Image.Resampling.BICUBIC,expand=True);native=Image.new('RGBA',(32,32));native.alpha_composite(rotated,((32-rotated.width)//2,(32-rotated.height)//2))
        projectile_frames.append(save(native,SOURCES/'projectile'/('native-'+VERSION)/f'angle-{i}.png'))
    projectile_source=SOURCES/'projectile'/('cohort-'+VERSION+'.json');put(projectile_source,enc({'painted_master':rel(raw),'painted_master_sha256':sha(raw),'frameAngles':[90,45,0,-45,-90],'frames':projectile_frames,'technical_assembly':'Uniform scale of own painted single knife and rigid projectile orientations; no creature pose synthesis'}))
    projectile_generation=json.loads((SOURCES/'throwing-knife-projectile.generation.json').read_text());projectile_generation.pop('reference',None);projectile_generation.update(painted_master=rel(raw),painted_master_sha256=sha(raw),image_generation_used=True,model='not exposed by built-in tool')
    projectile=recipe('throwingKnife','projectile',projectile_generation,recipe_type='vcmi_animation',canvas=[32,32],pivot={'x':16,'y':16},source=rel(projectile_source),source_sha256=sha(projectile_source),generateOverlay=0,generateShadow=0,groups=[{'group':0,'frames':projectile_frames}])
    projectile['output_path']=PREFIX+'projectiles/throwingKnife.json';projectile['id']='noxus.projectile.throwingKnife';del projectile['unit'];recipes.append(projectile)
    for r in recipes:
        masters=[SOURCES/('spider-pair-master.png'if r.get('unit','').startswith(('arachnoid','brood'))else'knife-pair-master.png'),producer]
        r['source_cohorts']=[{'path':rel(p),'sha256':sha(p)}for p in masters]
        put(CANDIDATES/('recipes-'+VERSION)/((r.get('unit','projectile'))+'-'+Path(r['output_path']).stem+'.json'),enc(r))
    inventories=[];all_receipts=[]
    for version in ('assembly-a-'+VERSION,'assembly-b-'+VERSION):
        inventory={};receipts=[]
        for rp in sorted((CANDIDATES/('recipes-'+VERSION)).glob('*.json')):
            planned,receipt=OWN.plan(PROJECT,rp);receipts.append(receipt)
            for name,payload in planned.items():
                put(REPORT/version/name,payload);inventory[name]=hashlib.sha256(payload).hexdigest()
        inventories.append(inventory);all_receipts.append(receipts)
    assert inventories[0]==inventories[1]
    summary={'status':'authored configuration','units':unit_records,'logical_recipes':len(recipes),'physical_outputs':len(inventories[0]),'actual_compiler':'runeterra-noxus/scripts/art_compile.py plan','actual_compiler_sha256':sha(PROJECT/'scripts/art_compile.py'),'two_actual_converter_passes_identical':True,'output_inventory':inventories[0],'recipe_inventory':{rel(p):sha(p)for p in (CANDIDATES/('recipes-'+VERSION)).glob('*.json')},'limitations':['No native playback or final human/rights acceptance','Map uses compatible own battle gait camera, not independently painted elevated view','Left map attack icon mirrors own genuine contact pose','New genuine opposite-leg halfcycles require independent source/loop review and native timing verification']}
    put(REPORT/('handoff-'+VERSION+'.json'),enc(summary));put(REPORT/('converter-receipts-'+VERSION+'.json'),enc(all_receipts));print(json.dumps({'recipes':len(recipes),'outputs':len(inventories[0]),'crop_failures':{x['unit']:sum(not v['stock120_intact']for v in x['stock_crop_checks'])for x in unit_records}}))

if __name__=='__main__': main()
