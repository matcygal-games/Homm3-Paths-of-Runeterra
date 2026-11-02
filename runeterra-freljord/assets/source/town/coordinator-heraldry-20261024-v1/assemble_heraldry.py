"""Local technical compositing of genuine imagegen crest edits; no drawn art."""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SPECS = {
    "villageHall": ("assets/source/town/buildings-v1/villageHall/master.png", [(465,249,630,376)]),
    "townHall": ("assets/source/town/buildings-v1/townHall/master.png", [(470,227,610,380)]),
    "cityHall": ("assets/source/town/buildings-v1/cityHall/master.png", [(493,333,650,480)]),
    "capitol": ("assets/source/town/buildings-v5/capitol/master.png", [
        (490,408,646,527), (249,682,281,779), (956,369,1000,488),
        (1028,736,1074,836), (1400,490,1432,590), (1327,734,1358,835)]),
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

records = []
for name, (original_path, rectangles) in SPECS.items():
    folder = HERE / name
    original = ROOT / original_path
    edited = folder / "imagegen-edit.png"
    with Image.open(original) as value:
        base = value.convert("RGBA")
    with Image.open(edited) as value:
        patch = value.convert("RGBA")
    assert base.size == patch.size == (1536,1024)
    mask = Image.new("L", base.size, 0)
    draw = ImageDraw.Draw(mask)
    for x0,y0,x1,y1 in rectangles:
        draw.rectangle((x0,y0,x1-1,y1-1), fill=255)
    # Two-pixel transition is purely a seam in the selected local edited pixels.
    mask = mask.filter(ImageFilter.GaussianBlur(1))
    merged = Image.composite(patch, base, mask)
    merged.putalpha(base.getchannel("A"))
    merged.save(folder / "master.png")
    mask.save(folder / "technical-composite-mask.png")
    before, after, selected = np.asarray(base), np.asarray(merged), np.asarray(mask)
    assert np.array_equal(before[:,:,3], after[:,:,3])
    assert np.array_equal(before[selected==0], after[selected==0])
    changed = np.any(before != after, axis=2)
    record = {"state": name, "source": original_path, "source_sha256": sha(original),
              "genuine_imagegen_edit": str(edited.relative_to(ROOT)).replace("\\","/"),
              "edit_sha256": sha(edited), "local_rectangles": rectangles,
              "technical_mask_sha256": sha(folder / "technical-composite-mask.png"),
              "output": str((folder / "master.png").relative_to(ROOT)).replace("\\","/"),
              "output_sha256": sha(folder / "master.png"), "dimensions": list(base.size),
              "alpha_preserved_exactly": True, "pixels_outside_mask_preserved_exactly": True,
              "changed_pixels": int(changed.sum()), "mask_pixels": int((selected>0).sum())}
    (folder / "assembly.json").write_text(json.dumps(record,indent=2)+"\n")
    records.append(record)
    # Native-size technical previews only; selected final site dimensions are owner-controlled.
    merged.thumbnail((200,140),Image.Resampling.LANCZOS)
    merged.save(folder / "native-preview.png")
(HERE / "selection.json").write_text(json.dumps({"status":"authored configuration", "method":"built-in imagegen edits plus bounded technical compositing", "scope":"Four communal hall heraldry candidates; no active selection, no native or release approval", "records":records},indent=2)+"\n")
print(json.dumps({"masters":len(records),"outside_mask_changes":0,"alpha_changes":0}))
