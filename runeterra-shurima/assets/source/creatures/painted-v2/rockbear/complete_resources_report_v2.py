"""Reused painted-Nomad six-resource pattern; direct shared plan, report output only."""
from pathlib import Path
from PIL import Image,ImageDraw
import argparse,hashlib,json,subprocess,sys
import assemble_keys as assembly
sys.dont_write_bytecode=True
SOURCE=Path(__file__).resolve().parent;PROJECT=SOURCE.parents[4]
REPORT=PROJECT/'build/reports/painted-rockbear-actions-20261023-v1'
POSE_KEYS=['standing-v2','walk-contact-a-v1','walk-down-a-v1','walk-passing-a-v1','walk-contact-b-v1','walk-down-b-v1','walk-passing-b-v2','fidget-look-v1','hit-recoil-v1','defend-brace-v1','death-buckle-v1','death-fall-v1','death-corpse-v1','turn-quarter-v1','turn-front-v1','attack-preparation-v1','attack-up-contact-v1','attack-front-contact-v1','attack-down-contact-v1','attack-recovery-v1']
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def rel(path):return path.relative_to(PROJECT).as_posix()
def write(path,value):path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def main():
 parser=argparse.ArgumentParser();parser.add_argument('unit',choices=('rockbear','elderRockbear'));parser.add_argument('--passing-b',default='walk-passing-b-v2');args=parser.parse_args()
 unit=args.unit;directory=SOURCE.parent/unit;recipes=REPORT/'recipe-payload'/unit
 recipes.mkdir(parents=True,exist_ok=True)
 if any(recipes.iterdir()):raise ValueError('Preserve existing report recipe payload; choose a new version before replay')
 keys=[args.passing_b if k=='walk-passing-b-v2' else k for k in POSE_KEYS]
 assert len(set(keys))==20 and all((directory/(k+'.png')).is_file() for k in keys)
 run=subprocess.run([sys.executable,'-B',str(SOURCE/'assemble_keys.py'),unit,'--label','all-keys-native1x-v1',*keys],cwd=PROJECT.parent,capture_output=True,text=True,encoding='utf-8')
 (REPORT/(unit+'-assembly-v1.log')).write_text(run.stdout+run.stderr,encoding='utf-8');assert run.returncode==0,run.stderr
 stand='standing-v2';recovery='attack-recovery-v1';prep='attack-preparation-v1'
 groups={0:keys[1:7],1:[stand,'fidget-look-v1',stand],2:[stand],3:[stand,'hit-recoil-v1',stand],4:[stand,'defend-brace-v1',stand],5:[stand,'death-buckle-v1','death-fall-v1','death-corpse-v1'],7:[stand,'turn-quarter-v1','turn-front-v1'],8:['turn-front-v1-left','turn-quarter-v1',stand],11:[stand,prep,'attack-up-contact-v1',recovery,stand],12:[stand,prep,'attack-front-contact-v1',recovery,stand],13:[stand,prep,'attack-down-contact-v1',recovery,stand]}
 def frame(key):
  path=directory/'native'/(key+'.png');return {'source':rel(path),'source_sha256':sha(path),'sha256':sha(path),'source_canvas':[450,400]}
 base={'status':'authored configuration','production_status':'painted-master-complete-unapproved','visual_approval_granted':False,'unit':unit,'credits':{'author':'Project-directed OpenAI built-in imagegen paintings; deterministic technical2D assembly','license':None,'redistribution':'unresolved; release prohibited'},'generation':{'image_generation_used':True,'provider':'OpenAI built-in imagegen; original independently painted action keys','model':'not exposed by built-in tool','painted_master':rel(directory/'standing-v2.png'),'painted_master_sha256':sha(directory/'standing-v2.png'),'provenance':rel(directory/'generation-ledger-v1.json'),'method':'One shared logical2048x1152 canvas, uniform full-canvas resolution normalization, fixed cohort scale/root; no per-frame opaque-bbox crop, recenter or fit. Painted shadows retained.','prompt':'Individual portable *-prompt-v1.txt/v2.txt and pose-prompts-v1.json in own source leaf; one animal pose per image, no3D or atlas.'},'acceptance':'Painted source candidate, native visual/motion/identity/rights approval and runtime acceptance pending.'}
 prefix='Content/Sprites/runeterra/shurima/creatures/'+unit+'/'
 battle=dict(base,recipe_type='vcmi_animation',canvas=[450,400],pivot={'x':218,'y':266},generateShadow=0,generateOverlay=1,output_path=prefix+'battle.json',groups=[{'group':g,'frames':[frame(k) for k in group]} for g,group in groups.items()])
 write(recipes/'battle.json',battle)
 write(directory/'action-map-v1.json',{'status':'authored configuration','groups':groups,'gait_supports':'Six actually painted limb-support phases; no still translation or flat-image rotation as new keys.','boundary_reuse':'Actual holding reused only at genuine preparation/recovery boundaries; counts are not independent image-generation claims.','turn_join':'Engine changes facing after group7; group8 begins with technically mirrored frontal master so displayed raw frontal boundary remains identical.','logical_canvas':[2048,1152],'source_root':[1037,992],'native_canvas':[450,400],'native_root':[218,266],'uniform_scale':.075,'per_frame_body_fit':False,'selected_for_build':False,'visual_approval_granted':False})
 resources=directory/'resources-v1';resources.mkdir(exist_ok=True)
 standing=Image.open(directory/'standing-v2.png').convert('RGBA');contact=Image.open(directory/'attack-front-contact-v1.png').convert('RGBA')
 map_root=(64,60);map_scale=.032
 frames={'map-000':assembly.native(standing,(96,64),map_root,map_scale),'attackRight':assembly.native(contact,(96,64),map_root,map_scale)}
 frames['attackLeft']=assembly.mirror(frames['attackRight'],map_root)
 # Fixed declared head/shoulder crop in logical canvas coordinates, not a pose bbox.
 portrait=(1250,380,1970,1000);factor=standing.width/2048
 crop=standing.crop(tuple(round(v*factor) for v in portrait))
 for name,size in (('large',(58,64)),('small',(32,32))):
  scale=min(size[0]/crop.width,size[1]/crop.height);dims=(round(crop.width*scale),round(crop.height*scale));view=crop.resize(dims,Image.Resampling.LANCZOS);out=Image.new('RGBA',size);out.paste(view,((size[0]-dims[0])//2,(size[1]-dims[1])//2));frames[name]=out
 for name,image in frames.items():image.save(resources/(name+'.png'),compress_level=9)
 conversion={'status':'authored configuration','logical_source_canvas':[2048,1152],'source_root':[1037,992],'adventure_canvas':[96,64],'adventure_root':map_root,'uniform_map_scale':map_scale,'portrait_fixed_logical_crop':portrait,'per_pose_body_fit':False,'technical_producer':{'source':rel(Path(__file__).resolve()),'source_sha256':sha(Path(__file__).resolve())},'assembly_source':{'source':rel(SOURCE/'assemble_keys.py'),'source_sha256':sha(SOURCE/'assemble_keys.py')},'outputs':[{'source':rel(resources/(name+'.png')),'source_sha256':sha(resources/(name+'.png')),'size':list(image.size),'border_alpha_max':assembly.alpha_edge(image)} for name,image in frames.items()],'native_execution':False,'visual_approval_granted':False}
 write(directory/'resource-conversion-v1.json',conversion)
 for role in ('map','large','small','attackLeft','attackRight'):
  recipe=dict(base);recipe['generation']=dict(base['generation'],provenance=rel(directory/'resource-conversion-v1.json'));recipe['output_path']=prefix+role+('.json' if role=='map' else '.png')
  if role=='map':
   path=resources/'map-000.png';recipe.update(recipe_type='vcmi_animation',canvas=[96,64],pivot={'x':64,'y':60},generateShadow=0,generateOverlay=1,groups=[{'group':0,'frames':[{'source':rel(path),'source_sha256':sha(path),'source_canvas':[96,64]}]}])
  else:
   path=resources/(role+'.png');recipe.update(recipe_type='raster',source=rel(path),source_sha256=sha(path),source_canvas=list(frames[role].size),size=list(frames[role].size),fit='exact',require_alpha=True)
  write(recipes/(role+'.json'),recipe)
 assert len(list(recipes.glob('*.json')))==6
 manifest=json.loads((PROJECT/'assets/manifest.json').read_text());requirements=next(row['required_groups'] for row in manifest['assets'] if row.get('unit')==unit and row.get('role')=='creature-battle-animation')
 assert set(map(int,requirements))==set(groups) and all(len(groups[int(g)])>=n for g,n in requirements.items())
 sys.path.insert(0,str(PROJECT.parent/'scripts'));import faction_art_compile
 compiler=faction_art_compile.create_compiler('shurima');runs=[];receipts=[]
 for number in (1,2):
  pins={}
  for path in sorted(recipes.glob('*.json')):
   outputs,proof=compiler.plan(PROJECT,path)
   if number==1:receipts.append(proof)
   for name,data in outputs.items():
    target=REPORT/(unit+'-compiler-run'+str(number))/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data);pins[name]=hashlib.sha256(data).hexdigest()
  runs.append(pins)
 assert runs[0]==runs[1]
 write(REPORT/(unit+'-compiler-receipts-v1.json'),receipts)
 board=Image.new('RGBA',(420,270),(35,35,35,255));draw=ImageDraw.Draw(board)
 display=[('map-right',frames['map-000']),('map-left',assembly.mirror(frames['map-000'],map_root)),('attackLeft',frames['attackLeft']),('attackRight',frames['attackRight']),('large',frames['large']),('small',frames['small'])]
 for i,(name,image) in enumerate(display):
  x=(i%3)*140;y=(i//3)*135;bg=assembly.checker(image.size);bg.alpha_composite(image);board.paste(bg,(x,y+22));draw.text((x+2,y+2),name,fill='white')
 board.save(REPORT/(unit+'-remaining-five-native1x.png'))
 write(REPORT/(unit+'-six-resource-proof-v1.json'),{'status':'authored configuration','resource_count':6,'group_counts':{g:len(v) for g,v in groups.items()},'actual_manifest_required_groups':requirements,'independent_painted_keys_consumed':20,'actual_shared_plan_twice_byte_exact':True,'compiled_files_per_run':len(runs[0]),'output_hashes':runs[0],'recipe_pins':{rel(p):sha(p) for p in sorted(recipes.glob('*.json'))},'map_reaction_border_alpha':{k:assembly.alpha_edge(v) for k,v in frames.items() if k not in ('large','small')},'portrait_edge_note':'Fixed intentional portrait bust crop; not an action body fitting.','conversion':conversion,'native_execution':False,'selected_for_build':False,'visual_approval_granted':False})
 print(json.dumps({'unit':unit,'resources':6,'groups':len(groups),'frames':sum(map(len,groups.values())),'independent_keys':20,'compiled_files_per_run':len(runs[0]),'byte_exact_two_shared_plans':True}))
if __name__=='__main__':main()
