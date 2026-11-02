"""Technical alpha-matting proposal from exact held native pixels, no art edits."""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw, ImageChops

HERE = Path(__file__).resolve().parent
PROJECT = next(p for p in HERE.parents if p.name == "runeterra-ionia")
BASE = HERE.parent
REPORT = PROJECT / "build/reports/complete-town-20261028-v1/physical-contract-v1-contour-proposal-v2"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    plan = json.loads((HERE / "contour-proposal-v2.json").read_text())
    freeze = json.loads((BASE / "FRAME-FREEZE-v1.json").read_text())
    source_path = PROJECT / plan["source"]
    assert sha(source_path) == plan["source_sha256"]
    source = Image.open(source_path).convert("RGBA")
    states = {}
    for state in ("blacksmith", "shipyard", "ship"):
        item = freeze["frames"][state]
        path = PROJECT / item["path"]
        assert sha(path) == item["sha256"]
        states[state] = Image.open(path).convert("RGBA")
    output = HERE / "contour-proposal-v2"
    output.mkdir(exist_ok=False)
    REPORT.mkdir(parents=True, exist_ok=False)
    masks = {}
    prior = states["blacksmith"].getchannel("A").point(lambda x: 255 if x >= 8 else 0)
    proposal = prior.copy()
    ImageDraw.Draw(proposal).rectangle((0,0,799,288), fill=0)
    top = Image.new("L", source.size)
    ImageDraw.Draw(top).polygon([tuple(p) for p in plan["workshop_upper_polygon"]], fill=255)
    proposal = ImageChops.lighter(proposal, top)
    box = plan["garden_water_key_bounds"]
    for y in range(box[1],box[3]):
        for x in range(box[0],box[2]):
            r,g,b,_ = source.getpixel((x,y))
            if g > r+10 and b > r+10 and b > g+2:
                proposal.putpixel((x,y),0)
    masks["blacksmith"] = proposal
    for state in ("shipyard","ship"):
        old = states[state].getchannel("A").point(lambda x:255 if x>=8 else 0)
        masks[state] = ImageChops.subtract(old, proposal)
    facts = {}
    for state, mask in masks.items():
        old = states[state].getchannel("A").point(lambda x:255 if x>=8 else 0)
        added,removed = ImageChops.subtract(mask,old),ImageChops.subtract(old,mask)
        mask_path = output / (state+"-proposed-mask.png")
        mask.convert("RGBA").save(mask_path)
        # Preview uses untouched actual selected painted RGB, only proposed alpha.
        preview = source.copy()
        preview.putalpha(mask)
        background = Image.new("RGBA",source.size,(45,45,45,255))
        background.alpha_composite(preview)
        background.convert("RGB").save(REPORT/(state+"-proposed-visible.png"))
        overlay=source.convert("RGB")
        layer=Image.new("RGBA",source.size)
        layer.paste((255,50,30,210),(0,0),removed)
        layer.paste((20,220,255,210),(0,0),added)
        overlay=Image.alpha_composite(overlay.convert("RGBA"),layer)
        overlay.save(REPORT/(state+"-ownership-delta.png"))
        crop=background.convert("RGB").crop((0,200,280,290)).resize((1120,360),Image.Resampling.NEAREST)
        crop.save(REPORT/(state+"-coast-roof-detail-4x.png"))
        facts[state]={"mask_path":mask_path.relative_to(PROJECT).as_posix(),"mask_sha256":sha(mask_path),
                      "pixels_added":added.histogram()[255],"added_bounds":added.getbbox(),
                      "pixels_removed":removed.histogram()[255],"removed_bounds":removed.getbbox()}
    result={"status":"design proposal","source":plan["source"],"source_sha256":sha(source_path),
            "held_frame_index_sha256":freeze["frame_index"]["sha256"],"proposals":facts,
            "frame_pixels_or_files_modified":False,"source_rgb_painting_modified":False,
            "art_owner_review_required":True,"physical_geometry_accepted":False,"release_accepted":False}
    (output/"proposal-receipt.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    (REPORT/"proposal-receipt.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps(result,indent=2))


if __name__ == "__main__":
    main()
