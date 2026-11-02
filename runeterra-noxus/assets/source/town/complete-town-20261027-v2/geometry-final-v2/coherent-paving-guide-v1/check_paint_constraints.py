"""Exact pixel/source constraints only; never visual or final admission."""
from pathlib import Path
import argparse,json,hashlib,numpy as np
from PIL import Image
G=Path(__file__).resolve().parent;R=G.parents[5]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',required=True);ap.add_argument('--surface-control',required=True);args=ap.parse_args();candidate=Path(args.candidate).resolve();control_path=Path(args.surface_control).resolve();control=json.loads(control_path.read_text());source=G/'reference/reference-empty-native.png';base=Image.open(source).convert('RGBA');new=Image.open(candidate).convert('RGBA')
 if new.size!=(800,374):raise ValueError('Exact native800x374 canvas required')
 mask_path=R/control['paintable_mask']['path']
 if sha(mask_path)!=control['paintable_mask']['sha256']:raise ValueError('Surface edit mask differs from its declared pin')
 editable=np.asarray(Image.open(mask_path).convert('L'))>0;before=np.asarray(base);after=np.asarray(new);diff=np.any(before!=after,axis=2);outside=diff&~editable;violations=[]
 frozen=json.loads((G/'immutable-building-layers/index.json').read_text())
 for state in frozen['states']:
  for key in('frame','body','silhouette','foundation','complete-contact','full-entry','own-horizontal-treads'):
   rr=state[key]
   if sha(R/rr['path'])!=rr['sha256']:violations.append(state['state']+'/'+key)
 source_index=R/frozen['source_index']['path']
 if sha(source_index)!=frozen['source_index']['sha256']:violations.append('actual source state index')
 for row in json.loads(source_index.read_text())['states']:
  for key in('frame','body_mask','silhouette_mask','foundation_mask','door_mask','own_treads_mask','semantic_zone_mask'):
   rr=row[key]
   if sha(R/rr['path'])!=rr['sha256']:violations.append('actual selected '+row['state']+'/'+key)
 v={'scope':'Pixel/source preservation check ONLY; no visual/material/physical or final acceptance.','candidate':str(candidate),'candidate_sha256':sha(candidate),'surface_control_sha256':sha(control_path),'paintable_mask_sha256':sha(mask_path),'changed_pixels':int(diff.sum()),'changed_outside_approved_art_surface':int(outside.sum()),'immutable_source_violations':violations,'constraints_hold':not outside.any()and not violations,'visual_approval':False,'final_admission_allowed':False};print(json.dumps(v))
 if not v['constraints_hold']:raise SystemExit(2)
if __name__=='__main__':main()
