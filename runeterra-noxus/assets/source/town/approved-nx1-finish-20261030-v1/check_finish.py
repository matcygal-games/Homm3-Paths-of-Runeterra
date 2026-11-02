"""Executed NX1 candidate checks; actual converter, masks and native consumers."""
from pathlib import Path
import hashlib,importlib.util,io,json,sys,unittest
from PIL import Image,ImageChops,ImageFilter
from finish_plan import HERE,PRIOR,SIZE,SITES,ROUTES,COAST
ROOT=HERE.parents[3];REPORT=ROOT/'build/reports/approved-nx1-finish-20261030-v1'
spec=importlib.util.spec_from_file_location('nx1_finish_compiler',ROOT/'scripts/art_compile.py');compiler=importlib.util.module_from_spec(spec);spec.loader.exec_module(compiler)
def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def m(p):
 im=Image.open(p);return im.getchannel('A') if im.mode=='RGBA' else im.convert('L')
def subset(a,b):return ImageChops.subtract(a,b).getbbox() is None
def pixels(a):return a.histogram()[255]
def geometry(layer,area,foundation):
 alpha=layer.getchannel('A').point(lambda v:255 if v>=128 else 0)
 return (bool(area.getbbox()) and subset(area,alpha) and bool(foundation.getbbox()) and subset(foundation,area))
def dry_geometry(layer,area,foundation,water):return geometry(layer,area,foundation) and ImageChops.multiply(foundation,water).getbbox() is None

