"""Technical assembly and unchanged real compiler, two private deterministic passes."""
from pathlib import Path
import json,hashlib,sys
from PIL import Image,ImageDraw
import assemble
SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[4]
UNIT=SOURCE.name
REPORT=PROJECT/'build/reports/painted-runners-production-20261024-v1'
RECIPES=REPORT/'recipe-overlays'/UNIT
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(PROJECT).as_posix()
def write(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def border(im):
    a=im.getchannel('A');w,h=im.size
    return max(a.crop(b).getextrema()[1] for b in [(0,0,w,1),(0,h-1,w,h),(0,0,1,h),(w-1,0,w,h)])
def pins(folder):return {f.name:sha(f) for f in sorted(folder.glob('*.png'))}
def main():
    action=json.loads((SOURCE/'action-map-v1.json').read_text())
    protected=SOURCE/'standing-master-v0.png';before=sha(protected)
    assemble.main();first=pins(SOURCE/'native');assemble.main();second=pins(SOURCE/'native')
    assert first==second,'Native assembly nondeterminism'
    chosen=sorted({n.removesuffix('-left') for names in action['groups'].values() for n in names})
    for n in chosen:assert Image.open(SOURCE/(n+'.png')).size in [(1330,1182),(1331,1182),(1330,1183),(1331,1183)],n
    masters=[]
    for f in sorted(SOURCE.glob('*-v*.png')):
        if 'reference' in f.stem:continue
        im=Image.open(f)
        masters.append({'source':rel(f),'source_sha256':sha(f),'canvas':list(im.size),'used_as_action_key':f.stem in chosen,'image_metadata_keys':sorted(im.info)})
    raw_receipt=REPORT/'generation-tool-receipts-v1.json'
    ledger={'status':'authored configuration','provider':'OpenAI built-in imagegen','model':'not exposed by built-in tool','derived_from_blender':False,'original_identity':{'source':rel(protected),'source_sha256':before},'private_tool_receipt_sha256':sha(raw_receipt),'painted_sources':masters,'prompt_sources':[{'source':rel(f),'source_sha256':sha(f)} for f in sorted(SOURCE.glob('*prompt*')) if f.is_file()],'technical_producers':[{'source':rel(f),'source_sha256':sha(f)} for f in [SOURCE/'assemble.py',SOURCE/'finalize.py']],'fixed_transform':{'canvas':[450,400],'source_root':[640,1130],'native_root':[218,266],'scale':.095,'per_frame_body_fit':False,'surplus_source_row_column_policy':'At most one surplus row/column accepted without changing origin/scale; never resized to nominal canvas.'},'visual_approval_granted':False,'native_execution':False,'selected_for_build':False}
    write(SOURCE/'generation-ledger-v1.json',ledger)
    generation={'image_generation_used':True,'model':'not exposed by built-in tool','provider':'OpenAI built-in imagegen; pure painted2D single-pose masters','prompt':'Portable pose-prompts-v4.json and individual correction prompts; no atlas or3D source.','painted_master':rel(SOURCE/'grounded-standing-v1.png'),'painted_master_sha256':sha(SOURCE/'grounded-standing-v1.png'),'provenance':rel(SOURCE/'generation-ledger-v1.json'),'method':'One fixed whole-family uniform transform; no per-frame body fit or actor alpha threshold; painted contact shadows retained.'}
    base={'unit':UNIT,'production_status':'painted-master-complete-unapproved','status':'authored configuration','visual_approval_granted':False,'generation':generation,'credits':{'author':'Project-directed built-in imagegen; technical2D assembly','license':None,'redistribution':'unresolved; release prohibited'},'acceptance':'Candidate source/technical conversion only; independent pixel/motion/native/rights acceptance pending.'}
    groups=[];frame_map=[]
    for g,names in sorted(action['groups'].items(),key=lambda x:int(x[0])):
        frames=[]
        for i,n in enumerate(names):
            p=SOURCE/'native'/(n+'.png');im=Image.open(p).convert('RGBA');assert im.size==(450,400) and border(im)==0,(g,n)
            frames.append({'source':rel(p),'source_sha256':sha(p),'sha256':sha(p),'source_canvas':[450,400]})
            frame_map.append({'group':int(g),'index':i,'pose':n,'source':rel(p),'sha256':sha(p),'bbox':im.getbbox(),'border_alpha_max':border(im)})
        groups.append({'group':int(g),'frames':frames})
    manifest=json.loads((PROJECT/'assets/manifest.json').read_text())['assets']
    required=next(a['required_groups'] for a in manifest if a.get('unit')==UNIT and a['role']=='creature-battle-animation')
    actual={str(g['group']):len(g['frames']) for g in groups};assert all(actual.get(g,0)>=v for g,v in required.items())
    battle=dict(base,recipe_type='vcmi_animation',output_path=f'Content/Sprites/runeterra/shurima/creatures/{UNIT}/battle.json',canvas=[450,400],pivot={'x':218,'y':266},generateShadow=0,generateOverlay=1,groups=groups)
    write(RECIPES/'battle.json',battle)
    folder=SOURCE/'resources-v1';folder.mkdir(exist_ok=True)
    standing=Image.open(SOURCE/'grounded-standing-v1.png').convert('RGBA');contact=Image.open(SOURCE/'attack-front-contact-v2.png').convert('RGBA')
    map_root=(64,60);map_scale=.04
    resource={'map-000':assemble.native(standing,(96,64),map_root,map_scale),'attackRight':assemble.native(contact,(96,64),map_root,map_scale)}
    resource['attackLeft']=assemble.mirror(resource['attackRight'],map_root)
    portrait_box=(420,0,1300,900)
    for n,size in [('large',(58,64)),('small',(32,32))]:
        crop=standing.crop(portrait_box);s=min(size[0]/crop.width,size[1]/crop.height);dims=(round(crop.width*s),round(crop.height*s));view=crop.resize(dims,Image.Resampling.LANCZOS)
        im=Image.new('RGBA',size);im.paste(view,((size[0]-dims[0])//2,(size[1]-dims[1])//2));resource[n]=im
    for n,im in resource.items():im.save(folder/(n+'.png'),compress_level=9)
    conversion={'status':'authored configuration','standing_source':{'source':rel(SOURCE/'grounded-standing-v1.png'),'source_sha256':sha(SOURCE/'grounded-standing-v1.png')},'reaction_source':{'source':rel(SOURCE/'attack-front-contact-v2.png'),'source_sha256':sha(SOURCE/'attack-front-contact-v2.png')},'source_root':[640,1130],'adventure_canvas':[96,64],'adventure_root':list(map_root),'uniform_map_scale':map_scale,'per_pose_body_fit':False,'map_group0':'One standing frame allowed by current contract; no animated idle asserted.','portrait_fixed_source_crop':portrait_box,'portrait_method':'Uniform scale of same predefined rectangle plus transparent padding; no opaque body fit.','outputs':[{'source':rel(folder/(n+'.png')),'source_sha256':sha(folder/(n+'.png')),'canvas':list(im.size),'border_alpha_max':border(im)} for n,im in resource.items()],'visual_approval_granted':False}
    write(SOURCE/'resource-conversion-v1.json',conversion)
    for role in ['map','large','small','attackLeft','attackRight']:
        d=dict(base);d['generation']=dict(generation,provenance=rel(SOURCE/'resource-conversion-v1.json'));d['output_path']=f'Content/Sprites/runeterra/shurima/creatures/{UNIT}/'+role+('.json' if role=='map' else '.png')
        p=folder/('map-000.png' if role=='map' else role+'.png')
        if role=='map':d.update(recipe_type='vcmi_animation',canvas=[96,64],pivot={'x':64,'y':60},generateShadow=0,generateOverlay=1,groups=[{'group':0,'frames':[{'source':rel(p),'source_sha256':sha(p),'source_canvas':[96,64]}]}])
        else:d.update(recipe_type='raster',source=rel(p),source_sha256=sha(p),source_canvas=list(resource[role].size),size=list(resource[role].size),fit='exact',require_alpha=True)
        write(RECIPES/(role+'.json'),d)
    sys.path.insert(0,str(PROJECT.parent/'scripts'));import faction_art_compile
    compiler=faction_art_compile.create_compiler('shurima');runs=[];receipts=[];decoded=0
    for run in [1,2]:
        outputs_all={};proofs=[]
        for recipe in sorted(RECIPES.glob('*.json')):
            outputs,proof=compiler.plan(PROJECT,recipe);proofs.append(proof)
            assert not (outputs_all.keys()&outputs.keys()),'Duplicate compiler output';outputs_all.update(outputs)
        output_pins={}
        for n,data in sorted(outputs_all.items()):
            p=REPORT/UNIT/f'compiler-run{run}'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);output_pins[n]=hashlib.sha256(data).hexdigest()
        if run==1:
            receipts=proofs
            source_by_output={o['output_path']:o['source'] for proof in proofs for o in proof['outputs'] if o.get('source')}
            for n,data in outputs_all.items():
                if n.endswith('.png'):
                    im=Image.open(REPORT/UNIT/'compiler-run1'/n).convert('RGBA');src=Image.open(PROJECT/source_by_output[n]).convert('RGBA');assert im.size==src.size and im.tobytes()==src.tobytes();decoded+=1
        runs.append(output_pins)
    assert runs[0]==runs[1],'Real compiler nondeterminism'
    write(REPORT/UNIT/'compiler-receipts-v1.json',receipts)
    cell_w=197;cell_h=170
    for facing in ['right','left']:
        board=Image.new('RGBA',(cell_w*6,cell_h*len(groups)),(35,35,35,255));d=ImageDraw.Draw(board)
        for row,g in enumerate(groups):
            for col,desc in enumerate(g['frames']):
                im=Image.open(PROJECT/desc['source']).convert('RGBA')
                if facing=='left':im=assemble.mirror(im)
                crop=im.crop(assemble.ROI);bg=assemble.checker(crop.size);bg.alpha_composite(crop);board.paste(bg,(col*cell_w,row*cell_h+18));d.text((col*cell_w+2,row*cell_h+2),f"g{g['group']:02d} f{col}",fill='white')
        board.save(REPORT/UNIT/('battle-all-groups-'+facing+'-native1x.png'),compress_level=9)
    for g in groups:
        imgs=[]
        for desc in g['frames']:
            im=Image.open(PROJECT/desc['source']).convert('RGBA');pair=Image.new('RGBA',(382,150),(35,35,35,255))
            for col,frame in enumerate([im,assemble.mirror(im)]):
                crop=frame.crop(assemble.ROI);bg=assemble.checker(crop.size);bg.alpha_composite(crop);pair.paste(bg,(col*197,0))
            imgs.append(pair.convert('RGB'))
        imgs[0].save(REPORT/UNIT/f"g{g['group']:02d}-both-facing-motion.gif",save_all=True,append_images=imgs[1:],duration=160,loop=0,disposal=2)
    board=Image.new('RGBA',(420,270),(35,35,35,255));d=ImageDraw.Draw(board)
    for i,(n,im) in enumerate([('map-right',resource['map-000']),('map-left',assemble.mirror(resource['map-000'],map_root)),('attackLeft',resource['attackLeft']),('attackRight',resource['attackRight']),('large',resource['large']),('small',resource['small'])]):
        x=(i%3)*140;y=(i//3)*135;bg=assemble.checker(im.size);bg.alpha_composite(im);board.paste(bg,(x,y+22));d.text((x+2,y+2),n,fill='white')
    board.save(REPORT/UNIT/'remaining-five-resources-native1x.png',compress_level=9)
    assert sha(protected)==before
    proof={'status':'authored configuration','unit':UNIT,'resource_count':6,'native_frame_count':len(frame_map),'required_groups':required,'actual_groups':actual,'native_conversion_twice_byte_exact':first==second,'actual_shared_compiler_two_runs_byte_exact':runs[0]==runs[1],'compiled_files_per_run':len(runs[0]),'decoded_compiled_pngs_equal_native_inputs':decoded,'all_battle_native_borders_transparent':True,'map_reaction_border_alpha':{k:border(v) for k,v in resource.items() if k not in ['large','small']},'fixed_transform':ledger['fixed_transform'],'frame_map':frame_map,'output_hashes':runs[0],'recipe_pins':[{'source':rel(p),'source_sha256':sha(p)} for p in sorted(RECIPES.glob('*.json'))],'source_ledger_sha256':sha(SOURCE/'generation-ledger-v1.json'),'original_identity_preserved':before,'real_compiler_sha256':sha(PROJECT.parent/'scripts/faction_art_compile.py'),'cross_cell_contamination':'No atlases. One whole pose per master; native transparent borders checked. No other cell can be sampled.','open_visual_limits':action['open_visual_limits']+['Generated microdetail/proportions may vary across action keys; fixed transform forbids hidden fitting but does not establish anatomical continuity.','Sparse key timing and engine playback remain unverified.','Art/native/rights approval pending.'],'motion_review_timing_ms':160,'native_execution':False,'manifest_selected':False,'stage_written':False,'visual_approval_granted':False}
    write(REPORT/UNIT/'fullunit-technical-proof-v1.json',proof)
    print(json.dumps({'unit':UNIT,'frames':len(frame_map),'resources':6,'files':len(runs[0]),'decoded_equal':decoded,'two_runs_exact':runs[0]==runs[1],'map_edge':proof['map_reaction_border_alpha'],'proof_sha256':sha(REPORT/UNIT/'fullunit-technical-proof-v1.json')}))
if __name__=='__main__':main()
