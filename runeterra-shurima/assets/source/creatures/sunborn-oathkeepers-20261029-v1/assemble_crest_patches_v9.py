"""Register localized imagegen-painted embroidery; retain original action geometry.

This is deterministic source assembly, not generated geometric artwork. The
original RGBA is retained outside declared tabard rectangles, and original
alpha is retained everywhere. Every replacement RGB comes from a preserved
built-in imagegen edit. No original game frame enters the output.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parent
REPORT=ROOT.parents[4]/'reports/shurima-sunborn-revision-20261029-v1/art-t7-crest-v9'
UNITS={
 'sunbornOathkeeper':{
  'walk':('walk-v5.png','walk-crest-edit-v1.png',[(289,304),(768,304),(767,806)]),
  'locomotion':('locomotion-v3.png','locomotion-crest-edit-v1.png',[(901,587),(1267,594),(191,942),(553,942),(893,941)]),
  'combat':('combat-v2.png','combat-crest-edit-v2.png',[(198,247),(541,234),(867,245),(1245,242),(206,598),(546,595),(902,602),(1257,598),(206,948),(535,947),(897,949),(1249,941)]),
  'reactions':('reactions-v2.png','reactions-crest-edit-v1.png',[(229,357),(685,357),(1122,339),(1119,751),(1540,737)])},
 'exaltedOathkeeper':{
  'walk':('walk-v5.png','walk-crest-v1.png',[(279,305),(760,305),(759,810)]),
  'locomotion':('locomotion-v2.png','locomotion-crest-edit-v1.png',[(901,574),(1266,575),(193,933),(552,932),(896,930)]),
  'combat':('combat-v1.png','combat-crest-edit-v1.png',[(200,269),(495,267),(862,267),(1260,270),(216,599),(550,579),(908,577),(1261,583),(207,941),(559,941),(900,940),(1310,934)]),
  'reactions':('reactions-v1.png','reactions-crest-edit-v1.png',[(225,353),(675,329),(1124,313),(206,751)])}}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,data):
 path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists() and path.read_bytes()!=data:raise ValueError('Immutable output differs: '+str(path))
 if not path.exists():path.write_bytes(data)
def png(im):
 import io
 buf=io.BytesIO();im.save(buf,format='PNG');return buf.getvalue()

def registration(original,edited,x,y):
 # Local unchanged RGB ring registers each pose independently; the emblem is
 # excluded from the score. This does not deform either painted source.
 a=np.asarray(original.convert('RGBA'));b=np.asarray(edited.convert('RGBA'))
 radius=42; yy,xx=np.mgrid[-radius:radius,-radius:radius]
 ring=((abs(xx)>29)|(abs(yy)>31)) & ((xx % 3)==0) & ((yy % 3)==0)
 sample=a[y-radius:y+radius,x-radius:x+radius]
 valid=ring & (sample[:,:,3]>192)
 best=None
 for dy in range(-48,49,2):
  for dx in range(-48,49,2):
   other=b[y-radius+dy:y+radius+dy,x-radius+dx:x+radius+dx]
   if other.shape!=sample.shape:continue
   difference=np.abs(sample[:,:,:3].astype(np.int16)-other[:,:,:3].astype(np.int16)).mean(axis=2)
   score=float(difference[valid].mean()) + .025*(abs(dx)+abs(dy))
   if best is None or score<best[0]:best=(score,dx,dy)
 return best

def main():
 ledger={'status':'authored configuration','method':__doc__,'sources':[]};tiles=[]
 for unit,sheets in UNITS.items():
  for role,(original_name,edit_name,centres) in sheets.items():
   original_path=ROOT/unit/original_name; edit_path=ROOT/unit/edit_name
   original=Image.open(original_path).convert('RGBA');edit=Image.open(edit_path).convert('RGBA')
   if edit.size!=original.size:raise ValueError('Register edited sheet dimensions explicitly first')
   output=original.copy();patches=[]
   for index,(x,y) in enumerate(centres):
    score,dx,dy=registration(original,edit,x,y)
    # The patch stays inside the physical tabard. A short upper patch is used
    # where a polearm crosses below the emblem; hidden emblems are omitted.
    halfx,halfy=(26,50 if role=='walk' else 30)
    box=(x-halfx,y-halfy,x+halfx,y+halfy)
    srcbox=tuple(v+(dx if i%2==0 else dy) for i,v in enumerate(box))
    crop=edit.crop(srcbox);old=original.crop(box)
    # Preserve geometry/coverage. Patch feather affects only existing painted
    # RGB and does not add alpha, tint a silhouette or draw an emblem.
    arr=np.array(crop);oa=np.array(old)
    arr[:,:,3]=oa[:,:,3]
    mask=Image.new('L',old.size,255)
    edge=np.minimum.reduce([np.indices((old.height,old.width))[0],np.indices((old.height,old.width))[1],old.height-1-np.indices((old.height,old.width))[0],old.width-1-np.indices((old.height,old.width))[1]])
    mask=Image.fromarray(np.minimum(255,edge*85).astype('uint8'))
    combined=Image.composite(Image.fromarray(arr),old,mask)
    output.paste(combined,box[:2])
    patches.append({'box':list(box),'edit_box':list(srcbox),'registration_offset':[dx,dy],'ring_score':score})
    tile=Image.new('RGBA',(216,145),'#252525');draw=ImageDraw.Draw(tile)
    draw.text((4,2),f'{unit[:1]} {role} {index}',fill='white')
    tile.alpha_composite(old.resize((104,120)),(2,20));tile.alpha_composite(combined.resize((104,120)),(110,20));tiles.append(tile)
   oldarr=np.array(original);outarr=np.array(output)
   assert np.array_equal(oldarr[:,:,3],outarr[:,:,3])
   allowed=np.zeros(oldarr.shape[:2],bool)
   for p in patches:
    l,t,r,b=p['box'];allowed[t:b,l:r]=True
   assert np.array_equal(oldarr[~allowed],outarr[~allowed])
   target=ROOT/unit/(role+'-crest-local-v9.png');write(target,png(output))
   ledger['sources'].append({'unit':unit,'role':role,'input':original_path.relative_to(ROOT).as_posix(),'input_sha256':sha(original_path),'painted_edit':edit_path.relative_to(ROOT).as_posix(),'painted_edit_sha256':sha(edit_path),'output':target.relative_to(ROOT).as_posix(),'output_sha256':sha(target),'alpha_identical':True,'outside_patch_rgba_identical':True,'patches':patches})
 sheet=Image.new('RGBA',(216*6,145*((len(tiles)+5)//6)),'#252525')
 for i,tile in enumerate(tiles):sheet.alpha_composite(tile,((i%6)*216,(i//6)*145))
 write(REPORT/'patch-before-after.png',png(sheet))
 write(REPORT/'patch-ledger.json',(json.dumps(ledger,sort_keys=True,indent=2)+'\n').encode())
 print(json.dumps({'sheets':len(ledger['sources']),'patches':len(tiles),'alpha_preserved':True}))
if __name__=='__main__':main()
