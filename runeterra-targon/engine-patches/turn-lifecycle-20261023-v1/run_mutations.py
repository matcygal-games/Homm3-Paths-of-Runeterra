from pathlib import Path
import subprocess,os,json,hashlib
r=Path(__file__).resolve().parent
base=(r/'tests/patched/consumer_regression.cpp').read_text()
vcvars=Path('C:/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/VC/Auxiliary/Build/vcvars64.bat')
p=subprocess.run(f'cmd /d /s /c ""{vcvars}" >nul && set"',text=True,capture_output=True,check=True)
env=dict(os.environ)
for l in p.stdout.splitlines():
 if '=' in l and not l.startswith('='):k,v=l.split('=',1);env[k]=v
cl='C:/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/VC/Tools/MSVC/14.51.36231/bin/Hostx64/x64/cl.exe'
late='''\t// Register request ownership before transport can deliver a reply or the next turn.
\tif(vstd::contains(playerint, player))
\t\tplayerint[player]->requestSent(&request, requestID);
\tGAME->server().sendGamePack(request);'''
early='''\tGAME->server().sendGamePack(request);
\tif(vstd::contains(playerint, player))
\t\tplayerint[player]->requestSent(&request, requestID);'''
mutations={'unscoped-ack':('if(accepted && request->second == turnGeneration)','if(accepted)'), 'unscoped-retry':('while(status.haveTurn(generation))','while(status.haveTurn())'),'late-registration':(late,early)}
results={}
for name,(old,new) in mutations.items():
 assert base.count(old)==1
 cwd=r/'tests/mutations'/name;cwd.mkdir(parents=True,exist_ok=True);src=cwd/'consumer_regression.cpp';src.write_text(base.replace(old,new),encoding='utf-8',newline='\n')
 cmd=[cl,'/nologo','/std:c++17','/EHsc','/Od',str(src),f'/Fe:{cwd/"consumer_regression.exe"}',f'/Fo:{cwd/"consumer_regression.obj"}']
 p=subprocess.run(cmd,env=env,cwd=cwd,text=True,capture_output=True);(cwd/'compile.log').write_text(p.stdout+p.stderr)
 item={'compile_exit_code':p.returncode,'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'mutation':{'old':old,'new':new}}
 if p.returncode==0:
  run=subprocess.run([str(cwd/'consumer_regression.exe')],cwd=cwd,env=env,text=True,capture_output=True,timeout=15);(cwd/'run.log').write_text(run.stdout+run.stderr);item.update({'run_exit_code':run.returncode,'output':run.stdout+run.stderr,'mutation_detected':run.returncode!=0})
 results[name]=item
(r/'mutation-results.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
assert all(v.get('mutation_detected') for v in results.values())
