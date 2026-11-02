"""Bounded real-consumer regressions for ten unselected Bilgewater candidates."""
from pathlib import Path
import copy,hashlib,io,json,sys,tempfile,unittest
from PIL import Image,ImageOps,ImageChops
S=Path(__file__).resolve().parent;P=S.parents[3];W=P.parent;R=P/'build/reports/painted-creature-completion-20261028-v1/final-packet-v4';R.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(W/'scripts'))
import faction_art_compile,source_export_guard
from faction_creature_preview import measure_rgba,native_crop_contract
U=['bilgeRat','seaDog','corsair','pirateMarksman','shellshotGunner','reefBombardier','krakenPriest','tideHierophant','boardingCaptain','fleetVeteran']
REC=S/'proposed-recipes-v4';COMP=faction_art_compile.create_compiler('bilgewater')
def load(p):return json.loads(p.read_text())
def sha(raw):return hashlib.sha256(raw).hexdigest()
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def frames(unit,g):
 b=load(REC/unit/'battle.json');return [Image.open(P/f['source']).convert('RGBA')for f in next(a for a in b['groups']if a['group']==g)['frames']]
def visible_equal(a,b):
 if a.getchannel('A').tobytes()!=b.getchannel('A').tobytes():return False
 bg=Image.new('RGBA',a.size,(86,91,84,255));x=Image.alpha_composite(bg,a).convert('RGB');y=Image.alpha_composite(bg,b).convert('RGB')
 return ImageChops.difference(x,y).getbbox()is None
def displayed8(im):
 out=Image.new('RGBA',(450,400));out.alpha_composite(ImageOps.mirror(im),(-58,0));return out
def settled(death,dead,ready):
 if death.tobytes()!=dead.tobytes()or dead.tobytes()==ready.tobytes():raise ValueError('Persistent DEAD22 differs from genuine settled DEATH or equals standing')
