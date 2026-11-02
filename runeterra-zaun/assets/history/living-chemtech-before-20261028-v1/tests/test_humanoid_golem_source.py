"""Actual current/candidate humanoid source checks; no gameplay/art acceptance."""
from pathlib import Path
from copy import deepcopy
import hashlib,importlib.util,json,sys,unittest
from unittest.mock import patch
from PIL import Image
PROJECT=Path(__file__).resolve().parents[1]
WORKSPACE=PROJECT.parent
SOURCE=PROJECT/'assets/source/creatures/humanoid-20261025-v1'
RECIPE_BASE=PROJECT/'assets/recipes/creatures'
sys.path.insert(0,str(WORKSPACE/'scripts'))
import faction_artifacts as converter
UNITS=('chemGolem','pressureColossus')
ROLES=('battle','map','large','small','attackLeft','attackRight')
COUNTS={0:6,1:4,2:1,3:4,4:4,5:6,7:4,8:4,11:6,12:6,13:6,22:1}
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def recipe(unit,role):return read(RECIPE_BASE/f'{unit}-{role}.json')
def pose_hash(path):
 with Image.open(path) as raw:
  im=raw.convert('RGBA');bounds=im.getchannel('A').point(lambda a:255 if a>=30 else 0).getbbox()
  return hashlib.sha256(im.crop(bounds).tobytes()).hexdigest()
class HumanoidSourceContracts(unittest.TestCase):
 def test_all_canonical_roles_bind_new_own_sources_without_old_body_fallback(self):
  content=read(PROJECT/'content/creatures.json');masters=set()
  sizes={'battle':[450,400],'map':[96,64],'large':[58,64],'small':[32,32],'attackLeft':[64,64],'attackRight':[64,64]}
  graphics={'battle':'animation','map':'map','large':'iconLarge','small':'iconSmall','attackLeft':'mapAttackFromLeft','attackRight':'mapAttackFromRight'}
  for unit in UNITS:
   for role in ROLES:
    r=recipe(unit,role);self.assertEqual(unit,r['unit']);self.assertEqual(sizes[role],r['canvas'])
    self.assertEqual(content[unit]['graphics'][graphics[role]],r['output_path'].removeprefix('Content/Sprites/'))
    descriptors=[f for g in r.get('groups',[]) for f in g['frames']] if 'groups' in r else [{'source':r['source'],'source_sha256':r['source_sha256']}]
    for d in descriptors:
     self.assertTrue(d['source'].startswith('assets/source/creatures/humanoid-20261025-v1/'),d['source'])
     self.assertEqual(d.get('source_sha256',d.get('sha256')),sha(PROJECT/d['source']))
     with Image.open(PROJECT/d['source']) as im:self.assertEqual('RGBA',im.mode);self.assertEqual(tuple(sizes[role]),im.size)
    generation=r['generation'];master=generation['painted_master'];self.assertTrue(master.startswith('assets/source/creatures/humanoid-20261025-v1/'));masters.add(master)
    self.assertEqual(generation['painted_master_sha256'],sha(PROJECT/master))
    for item in generation.get('supplemental_masters',[]):
     self.assertTrue(item['path'].startswith('assets/source/creatures/humanoid-20261025-v1/'));self.assertEqual(item['sha256'],sha(PROJECT/item['path']));masters.add(item['path'])
  self.assertEqual(8,len(masters))
 def test_finite_melee_turn_and_corpse_source_contract(self):
  for unit in UNITS:
   r=recipe(unit,'battle');groups={g['group']:g['frames'] for g in r['groups']}
   self.assertEqual(COUNTS,{g:len(fs) for g,fs in groups.items()})
   self.assertEqual({'x':218,'y':266},r['pivot']);self.assertEqual(1,r['generateShadow']);self.assertEqual(1,r['generateOverlay'])
   self.assertEqual([f['source'] for f in groups[8]],[f['source'] for f in reversed(groups[7])])
   self.assertEqual(groups[2][0]['source'],groups[7][0]['source']);self.assertEqual(groups[5][-1]['source'],groups[22][0]['source'])
   self.assertEqual(46,len({f['source'] for fs in groups.values() for f in fs}))
   # Reject exact translated/cloned idle cohorts; different pixels do not prove native motion quality.
   for group in [0,11,12,13]:
    hashes={pose_hash(PROJECT/f['source']) for f in groups[group]};self.assertGreaterEqual(len(hashes),4,(unit,group))
   self.assertEqual([0],[g['group'] for g in recipe(unit,'map')['groups']])
 def test_actual_stock_crop_functions_accept_every_new_core_frame(self):
  spec=importlib.util.spec_from_file_location('humanoid_actual_crop_guard',PROJECT/'tests/test_industrial_native_crops.py')
  crop=importlib.util.module_from_spec(spec);spec.loader.exec_module(crop)
  for unit in UNITS:
   r=recipe(unit,'battle')
   for g in r['groups']:
    if g['group'] not in [0,2]:continue
    for frame in g['frames']:
     with Image.open(PROJECT/frame['source']) as raw:im=raw.convert('RGBA')
     for background in crop.backgrounds().values():crop.require_core_frame(im,crop.crop_box(True,background['size']),True,g['group'])
 def test_actual_converter_refuses_checksum_canvas_and_duplicate_group_before_writes(self):
  for unit in UNITS:
   base=recipe(unit,'battle');cases=[]
   bad=deepcopy(base);bad['groups'][0]['frames'][0].update({'source_sha256':'0'*64,'sha256':'0'*64});cases.append(bad)
   bad=deepcopy(base);bad['canvas']=[451,400];cases.append(bad)
   bad=deepcopy(base);bad['groups'].append(deepcopy(bad['groups'][0]));cases.append(bad)
   for changed in cases:
    with self.subTest(unit=unit),patch.object(converter,'store_output',side_effect=AssertionError('Unexpected active output write')) as store:
     with self.assertRaises(ValueError):converter.convert_animation(PROJECT,changed,'Content/Sprites/runeterra/zaun/',False,{})
     store.assert_not_called()
if __name__=='__main__':unittest.main(verbosity=2)
