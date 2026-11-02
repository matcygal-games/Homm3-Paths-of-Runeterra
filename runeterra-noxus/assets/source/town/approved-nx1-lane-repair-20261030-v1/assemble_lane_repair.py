"""Replay the frozen sparse painted road edit; no selection or stage writes."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw,ImageFilter,ImageChops
HERE=Path(__file__).resolve().parent
PRIOR=HERE.parent/'approved-nx1-20261029-v1'
PATHS=[[(130,100),(130,115),(215,127),(221,155),(218,185),(209,199),(178,220),(179,248),(180,280),(180,326),(185,337)],[(302,119),(330,133),(336,155),(339,190),(336,217),(346,235),(365,251),(365,279),(364,313),(380,325)],[(508,120),(520,135),(526,159),(526,184),(525,216),(520,235),(487,257),(480,279),(478,309),(483,329),(489,346),(501,358)],[(650,114),(637,137),(632,164),(632,189),(643,217),(645,243),(687,246),(716,249),(742,261),(779,285)]]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 receipt=json.loads((HERE/'repair-receipt-v1.json').read_text())
 if sha(PRIOR/'approved-native.png')!=receipt['approved_native_sha256'] or sha(HERE/'whole-lane-repair-master.png')!=receipt['painted_master_sha256']:raise ValueError('Frozen painted input changed')
 a=Image.open(PRIOR/'approved-native.png').convert('RGB');b=Image.open(HERE/'whole-lane-repair-master.png').convert('RGB').resize(a.size,Image.Resampling.LANCZOS)
 mask=Image.new('L',a.size);draw=ImageDraw.Draw(mask)
 for path in PATHS:draw.line(path,fill=255,width=15)
 mask=mask.filter(ImageFilter.GaussianBlur(.5));final=Image.composite(b,a,mask)
 if final.tobytes()!=Image.open(HERE/'repaired-native-v1.png').convert('RGB').tobytes():raise ValueError('Sparse whole-scene replay differs')
 if mask.tobytes()!=Image.open(HERE/'repair-region-mask-v1.png').convert('L').tobytes():raise ValueError('Sparse mask replay differs')
 outside=ImageChops.invert(mask.point(lambda x:255 if x else 0));difference=ImageChops.difference(a,final)
 if ImageChops.multiply(difference,Image.merge('RGB',(outside,)*3)).getbbox():raise ValueError('Pixels outside finite repair region changed')
 print(json.dumps({'replay_verified':True,'sparse_region_only':True,'selection_or_native_changed':False}))
if __name__=='__main__':main()
