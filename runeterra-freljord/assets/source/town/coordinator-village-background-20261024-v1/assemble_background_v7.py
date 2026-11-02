"""Tightly assemble two genuinely painted openings without changing other scenery."""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
HERE = Path(__file__).resolve().parent
with Image.open(HERE / "background-v6-native.png") as image:
    base = image.convert("RGB")
result = base.copy()
union = Image.new("L",base.size)
specs = [("seer",(293,264),(307,274,331,292)),("draklorn",(437,251),(449,263,473,281))]
for name, origin, rect in specs:
    with Image.open(HERE / (name+"-opening-imagegen-v7.png")) as image:
        painted = image.convert("RGB").resize((56,46),Image.Resampling.LANCZOS)
    layer = result.copy()
    layer.paste(painted,origin)
    mask = Image.new("L",base.size)
    ImageDraw.Draw(mask).rectangle((rect[0],rect[1],rect[2]-1,rect[3]-1),fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(1))
    result = Image.composite(layer,result,mask)
    union = Image.fromarray(np.maximum(np.asarray(union),np.asarray(mask)))
    mask.save(HERE / (name+"-opening-assembly-mask-v7.png"))
before,after,selected = np.asarray(base),np.asarray(result),np.asarray(union)
assert np.array_equal(before[selected==0],after[selected==0])
result.save(HERE / "background-v7-native.png")
union.save(HERE / "openings-union-mask-v7.png")
print(json.dumps({"background_sha256":hashlib.sha256((HERE / "background-v7-native.png").read_bytes()).hexdigest(),"outside_masks_changes":0,"scope":"Genuine painted path pixels; two bounded technical assemblies; no coordinate changes or code-drawn art."}))
