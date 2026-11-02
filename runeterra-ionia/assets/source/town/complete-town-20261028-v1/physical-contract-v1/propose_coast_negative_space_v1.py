"""Bounded technical river/air alpha extraction; preserves exact painted RGB."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageChops

HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if p.name=="runeterra-ionia")
BASE=HERE.parent
OUT=HERE/"coast-negative-space-proposal-v1"
REPORT=PROJECT/"build/reports/complete-town-20261028-v1/physical-contract-v1-coast-negative-space-proposal-v1"

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def extract(image,mask,bounds):
    result=mask.copy()
    for y in range(bounds[1],bounds[3]):
        for x in range(bounds[0],bounds[2]):
            if not result.getpixel((x,y)):continue
            r,g,b,_=image.getpixel((x,y))
            if g>r+12 and b>r+12 and b>g-8:result.putpixel((x,y),0)
    return result

def main():
    plan=json.loads((HERE/"coast-negative-space-proposal-v1.json").read_text())
    freeze=json.loads((BASE/"FRAME-FREEZE-v1.json").read_text())
    source_path=PROJECT/plan["hidden_pier_source"];hidden_path=HERE/plan["hidden_mask"]
    assert sha(source_path)==plan["hidden_pier_source_sha256"]and sha(hidden_path)==plan["hidden_mask_sha256"]
    hidden_source=Image.open(source_path).convert("RGBA");hidden_before=Image.open(hidden_path).getchannel("R")
    hidden=extract(hidden_source,hidden_before,plan["bounds"])
    OUT.mkdir(exist_ok=False);REPORT.mkdir(parents=True,exist_ok=False)
    hidden_output=OUT/"hidden-main-pier-negative-spaces.png";hidden.convert("RGBA").save(hidden_output)
    rows={}
    for state in ("shipyard","ship"):
        reference=freeze["frames"][state];path=PROJECT/reference["path"];assert sha(path)==reference["sha256"]
        source=Image.open(path).convert("RGBA")
        old=Image.open(HERE/"contour-proposal-v2"/(state+"-proposed-mask.png")).getchannel("R")
        visible=extract(source,old,plan["bounds"])
        target=OUT/(state+"-visible-negative-spaces.png");visible.convert("RGBA").save(target)
        main=source.copy();main.putalpha(visible)
        patch=hidden_source.copy();patch.putalpha(hidden)
        actor=Image.new("RGBA",(800,374));actor.alpha_composite(main);actor.alpha_composite(patch)
        preview=Image.new("RGBA",(800,374),(45,45,45,255));preview.alpha_composite(actor)
        preview.convert("RGB").crop((0,155,200,280)).resize((1000,625),Image.Resampling.NEAREST).save(REPORT/(state+"-negative-spaces-5x.png"))
        removed=ImageChops.subtract(old,visible)
        rows[state]={"visible_mask_path":target.relative_to(PROJECT).as_posix(),"visible_mask_sha256":sha(target),
                     "ambient_blue_pixels_removed":removed.histogram()[255],"removed_bounds":removed.getbbox(),
                     "actual_painted_rgb_changed":False}
    result={"status":"design proposal","visible_masks":rows,
            "hidden_mask":{"path":hidden_output.relative_to(PROJECT).as_posix(),"sha256":sha(hidden_output),"retained_pixels":hidden.histogram()[255],"ambient_blue_removed":ImageChops.subtract(hidden_before,hidden).histogram()[255]},
            "frame_or_source_files_modified":False,"art_owner_review_required":True,"physical_contact_acceptance":False,"release_accepted":False}
    (OUT/"proposal-receipt.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    (REPORT/"proposal-receipt.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps(result,indent=2))

if __name__=="__main__":main()
