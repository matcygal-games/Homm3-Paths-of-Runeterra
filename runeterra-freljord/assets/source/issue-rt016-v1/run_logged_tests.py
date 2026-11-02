"""Capture Python unittest stderr directly, retaining the actual process exit.

PowerShell turns unittest's ordinary stderr progress into NativeCommandError.
The earlier logs/receipts remain unchanged; this run has fresh owned output.
"""
from pathlib import Path
import json
import os
import subprocess
import sys
sys.dont_write_bytecode=True
import author_walks as a

out=a.REPORT/'clean-process-test-run'
out.mkdir(exist_ok=False)
for name in ('selected-before.json','dependency-pins.json'):
    (out/name).write_bytes((a.REPORT/name).read_bytes())
source='''import sys,runpy
sys.dont_write_bytecode=True
sys.path.insert(0,sys.argv[1])
import author_walks as a
from pathlib import Path
a.REPORT=Path(sys.argv[2])
runpy.run_path(str(Path(sys.argv[1])/'test_walks.py'),run_name='__main__')
'''
env=dict(os.environ,OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
result=subprocess.run([sys.executable,'-B','-c',source,str(a.HERE),str(out)],capture_output=True,
                      text=True,env=env,timeout=300,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
(out/'process.log').write_text(result.stdout+result.stderr,encoding='utf-8')
receipt={'exit_code':result.returncode,'tests':json.loads((out/'candidate-tests-v2.json').read_text()),
         'test_source_sha256':a.sha(a.HERE/'test_walks.py'),'wrapper_sha256':a.sha(Path(__file__)),
         'stdout_stderr_captured_directly':True}
(out/'process-result.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(receipt,sort_keys=True))
sys.exit(result.returncode)
