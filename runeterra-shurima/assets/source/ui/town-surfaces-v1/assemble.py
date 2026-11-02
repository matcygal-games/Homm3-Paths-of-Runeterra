"""Compose native UI surfaces from own painted layers, without drawing artwork."""
from pathlib import Path
import hashlib,json,sys
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;P=HERE.parents[3]
R=P/'build/reports/town-interface-painted-20261024-v1';R.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(P.parent/'scripts'))
from faction_art_compile import create_compiler
C=create_compiler('shurima')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(P).as_posix()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
plate=P/'assets/source/town/landscape-v1/native-rgba.png'
terrain=Image.open(plate).convert('RGBA')
ids=C.indexed_building_ids(P)
frames=[];records=[]
sheet=Image.new('RGB',(600,((len(ids)+3)//4)*92),(55,49,41));draw=ImageDraw.Draw(sheet)
for n,(building,index) in enumerate(sorted(ids.items(),key=lambda pair:pair[1])):
    layer=P/f'assets/source/town/painted-resume-v6/{building}/frame.png'
    image=Image.open(layer).convert('RGBA');box=image.getchannel('A').point(lambda a:255 if a>=32 else 0).getbbox()
    assert box
    scene=terrain.copy();scene.alpha_composite(image)
    x=min(max(round((box[0]+box[2])/2-200),0),400)
    y=min(max(box[3]-167,0),187)
    crop=[x,y,x+400,y+187]
    icon=scene.crop(crop).resize((150,70),Image.Resampling.LANCZOS)
    target=HERE/'building-icons'/f'{building}.png';target.parent.mkdir(exist_ok=True);icon.save(target)
    frames.append({'building':building,'frame':index,'source':rel(target),'source_sha256':sha(target),'source_canvas':[150,70]})
    records.append({'building':building,'native_building_id':index,'layer':rel(layer),
        'layer_sha256':sha(layer),'terrain':rel(plate),'terrain_sha256':sha(plate),'crop':crop,
        'output':rel(target),'sha256':sha(target)})
    sx,sy=(n%4)*150,(n//4)*92;sheet.paste(icon,(sx,sy+20));draw.text((sx+3,sy+3),f'{index}: {building}',fill='white')
generation={'image_generation_used':True,'provider':'OpenAI built-in imagegen; technical2D composition',
    'model':'not exposed by built-in tool','prompt':'Own painted Shurima terrain and selected35painted building states. Exact retained generation prompts live alongside their original masters.',
    'painted_master':rel(plate),'painted_master_sha256':sha(plate),
    'producer':rel(Path(__file__)),'method':'NativeID indexing and uniform local scene crops of own painted terrain and building layers.'}
base={'production_status':'painted-master-complete-unapproved','status':'authored configuration',
    'generation':generation,'visual_approval_granted':False,
    'credits':{'author':'Project-directed built-in imagegen; technical2D composition','license':None,'redistribution':'unresolved; release prohibited'}}
indexed={**base,'recipe_type':'indexed_animation','output_path':'Content/Sprites/runeterra/shurima/town/buildingIcons.json',
    'canvas':[150,70],'pivot':{'x':75,'y':35},'generateOverlay':0,'generateShadow':0,'frames':frames}
recipes=[P/'assets/recipes/ui/town-surfaces-v1/buildingIcons.json'];write(recipes[0],indexed)
cross=Image.open(HERE/'status-x-master.png').convert('RGBA');cross_box=cross.getchannel('A').getbbox();assert cross_box
cross=cross.crop(cross_box)
icon_sheet=Image.new('RGB',(8*80,100),(55,49,41));icon_draw=ImageDraw.Draw(icon_sheet)
for kind,state in (('village','village'),('fort','fort')):
    map_source=P/f'assets/source/town/map-painted-v1/native/{state}-000.png'
    map_image=Image.open(map_source).convert('RGBA')
    box=map_image.getchannel('A').point(lambda a:255 if a>=32 else 0).getbbox();assert box
    body=map_image.crop(box)
    for flag in ('normal','built'):
        for size_name,size in (('large',(58,64)),('small',(48,32))):
            width,height=size
            backdrop=terrain.crop((220,0,560,374)).resize(size,Image.Resampling.LANCZOS)
            fit=body.copy();fit.thumbnail((width-2,height-8),Image.Resampling.LANCZOS)
            position=((width-fit.width)//2,height-fit.height-2)
            backdrop.alpha_composite(fit,position)
            if flag=='built':
                edge=12 if size_name=='large' else 8
                glyph=cross.resize((edge,edge),Image.Resampling.LANCZOS)
                backdrop.alpha_composite(glyph,(width-edge-1,height-edge-1))
            name=f'{kind}_{flag}_{size_name}'
            target=HERE/'town-icons'/f'{name}.png';target.parent.mkdir(exist_ok=True);backdrop.save(target)
            master=P/f'assets/source/town/map-painted-v1/{state}-master-v{2 if state=="village" else 1}.png'
            gen={**generation,'painted_master':rel(master)}
            gen['painted_master_sha256']=sha(P/gen['painted_master'])
            recipe={**base,'generation':gen,'recipe_type':'raster','output_path':f'Content/Sprites/runeterra/shurima/town/icons/{name}.png',
                'size':list(size),'source':rel(target),'source_sha256':sha(target),'source_canvas':list(size),'fit':'exact'}
            path=P/f'assets/recipes/ui/town-surfaces-v1/{name}.json';write(path,recipe);recipes.append(path)
            index=len(recipes)-2;icon_sheet.paste(backdrop,(index*80,24),backdrop);icon_draw.text((index*80+2,3),name[:12],fill='white')
sheet.save(R/'building-icons-native-1x.png');icon_sheet.save(R/'town-icons-native-1x.png')
all_outputs={}
for path in recipes:
    first,_=C.plan(P,path);second,_=C.plan(P,path);assert first==second
    for name,data in first.items():
        assert name not in all_outputs;all_outputs[name]=hashlib.sha256(data).hexdigest()
        dest=R/'compiled'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
write(HERE/'composition-provenance.json',{'buildings':records,'native_icon_sizes':{'large':[58,64],'small':[48,32]},
    'status_glyph':{'master':rel(HERE/'status-x-master.png'),'sha256':sha(HERE/'status-x-master.png')},
    'native_building_icon_canvas':[150,70],'source_references':'Private original HALLCSTL/ITPT/ITPA frames measured in town-map report, excluded from package.',
    'visual_approval_granted':False})
write(R/'conversion.json',{'status':'authored configuration','required_outputs':len(recipes),'expanded_files':len(all_outputs),
    'actual_building_ids':ids,'native_index_gaps_retained':True,'output_sha256':all_outputs,
    'repeat_strict_plan_byte_exact':True,'native_execution':False,'visual_approval_granted':False})
print(json.dumps({'recipes':len(recipes),'building_frames':len(frames),'expanded_files':len(all_outputs)}))
