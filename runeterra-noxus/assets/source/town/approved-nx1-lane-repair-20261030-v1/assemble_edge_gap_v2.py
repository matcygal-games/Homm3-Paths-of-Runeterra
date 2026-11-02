"""Finite technical composite of two generated supported-stair corrections."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFilter,ImageChops
HERE=Path(__file__).resolve().parent
PATHS=[[(577,174),(598,174),(613,177)],[(779,285),(795,300),(794,332),(794,373)]]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 prior=Image.open(HERE/'repaired-native-v1.png').convert('RGBA')
 generated=Image.open(HERE/'edge-gap-master-v2.png').convert('RGBA').resize(prior.size,Image.Resampling.LANCZOS)
 mask=Image.new('L',prior.size);d=ImageDraw.Draw(mask)
 d.line(PATHS[0],fill=255,width=11);d.line(PATHS[1],fill=255,width=23)
 mask=mask.filter(ImageFilter.GaussianBlur(.5))
 scene=Image.composite(generated,prior,mask)
 original=Image.open(HERE.parent/'approved-nx1-20261029-v1/approved-native.png').convert('RGBA')
 delta=ImageChops.difference(scene.convert('RGB'),original.convert('RGB'));changed=sum(any(delta.getpixel((x,y)))for y in range(374)for x in range(800))
 scene.save(HERE/'repaired-native-v2.png',compress_level=9);mask.save(HERE/'edge-gap-region-v2.png')
 edge_delta=ImageChops.difference(scene,prior)
 receipt={'status':'authored configuration','candidate_only':True,'not_selected':True,'master_sha256':sha(HERE/'edge-gap-master-v2.png'),'prompt_sha256':sha(HERE/'edge-gap-v2.prompt.txt'),'native_sha256':sha(HERE/'repaired-native-v2.png'),'original_approved_sha256':sha(HERE.parent/'approved-nx1-20261029-v1/approved-native.png'),'changed_pixels_from_approved':changed,'changed_percent_from_approved':100*changed/(800*374),'edge_region_pixels':sum(bool(v)for v in mask.getdata()),'edge_region_sha256':sha(HERE/'edge-gap-region-v2.png'),'outside_edge_region_changed_from_v1':sum(any(edge_delta.getpixel((x,y)))for y in range(374)for x in range(800)if not mask.getpixel((x,y))),'paths':PATHS}
 (HERE/'edge-gap-receipt-v2.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
