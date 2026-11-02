from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import hashlib,json
P=Path('runeterra-freljord')
WINDOWS={'starlitSeer':{'shot-release-up':(1075,0,1254,180),'shot-release-down':(1080,704,1254,870)},
'winterVeilSeer':{'shot-release-up':(1058,75,1254,218),'shot-release-front':(1110,300,1254,420),'shot-release-down':(1038,742,1254,850)}}
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for unit,poses in WINDOWS.items():
 folder=P/f'assets/source/creatures/painted-20261024/{unit}';dest=folder/'release-split-v1';dest.mkdir(exist_ok=True)
 receipts=[]
 for key,box in poses.items():
  source=folder/'masters'/f'{key}.png';raw=Image.open(source).convert('RGBA')
  body=raw.copy();body.paste((0,0,0,0),box)
  loose=Image.new('RGBA',raw.size);loose.paste(raw.crop(box),box[:2])
  mask=Image.new('L',raw.size);ImageDraw.Draw(mask).rectangle((box[0],box[1],box[2]-1,box[3]-1),fill=255)
  bp=dest/f'{key}-body.png';lp=dest/f'{key}-detached-projectile.png';mp=dest/f'{key}-mask.png'
  body.save(bp);loose.save(lp);mask.save(mp)
  differences=ImageChops.difference(body,raw)
  differences.paste((0,0,0,0),box)
  unchanged=all(channel.getbbox() is None for channel in differences.split())
  if not unchanged:raise AssertionError('Body changed outside detached-object mask')
  receipts.append(dict(pose=key,raw_source=source.relative_to(P).as_posix(),raw_sha256=h(source),
   manual_detached_object_rectangle=list(box),body=bp.relative_to(P).as_posix(),body_sha256=h(bp),
   detached_projectile=lp.relative_to(P).as_posix(),detached_projectile_sha256=h(lp),mask_sha256=h(mp),
   assertion='Every body pixel outside manually inspected detached-projectile rectangle remains unchanged.',
   verified_outside_mask_unchanged=unchanged))
 (dest/'technical-alpha-split-v1.json').write_text(json.dumps(dict(status='authored configuration',
   method='Technical alpha separation of already detached painted projectile. Open hand and every original body pixel are preserved.',
   records=receipts),sort_keys=True,indent=2)+'\n')
 print(unit,len(receipts))

