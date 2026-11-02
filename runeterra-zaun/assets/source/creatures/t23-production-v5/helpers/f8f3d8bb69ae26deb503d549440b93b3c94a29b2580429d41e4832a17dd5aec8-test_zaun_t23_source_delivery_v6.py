"""Tamper controls using the real frozen52-frame source copied into isolation.

These exercise a source-delivery gate, not artistic quality or runtime gameplay.
No fixture report or copied frame is eligible for production delivery.
"""
from pathlib import Path
import copy, json, shutil, tempfile, unittest
from unittest.mock import patch
from PIL import Image
import zaun_t23_source_delivery_v6 as gate

class SourceDeliveryControls(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.original=gate.PROJECT
  cls.temp=tempfile.TemporaryDirectory(prefix='zaun-t23-source-gate-')
  cls.base=Path(cls.temp.name)/'read-only-real-fixture';cls.base.mkdir()
  cls.cohort='assets/source/creatures/chemRavager/painted-battle-v6/battle-cohort-v6.json'
  cls.review='review/test-only-independent-copy.json'
  c=json.loads((cls.original/cls.cohort).read_text());rpath=cls.original/'build/reports/perfect-worker-independent-review/chemRavager-v6-source-review.json'
  paths={cls.cohort,c['contact_sheet']['path'],c['producer']['path'],c['atlas_selector']['path']}
  paths.update(f['source']for fs in c['groups'].values()for f in fs)
  for m in c['masters']:
   paths.add(m['master']['path']);paths.add(str(Path(m['master']['path']).with_name('generation.json')).replace('\\','/'))
  paths.update(f'assets/recipes/creatures/{u}-{k}.json'for u in gate.UNITS for k in ('map','large','small','attackLeft','attackRight'))
  paths.add('assets/recipes/creatures/chemRavager-battle.json')
  for rel in paths:
   dest=cls.base/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(cls.original/rel,dest)
  # The immutable historical recipe permits this isolated delivery test to be
  # rerun after production selection, without modifying the real selected file.
  historical=cls.original/'assets/reviews/creatures/chemRavager-battle-source-v6-20261021/blocked-recipe-before-selection.json'
  if historical.exists():shutil.copy2(historical,cls.base/'assets/recipes/creatures/chemRavager-battle.json')
  (cls.base/cls.review).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(rpath,cls.base/cls.review)
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def setUp(self):
  self.case=Path(self.temp.name)/self.id().rsplit('.',1)[-1];shutil.copytree(self.base,self.case)
  self.patch=patch.object(gate,'PROJECT',self.case);self.patch.start()
  self.rp=self.case/self.review
 def tearDown(self):self.patch.stop()
 def edit_review(self,callback):
  r=json.loads(self.rp.read_text());callback(r);self.rp.write_text(json.dumps(r))
 def check(self):return gate.validate('chemRavager',6,self.rp)
 def test_exact_real_source_passes_without_recipe_writes(self):
  p=self.case/'assets/recipes/creatures/chemRavager-battle.json';before=p.read_bytes();self.assertEqual(len(self.check()[3]),52);self.assertEqual(p.read_bytes(),before)
 def test_changed_native_png_is_rejected(self):
  c=json.loads((self.case/self.cohort).read_text());p=self.case/c['groups']['0'][0]['source'];im=Image.open(p);im.putpixel((175,200),(255,0,255,255));im.save(p)
  with self.assertRaisesRegex(ValueError,'Changed pinned evidence'):self.check()
 def test_review_missing_one_actual_frame_is_rejected(self):
  self.edit_review(lambda r:r['frames'].pop())
  with self.assertRaisesRegex(ValueError,'ordered frames'):self.check()
 def test_reordered_review_frames_are_rejected(self):
  self.edit_review(lambda r:r['frames'].reverse())
  with self.assertRaisesRegex(ValueError,'ordered frames'):self.check()
 def test_self_review_cannot_promote_source(self):
  self.edit_review(lambda r:r.update(reviewer='Codex /root/zaun_creatures_a'))
  with self.assertRaisesRegex(ValueError,'independent reviewer'):self.check()
 def test_final_art_flag_cannot_be_promoted(self):
  self.edit_review(lambda r:r.update(final_art_acceptance=True))
  with self.assertRaisesRegex(ValueError,'without final approval'):self.check()
 def test_changed_painted_master_is_rejected(self):
  c=json.loads((self.case/self.cohort).read_text());p=self.case/c['masters'][0]['master']['path'];p.write_bytes(p.read_bytes()+b'changed')
  with self.assertRaisesRegex(ValueError,'Changed pinned evidence'):self.check()
 def test_safe_paths_reject_traversal_and_windows_ambiguity(self):
  for value in ('../elsewhere.png','C:/elsewhere.png','assets/x. /file.png','assets\\x.png'):
   with self.subTest(value=value),self.assertRaises(ValueError):gate.safe(value)
 def test_delivery_preserves_auxiliaries_and_acceptance_flags(self):
  before=gate.protected_aux();result=gate.deliver('chemRavager',6,self.rp);self.assertEqual(before,gate.protected_aux());self.assertEqual(result['frame_count'],52)
  p=self.case/'assets/recipes/creatures/chemRavager-battle.json';r=json.loads(p.read_text());self.assertEqual(r['status'],'built-unreviewed');self.assertFalse(r['visual_approval_granted']);self.assertFalse(r['source_review']['final_art_acceptance'])
  with self.assertRaisesRegex(ValueError,'Refuse implicit replacement'):gate.deliver('chemRavager',6,self.rp)

if __name__=='__main__':unittest.main(verbosity=2)
