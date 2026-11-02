"""Historical 27 October controls plus current selected NX1 source checks."""
from pathlib import Path
import hashlib,json,unittest
from PIL import Image,ImageChops,ImageFilter,ImageDraw,ImageOps

ROOT=next(p for p in Path(__file__).resolve().parents if p.name=='runeterra-noxus' and (p/'content/factions.json').is_file())
SOURCE=ROOT/'assets/source/town/rebuild-20261027-v1'
SELECTION=SOURCE/'selection.json'
def solid(im,t=128):return im.getchannel('A').point(lambda a:255 if a>=t else 0)
def pixels(im):return sum(im.histogram()[128:])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def moved(im,xy):
 bb=solid(im).getbbox();out=Image.new('RGBA',(800,374));out.alpha_composite(im.crop(bb),xy);return out
def foot(im):
 out=solid(im);bb=out.getbbox()
 if bb:out.paste(0,(0,0,800,max(0,bb[3]-7)))
 return out
def angled_foot(im):
 body=solid(im);out=Image.new('L',im.size);draw=ImageDraw.Draw(out)
 for x in range(im.width):
  bb=body.crop((x,0,x+1,im.height)).getbbox()
  if bb:draw.line((x,max(0,bb[3]-7),x,bb[3]-1),fill=255)
 return ImageChops.multiply(body,out)

