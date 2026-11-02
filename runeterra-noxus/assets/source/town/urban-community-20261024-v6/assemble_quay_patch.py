"""Technical placement of a genuinely imagegen-painted local terrain patch.

No vector/procedural paving or building edits. Pixels outside the declared crop
must remain exactly V5. Both painted input masters are retained for reproduction.
"""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageOps,ImageChops,ImageDraw
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
REPORT=ROOT/'build/reports/urban-town-community-20261024-v6'
BASE_SHA='14e00a87bcaa1eab9b46ce0a1c2943422cdfee51ac326646e773fcb68e504312'
RECT=(650,85,150,90)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def main():
 basepath=HERE/'background-native-v5.png';patchpath=HERE/'quay-local-painted-master-v6.png'
 if sha(basepath)!=BASE_SHA:raise ValueError('Base native painting changed; version the assembly')
 base=Image.open(basepath).convert('RGBA');patch=Image.open(patchpath).convert('RGBA')
 native=ImageOps.fit(patch,(150,90),method=Image.Resampling.LANCZOS)
 native.save(HERE/'quay-local-native-v6.png',compress_level=9)
 out=base.copy();out.alpha_composite(native,(RECT[0],RECT[1]));out.save(HERE/'background-master-v6.png',compress_level=9)
 diff=ImageChops.difference(base,out);outside=Image.new('L',(800,374),255);ImageDraw.Draw(outside).rectangle((650,85,799,174),fill=0)
 for band in diff.split():
  if ImageChops.multiply(band,outside).getbbox():raise ValueError('Pixels outside fixed painted patch changed')
 record={'status':'authored configuration','method':'Exact rectangular technical assembly of two genuine imagegen-painted2D sources, with uniform crop/downsample of local patch. No generated geometry, procedural paving, building pixels or painted filters.','base_native':rel(basepath),'base_native_sha256':sha(basepath),'base_painted_master':rel(HERE/'background-master-v5.png'),'base_painted_master_sha256':sha(HERE/'background-master-v5.png'),'painted_patch':rel(patchpath),'painted_patch_sha256':sha(patchpath),'painted_patch_original_size':list(patch.size),'native_patch':rel(HERE/'quay-local-native-v6.png'),'native_patch_sha256':sha(HERE/'quay-local-native-v6.png'),'patch_rectangle_xywh':RECT,'crop_fit':'Pillow ImageOps.fit LANCZOS, same5:3ratio','outside_patch_rgba_difference_pixels':0,'output':rel(HERE/'background-master-v6.png'),'output_sha256':sha(HERE/'background-master-v6.png'),'assembly_script':rel(Path(__file__)),'assembly_script_sha256':sha(Path(__file__)),'frozen_placement_plan_sha256':'93097eded68b7c275dd689c0fe344684b0e439102d4acf5c0549ba0b0c0b88c0','visual_approval_granted':False}
 write(HERE/'quay-patch-assembly-v6.json',record);write(REPORT/'quay-patch-assembly-v6.json',record)
 print(json.dumps(record))
if __name__=='__main__':main()
