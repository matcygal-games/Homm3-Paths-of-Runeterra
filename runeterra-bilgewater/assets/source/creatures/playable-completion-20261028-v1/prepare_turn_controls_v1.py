"""Read-only native-consumer endpoint diagnostics, no creative drawing."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageOps,ImageDraw
S=Path(__file__).resolve().parent;P=S.parents[3];R=P/'build/reports/painted-creature-completion-20261028-v1/private-controls/turn-endpoints-v1';R.mkdir(parents=True,exist_ok=True)
versions={'bilgeRat':3,'seaDog':3,'corsair':3,'pirateMarksman':3,'shellshotGunner':2,'reefBombardier':2,'krakenPriest':2,'tideHierophant':2,'boardingCaptain':2,'fleetVeteran':2}
records=[]
for unit,v in versions.items():
 folder=S/unit/f'native-v{v}/right';p=sorted(folder.glob('g07-*.png'))[-1];q=folder/'g02-f000.png'
 front=Image.open(p).convert('RGBA');mir=ImageOps.mirror(front);start=Image.new('RGBA',(450,400));start.alpha_composite(mir,(-58,0));end=Image.open(q).convert('RGBA')
 board=Image.new('RGB',(1440,650),(86,91,84));d=ImageDraw.Draw(board)
 for i,(label,im)in enumerate([('START: exact front after native-facing compensation',start),('END: right-facing ready',end)]):
  crop=im.crop((120,140,300,290)).resize((720,600),Image.Resampling.NEAREST);board.paste(crop,(i*720,40),crop);d.text((i*720+8,8),label,fill='white')
 out=R/f'{unit}.png';board.save(out)
 records.append({'unit':unit,'start_from':p.relative_to(P).as_posix(),'start_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'end_from':q.relative_to(P).as_posix(),'end_sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'transform':'Full450px horizontal reflection followed by x=-58px translation; only technical consumer endpoint reference','output':out.relative_to(P).as_posix(),'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest()})
(R/'controls.json').write_text(json.dumps(records,indent=2,sort_keys=True)+'\n')
