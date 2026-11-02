"""Replay the three genuine protected ground recoveries without rewriting them."""
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw,ImageChops
import json,hashlib
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pinned(r):
 p=PROJECT/r['path']
 if sha(p)!=r['sha256']:raise ValueError('Declared source changed: '+r['path'])
 return p
def main():
 record=json.loads((HERE/'additional-hidden-support-selection-v1.json').read_text())
 current=Image.open(pinned(record['before_background'])).convert('RGBA');budget=Image.open(HERE/'approved-full-opaque-budget.png').convert('L')
 for name,row in record['recoveries'].items():
  master=pinned(row['genuine_master']);native=ImageOps.fit(Image.open(master).convert('RGB').crop(row['raw_content_crop']),tuple(row['one_uniform_fit']),method=Image.Resampling.LANCZOS)
  if native.tobytes()!=Image.open(pinned(row['native_source'])).convert('RGB').tobytes():raise ValueError('Native one-fit changed: '+name)
  pinned(row['actual_prompt'])
  for r in row['controls']:pinned(r)
  mask=Image.new('L',(800,374));ImageDraw.Draw(mask).polygon([tuple(p) for p in row['planned_polygon']],fill=255);mask=ImageChops.multiply(mask,budget)
  if mask.tobytes()!=Image.open(pinned(row['selected_mask'])).convert('L').tobytes():raise ValueError('Protected selection changed: '+name)
  proposed=current.copy();box=row['native_context'];dx,dy=row['whole_painted_crop_registration'];proposed.paste(native,(box[0]+dx,box[1]+dy));current=Image.composite(proposed,current,mask)
 if current.tobytes()!=Image.open(pinned(record['new_background'])).convert('RGBA').tobytes():raise ValueError('Recovered final background changed')
 index=json.loads(pinned(record['state_index']).read_text());full=current.copy()
 for state in index['full_scene_states']:
  row=index['states'][state];p=PROJECT/row['frame']
  if sha(p)!=row['frame_sha256']:raise ValueError('Selected frame changed: '+state)
  full.alpha_composite(Image.open(p).convert('RGBA'))
 if full.convert('RGB').tobytes()!=Image.open(pinned(record['approved_full'])).convert('RGB').tobytes():raise ValueError('Approved full changed')
 print(json.dumps({'genuine_recoveries_replayed':len(record['recoveries']),'changed_output_pixels':0,'approved_full_changed_pixels':0,'sources_verified':True,'physical_baseline_passed':False}))
if __name__=='__main__':main()
