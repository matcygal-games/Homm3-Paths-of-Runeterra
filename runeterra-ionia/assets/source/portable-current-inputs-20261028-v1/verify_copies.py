"""Verify selected ordinary painted input copies; never creates artwork."""
from pathlib import Path
import argparse,hashlib,json
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[2]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check-originals-when-present',action='store_true');args=parser.parse_args();ledger=HERE/'selected-copies.json'
 if ledger.resolve()!=ledger.absolute() or ledger.stat().st_nlink!=1:raise ValueError('Selected copy ledger is aliased or redirected')
 value=json.loads(ledger.read_bytes());count=0;originals=0
 for old,row in value['copies_by_historical_original_path'].items():
  path=PROJECT/row['ordinary_copy']
  if (not path.absolute().is_relative_to(HERE.absolute()) or path.resolve()!=path.absolute() or not path.is_file() or path.stat().st_nlink!=1 or sha(path)!=row['sha256']):raise ValueError('Selected ordinary input missing, changed or aliased: '+row['ordinary_copy'])
  if args.check_originals_when_present and (PROJECT/old).exists():
   if sha(PROJECT/old)!=row['sha256']:raise ValueError('Preserved original byte comparison changed: '+old)
   originals+=1
  count+=1
 if count!=147:raise ValueError('Incomplete selected original copy cohort')
 print(json.dumps({'status':'authored configuration','ordinary_selected_inputs':count,'optional_original_comparisons':originals,'new_art_produced':False}))
if __name__=='__main__':main()
