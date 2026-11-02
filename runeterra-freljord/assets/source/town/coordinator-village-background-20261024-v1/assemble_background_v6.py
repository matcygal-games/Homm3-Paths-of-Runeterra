"""Reproduce retained genuine painted scene/harbor conversion and local assembly."""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
HERE = Path(__file__).resolve().parent
with Image.open(HERE / "imagegen-v5.png") as image:
    base = image.convert("RGB").resize((800,374),Image.Resampling.LANCZOS)
with Image.open(HERE / "harbor-imagegen-v6.png") as image:
    coast = image.convert("RGB").resize((120,100),Image.Resampling.LANCZOS)
coast.save(HERE / "harbor-native-v6.png")
layer = base.copy()
layer.paste(coast,(680,145))
mask = Image.new("L",base.size)
ImageDraw.Draw(mask).rectangle((680,145,799,244),fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(1))
result = Image.composite(layer,base,mask)
before,after,selected = np.asarray(base),np.asarray(result),np.asarray(mask)
assert np.array_equal(before[selected==0],after[selected==0])
result.save(HERE / "background-v6-native.png")
mask.save(HERE / "harbor-assembly-mask-v6.png")
# Diagnostic coast annotation only, not art, navigation or a general water detector.
a = np.asarray(coast)
r,g,b = [a[:,:,i].astype(int) for i in range(3)]
raw = (b-r>35)&(g-r>15)&(r<100)&(g<145)&(b>70)
water = np.zeros((374,800),dtype=np.uint8)
for y in range(35,100):
    xs = np.flatnonzero(raw[y])
    xs = xs[xs>=42]
    if len(xs)>=5:
        water[145+y,680+int(xs.min()):800] = 255
Image.fromarray(water).save(HERE / "painted-water-annotation-v6.png")
print(json.dumps({"background_sha256":hashlib.sha256((HERE / "background-v6-native.png").read_bytes()).hexdigest(),"outside_mask_changes":0,"scope":"Technical assembly and bounded diagnostic annotation; all artistic pixels from retained genuine paintings."}))
