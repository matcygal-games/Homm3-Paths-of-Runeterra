"""Replay the fixed painted physical-plane assembly against its actual prior bytes."""
from pathlib import Path
import hashlib,json,subprocess,sys,time
import assemble_packets as common
S=common.SOURCE;R=common.REPORT/'heraldry-v1'
def fingerprint():
 result={}
 for folder in ('heraldry-v1','recipe-payload-heraldry-v1'):
  for path in sorted((S/folder).rglob('*')):
   if path.is_file() and path.suffix in ('.png','.json'):
    result[path.relative_to(S).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
 return result
def main():
 before=fingerprint();started=time.time()
 command=[sys.executable,'-B',str(S/'build_heraldry.py'),'--produce']
 completed=subprocess.run(command,cwd=common.PROJECT.parent,capture_output=True,text=True)
 (R/'assembly-replay-v1.log').write_text(completed.stdout+'\n'+completed.stderr,encoding='utf-8')
 after=fingerprint();changed=[p for p in sorted(set(before)|set(after)) if before.get(p)!=after.get(p)]
 result={'status':'authored configuration','method':'A second real full assembly pass compared with the completed stable first pass; no cached output substitution','command':['project-python','-B',common.rel(S/'build_heraldry.py'),'--produce'],'producer':common.descriptor(S/'build_heraldry.py'),'returncode':completed.returncode,'elapsed_seconds':round(time.time()-started,2),'before_count':len(before),'after_count':len(after),'byte_identical':before==after,'changed':changed,'output_sha256':after,'runtime_execution':False,'visual_acceptance':False}
 common.put(R/'assembly-replay-v1.json',result)
 print(json.dumps({k:result[k] for k in ('returncode','before_count','after_count','byte_identical','changed','elapsed_seconds')}))
 if completed.returncode or changed:raise SystemExit(2)
if __name__=='__main__':main()
