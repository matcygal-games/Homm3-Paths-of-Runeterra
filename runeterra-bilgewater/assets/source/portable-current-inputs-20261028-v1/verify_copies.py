"""Verify exact ordinary copies; no artwork creation or historical fallback."""
from pathlib import Path
import argparse,hashlib,json
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--check-originals-when-present',action='store_true');args=parser.parse_args();ledger=HERE/'selected-copies.json'
 if ledger.resolve()!=ledger.absolute()or not ledger.is_file()or ledger.stat().st_nlink!=1:raise ValueError('Selected copy ledger is missing, redirected or aliased')
 values=json.loads(ledger.read_bytes())['copies_by_historical_original_path'];seen=set();originals=0
 for old,row in values.items():
  path=PROJECT/row['ordinary_copy']
  if row['ordinary_copy']in seen:raise ValueError('Duplicated ordinary selected source')
  seen.add(row['ordinary_copy'])
  if(not path.absolute().is_relative_to((HERE/'images').absolute())or path.resolve()!=path.absolute()or not path.is_file()or path.stat().st_nlink!=1 or sha(path)!=row['sha256']):raise ValueError('Selected ordinary image missing, changed, foreign or aliased: '+row['ordinary_copy'])
  original=PROJECT/old
  if args.check_originals_when_present and original.exists():
   if sha(original)!=row['sha256']:raise ValueError('Preserved original changed: '+old)
   originals+=1
 if len(seen)!=127:raise ValueError('Exact127ordinary selected image cohort required')
 print(json.dumps({'status':'authored configuration','ordinary_selected_images':len(seen),'optional_original_comparisons':originals,'new_art_produced':False}))
if __name__=='__main__':main()
