"""Technical conversion of existing painted keys to remaining five native resources."""
from pathlib import Path
import json,hashlib,sys
from PIL import Image,ImageDraw
import assemble

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[4]
REPORT=PROJECT/'build/reports/painted-nomad-actions-20261023-v1'
RECIPES=PROJECT/'assets/recipes/creatures/painted-v2/desertNomad'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(PROJECT).as_posix()
def write(p,d):p.write_text(json.dumps(d,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def alpha_edge(im):
    a=im.getchannel('A');w,h=im.size
    return max(a.crop(b).getextrema()[1] for b in [(0,0,w,1),(0,h-1,w,h),(0,0,1,h),(w-1,0,w,h)])

def main():
    folder=SOURCE/'resources';folder.mkdir(exist_ok=True)
    standing=Image.open(SOURCE/'grounded-standing-v1.png').convert('RGBA')
    contact=Image.open(SOURCE/'attack-front-contact-v2.png').convert('RGBA')
    map_root=(64,61);map_scale=.04
    frames={'map-000':assemble.native(standing,(96,64),map_root,map_scale),'attackRight':assemble.native(contact,(96,64),map_root,map_scale)}
    frames['attackLeft']=assemble.mirror(frames['attackRight'],map_root)
    portrait_box=(280,0,1000,800)
    for name,size in [('large',(58,64)),('small',(32,32))]:
        crop=standing.crop(portrait_box);scale=min(size[0]/crop.width,size[1]/crop.height)
        dims=(round(crop.width*scale),round(crop.height*scale));view=crop.resize(dims,Image.Resampling.LANCZOS)
        out=Image.new('RGBA',size);out.paste(view,((size[0]-dims[0])//2,(size[1]-dims[1])//2));frames[name]=out
    for name,im in frames.items():im.save(folder/(name+'.png'),compress_level=9)
    record={'status':'authored configuration','source_root':[640,1070],'adventure_canvas':[96,64],'adventure_root':list(map_root),'uniform_map_scale':map_scale,'per_pose_body_fit':False,'map_group0':'One actual standing frame, allowed current consumer contract; no fake animated idle asserted.','reaction_source':{'source':rel(SOURCE/'attack-front-contact-v2.png'),'source_sha256':sha(SOURCE/'attack-front-contact-v2.png')},'standing_source':{'source':rel(SOURCE/'grounded-standing-v1.png'),'source_sha256':sha(SOURCE/'grounded-standing-v1.png')},'portrait_fixed_source_crop':list(portrait_box),'portrait_fit':'Uniform scale of fixed predefined crop, centered transparent padding; no opaque-body fitting.','technical_producer':{'source':rel(Path(__file__).resolve()),'source_sha256':sha(Path(__file__).resolve())},'outputs':[{'source':rel(folder/(name+'.png')),'source_sha256':sha(folder/(name+'.png')),'source_canvas':list(im.size),'border_alpha_max':alpha_edge(im)} for name,im in frames.items()],'visual_approval_granted':False,'native_execution':False}
    write(SOURCE/'resource-conversion-v1.json',record)
    base=json.loads((RECIPES/'battle.json').read_text())
    for role in ['map','large','small','attackLeft','attackRight']:
        generation=dict(base['generation']);generation['provenance']=rel(SOURCE/'resource-conversion-v1.json')
        d={k:base[k] for k in ['unit','production_status','status','visual_approval_granted','credits','acceptance']};d['generation']=generation
        d['output_path']='Content/Sprites/runeterra/shurima/creatures/desertNomad/'+role+('.json' if role=='map' else '.png')
        if role=='map':
            f=folder/'map-000.png';d.update({'recipe_type':'vcmi_animation','canvas':[96,64],'pivot':{'x':64,'y':61},'generateShadow':0,'generateOverlay':1,'groups':[{'group':0,'frames':[{'source':rel(f),'source_sha256':sha(f),'source_canvas':[96,64]}]}]})
        else:
            f=folder/(role+'.png');d.update({'recipe_type':'raster','source':rel(f),'source_sha256':sha(f),'source_canvas':list(frames[role].size),'size':list(frames[role].size),'fit':'exact','require_alpha':True})
        write(RECIPES/(role+'.json'),d)
    sys.path.insert(0,str(PROJECT.parent/'scripts'));import faction_art_compile
    c=faction_art_compile.create_compiler('shurima');runs=[];receipts=[]
    for run in [1,2]:
        pins={}
        for recipe in sorted(RECIPES.glob('*.json')):
            outputs,proof=c.plan(PROJECT,recipe)
            if run==1:receipts.append(proof)
            for name,data in outputs.items():
                dest=REPORT/f'fullunit-compiler-run{run}'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);pins[name]=hashlib.sha256(data).hexdigest()
        runs.append(pins)
    assert runs[0]==runs[1]
    board=Image.new('RGBA',(420,270),(35,35,35,255));d=ImageDraw.Draw(board)
    display=[('map-right',frames['map-000']),('map-left',assemble.mirror(frames['map-000'],map_root)),('attackLeft',frames['attackLeft']),('attackRight',frames['attackRight']),('large',frames['large']),('small',frames['small'])]
    for i,(name,im) in enumerate(display):
        x=(i%3)*140;y=(i//3)*135;bg=assemble.checker(im.size);bg.alpha_composite(im);board.paste(bg,(x,y+22));d.text((x+2,y+2),name,fill='white')
    board.save(REPORT/'remaining-five-resources-native1x.png',compress_level=9)
    write(REPORT/'fullunit-compiler-receipts-v1.json',receipts)
    write(REPORT/'fullunit-six-resource-proof-v1.json',{'status':'authored configuration','resource_count':6,'compiled_files_per_run':len(runs[0]),'actual_shared_compiler_two_runs_byte_exact':runs[0]==runs[1],'recipe_pins':[{'source':rel(f),'source_sha256':sha(f)} for f in sorted(RECIPES.glob('*.json'))],'output_hashes':runs[0],'source_conversion':record,'map_and_reaction_border_alpha':{k:alpha_edge(v) for k,v in frames.items() if k not in ['large','small']},'portrait_edge_note':'Bust crop intentionally continues to edge; transparent canvas padding where crop aspect differs.','native_execution':False,'manifest_selected':False,'visual_approval_granted':False})
    print(json.dumps({'recipes':6,'compiled_files_per_run':len(runs[0]),'deterministic':runs[0]==runs[1],'map_reaction_border_alpha':{k:alpha_edge(v) for k,v in frames.items() if k not in ['large','small']},'proof_sha256':sha(REPORT/'fullunit-six-resource-proof-v1.json')}))

if __name__=='__main__':main()
