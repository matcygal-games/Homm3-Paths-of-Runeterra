"""Executed technical regressions for the unselected painted Bilge Rat cohort.

These reject real corrupted pins, source dimensions, corpse RGB/alpha changes,
and actual bottom-right displacement in the measured stock preview window.
They cannot approve gait, heraldry or native playability.
"""
from pathlib import Path
import copy, importlib.util, json, sys, tempfile, unittest
from PIL import Image, ImageChops
SOURCE=Path(__file__).resolve().parent;PROJECT=SOURCE.parents[3];WORKSPACE=PROJECT.parent
REPORT=PROJECT/'build/reports/painted-creature-completion-20261028-v1/bilgeRat'
RECIPES=SOURCE/'proposed-recipes/bilgeRat'
sys.path.insert(0,str(WORKSPACE/'scripts'));import faction_art_compile
COMPILER=faction_art_compile.create_compiler('bilgewater')
def load(p):return json.loads(p.read_text())
def decoded(recipe,group):
    sequence=next(g for g in recipe['groups']if g['group']==group)
    return [Image.open(PROJECT/f['source']).convert('RGBA')for f in sequence['frames']]
def corpse_contract(death,dead,holding):
    if death.tobytes()!=dead.tobytes():raise ValueError('DEAD must equal settled DEATH RGB and alpha')
    if dead.tobytes()==holding.tobytes():raise ValueError('DEAD must differ from standing')
def body_crop_contract(im,rect=(150,155,250,275)):
    a=im.getchannel('A').point(lambda v:255 if v>=128 else 0);b=a.getbbox()
    if not b or b[0]<rect[0]or b[1]<rect[1]or b[2]>rect[2]or b[3]>rect[3]:raise ValueError('Body is clipped by measured stock creature preview')
class CandidateTests(unittest.TestCase):
    def setUp(self):self.battle=load(RECIPES/'battle.json')
    def plan(self,recipe):
        with tempfile.TemporaryDirectory(prefix='actual-plan-',dir=REPORT)as tmp:
            p=Path(tmp)/'mutated-recipe.json';p.write_text(json.dumps(recipe));return COMPILER.plan(PROJECT,p)
    def test_actual_compiler_replays_are_identical(self):
        r=load(REPORT/'actual-compiler-replay-v1.json');self.assertTrue(r['deterministic']);self.assertEqual(48,r['outputs_per_pass']);self.assertFalse(r['visual_approval_granted']if 'visual_approval_granted'in r else False)
    def test_actual_compiler_rejects_changed_frame_pin(self):
        changed=copy.deepcopy(self.battle);changed['groups'][0]['frames'][0]['source_sha256']='0'*64
        with self.assertRaises(COMPILER.CompileError):self.plan(changed)
    def test_actual_compiler_rejects_wrong_source_canvas(self):
        changed=copy.deepcopy(self.battle);changed['groups'][0]['frames'][0]['source_canvas']=[449,400]
        with self.assertRaises(COMPILER.CompileError):self.plan(changed)
    def test_settled_death_and_dead22_match_decoded_rgba(self):
        corpse_contract(decoded(self.battle,5)[-1],decoded(self.battle,22)[0],decoded(self.battle,2)[0])
    def test_standing_alert_cannot_replace_dead22(self):
        with self.assertRaises(ValueError):corpse_contract(decoded(self.battle,5)[-1],decoded(self.battle,2)[0],decoded(self.battle,2)[0])
    def test_rgb_only_corpse_mutation_with_equal_alpha_is_rejected(self):
        corpse=decoded(self.battle,22)[0];bad=corpse.copy();a=bad.getchannel('A');b=a.point(lambda v:255 if v>=128 else 0).getbbox();x,y=b[0]+2,b[1]+2
        # Choose an actual opaque pixel, preserving its alpha exactly.
        for yy in range(b[1],b[3]):
            found=False
            for xx in range(b[0],b[2]):
                if a.getpixel((xx,yy))>=128:x,y=xx,yy;found=True;break
            if found:break
        r,g,bb,aa=bad.getpixel((x,y));bad.putpixel((x,y),((r+1)%256,g,bb,aa));self.assertEqual(a.tobytes(),bad.getchannel('A').tobytes())
        with self.assertRaises(ValueError):corpse_contract(corpse,bad,decoded(self.battle,2)[0])
    def test_holding_and_movement_fit_both_measured_stock_body_crops(self):
        for group in (0,2):
            for im in decoded(self.battle,group):
                for height in (120,130):body_crop_contract(im,(150,155,250,155+height))
    def test_actual_bottom_right_displacement_is_rejected(self):
        source=decoded(self.battle,2)[0];bad=Image.new('RGBA',source.size);bad.paste(source,(105,95))
        with self.assertRaises(ValueError):body_crop_contract(bad)
    def test_map_canvas_first_mask_column_is_transparent(self):
        im=Image.open(SOURCE/'bilgeRat/native-candidate-v1/companions/map.png').convert('RGBA');self.assertIsNone(im.getchannel('A').crop((0,0,32,64)).getbbox())
    def test_recipes_do_not_select_retired_producers(self):
        for path in RECIPES.glob('*.json'):
            text=path.read_text().lower();self.assertNotIn('.blend',text);self.assertNotIn('articulated-v4',text);self.assertNotIn('geometry_source',text)
    def test_real_native_half_turn_boundary_reuses_front_pose(self):
        self.assertEqual(decoded(self.battle,7)[-1].tobytes(),decoded(self.battle,8)[0].tobytes())
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(CandidateTests))
    record={'status':'authored configuration','tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'successful':result.wasSuccessful(),'native_execution':False,'visual_approval_granted':False,'art_gaps':['Opposite-support gait remains unapproved','Plate camera/root continuity must be reviewed in motion','Extended front-attack stock preview clipping is separate from full-canvas source clipping']}
    (REPORT/'executed-technical-tests-v1.json').write_text(json.dumps(record,indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful()else 2)
