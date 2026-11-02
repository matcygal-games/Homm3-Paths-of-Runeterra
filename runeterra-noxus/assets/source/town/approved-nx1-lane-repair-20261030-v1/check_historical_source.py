"""Run preserved historical suites from proposed canonical test module."""
from pathlib import Path
import importlib.util,unittest,json,sys
import assemble_candidate as A
def main():
 path=A.REPORT/'next-test_town_community_revision.py';spec=importlib.util.spec_from_file_location('noxus_proposed_selection_tests',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(getattr(module,name))for name in ('HistoricalTownCommunity20261027','HistoricalApprovedNX1Finish20261030'))
 with(A.REPORT/'historical-checks.log').open('w',encoding='utf8')as stream:result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
 receipt={'status':'authored configuration','actual_executed_tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'passed':result.wasSuccessful(),'test_patch_sha256':A.sha(path),'historical_evidence_overwritten':False};A.write(A.REPORT/'historical-checks.json',receipt);print(json.dumps(receipt));sys.exit(0 if result.wasSuccessful()else 2)
if __name__=='__main__':main()