class HistoricalTownCommunity20261027(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data=json.loads(SELECTION.read_text(encoding='utf-8'));cls.rows={r['state']:r for r in cls.data['states']}
  cls.images={s:Image.open(ROOT/r['native_layer']).convert('RGBA') for s,r in cls.rows.items()}
  cls.water=Image.new('L',(800,374));ImageDraw.Draw(cls.water).polygon(cls.data['terrain']['water_polygon'],fill=255)
  cls.town=json.loads((ROOT/'content/factions.json').read_text(encoding='utf-8'))['noxus']['town']
  # This historical suite executes the frozen27October source, not current selection.
  cls.town['structures']={state:{'x':0,'y':0,'z':row['native_z']} for state,row in cls.rows.items()}
  cls.baseline=json.loads((SOURCE/'preserved-building-master-inventory.json').read_text(encoding='utf-8'))['states']

 def test_exact_states_and_in_place_troop_pairs(self):
  self.assertEqual(set(self.rows),set(self.town['structures']));self.assertEqual((len(self.rows),len(self.data['sites'])),(36,19));self.assertEqual(self.data['ordinary_land_sites'],17)
  for tier in range(1,8):
   a,b=f'dwellingLvl{tier}',f'dwellingUpLvl{tier}'
   self.assertEqual(self.rows[a]['site'],self.rows[b]['site']);self.assertEqual(self.rows[a]['composition_rectangle'],self.rows[b]['composition_rectangle'])

 def test_real_alpha_masks_and_native_binding(self):
  for state,im in self.images.items():
   row=self.rows[state];folder=(ROOT/row['native_layer']).parent
   with self.subTest(state=state):
    expected=solid(im);self.assertGreater(pixels(expected),40);self.assertEqual(im.size,(800,374))
    self.assertEqual(Image.open(folder/'area.png').getchannel('A').tobytes(),expected.tobytes())
    self.assertEqual(Image.open(folder/'border.png').getchannel('A').tobytes(),ImageChops.subtract(expected.filter(ImageFilter.MaxFilter(5)),expected).tobytes())
    s=self.town['structures'][state];self.assertEqual([s['x'],s['y'],s['z']],[0,0,row['native_z']])
    recipe=json.loads((SOURCE/f'candidate-v3/candidate-recipes/assets/recipes/town/structures/{state}-animation.json').read_text())
    self.assertEqual(recipe['groups'][0]['frames'][0]['source'],row['native_layer']);self.assertEqual(recipe['groups'][0]['frames'][0]['source_sha256'],sha(ROOT/row['native_layer']))

 def test_every_distinct_site_state_pair_has_no_solid_or_shadow_collision(self):
  states=list(self.rows)
  for i,a in enumerate(states):
   for b in states[i+1:]:
    if self.rows[a]['site']==self.rows[b]['site']:continue
    for threshold in (1,128):
     with self.subTest(a=a,b=b,alpha=threshold):self.assertEqual(pixels(ImageChops.multiply(solid(self.images[a],threshold),solid(self.images[b],threshold))),0)

 def test_dry_foundations_and_complete_angled_tower_bases(self):
  for state,im in self.images.items():
   if self.rows[state]['site']=='shipyard':continue
   foundation=angled_foot(im) if state in ('fort','citadel','castle') else foot(im)
   with self.subTest(state=state):self.assertEqual(pixels(ImageChops.multiply(foundation,self.water)),0)
  badwater=Image.new('L',(800,374));ImageDraw.Draw(badwater).rectangle((747,108,789,128),fill=255)
  for state in ('fort','citadel','castle'):self.assertGreater(pixels(ImageChops.multiply(angled_foot(self.images[state]),badwater)),0)

 def test_complete_opaque_shadow_bounds_and_purposeful_dock_water(self):
  for state,im in self.images.items():
   with self.subTest(state=state):
    x0,y0,x1,y1=solid(im,1).getbbox();self.assertGreater(x0,0);self.assertGreater(y0,0);self.assertLess(x1,800);self.assertLess(y1,374)
    x,y=self.rows[state]['native_position'];w,h=self.rows[state]['native_size'];self.assertLessEqual(x+w,798);self.assertLessEqual(y+h,372)
  self.assertGreater(pixels(ImageChops.multiply(solid(self.images['ship']),self.water)),0)
  bad=moved(self.images['blacksmith'],(760,275));self.assertEqual(solid(bad,1).getbbox()[2],800)

 def test_native_replacement_families_share_visual_depth(self):
  for state,building in self.town['buildings'].items():
   predecessor=building.get('upgrades')
   if predecessor and predecessor in self.rows:
    with self.subTest(state=state):self.assertEqual(self.rows[state]['site'],self.rows[predecessor]['site']);self.assertEqual(self.rows[state]['native_z'],self.rows[predecessor]['native_z'])
  self.assertEqual(self.rows['ship']['native_z'],self.rows['shipyard']['native_z'])

 def test_actual_bad_placements_are_detected(self):
  target=self.images['dwellingLvl1'];bb=solid(target).getbbox();bad=moved(self.images['dwellingLvl3'],(bb[0],bb[1]))
  self.assertGreater(pixels(ImageChops.multiply(solid(bad),solid(target))),0)
  im=self.images['resourceSilo'];bb=solid(im).getbbox();wet=moved(im,(777,194-(bb[3]-bb[1])))
  self.assertGreater(pixels(ImageChops.multiply(foot(wet),self.water)),0)

 def test_preserved_master_lineage_and_exact_allocation_rejects_rescaling(self):
  # No universal near/far width ratio is artistic acceptance. Test the actual
  # requested unchanged-master lineage and reviewed whole-frame allocation.
  for state,row in self.rows.items():
   before=self.baseline[state];self.assertEqual((row['master'],row['master_sha256']),(before['master'],before['master_sha256']));self.assertEqual(sha(ROOT/row['master']),before['master_sha256'])
   im=Image.open(ROOT/row['master']).convert('RGBA')
   if row['mirror_x']:im=ImageOps.mirror(im)
   bb=solid(im,8).getbbox();self.assertEqual(list(bb),row['source_crop']);box=row['composition_rectangle']
   fit=ImageOps.contain(im.crop(bb),(box[2]-4,box[3]-4),Image.Resampling.LANCZOS);self.assertEqual(list(fit.size),row['native_size'])
   expected=Image.new('RGBA',(800,374));expected.alpha_composite(fit,tuple(row['native_position']));self.assertEqual(expected.tobytes(),self.images[state].tobytes())
   changed=Image.new('RGBA',(800,374));changed.alpha_composite(fit.resize((max(1,fit.width-3),max(1,fit.height-3))),tuple(row['native_position']));self.assertNotEqual(changed.tobytes(),expected.tobytes())
   self.assertNotEqual(ImageOps.mirror(expected).tobytes(),expected.tobytes())
  self.assertGreater(len({tuple(r['native_size']) for r in self.rows.values()}),15)



# The source-only NX1 checker remains independently executable in its source cohort.
# Current assertions below bind its geometry to the actual selected canonical files.
import importlib.util,sys
CURRENT_SOURCE=ROOT/'assets/source/town/approved-nx1-finish-20261030-v1'
sys.path.insert(0,str(CURRENT_SOURCE))
_spec=importlib.util.spec_from_file_location('noxus_current_nx1_checks',CURRENT_SOURCE/'check_finish.py')
_nx1=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_nx1)

