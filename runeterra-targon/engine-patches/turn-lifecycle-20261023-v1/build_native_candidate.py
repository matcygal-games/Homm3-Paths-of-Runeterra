from pathlib import Path
import sys,os,json,hashlib,subprocess,time,shutil,argparse,datetime
R=Path(__file__).resolve().parent
W=Path('C:/Users/matcy/Documents/code/Homm3')
D=Path('D:/runeterra-work/targon-engine-66fa-turn-20261023-v1')
COMMIT='66fa496c6328a276c4eb14c0011b3a9d751dfac3'
CACHE=W/'runeterra-freljord/.tools/engine-shutdown-fix'
VS=Path('C:/Program Files (x86)/Microsoft Visual Studio/18/BuildTools')
CMAKE=VS/'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
NINJA=VS/'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe'
CL=VS/'VC/Tools/MSVC/14.51.36231/bin/Hostx64/x64/cl.exe'
GI=1024**3
sys.path.insert(0,str(W/'runeterra-demacia/scripts'))
from live_preview import WindowsOwnedJob,spawn_owned

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def footprint(p):return sum(f.stat().st_size for f in p.rglob('*') if f.is_file())
def guard():
 stats={d:shutil.disk_usage(d).free for d in ['C:/','D:/']};growth=footprint(D)
 if stats['C:/']<9*GI or stats['D:/']<9*GI or growth>12*GI:raise RuntimeError(f'disk budget violated: {stats}, own cumulative bytes {growth}')
 return {'free':stats,'owned_bytes':growth}
def env_setup():
 vcvars=VS/'VC/Auxiliary/Build/vcvars64.bat'
 p=subprocess.run(f'cmd /d /s /c ""{vcvars}" >nul && set"',capture_output=True,text=True,check=True)
 e=dict(os.environ)
 for l in p.stdout.splitlines():
  if '=' in l and not l.startswith('='):k,v=l.split('=',1);e[k]=v
 e.update({'TEMP':str(D/'temp'),'TMP':str(D/'temp'),'GIT_TERMINAL_PROMPT':'0','RUNETERRA_TARGON_USER':str(D/'unit-profile'),'CMAKE_BUILD_PARALLEL_LEVEL':'2'})
 return e

def run(name,cmd,env,cwd,timeout=600):
 guard()
 if (D/'logs'/(name+'.log')).exists():name=name+'-'+str(time.time_ns())
 log=D/'logs'/(name+'.log');job=WindowsOwnedJob();start=time.monotonic();samples=[]
 with log.open('wb') as out:
  p=spawn_owned(cmd,job=job,cwd=cwd,env=env,stdout=out,stderr=subprocess.STDOUT)
  try:
   while p.poll() is None:
    elapsed=time.monotonic()-start;sample=guard();sample.update({'elapsed':elapsed,'pids':job.pids()});samples.append(sample)
    dump(D/'active-command.json',{'name':name,'command':cmd,'samples':samples[-5:]})
    if elapsed>timeout or log.stat().st_size>128*1024**2:raise RuntimeError('command time/log bound exceeded')
    print(name,round(elapsed),'s',sample,flush=True);time.sleep(15 if name=='build' else .5)
   code=p.returncode
  finally:job.close()
 result={'name':name,'command':cmd,'exit_code':code,'seconds':time.monotonic()-start,'log_sha256':sha(log),'cleanup_complete':not job.pids(),'samples':samples}
 dump(D/'logs'/(name+'-result.json'),result)
 if code:raise RuntimeError(f'{name} failed exit{code}; inspect{log}')
 return result

