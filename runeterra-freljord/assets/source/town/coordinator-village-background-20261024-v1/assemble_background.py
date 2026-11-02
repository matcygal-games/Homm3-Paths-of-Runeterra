"""Reproduce technical conversion of retained genuine painted background edits."""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

HERE = Path(__file__).resolve().parent

for index in (1,2):
    with Image.open(HERE / f"imagegen-v{index}.png") as image:
        image.convert("RGB").resize((800,374),Image.Resampling.LANCZOS).save(HERE / f"background-v{index}-native.png")
with Image.open(HERE / "quay-imagegen-edit.png") as source:
    # Select only the genuine all-dry upper part; the generator's water is not selected.
    patch = source.convert("RGB").crop((0,0,source.width,420)).resize((240,80),Image.Resampling.LANCZOS)
patch.save(HERE / "quay-selected-dry-paint.png")
with Image.open(HERE / "background-v2-native.png") as source:
    base = source.convert("RGB")
layer = base.copy()
layer.paste(patch,(560,110))
mask = Image.new("L",base.size)
ImageDraw.Draw(mask).rectangle((560,110,799,189),fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(.7))
result = Image.composite(layer,base,mask)
before,after,selected = np.asarray(base),np.asarray(result),np.asarray(mask)
assert np.array_equal(before[selected==0],after[selected==0])
mask.save(HERE / "quay-assembly-mask.png")
result.save(HERE / "background-v3-native.png")
print(json.dumps({"native_canvas":[800,374],"background_sha256":hashlib.sha256((HERE / "background-v3-native.png").read_bytes()).hexdigest(),"outside_mask_changes":0,"art_created_by_code":False}))