class CurrentApprovedNX1(_nx1.NX1Finish):
 @classmethod
 def setUpClass(cls):
  design=json.loads((ROOT/'design/town-visuals.json').read_text(encoding='utf8'))
  cls.active_path=ROOT/design['selected_source'];cls.s=json.loads(cls.active_path.read_text(encoding='utf8'));cls.rows={r['state']:r for r in cls.s['states']}
  cls.town=json.loads((ROOT/'content/factions.json').read_text(encoding='utf8'))['noxus']['town']
 def test_canonical_and_protected_reference_remain_unchanged(self):
  # Superseding user selection changes canonical visual bindings intentionally.
  # Check those bindings and pins rather than falsely requiring the old selection.
  design=json.loads((ROOT/'design/town-visuals.json').read_text(encoding='utf8'))
  self.assertEqual(sha(self.active_path),design['selected_source_sha256'])
  self.assertFalse(self.s['candidate_only']);self.assertFalse(self.s['runtime_verified']);self.assertFalse(self.s['release_accepted'])
  for state,row in self.rows.items():
   self.assertEqual({k:self.town['structures'][state][k] for k in ('x','y','z')},self.s['structures'][state])
  for recipe,pin in self.s['recipes'].items():self.assertEqual(sha(ROOT/recipe),pin,recipe)
 def test_exact_approved_inland_full_pixels_and_protected_master(self):
  approved=Image.open(CURRENT_SOURCE.parent/'approved-nx1-20261029-v1/approved-native.png').convert('RGB')
  background_recipe=json.loads((ROOT/'assets/recipes/town/background.json').read_text())
  actual=Image.open(ROOT/'assets/generated'/background_recipe['output_path']).convert('RGBA')
  states=[v['top'] for v in _nx1.SITES.values()]
  for state in sorted(states,key=lambda state:self.rows[state]['native_z']):
   recipe=json.loads((ROOT/f'assets/recipes/town/structures/{state}-animation.json').read_text())
   outputs,_=_nx1.compiler.plan(ROOT,ROOT/f'assets/recipes/town/structures/{state}-animation.json')
   definition=json.loads(outputs[recipe['output_path']]);frame=definition['sequences'][0]['frames'][0]
   frame_name='Content/Sprites/'+definition['basepath']+'/'+frame
   actual.alpha_composite(Image.open(ROOT/'assets/generated'/frame_name).convert('RGBA'))
  self.assertIsNone(ImageChops.difference(approved,actual.convert('RGB')).getbbox())
 def test_actual_converter110_recipes182_buffers_twice(self):
  produced={}
  for name in self.s['recipes']:
   outputs,_=_nx1.compiler.plan(ROOT,ROOT/name);second,_=_nx1.compiler.plan(ROOT,ROOT/name);self.assertEqual(outputs,second)
   for output,data in outputs.items():
    self.assertNotIn(output,produced);produced[output]=data
    self.assertEqual(data,(ROOT/'assets/generated'/output).read_bytes(),output)
  self.assertEqual((len(self.s['recipes']),len(produced)),(110,182))

if __name__=='__main__':
 if '--historical-only' in sys.argv:
  sys.argv.remove('--historical-only');suite=unittest.defaultTestLoader.loadTestsFromTestCase(HistoricalTownCommunity20261027);result=unittest.TextTestRunner(verbosity=2).run(suite);raise SystemExit(0 if result.wasSuccessful() else 2)
 unittest.main()