def fetch_repo(target,url,commit,env,label):
 if target.exists():
  existing=subprocess.run(['git','-C',str(target),'rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
  if existing!=commit:raise RuntimeError('Existing owned source commit mismatch')
  return
 target.mkdir(parents=True)
 run(label+'-init',['git','init',str(target)],env,D)
 run(label+'-autocrlf',['git','-C',str(target),'config','core.autocrlf','false'],env,D)
 run(label+'-remote',['git','-C',str(target),'remote','add','origin',url],env,D)
 run(label+'-fetch',['git','-C',str(target),'fetch','--depth','1','origin',commit],env,D,600)
 run(label+'-checkout',['git','-C',str(target),'checkout','--detach','FETCH_HEAD'],env,D)

def snapshot_dependencies():
 roots=[CACHE/'conan-home',CACHE/'conan-generated'];records={}
 for base in roots:
  for p in sorted(base.rglob('*')):
   if p.is_file():records[str(p)]={'bytes':p.stat().st_size,'sha256':sha(p)}
 return records

def prepare(env):
 # Full inventory before any configuration reads shared dependency inputs.
 before=json.loads((D/'dependencies-before.json').read_text()) if (D/'dependencies-before.json').exists() else snapshot_dependencies()
 if not (D/'dependencies-before.json').exists():dump(D/'dependencies-before.json',before)
 fetch_repo(D/'source','https://github.com/vcmi/vcmi.git',COMMIT,env,'source')
 tree=json.loads((R/'official-source-tree.json').read_bytes());expected={x['path']:x for x in tree['tree'] if x['type']=='blob'}
 paths=list(expected)
 normalized=subprocess.run(['git','-C',str(D/'source'),'hash-object','--stdin-paths'],input='\n'.join(paths)+'\n',capture_output=True,text=True,check=True).stdout.splitlines()
 if len(normalized)!=len(paths):raise RuntimeError('source blob verification count differs')
 working={}
 for rel,blob in zip(paths,normalized):
  p=D/'source'/rel
  if not p.is_file() or blob!=expected[rel]['sha']:raise RuntimeError('source blob differs '+rel)
  working[rel]={'git_blob_sha1':blob,'working_file_sha256':sha(p),'bytes':p.stat().st_size}
 dump(D/'complete-source-working-files.json',working)
 dump(D/'complete-source-tree-verification.json',{'commit':COMMIT,'tree_response_sha256':sha(R/'official-source-tree.json'),'verified_blobs':len(expected),'all_match':True})
 for label,path,url,commit in [('dependencies','dependencies','https://github.com/vcmi/vcmi-dependencies.git','68f3f22614a3b17c80aa603b0c013181db845048'),('googletest','test/googletest','https://github.com/google/googletest.git','b514bdc898e2951020cbdca1304b75f5950d1f59')]:
  target=D/'source'/path
  if target.exists() and not any(target.iterdir()):target.rmdir()
  fetch_repo(target,url,commit,env,label)
 run('patch-check',['git','-C',str(D/'source'),'apply','--check',str(R/'0001-bind-end-turn-acknowledgements-to-turn-generation.patch')],env,D)
 run('patch-apply',['git','-C',str(D/'source'),'apply',str(R/'0001-bind-end-turn-acknowledgements-to-turn-generation.patch')],env,D)
 shutil.copy2(R/'tests/native/TurnGenerationTest.cpp',D/'source/test/TurnGenerationTest.cpp')
 with (D/'source/test/CMakeLists.txt').open('a',encoding='utf-8',newline='\n') as f:f.write('\n# Private native consumer regression overlay.\ntarget_sources(vcmitest PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/TurnGenerationTest.cpp")\n')
 args=[str(CMAKE),'-S',str(D/'source'),'-B',str(D/'build'),'-G','Ninja',f'-DCMAKE_MAKE_PROGRAM={NINJA}',f'-DCMAKE_TOOLCHAIN_FILE={CACHE / "conan-generated/conan_toolchain.cmake"}',f'-DCMAKE_INSTALL_PREFIX={D / "runtime"}','-DCMAKE_BUILD_TYPE=Release','-DENABLE_CLIENT=ON','-DENABLE_SERVER=ON','-DENABLE_NULLKILLER2_AI=ON','-DENABLE_BATTLE_AI=ON','-DENABLE_STUPID_AI=ON','-DENABLE_TEST=ON','-DENABLE_EDITOR=OFF','-DENABLE_LAUNCHER=OFF','-DENABLE_LOBBY=OFF','-DENABLE_MMAI=OFF','-DENABLE_DISCORD=OFF','-DENABLE_LTO=OFF','-DENABLE_PCH=ON','-DENABLE_TRANSLATIONS=OFF','-DENABLE_SDL3=ON','-DENABLE_COPY_CONAN_RUNTIME_DLLS=ON','-DENABLE_MINIMAL_LIB=OFF','-DENABLE_GITVERSION=ON','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON','-DCMAKE_GTEST_DISCOVER_TESTS_DISCOVERY_MODE=PRE_TEST']
 run('configure',args,env,D,600)
 after=snapshot_dependencies();dump(D/'dependencies-after-prepare.json',after)
 if before!=after:raise RuntimeError('Read-only dependency inputs changed during preparation')
 # Configure own writable unit profile before any test executable is invoked.
 profile=D/'unit-profile'
 for name in ['cache','config','logs','Saves']: (profile/name).mkdir(parents=True,exist_ok=True)
 dirs={'userCachePath':'%RUNETERRA_TARGON_USER%/cache','userConfigPath':'%RUNETERRA_TARGON_USER%/config','userDataPath':'%RUNETERRA_TARGON_USER%','userLogsPath':'%RUNETERRA_TARGON_USER%/logs','userSavePath':'%RUNETERRA_TARGON_USER%/Saves'}
 (D/'build/bin/config').mkdir(parents=True,exist_ok=True);dump(D/'build/bin/config/dirs.json',dirs)
 rec={'status':'authored configuration','prepared':True,'build_started':False,'source_commit':COMMIT,'source_tree_blob_count':len(expected),'patch_sha256':sha(R/'0001-bind-end-turn-acknowledgements-to-turn-generation.patch'),'dependency_inventory_sha256':sha(D/'dependencies-before.json'),'dependency_inputs':len(before),'dependencies_unchanged':True,'tools':{str(p):sha(p) for p in [CL,CMAKE,NINJA]},'configure_command':args,'disk':guard(),'native_game_launched':False,'protected_checkout_modified':False,'old_objects_importlibs_or_DLLs_reused':False}
 dump(D/'preflight.json',rec);dump(R/'native-build-preflight-pointer.json',{'path':str(D/'preflight.json'),'sha256':sha(D/'preflight.json')});print('PREPARED',json.dumps(rec),flush=True)

if __name__=='__main__':
 mode=sys.argv[1] if len(sys.argv)>1 else 'prepare'
 D.mkdir(parents=True,exist_ok=True)
 for name in ['logs','temp']:(D/name).mkdir(exist_ok=True)
 env=env_setup()
 try:
  if mode=='prepare':prepare(env)
  elif mode=='build':run('build',[str(CMAKE),'--build',str(D/'build'),'--target','vcmiclient','vcmiserver','vcmitest','--parallel','2'],env,D,2400)
  else:raise ValueError('unknown mode')
 except BaseException as e:
  dump(D/('failure-'+mode+'-'+str(time.time_ns())+'.json'),{'error':repr(e),'disk':{'C':shutil.disk_usage('C:/').free,'D':shutil.disk_usage('D:/').free},'mode':mode});raise
