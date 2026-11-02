"""Restore only the pinned third-party payloads to a new private SDK directory.
The original cache/archive is read-only. No Conan invocation or engine launch.
"""
from pathlib import Path,PurePosixPath
import argparse,hashlib,json,shutil,tarfile,time

HERE=Path(__file__).resolve().parent

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  while body:=f.read(1024*1024):h.update(body)
 return h.hexdigest()

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--archive',type=Path,required=True)
 parser.add_argument('--output-root',type=Path)
 parser.add_argument('--check-only',action='store_true')
 args=parser.parse_args()
 start=time.monotonic();public=json.loads((HERE/'public-provenance.json').read_text());inventory=json.loads((HERE/'selected-sdk-inputs.json').read_text())
 archive=args.archive.resolve()
 if sha(archive)!=public['original_sdk_archive']['sha256']:raise ValueError('Official SDK archive checksum differs')
 expected={}
 for entry in inventory['files']:
  name=inventory['directories'][entry[0]]+'/'+entry[1]
  if not name.startswith('conan-home/p/'):continue
  path=PurePosixPath(name)
  if path.is_absolute() or '..' in path.parts:raise ValueError('Unsafe selected SDK path')
  expected[name]={'bytes':entry[2],'sha256':entry[3]}
 manifest_to_package={}
 for path,value in expected.items():
  if path.endswith('/p/conanmanifest.txt'):
   package=PurePosixPath(path).parts[2]
   if value['sha256'] in manifest_to_package:raise ValueError('Ambiguous package manifest')
   manifest_to_package[value['sha256']]=package
 prefixes={}
 with tarfile.open(archive,'r|xz') as source:
  for member in source:
   if time.monotonic()-start>600:raise TimeoutError('SDK verification time bound exceeded')
   if member.isfile() and member.name.endswith('/p/conanmanifest.txt'):
    stream=source.extractfile(member);body=stream.read();digest=hashlib.sha256(body).hexdigest()
    if digest in manifest_to_package:
     prefix=member.name.rsplit('/',1)[0]
     if prefix in prefixes:raise ValueError('Duplicate package prefix')
     prefixes[prefix]=manifest_to_package[digest]
 if set(prefixes.values())!=set(manifest_to_package.values()):raise ValueError('Official archive does not contain every exact selected package manifest')
 target=None
 if not args.check_only:
  if args.output_root is None:raise ValueError('--output-root is required for extraction')
  target=args.output_root.resolve()
  if target.exists() and any(target.iterdir()):raise ValueError('Output must be a new or empty private directory')
  target.parent.mkdir(parents=True,exist_ok=True)
  if shutil.disk_usage(target.parent).free<sum(v['bytes'] for v in expected.values())+9*1024**3:raise ValueError('SDK extraction must preserve 9 GiB free')
  target.mkdir(exist_ok=True)
 seen=set()
 with tarfile.open(archive,'r|xz') as source:
  for member in source:
   if time.monotonic()-start>600:raise TimeoutError('SDK verification time bound exceeded')
   prefix=next((p for p in prefixes if member.name.startswith(p+'/')),None)
   if prefix is None:continue
   tail=member.name[len(prefix)+1:]
   relative='conan-home/p/'+prefixes[prefix]+'/p/'+tail
   if relative not in expected:continue
   path=PurePosixPath(relative)
   if path.is_absolute() or '..' in path.parts or not member.isfile():raise ValueError('Unsafe selected archive member')
   if relative in seen:raise ValueError('Duplicate selected archive member')
   value=expected[relative]
   if member.size!=value['bytes']:raise ValueError('Selected SDK member size differs: '+relative)
   stream=source.extractfile(member);digest=hashlib.sha256();written=0;output=None
   if target:
    destination=target.joinpath(*path.parts);destination.parent.mkdir(parents=True,exist_ok=True);output=destination.open('xb')
   try:
    while body:=stream.read(1024*1024):
     written+=len(body);digest.update(body)
     if output:output.write(body)
   finally:
    if output:output.close()
   if written!=value['bytes'] or digest.hexdigest()!=value['sha256']:raise ValueError('Selected SDK member checksum differs: '+relative)
   seen.add(relative)
 if seen!=set(expected):raise ValueError('Missing selected SDK payloads: '+str(sorted(set(expected)-seen)[:5]))
 result={'status':'authored configuration','official_archive_sha256':public['original_sdk_archive']['sha256'],'exact_selected_packages':len(prefixes),'verified_payload_files':len(seen),'verified_payload_bytes':sum(v['bytes'] for v in expected.values()),'extracted':bool(target),'game_or_build_launched':False,'seconds':time.monotonic()-start}
 if target:(target/'sdk-preparation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(result))

if __name__=='__main__':main()
