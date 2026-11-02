"""Keep genuine selected art; correct actual native animation/resource semantics."""
from pathlib import Path
from PIL import Image,ImageOps
import copy,json,hashlib,sys
import assemble_packets as common
SOURCE=common.SOURCE;PROJECT=common.PROJECT;REPORT=common.REPORT
EXISTING=['desertNomad','sandWarrior','shurimanArcher','sunPriest','highPriest','sandstoneChimera','gildedChimera']
def existing(unit):
 manifest=json.loads((PROJECT/'assets/manifest.json').read_text());records=[a for a in manifest['assets'] if a.get('unit')==unit and 'projectile' not in a.get('role','')]
 recipes=SOURCE/'recipe-payload'/unit;recipes.mkdir(parents=True,exist_ok=True)
 before=[]
 for row in records:
  old=PROJECT/row['source']['recipe_path'];recipe=json.loads(old.read_text());before.append(common.descriptor(old))
  role=Path(recipe['output_path']).stem
  if role=='battle':
   groups={r['group']:r['frames'] for r in recipe['groups']}
   for g in (11,12,13):
    seq=groups[g]
    if len(seq)==5:groups[g]=[seq[0],seq[1],seq[2],seq[2],seq[3],seq[4]]
   groups[22]=[copy.deepcopy(groups[5][-1])]
   if 20 not in groups:groups[20]=[copy.deepcopy(groups[2][0]),copy.deepcopy(groups[0][0])]
   if 21 not in groups:groups[21]=[copy.deepcopy(groups[0][-1]),copy.deepcopy(groups[2][0])]
   groups={g:[copy.deepcopy(frame) for frame in seq] for g,seq in groups.items()}
   for g,seq in groups.items():
    for i,frame in enumerate(seq):frame['frame']=i
   recipe['groups']=[{'group':g,'frames':seq} for g,seq in sorted(groups.items())]
  elif role in ('attackLeft','attackRight'):
   im=Image.open(PROJECT/recipe['source']).convert('RGBA')
   if im.size!=(96,64):raise ValueError('Inspect distinct existing encounter canvas first')
   # Existing generated right action is mislabeled attackRight. Actual native FromLeft is RIGHT.
   source_name='attackRight' if role=='attackLeft' else 'attackLeft'
   opposite=next(a for a in records if Path(a['output_path']).stem==source_name)
   old_other=json.loads((PROJECT/opposite['source']['recipe_path']).read_text())
   image=Image.open(PROJECT/old_other['source']).convert('RGBA').crop((32,0,96,64))
   dest=SOURCE/unit/'resources'/(role+'.png');common.png(dest,image)
   recipe.update(common.descriptor(dest),size=[64,64],fit='exact',require_alpha=True)
  common.put(recipes/(role+'.json'),recipe)
 sys.path.insert(0,str(PROJECT.parent/'scripts'));import faction_art_compile
 compiler=faction_art_compile.create_compiler('shurima');runs=[]
 for run in (1,2):
  pins={}
  for p in sorted(recipes.glob('*.json')):
   outputs,receipt=compiler.plan(PROJECT,p)
   for name,data in outputs.items():
    pins[name]=hashlib.sha256(data).hexdigest()
    if run==1:
     dest=REPORT/'compiled'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
  runs.append(pins)
 assert runs[0]==runs[1]
 result={'status':'authored configuration','unit':unit,'retained_selected_recipe_pins':before,'actual_shared_compiler_runs':2,'two_runs_byte_exact':True,'resource_count':len(list(recipes.glob('*.json'))),'outputs':runs[0],'semantic_repairs':['DEAD22 exact terminal DEATH5 corpse','five-frame melee contact retained at native HIT index3/6','existing fly takeoff/landing groups preserved','actual encounter selector facing and64x64 canvas'],'visual_approval_granted':False,'native_execution':False}
 common.put(REPORT/unit/'existing-repair-proof-v1.json',result)
 return {'unit':unit,'resources':result['resource_count'],'physical_outputs':len(runs[0])}
