"""Propose actual short-pier Ship matting; never edit the held painted source."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw,ImageChops

HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if p.name=="runeterra-ionia")
REPORT=PROJECT/"build/reports/complete-town-20261028-v1/physical-contract-v1-short-dock-contour-proposal-v3"
SPEC=HERE/"short-dock-contour-proposal-v3.json"
OUT=HERE/"short-dock-contour-proposal-v3"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    spec=json.loads(SPEC.read_text());source=PROJECT/spec["source"]["path"]
    if sha(source)!=spec["source"]["sha256"]:raise ValueError("Held source changed")
    image=Image.open(source).convert("RGBA");mask=Image.new("L",image.size);draw=ImageDraw.Draw(mask)
    for points in spec["positive_object_polygons"]:draw.polygon([tuple(p)for p in points],fill=255)
    before=mask.copy();pixels=image.load();selected=mask.load()
    for y in range(374):
        for x in range(800):
            if not selected[x,y]:continue
            r,g,b,a=pixels[x,y]
            if g>r+12 and b>r+12 and b>g-8:selected[x,y]=0
    for item in spec.get("protected_object_polygons",[]):draw.polygon([tuple(p)for p in item["points"]],fill=255)
    for item in spec.get("protected_object_lines",[]):draw.line([tuple(p)for p in item["points"]],fill=255,width=item["width"])
    for points in spec.get("negative_air_water_polygons",[]):draw.polygon([tuple(p)for p in points],fill=0)
    for x,y in spec.get("inspected_unowned_pixels",[]):selected[x,y]=0
    OUT.mkdir(exist_ok=False);REPORT.mkdir(exist_ok=False)
    mask_path=OUT/"shipyard-mask.png";mask.convert("RGBA").save(mask_path)
    frame=image.copy();frame.putalpha(mask);frame_path=OUT/"shipyard-visible.png";frame.save(frame_path)
    dark=Image.new("RGBA",image.size,(30,33,38,255));dark.alpha_composite(frame)
    box=(0,155,145,260)
    dark.crop(box).resize((1160,840),Image.Resampling.NEAREST).save(REPORT/"shipyard-complete-objects-negative-spaces-8x.png")
    context=image.copy();tint=Image.new("RGBA",image.size);tint.paste((255,50,0,150),(0,0),mask);Image.alpha_composite(context,tint).crop(box).resize((1160,840),Image.Resampling.NEAREST).save(REPORT/"shipyard-owned-source-context-8x.png")
    dark.save(REPORT/"shipyard-whole-canvas.png")
    removed=ImageChops.subtract(before,mask)
    receipt={"status":"design proposal","source":spec["source"],"annotation":{"path":SPEC.relative_to(PROJECT).as_posix(),"sha256":sha(SPEC)},"mask":{"path":mask_path.relative_to(PROJECT).as_posix(),"sha256":sha(mask_path)},"visible_frame":{"path":frame_path.relative_to(PROJECT).as_posix(),"sha256":sha(frame_path)},"mask_pixels":mask.histogram()[255],"bounds":mask.getbbox(),"removed_negative_air_water_pixels":removed.histogram()[255],"source_rgb_unchanged":True,"held_frame_writes":False,"semantic_role_review_pending":True,"consumer_execution":False,"native_execution":False,"release_accepted":False}
    (REPORT/"receipt.json").write_text(json.dumps(receipt,indent=2)+"\n");print(json.dumps(receipt,indent=2))
if __name__=="__main__":main()
