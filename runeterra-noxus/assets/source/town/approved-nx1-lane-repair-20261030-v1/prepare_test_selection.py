"""Propose current-selection checks while retaining historical executable suites."""
from pathlib import Path
import assemble_candidate as A
ROOT=A.ROOT;HERE=A.HERE;REPORT=A.REPORT
EXTRA=r'''
class HistoricalApprovedNX1Finish20261030(_nx1.NX1Finish):
 def test_canonical_and_protected_reference_remain_unchanged(self):
  # A superseded source cohort pins its own immutable recipes, source frames,
  # masters and protected reference. Its old canonical pointer is historical.
  selection=json.loads((CURRENT_SOURCE/'candidate/selection.json').read_text())
  for recipe,pin in selection['recipes'].items():self.assertEqual(sha(CURRENT_SOURCE/'candidate/recipes'/recipe),pin)
  for row in selection['states']:self.assertEqual(sha(ROOT/row['native_layer']),row['native_layer_sha256'])
  self.assertEqual(sha(ROOT.parent/'runeterra-demacia/references/images/tbcsback.pcx.png'),'949012ea68999207934bc482f1552858474fe50cefddef17eaac00d4b98c2be9')
 def test_actual_converter110_recipes182_buffers_twice(self):
  # Preserve the conversion assertion without overwriting historical reports.
  outputs={};receipts=[]
  for p in sorted((CURRENT_SOURCE/'candidate/recipes/assets/recipes/town').rglob('*.json')):
   first,receipt=_nx1.compiler.plan(ROOT,p);second,_=_nx1.compiler.plan(ROOT,p);self.assertEqual(first,second)
   for name,data in first.items():self.assertNotIn(name,outputs);outputs[name]=data
   receipts.append(receipt)
  self.assertEqual((len(receipts),len(outputs)),(110,182))

LANE_SOURCE=ROOT/'assets/source/town/approved-nx1-lane-repair-20261030-v1'
sys.path.insert(0,str(LANE_SOURCE))
_lane_spec=importlib.util.spec_from_file_location('noxus_current_lane_checks',LANE_SOURCE/'check_strict_fixture.py')
_lane=importlib.util.module_from_spec(_lane_spec);_lane_spec.loader.exec_module(_lane)

class CurrentApprovedNX1(_lane.ActualStrictCandidate):
 def test_11_active_selected_pins_and_all36_native_states(self):
  design=json.loads((ROOT/'design/town-visuals.json').read_text());selection_path=ROOT/design['selected_source'];selection=json.loads(selection_path.read_text())
  self.assertEqual(sha(selection_path),design['selected_source_sha256']);self.assertFalse(selection['candidate_only']);self.assertEqual(len(selection['states']),36)
  self.assertEqual(set(self.town['buildings']),{r['state']for r in selection['states']})
  for recipe,pin in selection['recipes'].items():self.assertEqual(sha(ROOT/recipe),pin)
  for row in selection['states']:self.assertEqual(sha(ROOT/row['native_layer']),row['native_layer_sha256'])
 def test_12_current_canonical_actual_strict_contract_and_outputs(self):
  design=json.loads((ROOT/'design/town-visuals.json').read_text());self.assertEqual(design['layout_contract']['path'],(LANE_SOURCE/'strict-contract-v1/town-layout.json').relative_to(ROOT).as_posix());self.assertEqual(design['layout_contract']['sha256'],sha(LANE_SOURCE/'strict-contract-v1/town-layout.json'))
  errors,_=_lane.B.consumer.inspect(ROOT,self.content,'noxus');self.assertEqual([],errors)
 def test_13_current110_recipe_buffers_equal_selected_generated_assets(self):
  selection=json.loads((ROOT/json.loads((ROOT/'design/town-visuals.json').read_text())['selected_source']).read_text());produced={}
  for name in selection['recipes']:
   first,_=_nx1.compiler.plan(ROOT,ROOT/name);second,_=_nx1.compiler.plan(ROOT,ROOT/name);self.assertEqual(first,second)
   for output,data in first.items():self.assertNotIn(output,produced);produced[output]=data;self.assertEqual(data,(ROOT/'assets/generated'/output).read_bytes())
  self.assertEqual((len(selection['recipes']),len(produced)),(110,182))
 def test_14_current_whole_native_composition_and_quantified_repair(self):
  scene=Image.open(ROOT/'assets/generated/Content/Sprites'/self.town['townBackground']).convert('RGBA')
  for state in self.contract['silhouette_plan']['complete_scene_states']:
   definition=json.loads((ROOT/'assets/generated/Content/Sprites'/self.town['structures'][state]['animation']).read_text());scene.alpha_composite(Image.open(ROOT/'assets/generated/Content/Sprites'/(definition['basepath']+definition['sequences'][0]['frames'][0])).convert('RGBA'))
  self.assertEqual(scene.tobytes(),Image.open(ROOT/self.contract['silhouette_plan']['complete_scene']['path']).convert('RGBA').tobytes())
  approved=Image.open(LANE_SOURCE.parent/'approved-nx1-20261029-v1/approved-native.png').convert('RGB');delta=ImageChops.difference(approved,scene.convert('RGB'));actual=sum(any(v)for v in delta.getdata());receipt=json.loads((LANE_SOURCE/'candidate/approved-diff.json').read_text());self.assertEqual(actual,receipt['changed_pixels']);self.assertLess(actual,800*374*.08)

if __name__=='__main__':unittest.main()
'''
def main():
 text=(HERE/'historical-test-baseline.py').read_text(encoding='utf8');prefix=text[:text.index('class CurrentApprovedNX1(')];(REPORT/'next-test_town_community_revision.py').write_text(prefix+EXTRA,encoding='utf8')
if __name__=='__main__':main()
