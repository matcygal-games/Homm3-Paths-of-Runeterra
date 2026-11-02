"""Reproduce native repair bitmaps from genuine held painted masters, no artwork."""
from pathlib import Path
from io import BytesIO
import json,hashlib
from PIL import Image
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if p.name=='runeterra-ionia')
def digest(data):return hashlib.sha256(data).hexdigest()
def main():
 records=json.loads((HERE/'painted-repairs-provenance.json').read_text())['records'];products={}
 for row in records:
  raw=PROJECT/row['master']['path'];native=PROJECT/row['native']['path']
  if digest(raw.read_bytes())!=row['master']['sha256']:raise ValueError('Painted master changed: '+row['id'])
  if not native.resolve().is_relative_to(HERE):raise ValueError('Native conversion escapes assigned source')
  image=Image.open(raw).convert('RGBA').resize(tuple(row['native_dimensions']),Image.Resampling.LANCZOS);stream=BytesIO();image.save(stream,format='PNG');data=stream.getvalue()
  if digest(data)!=row['native']['sha256']:raise ValueError('Replayed genuine master conversion changed: '+row['id'])
  products[native]=data
 for path,data in products.items():path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
 print(json.dumps({'status':'authored configuration','genuine_master_native_replays':len(products),'all_source_PNG_hashes_exact':True,'artwork_created_by_this_script':False}))
if __name__=='__main__':main()
