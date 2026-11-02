"""Full actual production inspect, isolated source/converted linkage fixture.

No canonical inputs, generated buffers, shared policies or stage files mutate.
Fixtures are direct ordinary copies; no hardlinks/junctions are created.
"""
from pathlib import Path
import json,copy,shutil,unittest,sys,hashlib
from PIL import Image,ImageDraw,ImageChops
import build_strict_contract_v1 as B
ROOT=B.ROOT;HERE=B.HERE;SOURCE=B.OUT;REPORT=ROOT/'build/reports/approved-nx1-lane-repair-20261030-v1';FIX=REPORT/'strict-source-fixture'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,sort_keys=True,indent=2)+'\n',encoding='utf8')
def refs(obj):
 if isinstance(obj,dict):
  if isinstance(obj.get('path'),str):yield obj
  for v in obj.values():yield from refs(v)
 elif isinstance(obj,list):
  for v in obj:yield from refs(v)
class ActualStrictCandidate(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.contract=json.loads((SOURCE/'town-layout.json').read_text());cls.content={'factions':json.loads((ROOT/'content/factions.json').read_text())};cls.town=cls.content['factions']['noxus']['town'];FIX.mkdir(parents=True,exist_ok=True)
  for reference in refs(cls.contract):
   src=ROOT/reference['path'];dest=FIX/reference['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
  cls.contract_relative=(SOURCE/'town-layout.json').relative_to(ROOT).as_posix();cls.persist(cls.contract)
  # Real selected recipe buffers, never expected-frame copies masquerading as
  # converted evidence. Definitions and pixels both come from compiler.plan.
  import convert_candidate
  convert_candidate.REPORT=REPORT;convert_candidate.FIX=FIX
  convert_candidate.main()
 @classmethod
 def persist(cls,contract):
  write(FIX/cls.contract_relative,contract);write(FIX/'design/town-visuals.json',{'layout_geometry_mode':'silhouette-v2','layout_contract':{'path':cls.contract_relative,'sha256':sha(FIX/cls.contract_relative)}})
 def tearDown(self):self.persist(self.contract)
 def inspect(self):return B.consumer.inspect(FIX,self.content,'noxus')[0]
 def replace_mask(self,contract,reference,mask):
  path=FIX/reference['path'];old=path.read_bytes();mask.convert('RGB').save(path,compress_level=9);reference['sha256']=sha(path);self.addCleanup(path.write_bytes,old);self.persist(contract)
 def test_01_full_actual_consumer_accepts_current_36_frames(self):self.assertEqual([],self.inspect())
 def test_02_generated_frame_selection_mismatch_is_rejected(self):
  state='villageHall';definition=json.loads((FIX/'assets/generated/Content/Sprites'/self.town['structures'][state]['animation']).read_text());file=FIX/'assets/generated/Content/Sprites'/(definition['basepath']+definition['sequences'][0]['frames'][0]);old=file.read_bytes();shutil.copyfile(ROOT/self.contract['frames']['townHall']['path'],file)
  try:self.assertTrue(any('selected town pixels differ' in e for e in self.inspect()))
  finally:file.write_bytes(old)
 def test_03_unsupported_real_body_contact_cannot_pass(self):
  contract=copy.deepcopy(self.contract);ref=contract['silhouette_plan']['states']['villageHall']['foundation_mask'];mask=Image.open(FIX/ref['path']).convert('L');body=Image.open(FIX/contract['silhouette_plan']['states']['villageHall']['body_mask']['path']).convert('L');support=Image.open(FIX/contract['silhouette_plan']['support_mask']['path']).convert('L');bad=ImageChops.subtract(body,support);point=next((x,y)for y in range(374)for x in range(800)if bad.getpixel((x,y)));mask.putpixel(point,255);self.replace_mask(contract,ref,mask);self.assertTrue(any('lacks level support' in e for e in self.inspect()))
 def test_04_forced_opaque_roof_path_is_rejected(self):
  contract=copy.deepcopy(self.contract);ref=contract['silhouette_plan']['paths_mask'];mask=Image.open(FIX/ref['path']).convert('L');ImageDraw.Draw(mask).line([(380,320),(380,190),(429,190)],fill=255,width=2);self.replace_mask(contract,ref,mask);self.assertTrue(any('Global path passes through an actual solid building' in e for e in self.inspect()))
 def test_05_missing_bounded_overlap_is_rejected(self):
  contract=copy.deepcopy(self.contract);self.assertTrue(contract['silhouette_plan']['overlaps']);contract['silhouette_plan']['overlaps'].pop();self.persist(contract);self.assertTrue(any('Unapproved actual full-silhouette overlap' in e for e in self.inspect()))
 def test_06_disconnected_public_path_is_rejected(self):
  contract=copy.deepcopy(self.contract);ref=contract['silhouette_plan']['paths_mask'];mask=Image.open(FIX/ref['path']).convert('L');mask.putpixel((799,0),255);self.replace_mask(contract,ref,mask);self.assertTrue(any('disconnected components' in e for e in self.inspect()))
 def test_07_all_actual_state_local_routes_avoid_other_bodies(self):
  records=self.contract['silhouette_plan']['states'];images={s:Image.open(FIX/records[s]['body_mask']['path']).convert('L')for s in records};site_for={s:site['id']for site in self.contract['sites']for s in site['states']}
  for state,record in records.items():
   route=Image.open(FIX/record['approach_mask']['path']).convert('L')
   for other,body in images.items():
    if site_for[state]!=site_for[other]:self.assertIsNone(ImageChops.multiply(route,body).getbbox(),state+'/'+other)
 def test_08_ship_is_complete_quay_replacement(self):
  buildings=self.town['buildings'];self.assertEqual('shipyard',buildings['ship']['upgrades']);dock=Image.open(FIX/self.contract['frames']['shipyard']['path']).convert('RGBA');ship=Image.open(FIX/self.contract['frames']['ship']['path']).convert('RGBA');self.assertEqual(self.town['structures']['ship']['z'],self.town['structures']['shipyard']['z']);self.assertGreater(ship.getchannel('A').histogram()[255],3000);self.assertEqual((800,374),ship.size);self.assertIsNone(ImageChops.subtract(dock.getchannel('A'),ship.getchannel('A')).getbbox())
 def test_09_repair_reconstruction_is_exact_current_whole_view(self):
  full=Image.open(FIX/self.contract['background']['path']).convert('RGBA')
  for state in self.contract['silhouette_plan']['complete_scene_states']:full.alpha_composite(Image.open(FIX/self.contract['frames'][state]['path']).convert('RGBA'))
  self.assertEqual(full.tobytes(),Image.open(FIX/self.contract['silhouette_plan']['complete_scene']['path']).convert('RGBA').tobytes())
 def test_10_original_approved_native_and_master_unchanged(self):
  self.assertEqual('eefa99a0c4e992cdf0f2eba0e29640c1ae210ad640db587c8bbb34333e1eed63',sha(HERE.parent/'approved-nx1-20261029-v1/approved-native.png'));self.assertEqual('e37cfa2aff3c7764806772d57ccc5d5b547f10b8a3e4a0954645d90ecbd22241',sha(HERE.parent/'approved-nx1-20261029-v1/approved-master.png'))
if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--report-dir');args=parser.parse_args()
 if args.report_dir:REPORT=Path(args.report_dir).resolve();FIX=REPORT/'strict-source-fixture'
 REPORT.mkdir(parents=True,exist_ok=True)
 with(REPORT/'strict-source-tests.log').open('w',encoding='utf8')as stream:result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ActualStrictCandidate))
 receipt={'status':'authored configuration','actual_executed_tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'passed':result.wasSuccessful(),'canonical_or_shared_sources_mutated':False,'consumer_sha256':sha(ROOT.parent/'scripts/faction_town_layout.py'),'contract_sha256':sha(SOURCE/'town-layout.json')};write(REPORT/'strict-source-tests.json',receipt);print(json.dumps(receipt,indent=2));sys.exit(0 if result.wasSuccessful()else 2)
