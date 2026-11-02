from pathlib import Path
import subprocess, os, json, hashlib, datetime
r=Path(__file__).resolve().parent
vcvars=Path('C:/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/VC/Auxiliary/Build/vcvars64.bat')
envout=subprocess.run(f'cmd /d /s /c ""{vcvars}" >nul && set"',text=True,capture_output=True,check=True)
env=dict(os.environ)
for line in envout.stdout.splitlines():
 if '=' in line and not line.startswith('='):k,v=line.split('=',1);env[k]=v
cl=Path('C:/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/VC/Tools/MSVC/14.51.36231/bin/Hostx64/x64/cl.exe')
rec={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'compiler':str(cl),'compiler_sha256':hashlib.sha256(cl.read_bytes()).hexdigest(),'scope':'Extracted actual pinned consumer methods compiled against minimal dependency fixtures. Not a complete engine build or native gameplay test.','variants':{}}
for variant in ['upstream','patched']:
 cwd=r/'tests'/variant;source=cwd/'consumer_regression.cpp'
 cmd=[str(cl),'/nologo','/std:c++17','/EHsc','/W4','/Od',str(source),f'/Fe:{cwd / "consumer_regression.exe"}',f'/Fo:{cwd / "consumer_regression.obj"}']
 build=subprocess.run(cmd,cwd=cwd,env=env,text=True,capture_output=True)
 (cwd/'compile.log').write_text(build.stdout+build.stderr)
 result={'compile_command':cmd,'compile_exit_code':build.returncode,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
 if build.returncode==0:
  run=subprocess.run([str(cwd/'consumer_regression.exe')],cwd=cwd,env=env,text=True,capture_output=True,timeout=15)
  (cwd/'run.log').write_text(run.stdout+run.stderr);result.update({'run_exit_code':run.returncode,'output':run.stdout+run.stderr,'binary_sha256':hashlib.sha256((cwd/'consumer_regression.exe').read_bytes()).hexdigest()})
 else:result['compile_output']=build.stdout+build.stderr
 rec['variants'][variant]=result
 print(variant,json.dumps(result,indent=2))
(r/'regression-result.json').write_text(json.dumps(rec,indent=2)+'\n')
assert rec['variants']['upstream'].get('compile_exit_code') == 0
assert rec['variants']['upstream'].get('run_exit_code') == 1
assert rec['variants']['patched'].get('compile_exit_code') == 0
assert rec['variants']['patched'].get('run_exit_code') == 0