class NX1Finish(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.s=read(HERE/'candidate/selection.json');cls.rows={r['state']:r for r in cls.s['states']}
 def test_exact_approved_inland_full_pixels_and_protected_master(self):
  a=Image.open(PRIOR/'approved-native.png').convert('RGB');b=Image.open(REPORT/'full-with-grail.png').convert('RGB')
  self.assertIsNone(ImageChops.difference(a,b).getbbox());self.assertEqual(sha(PRIOR/'approved-master.png'),'e37cfa2aff3c7764806772d57ccc5d5b547f10b8a3e4a0954645d90ecbd22241')
 def test_complete36_states_and17land_contract(self):
  self.assertEqual(len(self.rows),36);self.assertEqual(self.s['ordinary_land_sites'],17);self.assertEqual((self.s['optional_coastal_sites'],self.s['grail_sites']),(1,1))
  self.assertEqual(set(self.rows),set(read(ROOT/'content/factions.json')['noxus']['town']['structures']))
  self.assertEqual(len({self.rows[f'dwellingLvl{i}']['site'] for i in range(1,8)}),7)
  for i in range(1,8):self.assertEqual(self.rows[f'dwellingLvl{i}']['site'],self.rows[f'dwellingUpLvl{i}']['site'])
 def test_all_body_layers_masks_foundations_and_native_pins(self):
  for state,row in self.rows.items():
   with self.subTest(state=state):
    f=HERE/'structures'/state;layer=Image.open(f/'layer.png').convert('RGBA');area=m(f/'area.png');foot=m(f/'foundation.png')
    self.assertEqual(layer.size,SIZE);self.assertTrue(geometry(layer,area,foot));self.assertEqual(sha(f/'layer.png'),row['native_layer_sha256'])
    interior=area.filter(ImageFilter.MinFilter(3));self.assertIsNone(ImageChops.multiply(interior,ImageChops.invert(layer.getchannel('A'))).getbbox())
    bb=area.getbbox();self.assertLess(pixels(area),(bb[2]-bb[0])*(bb[3]-bb[1])*.97)
 def test_exact_outward_highlight_and_no_click_on_coastal_water(self):
  for state in self.rows:
   with self.subTest(state=state):
    f=HERE/'structures'/state;area=m(f/'area.png');border=m(f/'border.png');self.assertEqual(border.tobytes(),ImageChops.subtract(area.filter(ImageFilter.MaxFilter(3)),area).tobytes())
  water=m(HERE/'terrain/coastal-water-mask.png');dock=m(HERE/'structures/shipyard/area.png')
  # Pilings may enter the river; water-only surface itself is not a click target.
  self.assertLess(pixels(ImageChops.multiply(dock,water)),pixels(water)//2)
 def test_local_external_routes_clear_all_neighbor_masonry(self):
  ordinary=[s for s,r in self.rows.items() if r['site']!='coast']
  for state in ordinary:
   f=HERE/'structures'/state;outside=ImageChops.subtract(m(f/'entry-route.png'),m(f/'area.png'))
   self.assertTrue(outside.getbbox(),state)
   for other in ordinary:
    if self.rows[state]['site']!=self.rows[other]['site']:
     with self.subTest(state=state,other=other):self.assertIsNone(ImageChops.multiply(outside,m(HERE/'structures'/other/'area.png')).getbbox())
 def test_all_state_doors_and_click_targets_survive_native_depth_sorting(self):
  for state,row in self.rows.items():
   higher=Image.new('L',SIZE)
   for other,other_row in self.rows.items():
    if row['site']!=other_row['site'] and other_row['native_z']>row['native_z']:higher=ImageChops.lighter(higher,m(HERE/'structures'/other/'area.png'))
   f=HERE/'structures'/state
   with self.subTest(state=state):
    self.assertGreaterEqual(pixels(ImageChops.subtract(m(f/'area.png'),higher)),40)
    self.assertGreaterEqual(pixels(ImageChops.subtract(m(f/'door.png'),higher)),5)
 def test_exact_frozen_occlusion_budget_and_displaced_overlap_negative(self):
  record=self.s['occlusion_budget'];self.assertEqual(sha(ROOT/record['path']),record['sha256'])
  def audit(masks):
   pairs=[]
   for a in self.rows:
    for b in self.rows:
     if a>=b or self.rows[a]['site']==self.rows[b]['site']:continue
     hit=ImageChops.multiply(masks[a],masks[b]);n=pixels(hit)
     if n:pairs.append({'a':a,'b':b,'pixels':n,'bbox':list(hit.getbbox()),'front':a if self.rows[a]['native_z']>self.rows[b]['native_z'] else b})
   return pairs
  masks={state:m(HERE/'structures'/state/'area.png') for state in self.rows};expected=read(ROOT/record['path'])['pairs'];self.assertEqual(audit(masks),expected)
  shifted=Image.new('L',SIZE);shifted.paste(masks['dwellingUpLvl3'],(130,-135));changed=dict(masks);changed['dwellingUpLvl3']=shifted;self.assertNotEqual(audit(changed),expected)
 def test_independent_frontage_hidden_wall_really_changes_solo_guild(self):
  self.assertNotEqual(self.rows['dwellingUpLvl1']['site'],self.rows['dwellingUpLvl3']['site'])
  before=Image.open(PRIOR/'structures/dwellingUpLvl3/layer.png').convert('RGBA');after=Image.open(HERE/'structures/dwellingUpLvl3/layer.png').convert('RGBA')
  self.assertTrue(ImageChops.difference(before.convert('RGB'),after.convert('RGB')).getbbox());self.assertEqual(self.rows['dwellingUpLvl3']['native_z'],248);self.assertEqual(self.rows['dwellingUpLvl1']['native_z'],249)
 def test_genuine_predecessors_and_coast_sources(self):
  for site,v in SITES.items():
   for state in v['states'][:-1]:
    self.assertNotEqual(self.rows[state]['painted_master'],self.rows[v['top']]['painted_master'])
  ledger=read(HERE/'source-ledger.json');self.assertEqual(ledger['generation_calls'],4)
  for entry in ledger['entries']:
   self.assertEqual(sha(HERE/entry['source']),entry['sha256']);self.assertEqual(sha(HERE/entry['prompt']),entry['prompt_sha256'])
 def test_native_coast_semantics_and_overlay_excludes_ordinary_solids(self):
  text=(ROOT.parent/'vcmi-develop/vcmi-develop/client/windows/CCastleInterface.cpp').read_text(encoding='utf8')
  self.assertIn('if(town->hasBuilt(BuildingID::SHIPYARD))',text);self.assertIn('buildingsCopy.insert(BuildingID::SHIP)',text)
  coast=m(HERE/'structures/shipyard/layer.png')
  for site,v in SITES.items():
   if site!='grail':self.assertIsNone(ImageChops.multiply(coast,m(HERE/'structures'/v['top']/'area.png')).getbbox(),site)
  self.assertEqual(Image.open(HERE/'terrain/water-mask.png').getextrema(),(0,0))
  f=m(HERE/'structures/shipyard/foundation.png');self.assertIsNone(ImageChops.multiply(f,m(HERE/'terrain/coastal-water-mask.png')).getbbox())
 def test_native_ship_replaces_shipyard_and_carries_complete_quay(self):
  buildings=read(ROOT/'content/factions.json')['noxus']['town']['buildings']
  self.assertEqual(buildings['ship']['upgrades'],'shipyard')
  def base(state):
   while buildings.get(state,{}).get('upgrades'):state=buildings[state]['upgrades']
   return state
  selected={}
  for state in ['shipyard','ship']:
   family=base(state)
   if state=='ship' or family not in selected:selected[family]=state
  self.assertEqual(list(selected.values()),['ship'])
  quay=Image.open(HERE/'structures/shipyard/layer.png').convert('RGBA');moored=Image.open(HERE/'structures/ship/layer.png').convert('RGBA');boat=Image.open(HERE/'structures/ship/boat-only-control.png').convert('RGBA')
  foot=m(HERE/'structures/shipyard/foundation.png');dock=m(HERE/'structures/shipyard/area.png')
  self.assertTrue(geometry(moored,dock,foot));self.assertFalse(geometry(boat,dock,foot))
  outside_boat=ImageChops.invert(boat.getchannel('A').point(lambda v:255 if v else 0))
  self.assertIsNone(ImageChops.multiply(ImageChops.difference(quay.convert('RGB'),moored.convert('RGB')),Image.merge('RGB',(outside_boat,)*3)).getbbox())
  self.assertEqual(self.rows['ship']['native_z'],self.rows['shipyard']['native_z'])
 def test_actual_converter110_recipes182_buffers_twice(self):
  all_outputs={};receipts=[]
  for p in sorted((HERE/'candidate/recipes/assets/recipes/town').rglob('*.json')):
   with self.subTest(recipe=p.name):
    a,receipt=compiler.plan(ROOT,p);b,_=compiler.plan(ROOT,p);self.assertEqual(a,b)
    for output,data in a.items():self.assertNotIn(output,all_outputs);all_outputs[output]=hashlib.sha256(data).hexdigest()
    receipts.append(receipt)
  self.assertEqual((len(receipts),len(all_outputs)),(110,182))
  (REPORT/'conversion.json').write_text(json.dumps({'status':'authored configuration','mode':'actual compiler plan; output buffers computed twice in memory','recipes':110,'outputs':all_outputs,'receipts':receipts},indent=2)+'\n',encoding='utf8')
 def test_native_icons_sparse_ids_and_dimensions(self):
  r=read(HERE/'candidate/recipes/assets/recipes/town/buildingIcons.json');self.assertEqual({f['building']:f['frame'] for f in r['frames']},compiler.indexed_building_ids(ROOT))
  for f in r['frames']:self.assertEqual(Image.open(ROOT/f['source']).size,(150,70));self.assertEqual(sha(ROOT/f['source']),f['source_sha256'])
 def test_changed_master_water_and_displaced_building_rejected(self):
  r=read(HERE/'candidate/recipes/assets/recipes/town/structures/capitol-animation.json');frame=dict(r['groups'][0]['frames'][0]);frame['source_sha256']='0'*64
  with self.assertRaises(compiler.CompileError):compiler.source_image(ROOT,frame,list(SIZE),exact=True)
  f=HERE/'structures/capitol';layer=Image.open(f/'layer.png').convert('RGBA');area=m(f/'area.png');foot=m(f/'foundation.png');moved=Image.new('RGBA',SIZE);moved.alpha_composite(layer,(0,-35));self.assertFalse(geometry(moved,area,foot))
  self.assertFalse(dry_geometry(layer,area,foot,foot))
 def test_canonical_and_protected_reference_remain_unchanged(self):
  for path,pin in read(HERE/'canonical-before.json').items():self.assertEqual(sha(ROOT/path),pin,path)
  self.assertEqual(sha(ROOT.parent/'runeterra-demacia/references/images/tbcsback.pcx.png'),'949012ea68999207934bc482f1552858474fe50cefddef17eaac00d4b98c2be9')

if __name__=='__main__':
 REPORT.mkdir(parents=True,exist_ok=True);stream=io.StringIO();suite=unittest.defaultTestLoader.loadTestsFromTestCase(NX1Finish);result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite);log=stream.getvalue();(REPORT/'source-checks.log').write_text(log,encoding='utf8');receipt={'status':'authored configuration','tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'successful':result.wasSuccessful(),'test_sha256':sha(Path(__file__)),'selection_sha256':sha(HERE/'candidate/selection.json'),'native_executed':False};(REPORT/'source-checks.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8');print(log);print(json.dumps(receipt));sys.exit(0 if result.wasSuccessful() else 2)
