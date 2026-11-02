"""Source-only NX1 checks and honest geometry audit; no game/build mutations."""
from pathlib import Path
import copy,hashlib,importlib.util,io,json,sys,unittest
from PIL import Image,ImageChops,ImageFilter
from nx1_plan import SIZE,SITES,UNRESOLVED
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
REPORT=ROOT/'build/reports/approved-nx1-20261029-v1'
spec=importlib.util.spec_from_file_location('noxus_candidate_art_compile',ROOT/'scripts/art_compile.py')
compiler=importlib.util.module_from_spec(spec);spec.loader.exec_module(compiler)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def mask(p):
 im=Image.open(p);return im.getchannel('A') if im.mode=='RGBA' else im.convert('L')
def n(im):return im.histogram()[255]
def subset(a,b):return ImageChops.subtract(a,b).getbbox() is None
def geometry_failures(layer,area,foundation,door,water,open_arch=False):
 issues=[];a=layer.getchannel('A').point(lambda v:255 if v>=128 else 0)
 if not area.getbbox():issues.append('empty-area')
 if not subset(area,a):issues.append('click-outside-paint')
 if not foundation.getbbox() or not subset(foundation,area):issues.append('unsupported-foundation')
 enclosed=False
 if open_arch and door.getbbox() and area.getbbox():
  db=door.getbbox();ab=area.getbbox();cx=(db[0]+db[2])//2;cy=(db[1]+db[3])//2
  enclosed=(db[0]>=ab[0] and db[2]<=ab[2] and db[1]>=ab[1] and db[3]<=ab[3]
   and area.crop((max(0,cx-35),max(0,cy-9),cx,min(SIZE[1],cy+10))).getbbox() is not None
   and area.crop((cx,max(0,cy-9),min(SIZE[0],cx+35),min(SIZE[1],cy+10))).getbbox() is not None
   and area.crop((max(0,cx-3),max(0,cy-30),min(SIZE[0],cx+4),cy)).getbbox() is not None)
 if n(door)<5 or (not subset(door,area) and not enclosed):issues.append('missing-or-outside-door')
 if ImageChops.multiply(foundation,water).getbbox():issues.append('land-foundation-in-water')
 return issues

