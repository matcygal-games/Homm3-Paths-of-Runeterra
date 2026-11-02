"""Bounded source/provenance, real converter and consumer-geometry verification."""
from pathlib import Path
import sys,json,hashlib,copy
from PIL import Image,ImageOps
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if p.name=='runeterra-world')
ROOT=PROJECT.parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'scripts'))
import runeterra_world as world
import faction_art_compile
compiler=faction_art_compile.create_compiler('world')
report=ROOT/'reports/world-expansion-art-20261030-v1'
paths=sorted((HERE/'candidate-recipes').glob('*.json'))+sorted((PROJECT/'assets/source/sites/world-expansion-20261030-v1').glob('*/recipe-candidate.json'))
results=[]
for p in paths:
 recipe=json.loads(p.read_text(encoding='utf8'));deps=world.recipe_dependencies(PROJECT,recipe)
 assert deps
 # A production recipe whose source bytes no longer match must fail the actual
 # consumer provenance verifier before any compiler can silently use it.
 bad=copy.deepcopy(recipe);bad['production_inputs'][0]['sha256']='0'*64
 try:world.recipe_dependencies(PROJECT,bad)
 except ValueError:pass
 else:raise AssertionError('Consumer accepted changed production source pin')
 bad=copy.deepcopy(recipe);bad['generation']['painted_master_sha256']='0'*64
 try:world.recipe_dependencies(PROJECT,bad)
 except ValueError:pass
 else:raise AssertionError('Consumer accepted changed painted master pin')
 a,_=compiler.plan(PROJECT,p);b,_=compiler.plan(PROJECT,p);assert a==b
 for dependency,raw in deps.items():
  if dependency.suffix=='.png':
   im=Image.open(dependency);assert not im.info,('Portable dependency still carries metadata',dependency)
 results.append({'recipe':p.relative_to(PROJECT).as_posix(),'dependency_count':len(deps),'production_pin_mutation_rejected':True,'master_pin_mutation_rejected':True,'double_actual_compiler_byte_identical':True,'output_count':len(a),'privacy_consumer_passed':True})
left=Image.open(HERE/'native/attackLeft.png');right=Image.open(HERE/'native/attackRight.png')
assert ImageOps.mirror(left).tobytes()==right.tobytes(),'Encounter facings are not a true pixel mirror'
animation=json.loads((report/'compiled-candidates/Content/Sprites/runeterra/world/creatures/voidgrub/battle.json').read_text())
assert sorted(s['group']for s in animation['sequences'])==[0,1,2,3,4,5,7,8,11,12,13,22]
for folder in [HERE/'native/battle',HERE/'native/map']:
 for p in folder.glob('*.png'):
  im=Image.open(p);b=im.getchannel('A').getbbox();assert b and b[0]>0 and b[1]>0 and b[2]<im.width and b[3]<im.height
  if folder.name=='map':assert b[0]>=32
for g in [0,1,5,11,12,13]:
 sources=sorted((HERE/'native/battle').glob(f'g{g:02d}-*.png'));assert len({Image.open(p).tobytes()for p in sources})>1,('Action group repeats one static bitmap',g)
value={'status':'authored configuration','recipe_checks':results,'encounter_mirror_pixels_verified':True,'native_group_identity_verified':True,'whole_subject_clip_count':0,'adventure_visible_mask_verified':True,'moving_and_death_groups_use_distinct_painted_poses':True,'runtime_verified':False,'visual_approval_granted':False}
(report/'source-consumer-checks.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf8')
print(json.dumps({'recipes_checked':len(results),'privacy_consumer':'passed','source_pin_mutation_rejections':len(results)*2,'double_assembly':'passed','native_runtime':'not_run'}))
