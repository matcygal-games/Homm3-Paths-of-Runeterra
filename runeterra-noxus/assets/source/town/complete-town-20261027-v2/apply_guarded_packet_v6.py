"""Coordinator-only integration. Default verifies frozen packet without writing."""
from pathlib import Path
import argparse,hashlib,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];W=ROOT.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--manifest',required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--apply',action='store_true');a=ap.parse_args();mp=ROOT/a.manifest;assert sha(mp)==a.sha256,'Manifest drift';m=json.loads(mp.read_text());assert m['selected_for_coordinator'] is True
 for path,pin in m['source_pins'].items():assert sha(ROOT/path)==pin,'Source drift '+path
 for path,pin in m['workspace_pins'].items():assert sha(W/path)==pin,'Helper drift '+path
 for r in m['canonical_files']:
  assert sha(ROOT/r['target'])==r['before_sha256'],'Canonical drift '+r['target'];assert sha(ROOT/r['payload']['path'])==r['after_sha256']==r['payload']['sha256'],'Payload drift '+r['target']
  if 'candidate'in r:assert sha(ROOT/r['candidate']['path'])==r['candidate']['sha256'],'Candidate drift '+r['target']
 if a.apply:
  backup=mp.parent/'pre-integration-canonical-backup';assert not backup.exists(),'Backup exists; do not repeat integration'
  for r in m['canonical_files']:
   p=backup/r['target'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/r['target']).read_bytes())
  for r in m['canonical_files']:(ROOT/r['target']).write_bytes((ROOT/r['payload']['path']).read_bytes())
  assert all(sha(ROOT/r['target'])==r['after_sha256']for r in m['canonical_files'])
 print(json.dumps({'preflight_passed':True,'canonical_files':len(m['canonical_files']),'applied':a.apply,'native_verified':False,'release_accepted':False}))
if __name__=='__main__':main()