class CandidateChecks(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.selection=load(HERE/'candidate/selection.json');cls.rows={r['state']:r for r in cls.selection['states']};cls.placed={k:v for k,v in cls.rows.items() if v.get('native_layer')};cls.recipes=sorted((HERE/'candidate/candidate-recipes/assets/recipes/town').rglob('*.json'))
 def test_01_approved_source_hash(self):
  self.assertEqual(sha(HERE/'approved-master.png'),'e37cfa2aff3c7764806772d57ccc5d5b547f10b8a3e4a0954645d90ecbd22241')
 def test_02_exact_approved_full_pixels(self):
  a=Image.open(HERE/'approved-native.png').convert('RGB');b=Image.open(REPORT/'full-with-grail-native.png').convert('RGB');self.assertIsNone(ImageChops.difference(a,b).getbbox())
 def test_03_canonical_inputs_unchanged(self):
  for path,pin in load(HERE/'canonical-readonly-snapshot.json').items():
   with self.subTest(path=path):self.assertEqual(sha(ROOT/path),pin)
 def test_04_current_contract_preserved(self):
  self.assertEqual((self.selection['ordinary_land_sites'],self.selection['site_count'],self.selection['state_count']),(17,19,36));self.assertEqual(len(self.placed),34);self.assertEqual(len(self.rows),36)
  old=load(ROOT/'content/factions.json')['noxus']['town']['structures'];self.assertEqual(set(old),set(self.rows))
 def test_05_one_site_per_tier(self):
  for tier in range(1,8):
   with self.subTest(tier=tier):self.assertEqual(self.rows['dwellingLvl'+str(tier)]['site'],self.rows['dwellingUpLvl'+str(tier)]['site'])
  self.assertEqual(len({self.rows['dwellingLvl'+str(t)]['site'] for t in range(1,8)}),7)
 def test_06_merged_frontage_not_silent_alias(self):
  self.assertNotEqual(self.rows['dwellingUpLvl1']['site'],self.rows['dwellingUpLvl3']['site']);self.assertTrue(any('party-wall' in x for x in self.selection['unresolved']))
  self.assertEqual(self.rows['special4']['site'],self.rows['dwellingUpLvl7']['site']);self.assertTrue(any('Rear rose portal' in x for x in self.selection['unresolved']))
 def test_07_native_layers_and_source_pins(self):
  for state,row in self.placed.items():
   with self.subTest(state=state):
    p=ROOT/row['native_layer'];im=Image.open(p);self.assertEqual(im.size,SIZE);self.assertEqual(im.mode,'RGBA');self.assertEqual(sha(p),row['native_layer_sha256']);self.assertEqual(sha(ROOT/row['painted_master']),row['painted_master_sha256'])
 def test_08_click_masks_follow_nonrectangular_body(self):
  for state in self.placed:
   with self.subTest(state=state):
    area=mask(HERE/'structures'/state/'area.png');body=mask(HERE/'structures'/state/'silhouette.png');bb=area.getbbox();self.assertTrue(subset(area,body));self.assertLess(n(area),(bb[2]-bb[0])*(bb[3]-bb[1])*.97)
    if self.rows[state]['conversion'].get('atlas_cell') is not None:
     alpha=Image.open(HERE/'structures'/state/'layer.png').getchannel('A').point(lambda v:255 if v>=128 else 0);self.assertEqual(area.tobytes(),alpha.tobytes())
 def test_09_opaque_bodies_prevent_background_bleed(self):
  for state,info in [(v['top'],v) for v in SITES.values()]:
   with self.subTest(state=state):
    layer=Image.open(HERE/'structures'/state/'layer.png');area=mask(HERE/'structures'/state/'area.png');alpha=layer.getchannel('A');self.assertEqual(n(ImageChops.multiply(alpha,area)),n(area))
 def test_10_exact_external_highlights(self):
  for state in self.placed:
   with self.subTest(state=state):
    area=mask(HERE/'structures'/state/'area.png');border=mask(HERE/'structures'/state/'border.png');expected=ImageChops.subtract(area.filter(ImageFilter.MaxFilter(3)),area);self.assertEqual(border.tobytes(),expected.tobytes());self.assertIsNone(ImageChops.multiply(area,border).getbbox())
 def test_11_foundations_doors_no_water(self):
  water=mask(HERE/'terrain/water-mask.png')
  for state in self.placed:
   with self.subTest(state=state):
    folder=HERE/'structures'/state;fail=geometry_failures(Image.open(folder/'layer.png'),mask(folder/'area.png'),mask(folder/'foundation.png'),mask(folder/'door.png'),water,open_arch=self.rows[state]['entry_kind']=='open_arch');self.assertEqual(fail,[])
 def test_12_true_predecessor_sources(self):
  for site,info in SITES.items():
   for state in info['states'][:-1]:
    with self.subTest(state=state):
     row=self.rows[state];self.assertNotEqual(row['painted_master'],self.rows[info['top']]['painted_master']);self.assertIn('atlas_cell',row['conversion']);self.assertNotEqual(row['native_layer_sha256'],self.rows[info['top']]['native_layer_sha256'])
 def test_13_native_icons_all36_sparse_ids(self):
  rec=load(HERE/'candidate/candidate-recipes/assets/recipes/town/buildingIcons.json');self.assertEqual({f['building']:f['frame'] for f in rec['frames']},compiler.indexed_building_ids(ROOT))
  for f in rec['frames']:
   with self.subTest(state=f['building']):self.assertEqual(Image.open(ROOT/f['source']).size,(150,70));self.assertEqual(sha(ROOT/f['source']),f['source_sha256'])
 def test_14_all_ready_recipes_use_actual_existing_converter(self):
  outputs={};receipts=[];blocked=[]
  for path in self.recipes:
   recipe=load(path)
   if recipe['production_status'].startswith('blocked-'):
    with self.assertRaises(compiler.CompileError):compiler.plan(ROOT,path)
    blocked.append(str(path.relative_to(HERE)));continue
   with self.subTest(recipe=path.name):
    first,receipt=compiler.plan(ROOT,path);second,_=compiler.plan(ROOT,path);self.assertEqual(first,second)
    for name,data in first.items():
     self.assertNotIn(name,outputs);outputs[name]=hashlib.sha256(data).hexdigest()
    receipts.append(receipt)
  self.assertEqual(len(receipts),104);self.assertEqual(len(blocked),6);self.assertEqual(len(outputs),174)
  (REPORT/'technical-conversion-plan.json').write_text(json.dumps({'status':'authored configuration','mode':'art_compile.plan only: output bytes computed twice in memory, never written to assets/generated, stage, sandbox or install.','ready_recipes':len(receipts),'blocked_recipes':blocked,'outputs':outputs,'output_count':len(outputs),'receipts':receipts,'runtime_verified':False},indent=2)+'\n')
 def test_15_reject_bad_source_pin(self):
  rec=load(HERE/'candidate/candidate-recipes/assets/recipes/town/structures/capitol-animation.json');bad=copy.deepcopy(rec['groups'][0]['frames'][0]);bad['source_sha256']='0'*64
  with self.assertRaises(compiler.CompileError):compiler.source_image(ROOT,bad,list(SIZE),exact=True)
 def test_16_reject_water_under_foundation(self):
  f=HERE/'structures/capitol';water=mask(f/'foundation.png');fail=geometry_failures(Image.open(f/'layer.png'),mask(f/'area.png'),water,mask(f/'door.png'),water);self.assertIn('land-foundation-in-water',fail)
 def test_17_reject_floating_shifted_art(self):
  f=HERE/'structures/capitol';im=Image.open(f/'layer.png');shift=Image.new('RGBA',SIZE);shift.alpha_composite(im,(0,-35));fail=geometry_failures(shift,mask(f/'area.png'),mask(f/'foundation.png'),mask(f/'door.png'),Image.new('L',SIZE));self.assertIn('click-outside-paint',fail)
 def test_18_reject_door_off_building(self):
  f=HERE/'structures/capitol';door=Image.new('L',SIZE,255);fail=geometry_failures(Image.open(f/'layer.png'),mask(f/'area.png'),mask(f/'foundation.png'),door,Image.new('L',SIZE));self.assertIn('missing-or-outside-door',fail)
 def test_19_coast_fail_closed_no_invented_inland_plot(self):
  patch=load(HERE/'candidate/town-structures.patch.candidate.json');self.assertEqual(patch['unplaced_states'],['shipyard','ship']);self.assertNotIn('shipyard',patch['structures']);self.assertIsNone(self.rows['ship']['native_layer']);self.assertFalse(self.selection['runtime_verified']);self.assertFalse(self.selection['release_accepted'])
 def test_20_external_approved_scenery_unchanged(self):
  a=Image.open(HERE/'approved-native.png').convert('RGB');b=Image.open(HERE/'terrain/background.png').convert('RGB');m=ImageChops.invert(mask(HERE/'terrain/removal-contours.png'));self.assertIsNone(ImageChops.multiply(ImageChops.difference(a,b),Image.merge('RGB',(m,m,m))).getbbox())
 def test_21_original_reference_unchanged(self):
  p=ROOT.parent/'runeterra-demacia/references/images/tbcsback.pcx.png';self.assertEqual(sha(p),'949012ea68999207934bc482f1552858474fe50cefddef17eaac00d4b98c2be9')
 def test_22_no_hidden_geometry_acceptance(self):
  self.assertTrue(any('route masks' in s for s in self.selection['unresolved']));self.assertTrue(any('empty plate' in s for s in self.selection['unresolved']));self.assertTrue(self.selection['candidate_only'])
 def test_23_no_master_approval_promoted_to_state_approval(self):
  for state,row in self.placed.items():
   with self.subTest(state=state):self.assertFalse(row['visual_approval_granted']);self.assertTrue(row['whole_composition_approved'])
 def test_24_all_native_architecture_interiors_are_opaque(self):
  for state in self.placed:
   with self.subTest(state=state):
    alpha=Image.open(HERE/'structures'/state/'layer.png').getchannel('A');interior=alpha.point(lambda v:255 if v>=128 else 0).filter(ImageFilter.MinFilter(3));self.assertIsNone(ImageChops.multiply(interior,ImageChops.invert(alpha)).getbbox())

def audit():
 selection=load(HERE/'candidate/selection.json');tops=[s['top'] for s in selection['sites'] if 'top' in s];routes=[];doors=[];overlaps=[]
 for state in tops:
  f=HERE/'structures'/state;area=mask(f/'area.png');route=ImageChops.subtract(mask(f/'entry-route.png'),area);door=mask(f/'door.png')
  for other in tops:
   if state==other:continue
   target=mask(HERE/'structures'/other/'area.png');rh=n(ImageChops.multiply(route,target));dh=n(ImageChops.multiply(door,target));body_overlap=n(ImageChops.multiply(area,target))
   if rh:routes.append({'state':state,'other':other,'pixels':rh})
   if dh:doors.append({'state':state,'other':other,'pixels':dh})
   if state<other and body_overlap:overlaps.append({'a':state,'b':other,'pixels':body_overlap,'meaning':'Visible2Dcontour overlap; identical approved RGB. Not a proof of hidden-face or independent-state completeness.'})
 result={'status':'authored configuration','native_canvas':list(SIZE),'door_neighbor_intersections':doors,'short_external_route_intersections':routes,'visible_contour_overlaps':overlaps,'integration_ready':False,'reason':'Unplaced coastal states, independent frontage party walls and external route/empty-state visual review remain open. Full master approval is not decomposition acceptance.','remaining':UNRESOLVED}
 (REPORT/'geometry-audit.json').write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':
 REPORT.mkdir(parents=True,exist_ok=True);stream=io.StringIO();suite=unittest.defaultTestLoader.loadTestsFromTestCase(CandidateChecks);result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite);log=stream.getvalue();(REPORT/'source-checks.log').write_text(log);a=audit();summary={'status':'authored configuration','tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'successful':result.wasSuccessful(),'native_test_run':False,'stage_or_generated_outputs_written':False,'integration_ready':False,'short_external_route_intersections':a['short_external_route_intersections'],'geometry_gaps':len(a['remaining']),'tested_inputs':{p.name:sha(p) for p in [HERE/'derive_candidate.py',HERE/'nx1_plan.py',Path(__file__),HERE/'candidate/selection.json',HERE/'canonical-readonly-snapshot.json']}};(REPORT/'source-checks.json').write_text(json.dumps(summary,indent=2)+'\n');print(log);print(json.dumps(summary));sys.exit(0 if result.wasSuccessful() else 2)
