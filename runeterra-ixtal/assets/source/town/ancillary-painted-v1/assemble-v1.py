"""Deterministic painted bitmap registration; no creative pixels/animation invented."""
from pathlib import Path
import hashlib,json,sys,io
import numpy as np
from PIL import Image,ImageDraw

HERE=Path(__file__).resolve().parent;P=HERE.parents[3];W=P.parent
REPORT=W/'build/reports/ixtal-implementation-20261026-v1/town/ancillary'
N=HERE/'native-v1';R=P/'assets/recipes/town-ancillary'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel(p):return Path(p).relative_to(P).as_posix()
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def save(p,im):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,compress_level=9)
def opened(p):return Image.open(p).convert('RGBA')
def box(im):return im.getchannel('A').point(lambda x:255 if x>=8 else 0).getbbox()
def pin(p):return {'path':rel(p),'sha256':sha(p)}
def gen(src):
    return {'image_generation_used':True,'provider':'OpenAI built-in imagegen','model':'Exact model identifier not exposed by tool','painted_master':rel(src),'painted_master_sha256':sha(src),'prompt':(src.parent/'prompt-v1.txt').read_text(encoding='utf-8')}
def dependencies(*paths):
    graph=HERE/'generation-ancestry-v1.json';records=json.loads(graph.read_text())['sources'];parents={str((P/v['source']['path']).resolve()):v for v in records.values()};result=[Path(__file__),HERE/'source-scope-v1.json',graph]
    def visit(p):
        p=Path(p)
        if p in result:return
        result.append(p);node=parents.get(str(p.resolve()))
        if node:
            for ref in [node['prompt'],node['metadata'],*node['own_creative_ancestors']]:visit(P/ref['path'])
    for p in paths:visit(p)
    return [pin(p) for p in result]
def raster(key,out,frame,master,extra=None,detail=None):
    recipe={'recipe_type':'raster','output_path':out,'production_status':'painted-master-complete-unapproved','source':rel(frame),'source_sha256':sha(frame),'source_canvas':list(opened(frame).size),'canvas':list(opened(frame).size),'fit':'exact','generation':gen(master),'production_inputs':dependencies(master,master.parent/'prompt-v1.txt',*(extra or [])),'visual_approval_granted':False}
    if detail:recipe['painted_source_derivation']=detail
    path=R/(key+'.json');dump(path,recipe);return path

