"""Assemble painted candidates twice and run the unchanged real shared compiler privately."""
from pathlib import Path
import hashlib, json, sys, io
from PIL import Image, ImageDraw
import assemble

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[4]
REPORT=PROJECT/'build/reports/painted-nomad-actions-20261023-v1'
RECIPES=PROJECT/'assets/recipes/creatures/painted-v2/desertNomad'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(PROJECT).as_posix()
def write(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def border(im):
    a=im.getchannel('A');w,h=im.size
    return max(a.crop(b).getextrema()[1] for b in [(0,0,w,1),(0,h-1,w,h),(0,0,1,h),(w-1,0,w,h)])
def stable_native_pins():
    return {f.name:sha(f) for f in sorted((SOURCE/'native').glob('*.png'))}

def main():
    action=json.loads((SOURCE/'action-map-v2.json').read_text())
    original=PROJECT/'assets/source/creatures/painted-v1/desertNomad-standing-master-v1.png'
    protected_before=sha(original)
    assemble.main(); first=stable_native_pins()
    assemble.main(); second=stable_native_pins()
    assert first==second, 'Native conversion nondeterministic'
    chosen=sorted(set(n.removesuffix('-left') for names in action['groups'].values() for n in names))
    for name in chosen:
        im=Image.open(SOURCE/(name+'.png'))
        assert im.size in [(1330,1182),(1331,1182)], (name,im.size)
    receipt=REPORT/'generation-tool-receipts-v2.json'
    masters=[]
    for f in sorted(SOURCE.glob('*-v*.png')):
        im=Image.open(f)
        masters.append({'source':rel(f),'source_sha256':sha(f),'source_canvas':list(im.size),'used_as_action_key':f.stem in chosen,'status':'authored configuration','image_metadata_keys':sorted(im.info)})
    source_ledger={'status':'authored configuration','provider':'OpenAI built-in imagegen','model':'not exposed by built-in tool','derived_from_blender':False,'original_identity':{'source':rel(original),'source_sha256':protected_before},'private_tool_receipt_sha256':sha(receipt),'painted_sources':masters,'prompt_sources':[{'source':rel(f),'source_sha256':sha(f)} for f in sorted(SOURCE.glob('*prompt*')) if f.is_file()],'technical_producers':[{'source':rel(f),'source_sha256':sha(f)} for f in [SOURCE/'assemble.py',SOURCE/'finalize.py']],'uniform_source_to_native':{'scale':.074,'source_root':[640,1070],'native_root':[193,266],'canvas':[450,400],'per_frame_body_fit':False,'source_canvas_policy':'1330x1182;1331x1182 accepted with identical origin/scale, surplus transparent right column neither recentered nor stretched'},'visual_approval_granted':False,'native_execution':False,'selected_for_build':False}
    write(SOURCE/'generation-ledger-v1.json',source_ledger)
    groups=[]; frame_map=[]
    for g,names in sorted(action['groups'].items(),key=lambda item:int(item[0])):
        frames=[]
        for index,name in enumerate(names):
            f=SOURCE/'native'/(name+'.png');im=Image.open(f).convert('RGBA')
            assert im.size==(450,400) and border(im)==0
            frames.append({'source':rel(f),'source_sha256':sha(f),'sha256':sha(f),'source_canvas':[450,400]})
            frame_map.append({'group':int(g),'index':index,'pose':name,'source':rel(f),'sha256':sha(f),'bbox':im.getbbox(),'border_alpha_max':border(im)})
        groups.append({'group':int(g),'frames':frames})
    manifest=json.loads((PROJECT/'assets/manifest.json').read_text())['assets']
    required=next(a['required_groups'] for a in manifest if a.get('unit')=='desertNomad' and a['role']=='creature-battle-animation')
    actual={str(g['group']):len(g['frames']) for g in groups}
    assert all(actual.get(g,0)>=minimum for g,minimum in required.items()),(actual,required)
    recipe={'recipe_type':'vcmi_animation','unit':'desertNomad','output_path':'Content/Sprites/runeterra/shurima/creatures/desertNomad/battle.json','canvas':[450,400],'pivot':{'x':193,'y':266},'generateShadow':0,'generateOverlay':1,'production_status':'painted-master-complete-unapproved','status':'authored configuration','visual_approval_granted':False,'generation':{'image_generation_used':True,'model':'not exposed by built-in tool','provider':'OpenAI built-in imagegen; independent pure painted2D action masters','prompt':'See portable pose-prompts-v1.json, repair-prompts-v2/v3.json, walk-transfer-prompts-v1.json and single-key prompts; one pose per generated image. No3D source or image atlas.','painted_master':rel(SOURCE/'grounded-standing-v1.png'),'painted_master_sha256':sha(SOURCE/'grounded-standing-v1.png'),'provenance':rel(SOURCE/'generation-ledger-v1.json'),'method':'One fixed uniform transform; no per-frame crop/body fit/alpha threshold. Existing generated painted shadows retained.'},'credits':{'author':'Project-directed built-in imagegen; technical2D assembly','license':None,'redistribution':'unresolved; release prohibited'},'acceptance':'Candidate battle action source only; gait continuity and native visual review remain pending. No art/native/rights approval.','groups':groups}
    recipe_path=RECIPES/'battle.json';write(recipe_path,recipe)
    sys.path.insert(0,str(PROJECT.parent/'scripts'))
    import faction_art_compile
    compiler=faction_art_compile.create_compiler('shurima')
    runs=[]
    for run in [1,2]:
        outputs,proof=compiler.plan(PROJECT,recipe_path)
        pins={}
        for name,data in sorted(outputs.items()):
            path=REPORT/('compiler-run-'+str(run))/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data);pins[name]=hashlib.sha256(data).hexdigest()
        write(REPORT/('compiler-run-'+str(run)+'-receipt.json'),proof);runs.append(pins)
    assert runs[0]==runs[1], 'Real compiler outputs nondeterministic'
    source_by_output={r['output_path']:r for r in proof['outputs'] if r.get('source')}
    decoded=0
    for name in runs[0]:
        if name.endswith('.png'):
            a=Image.open(REPORT/'compiler-run-1'/name).convert('RGBA');b=Image.open(PROJECT/source_by_output[name]['source']).convert('RGBA')
            assert a.size==b.size and a.tobytes()==b.tobytes();decoded+=1
    cell_w=145;cell_h=135
    for facing in ['right','left']:
        board=Image.new('RGBA',(cell_w*6,cell_h*len(groups)),(35,35,35,255));d=ImageDraw.Draw(board)
        for row,g in enumerate(groups):
            for col,desc in enumerate(g['frames']):
                im=Image.open(PROJECT/desc['source']).convert('RGBA')
                if facing=='left':im=assemble.mirror(im)
                crop=im.crop(assemble.ROI);bg=assemble.checker(crop.size);bg.alpha_composite(crop);board.paste(bg,(col*cell_w,row*cell_h+18));d.text((col*cell_w+2,row*cell_h+2),f"g{g['group']:02d} f{col}",fill='white')
        board.save(REPORT/('battle-all-groups-'+facing+'-native1x.png'),compress_level=9)
    motion=[]
    for g in groups:
        imgs=[]
        for desc in g['frames']:
            im=Image.open(PROJECT/desc['source']).convert('RGBA');pair=Image.new('RGBA',(282,115),(35,35,35,255))
            for col,frame in enumerate([im,assemble.mirror(im)]):
                crop=frame.crop(assemble.ROI);bg=assemble.checker(crop.size);bg.alpha_composite(crop);pair.paste(bg,(col*147,0))
            imgs.append(pair.convert('RGB'))
        durations=[160]*len(imgs)
        imgs[0].save(REPORT/(f"g{g['group']:02d}-both-facing-motion.gif"),save_all=True,append_images=imgs[1:],duration=durations,loop=0,disposal=2)
        motion.append({'group':g['group'],'frames':len(imgs),'duration_ms':durations,'note':'review timing only; native engine uses current content attack/walk/idle timings'})
    assert sha(original)==protected_before
    write(REPORT/'technical-assembly-v1.json',{'status':'authored configuration','scope':'battle source candidate only; map/portraits not authored by this batch','source_masters':len(masters),'unique_consumed_painted_action_masters':len(chosen),'required_groups':required,'actual_groups':actual,'native_frame_count':len(frame_map),'compiler_output_files_per_run':len(runs[0]),'actual_real_compiler':'scripts/faction_art_compile.py:create_compiler(shurima).plan','compiler_sha256':sha(PROJECT.parent/'scripts/faction_art_compile.py'),'two_native_conversion_runs_byte_exact':first==second,'two_real_compiler_runs_byte_exact':runs[0]==runs[1],'decoded_compiled_pngs_equal_native_inputs':decoded,'all_compiled_frame_borders_transparent':True,'source_roots':[640,1070],'native_roots':[193,266],'fixed_uniform_scale':.074,'per_frame_body_fit':False,'cross_cell_contamination':'No atlases: each source contains one pose and each technical frame conversion reads exactly one whole master. Native transparent border checked.','original_painted_identity_unchanged':protected_before,'recipe':{'source':rel(recipe_path),'source_sha256':sha(recipe_path)},'source_ledger_sha256':sha(SOURCE/'generation-ledger-v1.json'),'frame_map':frame_map,'output_hashes':runs[0],'motion':motion,'visual_approval_granted':False,'native_execution':False,'manifest_selected':False,'stage_written':False,'open_visual_limits':['Sparse key timing and gait transition continuity require independent native1x visual review.','Opposite leg support keys improved; do not infer acceptance from frame counts.','Generated facial/cloth microdetail varies between poses; fixed transform prevents technical size fitting but does not prove anatomical size is perfectly consistent.','Root/art/native/rights acceptance remains pending.']})
    print(json.dumps({'frame_count':len(frame_map),'groups':actual,'native_conversion_twice_exact':first==second,'real_compiler_twice_exact':runs[0]==runs[1],'compiled_files':len(runs[0]),'decoded_equal':decoded,'recipe_sha256':sha(recipe_path),'technical_receipt_sha256':sha(REPORT/'technical-assembly-v1.json')}))

if __name__=='__main__':main()