def projectile(family,units):
 master=SOURCE/('projectile-'+family+'-raw.png');im=Image.open(master).convert('RGBA');bbox=im.getchannel('A').point(lambda a:255 if a>=16 else 0).getbbox();crop=im.crop(bbox)
 if family=='arrow':ratio=26/crop.width
 else:ratio=5/max(crop.size)
 size=(max(1,round(crop.width*ratio)),max(1,round(crop.height*ratio)));small=crop.resize(size,Image.Resampling.LANCZOS)
 center=Image.new('RGBA',(40,40));center.paste(small,((40-size[0])//2,(40-size[1])//2))
 frames=[]
 for angle in (90,45,0,-45,-90):
  out=center.rotate(angle,resample=Image.Resampling.BICUBIC) if family=='arrow' else center.copy()
  dest=SOURCE/'projectiles'/family/(str(angle)+'.png');common.png(dest,out);frames.append(common.descriptor(dest))
 provenance=SOURCE/'projectiles'/family/'conversion-v1.json';common.put(provenance,{'status':'authored configuration','master':common.descriptor(master),'prompt':common.descriptor(SOURCE/('projectile-'+family+'-prompt.txt')),'technical_producer':common.descriptor(Path(__file__)),'source_crop':bbox,'common_uniform_scale':ratio,'native_center':[20,20],'canvas':[40,40],'headings':[90,45,0,-45,-90],'angular_frames_are_not_temporal_actions':True,'shared_physical_projectile_for_base_and_upgrade':list(units),'provider':'OpenAI built-in imagegen','model':'not exposed by tool','native_execution':False,'visual_approval_granted':False})
 sys.path.insert(0,str(PROJECT.parent/'scripts'));import faction_art_compile
 compiler=faction_art_compile.create_compiler('shurima');result=[]
 for unit in units:
  recipe={'status':'authored configuration','production_status':'painted-master-complete-unapproved','unit':unit,'recipe_type':'vcmi_animation','canvas':[40,40],'pivot':{'x':20,'y':20},'generateShadow':0,'generateOverlay':0,'output_path':'Content/Sprites/runeterra/shurima/projectiles/'+unit+'.json','groups':[{'group':0,'frames':frames}],
   'generation':{'image_generation_used':True,'provider':'OpenAI built-in imagegen','model':'not exposed by tool','painted_master':common.rel(master),'painted_master_sha256':common.sha(master),'provenance':common.rel(provenance),'method':'Original painted physical projectile; fixed technical downsample and staticheading rotation.','prompt':'Portable projectile-'+family+'-prompt.txt'},'credits':{'author':'Project-directed OpenAI imagegen','license':None,'redistribution':'unresolved; release prohibited'},'visual_approval_granted':False,'acceptance':'Physical projectile headings only. Native both-facing release origin/climax remains pending.'}
  path=SOURCE/'recipe-payload/projectiles'/(unit+'.json');common.put(path,recipe);runs=[]
  for run in (1,2):
   outputs,receipt=compiler.plan(PROJECT,path);runs.append({n:hashlib.sha256(b).hexdigest() for n,b in outputs.items()})
   if run==1:
    for name,data in outputs.items():
     dest=REPORT/'compiled'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
  assert runs[0]==runs[1];result.append({'unit':unit,'recipe':common.descriptor(path),'actual_two_shared_compiler_runs_byte_exact':True,'outputs':runs[0]})
 common.put(REPORT/('projectile-'+family+'-proof-v1.json'),result);return result
if __name__=='__main__':
 if '--projectiles' in sys.argv:print(json.dumps(projectile('arrow',['shurimanArcher','sunArcher'])+projectile('pellet',['sunPriest','highPriest'])))
 else:print(json.dumps([existing(u) for u in EXISTING]))
