"""Bounded genuine hidden Guild masonry proposals; preserve all visible RGB."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageChops
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if p.name=="runeterra-ionia")
OUT=HERE/"guild-plinth-recovery-proposal-v1"
REPORT=PROJECT/"build/reports/complete-town-20261028-v1/physical-contract-v1-guild-plinth-recovery-proposal-v1"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):return{"path":p.relative_to(PROJECT).as_posix(),"sha256":sha(p)}
def verify(r):
    p=PROJECT/r["path"]
    if sha(p)!=r["sha256"]:raise ValueError("Held input changed")
    return p
def main():
    specfile=HERE/"guild-plinth-recovery-proposal-v1.json";spec=json.loads(specfile.read_text())
    front=Image.open(verify(spec["opaque_front_kinkou"])).convert("L").point(lambda v:255 if v>=128 else 0)
    OUT.mkdir(exist_ok=False);REPORT.mkdir(exist_ok=False);rows=[]
    for state,row in spec["states"].items():
        source=Image.open(verify(row["genuine_absence_source"])).convert("RGBA")
        existing=Image.open(verify(row["corrected_existing_alpha"])).convert("L")
        visible=Image.open(verify(row["original_frame_rgb"])).convert("RGBA");visible.putalpha(existing)
        own=Image.new("L",(800,374));d=ImageDraw.Draw(own)
        for poly in row["own_masonry_polygons"]:d.polygon([tuple(p)for p in poly],fill=255)
        hidden=ImageChops.multiply(own,front)
        added=ImageChops.subtract(hidden,existing)
        merged=visible.copy();merged.paste(source,(0,0),added)
        alpha=ImageChops.lighter(existing,added);merged.putalpha(alpha)
        rawpath=OUT/(state+"-genuine-own-plinth-mask.png");own.convert("RGBA").save(rawpath)
        addpath=OUT/(state+"-hidden-recovery-mask.png");added.convert("RGBA").save(addpath)
        mergedpath=OUT/(state+"-proposed-frame.png");merged.save(mergedpath)
        box=(238,145,294,185);dark=Image.new("RGBA",(800,374),(31,33,38,255));dark.alpha_composite(merged)
        dark.crop(box).resize((672,480),Image.Resampling.NEAREST).save(REPORT/(state+"-proposed-complete-plinth-12x.png"))
        tint=Image.new("RGBA",source.size);tint.paste((255,20,0,170),(0,0),added);Image.alpha_composite(source,tint).crop(box).resize((672,480),Image.Resampling.NEAREST).save(REPORT/(state+"-recovered-pixels-on-actual-source-12x.png"))
        oldrgb=visible.convert("RGB");newrgb=merged.convert("RGB")
        changed=0
        for y in range(374):
            for x in range(800):
                if existing.getpixel((x,y))and oldrgb.getpixel((x,y))!=newrgb.getpixel((x,y)):changed+=1
        rowout={"state":state,"own_plinth":pin(rawpath),"new_hidden_recovery":pin(addpath),"proposed_frame":pin(mergedpath),"added_pixels":added.histogram()[255],"added_bounds":added.getbbox(),"previously_visible_rgb_changes":changed,"all_added_pixels_opaque_hidden_by_existing_highest_kinkou":ImageChops.subtract(added,front).getbbox()is None,"genuine_source":row["genuine_absence_source"],"semantic_review_pending":True};rows.append(rowout)
    receipt={"status":"design proposal","annotation":pin(specfile),"states":rows,"held_frames_modified":False,"consumer_execution":False,"native_execution":False,"release_accepted":False};(REPORT/"receipt.json").write_text(json.dumps(receipt,indent=2)+"\n");print(json.dumps(receipt,indent=2))
if __name__=="__main__":main()
