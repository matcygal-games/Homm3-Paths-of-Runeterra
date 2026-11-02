"""Reproduce selected pixels in memory from three owned inputs; never overwrite selection."""
from pathlib import Path
from PIL import Image,ImageOps
import hashlib,io,json
HERE=Path(__file__).resolve().parent
def main():
 base=Image.open(HERE/'input-scene/native-structural-base.png').convert('RGBA');master=Image.open(HERE/'whole-scene-master-v1.png').convert('RGBA');mask=Image.open(HERE/'surface-mask-v1.png').convert('L');paint=ImageOps.fit(master,(800,374),Image.Resampling.LANCZOS,centering=(.5,.5));out=Image.composite(paint,base,mask);b=io.BytesIO();out.save(b,format='PNG',compress_level=9);digest=hashlib.sha256(b.getvalue()).hexdigest();expected='3e049c20df7009209ba424c46a450581d0097b35d1daa216f59e2df4600f0a5b';assert digest==expected;assert b.getvalue()==(HERE/'surface-painted-native-v1.png').read_bytes();print(json.dumps({'reproduced_sha256':digest,'selected_bytes_identical':True,'selected_file_not_written':True,'global_master_fits':1,'local_texture_resizes':0}))
if __name__=='__main__':main()