class Tests(unittest.TestCase):
 def badplan(self,b):
  with tempfile.TemporaryDirectory(prefix='actual-compiler-mutation-',dir=R)as t:
   p=Path(t)/'recipe.json';p.write_text(json.dumps(b));return COMP.plan(P,p)
 def test_actual_two_pass_physical_outputs_match(self):
  for u in U:
   report=P/f'build/reports/painted-creature-completion-20261028-v1/{u}/candidate-v4';rec=load(report/'actual-compiler-replay-v1.json');self.assertTrue(rec['deterministic']);self.assertFalse(rec['visual_approval_granted'])
   first={p.relative_to(report/'compile-pass-1').as_posix():sha(p.read_bytes())for p in(report/'compile-pass-1').rglob('*')if p.is_file()};second={p.relative_to(report/'compile-pass-2').as_posix():sha(p.read_bytes())for p in(report/'compile-pass-2').rglob('*')if p.is_file()}
   self.assertEqual(first,second,u);self.assertEqual(first,rec['output_hashes'],u);self.assertEqual(len(first),rec['outputs_per_pass'])
 def test_actual_compiler_rejects_frame_pin_corruption(self):
  for u in U:
   b=load(REC/u/'battle.json');b['groups'][0]['frames'][0]['source_sha256']='0'*64
   with self.assertRaises(COMP.CompileError,msg=u):self.badplan(b)
 def test_actual_compiler_rejects_wrong_source_dimensions(self):
  for u in U:
   b=load(REC/u/'battle.json');b['groups'][0]['frames'][0]['source_canvas']=[449,400]
   with self.assertRaises(COMP.CompileError,msg=u):self.badplan(b)
 def test_all_selected_dependency_bytes_are_pinned_and_direct(self):
  for u in U:
   for p in(REC/u).glob('*.json'):
    r=load(p);g=r['generation'];self.assertEqual(sha((P/g['provenance']).read_bytes()),g['provenance_sha256']);self.assertEqual(sha((P/g['painted_master']).read_bytes()),g['painted_master_sha256'])
    for dep in g['production_inputs']:
     q=P/dep['path'];self.assertTrue(q.resolve().is_relative_to(P.resolve()));self.assertEqual(q.absolute(),q.resolve());self.assertEqual(1,q.stat().st_nlink);self.assertEqual(dep['sha256'],sha(q.read_bytes()))
    for group in r.get('groups',[]):
     for f in group['frames']:self.assertEqual(f['source_sha256'],sha((P/f['source']).read_bytes()))
 def test_no_selected_legacy_render_dependency(self):
  for p in REC.rglob('*.json'):
   t=p.read_text().lower();self.assertNotIn('.blend',t);self.assertNotIn('articulated-v4',t);self.assertNotIn('geometry_source',t)
 def test_actual_stock_holding_fidget_movement_crop(self):
  native_crop_contract(W)
  for u in U:
   for g in [0,1,2]:
    for im in frames(u,g):
     for h in [120,130]:self.assertEqual(0,measure_rgba(png(im),[150,155,250,155+h])['outside_pixels'],(u,g))
 def test_actual_preview_measure_detects_displaced_body(self):
  im=frames('bilgeRat',2)[0];bad=Image.new('RGBA',(450,400));bad.alpha_composite(im,(100,80));self.assertGreater(measure_rgba(png(bad),[150,155,250,275])['outside_pixels'],0)
 def test_persistent_corpse_is_real_settled_rgba(self):
  for u in U:settled(frames(u,5)[-1],frames(u,22)[0],frames(u,2)[0])
 def test_rgb_only_corpse_mutation_is_rejected(self):
  dead=frames('seaDog',22)[0];bad=dead.copy()
  for y in range(400):
   found=False
   for x in range(450):
    r,g,b,a=bad.getpixel((x,y))
    if a>=128:bad.putpixel((x,y),((r+1)%256,g,b,a));found=True;break
   if found:break
  self.assertEqual(dead.getchannel('A').tobytes(),bad.getchannel('A').tobytes())
  with self.assertRaises(ValueError):settled(dead,bad,frames('seaDog',2)[0])
 def test_standing_pose_cannot_substitute_dead22(self):
  with self.assertRaises(ValueError):settled(frames('bilgeRat',5)[-1],frames('bilgeRat',2)[0],frames('bilgeRat',2)[0])
 def test_displayed_native_turn_boundary_and_holding_endpoints(self):
  for u in U:
   self.assertTrue(visible_equal(frames(u,7)[-1],displayed8(frames(u,8)[0])),u);self.assertTrue(visible_equal(frames(u,7)[0],frames(u,2)[0]),u);self.assertTrue(visible_equal(frames(u,8)[-1],frames(u,2)[0]),u)
 def test_old_source_equality_fails_actual_displayed_turn(self):
  a=frames('seaDog',7)[-1];self.assertFalse(visible_equal(a,displayed8(a)))
 def test_map_mask_and_encounter_roots_share_world_anchor(self):
  for u in U:
   f=S/u/'native-v4/companions';m=Image.open(f/'map.png').convert('RGBA');left=Image.open(f/'attackLeft.png').convert('RGBA');right=Image.open(f/'attackRight.png').convert('RGBA')
   self.assertIsNone(m.getchannel('A').crop((0,0,32,64)).getbbox(),u);self.assertEqual(m.crop((32,0,96,64)).tobytes(),left.tobytes(),u)
   self.assertIsNotNone(left.getchannel('A').getbbox());self.assertIsNotNone(right.getchannel('A').getbbox())
 def test_actual_shoot_and_cast_climax_has_authored_event_pose(self):
  for u in U:
   c=load(S/u/'assembly-config-v4.json')
   for g in ['14','15','16']:
    if g in c['groups']:self.assertIn('Release',c['groups'][g][3]);self.assertNotEqual(frames(u,int(g))[3].tobytes(),frames(u,2)[0].tobytes())
   for g in ['30','31','32']:
    if g in c['groups']:self.assertTrue(any(v in c['groups'][g][4]for v in ['Aim','Release']));self.assertEqual(8,len(frames(u,int(g))))
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests));record={'status':'authored configuration','tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'successful':result.wasSuccessful(),'native_execution':False,'visual_approval_granted':False,'limitations':['Exact displayed turn boundary algebra is tested; intermediate quarter painting/handedness and gait still require native visual review','Source/export scope is bounded to this new source subtree; whole-faction export/release acceptance remains separate']};(R/'executed-tests-v4.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n');raise SystemExit(0 if result.wasSuccessful()else 2)
