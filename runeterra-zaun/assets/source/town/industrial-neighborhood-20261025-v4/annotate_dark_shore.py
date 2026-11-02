"""Diagnostic support annotation only; this never paints or edits the background."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
bg=ROOT/'assets/source/town/industrial-neighborhood-20261025-v3/background/master-v4-dark-paths.png'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if sha(bg)!='e76cc247150d352be2ef41c92a7c6ea828e88c86e8c71b5ed59821b631b782d3':raise ValueError('Actual inspected background changed')
points=[[743,338],[751,331],[799,324],[799,373],[712,373],[717,354],[741,346]]
mask=Image.new('L',(800,374));ImageDraw.Draw(mask).polygon([tuple(p) for p in points],fill=255);mask.save(HERE/'dark-shore-annotation.png',compress_level=9)
data={'status':'authored configuration','kind':'conservative manually inspected diagnostic annotation; not painted art or machine segmentation','painted_background':bg.relative_to(ROOT).as_posix(),'painted_background_sha256':sha(bg),'polygon':points,'water_mask':(HERE/'dark-shore-annotation.png').relative_to(ROOT).as_posix(),'water_mask_sha256':sha(HERE/'dark-shore-annotation.png'),'note':'Annotated from actual native coast enlarged8x, including a small uncertain antialiased water-edge margin. Prior permission mask is distinct and does not prove actual painting. Full actual door/footing/hull inspection remains required.'}
(HERE/'dark-shore-annotation.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps(data))