def siege():
    plan=json.loads((HERE/'siege-plan-v1.json').read_text());assets={a['id']:a for a in plan['assets']};records={};frames={};recipes=[]
    selected={key:'siege-'+key+'-v2' for key in ['SGIXDRW1','SGIXDRW2','SGIXDRW3','SGIXDRWC','SGIXMOAT','SGIXMLIP']}
    for a in plan['assets']:
        key=a['id'];master=HERE/selected.get(key,'siege-'+key)/'master-v1.png';im=opened(master);target=tuple(a['size']);b=box(im);t=a['native_reference_bbox'];parent=a.get('parent');ref=None
        if key=='SGIXBACK':
            out=im.resize(target,Image.Resampling.LANCZOS);detail={'method':'whole painted opaque landscape resized to native background','source_canvas':list(im.size),'target_canvas':list(target)}
        else:
            # Intact bodies establish each family's projected width/height. Related
            # damage canvases share that registration; remaining rubble is NEVER
            # independently density-fitted into an intact wall's full silhouette.
            family=parent if parent and not key.endswith(('C','WC')) else key
            a0=assets.get(family,a);reference=HERE/selected.get(family,'siege-'+family)/'master-v1.png';reference_im=opened(reference);b0=box(reference_im);t0=a0['native_reference_bbox']
            sx=(t0[2]-t0[0])/(b0[2]-b0[0]);sy=(t0[3]-t0[1])/(b0[3]-b0[1])
            if key!=family:
                im=im.resize(reference_im.size,Image.Resampling.LANCZOS);ref=reference
            part=im.resize((max(1,round(im.width*sx)),max(1,round(im.height*sy))),Image.Resampling.LANCZOS)
            offset=(round(t0[0]-b0[0]*sx),round(t0[1]-b0[1]*sy));out=Image.new('RGBA',target);out.alpha_composite(part,offset)
            detail={'method':'explicit per-axis native projected-fragment registration; not uniform scale, not3D, no creative raster paint','source_canvas':list(opened(master).size),'family_canvas':list(reference_im.size),'family':family,'family_material_bbox':list(b0),'target_native_bbox':t0,'axis_scales':[sx,sy],'offset':list(offset),'shared_parent_registration':bool(ref),'artwork_created_by_code':False,'licensed_reference_pixels_bundled':False}
        frame=N/'siege'/(key+'.png');save(frame,out);frames[key]=out
        recipes.append(raster('siege/'+key,a['output_path'],frame,master,[HERE/'siege-plan-v1.json']+([ref] if ref else []),detail))
        records[key]={'master':pin(master),'native':pin(frame),'native_canvas':list(target),'alpha_bbox':box(out),'position':a['position'],'derivation':detail}
    dump(HERE/'siege-native-registration-v1.json',records)
    # Diagnostic composites reflect actual configured native origins. They do not
    # simulate interaction, damage mechanics, or confer native runtime acceptance.
    for status in ['intact','damaged','breached']:
        im=frames['SGIXBACK'].copy();st=1 if status=='intact' else 2 if status=='damaged' else 3
        ids=['SGIXMOAT','SGIXTPWL','SGIXWA5','SGIXWA2','SGIXMLIP','SGIXMAN'+('1' if st==1 else '2'),'SGIXTW2'+('1' if st==1 else '2'),'SGIXTW1'+('1' if st==1 else '2')]+['SGIXWA'+n+str(st) for n in ['1','3','4','6']]+['SGIXARCH','SGIXDRW'+('3' if st==3 else '2')]
        for key in ids:
            xy=assets[key]['position'];im.alpha_composite(frames[key],(xy['x'],xy['y']))
        save(REPORT/('siege-'+status+'-native-v1.png'),im)
    sheet=Image.new('RGBA',(800,8*300),(28,30,26,255));d=ImageDraw.Draw(sheet)
    for i,a in enumerate(plan['assets']):
        key=a['id'];im=frames[key];x=(i%4)*200;y=(i//4)*300;d.text((x+6,y+5),key+' '+str(im.size),fill='white');im=im.copy();im.thumbnail((190,274),Image.Resampling.NEAREST);sheet.alpha_composite(im,(x+5,y+23))
    save(REPORT/'siege32-native-contact-v1.png',sheet)
    # Source-only turret diagnostic following the existing native450x400 tower
    # frame crop convention. Does not prove shooting animation or native draw.
    shooter=P/'assets/source/creatures/painted-v1/t4-t5/native/stoneshaper/battle/g02-f000.png'
    if shooter.is_file():
        figure=opened(shooter)
        if figure.size!=(450,400):raise ValueError('Review actual tower source canvas')
        figure=figure.transpose(Image.Transpose.FLIP_LEFT_RIGHT).crop((0,0,450,232))
        scene=opened(REPORT/'siege-intact-native-v1.png');town=json.loads((P/'content/factions.json').read_text())['ixtal']['town']['siege'];masks=[]
        for tower in ['keep','top','bottom']:
            at=town['towers'][tower]['creature'];scene.alpha_composite(figure,(at['x'],at['y']));masks.append({'tower':tower,'origin':at})
        for key in ['SGIXMANC','SGIXTW2C','SGIXTW1C','SGIXDRWC']:
            at=assets[key]['position'];scene.alpha_composite(frames[key],(at['x'],at['y']))
        save(REPORT/'tower-idle-clearance-native-v1.png',scene)
        dump(REPORT/'tower-idle-clearance-method-v1.json',{'scope':'Offline authored base Stoneshaper idle PNG only; not runtime/shooting acceptance','source':pin(shooter),'content':pin(P/'content/factions.json'),'cropped_figure_alpha_bbox':box(figure),'projected_figure_boxes':{v['tower']:[box(figure)[0]+v['origin']['x'],box(figure)[1]+v['origin']['y'],box(figure)[2]+v['origin']['x'],box(figure)[3]+v['origin']['y']] for v in masks},'transform':'Mirror whole450x400canvas horizontally, crop Rect0,0,450,232; configured tower creature origins; actual foreground lips drawn over','native_canvas':[800,556],'towers':masks,'native_observed':False})
    return recipes,frames

def maps_icons():
    recipes=[];records={};masters={};frames={};scope=json.loads((HERE/'source-scope-v1.json').read_text());canvas=tuple(scope['adventure_canvas']);root=scope['adventure_ground_root']
    # All five genuine painted edits preserve square1254canvas and the front
    # stair root near705,1100; this shared registration is not per-state bbox fit.
    source_root=(705,1100);scale=.123
    for key in scope['adventure_states']:
        master=HERE/('map-'+key)/'master-v1.png';im=opened(master);masters[key]=master
        if im.size!=(1254,1254):raise ValueError('Review map source camera/canvas before registration: '+key)
        a=np.array(im);mask=(a[:,:,2]>a[:,:,0]*1.5)&(a[:,:,2]>a[:,:,1]*1.35)&(a[:,:,2]>65)&(a[:,:,3]>8)
        # Source flag is the isolated blue ownership cloth, never jade crest.
        region=np.zeros(mask.shape,dtype=bool);region[180:620,200:570]=True;mask &= region
        if mask.sum()<100:raise ValueError('Painted ownership flag missing: '+key)
        flag=np.zeros_like(a);gray=np.clip(a[:,:,:3].max(axis=2)*1.8,80,255).astype('uint8')
        for c in range(3):flag[:,:,c]=np.where(mask,gray,0)
        flag[:,:,3]=np.where(mask,a[:,:,3],0)
        a[:,:,3]=np.where(mask,0,a[:,:,3]);body=Image.fromarray(a);flag=Image.fromarray(flag)
        def project(v):
            resized=v.resize((round(v.width*scale),round(v.height*scale)),Image.Resampling.LANCZOS);out=Image.new('RGBA',canvas);out.alpha_composite(resized,(round(root[0]-source_root[0]*scale),round(root[1]-source_root[1]*scale)));return out
        out=project(body);overlay=project(flag);frame=N/'map'/(key+'.png');over=N/'map'/(key+'-OVERLAY.png');save(frame,out);save(over,overlay);frames[key]=out
        r={'recipe_type':'vcmi_animation','output_path':'Content/Sprites/runeterra/ixtal/town/map/'+key+'.json','production_status':'painted-master-complete-unapproved','canvas':list(canvas),'pivot':{'x':root[0],'y':root[1]},'generateShadow':1,'generateOverlay':0,'groups':[{'group':0,'frames':[{'frame':0,'source':rel(frame),'source_sha256':sha(frame),'source_canvas':list(canvas),'overlay_source':rel(over),'overlay_sha256':sha(over)}]}],'generation':gen(master),'production_inputs':dependencies(master,master.parent/'prompt-v1.txt'),'visual_approval_granted':False,'animation_scope':'One painted static adventure-town pose, not creature motion'}
        path=R/'map'/(key+'.json');dump(path,r);recipes.append(path);records[key]={'master':pin(master),'frame':pin(frame),'overlay':pin(over),'source_canvas':[1254,1254],'source_ground_root':list(source_root),'native_root':root,'uniform_scale':scale,'alpha_bbox':box(out),'ownership_cloth_source_pixels':int(mask.sum()),'ground_root_not_bbox_fitted':True}
    dump(HERE/'map-native-registration-v1.json',records)
    # Pure image crop/scale/assembly from own paintings. Background is genuine
    # painted Ixtal battlefield terrain; X is an own painted construction marker.
    backdrop=opened(HERE/'siege-SGIXBACK/master-v1.png');cross=opened(HERE/'status-cross/master-v1.png');cross=cross.crop(box(cross))
    iconimages={}
    for settlement in ['village','fort']:
        for size,dim in scope['icons'].items():
            base=backdrop.crop((20,500,600,1030)).resize(tuple(dim),Image.Resampling.LANCZOS);subject=opened(masters[settlement]);subject=subject.crop(box(subject));subject.thumbnail((dim[0]-4,dim[1]-4),Image.Resampling.LANCZOS);base.alpha_composite(subject,((dim[0]-subject.width)//2,dim[1]-subject.height-2))
            for state in ['normal','built']:
                out=base.copy();mark=(12,12) if size=='large' else (8,8)
                if state=='built':out.alpha_composite(cross.resize(mark,Image.Resampling.LANCZOS),(dim[0]-mark[0]-1,dim[1]-mark[1]-1))
                name=settlement+'_'+state+'_'+size;frame=N/'icons'/(name+'.png');save(frame,out);iconimages[name]=out
                recipes.append(raster('icons/'+name,'Content/Sprites/runeterra/ixtal/town/icons/'+name+'.png',frame,masters[settlement],[HERE/'siege-SGIXBACK/master-v1.png',HERE/'status-cross/master-v1.png',HERE/'status-cross/prompt-v1.txt']))
    # Exact base Stoneshaper own portrait is the actual faction tower shooter.
    CR=P/'assets/source/creatures/painted-v1/t4-t5';master=CR/'stoneshaper/portrait-v1.png';portrait=opened(master);generation=json.loads((P/'assets/recipes/creatures/t4-t5/stoneshaper/large.json').read_text())['generation'];generation=dict(generation);generation['painted_master']=rel(master);generation['painted_master_sha256']=sha(master)
    for key,dim in scope['tower_portraits'].items():
        if key=='large':out=opened(CR/'native/stoneshaper/large.png')
        else:out=opened(CR/'native/stoneshaper/small.png')
        if list(out.size)!=dim:raise ValueError('Actual shooter portrait size changed')
        name='tower'+key.title();frame=N/'siege'/(name+'.png');save(frame,out)
        r={'recipe_type':'raster','canvas':dim,'source_canvas':dim,'source':rel(frame),'source_sha256':sha(frame),'fit':'exact','output_path':'Content/Sprites/runeterra/ixtal/siege/'+name+'.png','generation':generation,'production_status':'painted-master-complete-unapproved','production_inputs':dependencies(master,CR/'generation-ledger-v1.json',CR/'native/stoneshaper'/('large.png' if key=='large' else 'small.png')),'visual_approval_granted':False,'tower_shooter':'stoneshaper','scope':'Exact unchanged base own painted native portrait; not Axiom upgrade'}
        path=R/'siege'/(name+'.json');dump(path,r);recipes.append(path);iconimages[name]=out
    sheet=Image.new('RGBA',(5*210,260),(34,40,29,255));d=ImageDraw.Draw(sheet)
    for i,key in enumerate(scope['adventure_states']):
        x=i*210;d.text((x+8,5),key,fill='white');sheet.alpha_composite(frames[key],(x,25));ov=opened(N/'map'/(key+'-OVERLAY.png'));blue=Image.new('RGBA',ov.size,(40,70,220,255));blue.putalpha(ov.getchannel('A'));sheet.alpha_composite(blue,(x,25))
    for i,(key,im) in enumerate(iconimages.items()):x=i*100;sheet.alpha_composite(im,(x+6,190));d.text((x+3,253),key,fill='white')
    save(REPORT/'map-icons-tower-native-contact-v1.png',sheet)
    return recipes

def main():
    REPORT.mkdir(parents=True,exist_ok=True);rs,_=siege();rs+=maps_icons();assert len(rs)==47
    required={x['output'] for x in json.loads((REPORT/'actual-missing-47-v1.json').read_text())['assets']};actual={json.loads(p.read_text())['output_path'] for p in rs};assert required==actual
    dump(HERE/'candidate-recipes-v1.json',{'status':'authored configuration','recipes':[rel(p) for p in rs],'required_output_count':47,'native_observed':False,'release_accepted':False})
    print('47 required recipes authored; native static painted-source diagnostic composites saved, no production/staging/native run')
if __name__=='__main__':main()
