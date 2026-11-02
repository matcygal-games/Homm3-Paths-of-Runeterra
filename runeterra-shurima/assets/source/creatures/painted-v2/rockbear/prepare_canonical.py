"""Authorized transparent padding only; preserve raw PNG and pixel coordinates."""
from pathlib import Path
from PIL import Image
import json,hashlib
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
raw=Image.open(HERE/'standing-v1.png');raw.load();assert raw.size==(1774,887) and raw.mode=='RGBA'
canvas=Image.new('RGBA',(2048,1152),(0,0,0,0));canvas.paste(raw,(137,132))
dest=HERE/'standing-v2.png';assert not dest.exists();canvas.save(dest)
test=Image.open(dest);assert test.crop((137,132,1911,1019)).tobytes()==raw.tobytes()
data={'operation':'transparent canvas expansion only; not new art generation','raw':'standing-v1.png','raw_sha256':sha(HERE/'standing-v1.png'),'canvas':[2048,1152],'offset':[137,132],'source':'standing-v2.png','source_sha256':sha(dest),'full_rgba_source_region_identity':True,'source_root':[1037,992],'native_root':[218,266],'uniform_native_scale':0.075,'per_pose_crop_fit':False,'visual_approval_granted':False,'native_execution':False}
(HERE/'canonical-padding-v1.json').write_text(json.dumps(data,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(data))
