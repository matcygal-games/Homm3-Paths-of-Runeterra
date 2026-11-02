"""Actual native compiler twice; candidate only, no active outputs."""
from candidate_support import *
sys.path.insert(0,str(ROOT/"scripts"))
from faction_art_compile import create_compiler
def compile_one(slug):
 project=ROOT/('runeterra-'+slug);out=source(slug);prefix=f'Content/Sprites/runeterra/{slug}/';src=out.relative_to(project).as_posix()
 frames=read(out/'candidate-frames.json');recipes=out/'candidate-recipes';recipes.mkdir(exist_ok=True)
 compiler=create_compiler(slug)
 def generation(p):
  return {'image_generation_used':True,'workflow':'image-based-painted-2d','derived_from_blender':False,
   'model':'Not exposed by built-in tool','provider':'OpenAI built-in image_gen',
   'prompt':'Approved full-town design, genuine painted early/intermediate construction edits, and painted empty-terrain recovery; technical exact-pixel silhouette slicing, opaque bodies and proportional UI crops. See pinned generation-ledger.json.',
   'painted_master':src+'/'+p.name,'painted_master_sha256':sha(p),'source_generation_ledger':src+'/generation-ledger.json','source_generation_ledger_sha256':sha(out/'generation-ledger.json')}
 def common(master):return {'production_status':'painted-master-complete-unapproved','generation':generation(master),
  'visual_approval_granted':False,'credits':{'author':'Project-directed original painted2D via OpenAI image_gen; technical approved-composition decomposition','license':None,'redistribution':'Unresolved; no release approval'}}
 def raster(p,name,role):
  size=list(Image.open(p).size);return {**common(out/'approved-full-raw.png'),'recipe_type':'raster','output_path':prefix+name,'role':role,
   'canvas':size,'source_canvas':size,'source':p.relative_to(project).as_posix(),'source_sha256':sha(p),'fit':'exact'}
 packet=[]
 def put(name,r):p=recipes/(name+'.json');dump(p,r);packet.append(p)
 put('background',raster(out/'background-native.png','town/background.png','town-background'))
 for state,row in sorted(frames['states'].items()):
  p=out/row['frame']['path'];master=out/('approved-full-raw.png'if row['source_tag']=='approved'else row['source_tag']+'-states-raw.png')
  put(state,{**common(master),'recipe_type':'vcmi_animation','output_path':prefix+'town/structures/'+state+'.json','role':'town-structure-animation',
   'canvas':[800,374],'pivot':{'x':0,'y':0,'basis':'Full native canvas; exact approved registration in pixels'},'generateShadow':0,'generateOverlay':0,
   'groups':[{'group':0,'frames':[{'source':p.relative_to(project).as_posix(),'sha256':sha(p),'source_canvas':[800,374]}]}]})
  for suffix in ('area','border','campaign'):
   put(state+'_'+suffix,raster(out/'derived'/(state+'_'+suffix+'.png'),'town/structures/'+state+'_'+suffix+'.png','town-structure-'+suffix))
 ids=compiler.indexed_building_ids(project)
 put('buildingIcons',{**common(out/'approved-full-raw.png'),'recipe_type':'indexed_animation','output_path':prefix+'town/buildingIcons.json',
  'role':'town-construction-icons','canvas':[150,70],'pivot':{'x':0,'y':0,'basis':'Actual native BuildingIDs retain gaps'},
  'frames':[{'building':k,'frame':v,'source':(out/'construction'/(k+'.png')).relative_to(project).as_posix(),
   'source_sha256':sha(out/'construction'/(k+'.png')),'source_canvas':[150,70]}for k,v in sorted(ids.items(),key=lambda r:r[1])]})
 runs=[];alloutputs={};receipts=[]
 for run in range(2):
  outputs={};current=[]
  for p in packet:
   values,receipt=compiler.plan(project,p)
   duplicate=set(outputs)&set(values)
   if duplicate:raise ValueError('Duplicate native output '+str(duplicate))
   outputs.update(values);current.append(receipt)
  pins={k:hashlib.sha256(v).hexdigest()for k,v in sorted(outputs.items())};runs.append(pins)
  if run==0:alloutputs=outputs;receipts=current
 if runs[0]!=runs[1]:raise ValueError('Actual compiler plan is nondeterministic')
 report=HERE/slug;report.mkdir(exist_ok=True)
 # Write just the small native JSON definitions, not duplicate native frame
 # caches. Actual frame bytes are produced/decoded/hashes checked in memory.
 for name,data in alloutputs.items():
  if name.endswith('.json'):
   target=report/'native-definitions'/Path(name).name;target.parent.mkdir(exist_ok=True);target.write_bytes(data)
 dump(report/'conversion-twice.json',{'status':'authored configuration','converter':'scripts/faction_art_compile.py:create_compiler(...).plan',
  'converter_sha256':sha(ROOT/'scripts/faction_art_compile.py'),'actual_conversions':2,'deterministic':True,'native_logical_recipes':len(packet),
  'actual_native_outputs':len(alloutputs),'outputs':runs[0],'receipts':receipts,'source_recipe_pins':{p.relative_to(project).as_posix():sha(p)for p in packet},
  'scope':'Actual native compiler executed twice; outputs held in memory and hashes compared. No active cache, manifest, stage or game publication. Native/rendered-click/art acceptance pending.'})
 dump(out/'candidate-selection.json',{'status':'authored configuration','candidate_only':True,'recipes':[{'recipe':p.relative_to(project).as_posix(),'sha256':sha(p),'output_path':read(p)['output_path']}for p in packet],
  'native_output_pins':runs[0],'selection_authorized':False,'canonical_or_game_writes':False})
 print(json.dumps({'region':slug,'actual_conversions':2,'recipes':len(packet),'native_outputs':len(alloutputs),'deterministic':True}))

if __name__=='__main__':
 for slug in CONFIG:compile_one(slug)
