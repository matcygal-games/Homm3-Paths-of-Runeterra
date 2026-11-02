from pathlib import Path
import hashlib,json,shutil,time
R=Path(__file__).resolve().parent;D=Path('D:/runeterra-work/targon-engine-66fa-turn-20261023-v1');S=Path('D:/e2e/Heroes of Might & Magic III/Data');GI=1024**3

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()
def guard():
 own=sum(p.stat().st_size for p in D.rglob('*') if p.is_file())
 assert own<12*GI and shutil.disk_usage('D:/').free>9*GI and shutil.disk_usage('C:/').free>9*GI

records={};start=time.monotonic()
for src in sorted(p for p in S.rglob('*') if p.is_file()):
 guard();rel=src.relative_to(S);dst=D/'unit-profile/Data'/rel;dst.parent.mkdir(parents=True,exist_ok=True)
 before=sha(src);shutil.copy2(src,dst);after=sha(src);copied=sha(dst)
 assert before==after==copied
 records[rel.as_posix()]={'bytes':src.stat().st_size,'source_sha256_before':before,'source_sha256_after':after,'copy_sha256':copied};print('Unit data prepared',rel,flush=True)
 if time.monotonic()-start>600:raise RuntimeError('unit data preparation time cap')
(D/'unit-data-preservation.json').write_text(json.dumps({'source':str(S),'destination':str(D/'unit-profile/Data'),'files':records,'game_launched':False,'source_unchanged':True,'seconds':time.monotonic()-start},indent=2)+'\n',encoding='utf-8')
