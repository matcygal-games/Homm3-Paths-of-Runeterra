"""Execute and journal the public consumer against the explicit draft inputs.

No failure is promoted to a pass and physical negative controls only run after
the unchanged public helper accepts a complete baseline.
"""
from pathlib import Path
import sys,subprocess,json,hashlib
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[4]
WORKSPACE=PROJECT.parent
REPORT=PROJECT/'build/reports/complete-town-20261028-v1/approved-implementation-v1/physical-execution-v2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(PROJECT).as_posix()
def main():
 REPORT.mkdir(parents=True,exist_ok=False)
 tools=HERE/'physical-tools-v1';producer=HERE/'town-compiler-approved-v3'
 payload=producer/'payload-and-compiler.json';receipts=producer/'compiler-receipts.json'
 contract=tools/'draft-contract-v3/layout-contract.json'
 prepare=[sys.executable,'-B',str(tools/'prepare_fixture.py'),'--payload',rel(payload),'--payload-sha256',sha(payload),
  '--compiled-root','build/reports/complete-town-20261028-v1/approved-implementation-v1/town-compiler-approved-v3/compiled',
  '--compiler-receipts',rel(receipts),'--compiler-receipts-sha256',sha(receipts),
  '--contract',rel(contract),'--contract-sha256',sha(contract),'--out-name','draft-fixture-v2']
 observed=[]
 def execute(label,command):
  result=subprocess.run(command,cwd=WORKSPACE,capture_output=True)
  (REPORT/(label+'-stdout.log')).write_bytes(result.stdout);(REPORT/(label+'-stderr.log')).write_bytes(result.stderr)
  record={'label':label,'command':command,'exit_code':result.returncode,
   'stdout':{'path':rel(REPORT/(label+'-stdout.log')),'sha256':sha(REPORT/(label+'-stdout.log'))},
   'stderr':{'path':rel(REPORT/(label+'-stderr.log')),'sha256':sha(REPORT/(label+'-stderr.log'))}}
  observed.append(record);print(label,result.returncode,result.stdout.decode(errors='replace'),result.stderr.decode(errors='replace'))
  return result.returncode
 if execute('prepare-exact-source-fixture',prepare)==0:
  fixture=PROJECT/'build/reports/complete-town-20261028-v1/approved-implementation-v1/physical-consumer-v1/draft-fixture-v2/runeterra-bilgewater'
  execute('actual-public-consumer',[sys.executable,'-B',str(tools/'check_candidate.py'),'--fixture',str(fixture),'--attempt','draft-v2','--negative'])
 record={'status':'authored configuration','scope':'Actual source fixture/public-consumer execution. Source annotations remain unaccepted; execution failure is preserved, not converted into physical acceptance.',
  'executions':observed,'physical_baseline_passed':bool(len(observed)>1 and observed[1]['exit_code']==0),'native_verified':False,'canonical_inputs_modified':False}
 (REPORT/'execution.json').write_text(json.dumps(record,indent=2)+'\n')
 if not record['physical_baseline_passed']:raise SystemExit(2)
if __name__=='__main__':main()
