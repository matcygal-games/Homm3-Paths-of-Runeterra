"""Trace actual source coast objects; exclude ambient water/air/scenery gaps."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw,ImageChops

HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if p.name=="runeterra-ionia")
BASE=HERE.parent
OUT=HERE/"coast-object-envelope-proposal-v3"
REPORT=PROJECT/"build/reports/complete-town-20261028-v1/physical-contract-v1-coast-object-envelope-proposal-v3"

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    plan=json.loads((HERE/"coast-object-envelope-proposal-v3.json").read_text())
    freeze=json.loads((BASE/"FRAME-FREEZE-v1.json").read_text())
    OUT.mkdir(exist_ok=False);REPORT.mkdir(parents=True,exist_ok=False)
    rows={}
    for state in("shipyard","ship"):
        ref=freeze["frames"][state];path=PROJECT/ref["path"];assert sha(path)==ref["sha256"]
        source=Image.open(path).convert("RGBA")
        old=Image.open(HERE/"contour-proposal-v2"/(state+"-proposed-mask.png")).getchannel("R")
        envelope=Image.new("L",(800,374));d=ImageDraw.Draw(envelope)
        for polygon in [plan["deck_polygon"],plan["lamp_polygon"],*plan["pier_posts"]]:d.polygon([tuple(p)for p in polygon],fill=255)
        rigging=Image.new("L",(800,374))
        if state=="ship":
            for name in("ship_sail_polygon","ship_hull_polygon"):d.polygon([tuple(p)for p in plan[name]],fill=255)
            rd=ImageDraw.Draw(rigging)
            for line in plan["ship_rigging"]:rd.line([tuple(p)for p in line["points"]],fill=255,width=line["width"])
            envelope=ImageChops.lighter(envelope,rigging)
        mask=ImageChops.multiply(old,envelope)
        for y in range(155,275):
            for x in range(0,180):
                if not mask.getpixel((x,y)):continue
                r,g,b,_=source.getpixel((x,y))
                if g>r+12 and b>r+12 and b>g-8 and not rigging.getpixel((x,y)):mask.putpixel((x,y),0)
        for x,y in plan.get("negative_scenery_pixels",{}).get(state,[]):mask.putpixel((x,y),0)
        target=OUT/(state+"-proposed-mask.png");mask.convert("RGBA").save(target)
        actor=source.copy();actor.putalpha(mask)
        preview=Image.new("RGBA",(800,374),(45,45,45,255));preview.alpha_composite(actor)
        preview.convert("RGB").crop((0,155,175,275)).resize((1050,720),Image.Resampling.NEAREST).save(REPORT/(state+"-negative-spaces-6x.png"))
        removed=ImageChops.subtract(old,mask)
        rows[state]={"path":target.relative_to(PROJECT).as_posix(),"sha256":sha(target),"retained_pixels":mask.histogram()[255],"scenery_or_water_alpha_removed":removed.histogram()[255],"bounds":mask.getbbox()}
    result={"status":"design proposal","masks":rows,"actual_source_rgb_changed":False,"held_frame_files_modified":False,"art_owner_review_required":True,"physical_geometry_accepted":False,"long_underlap_accepted":False,"release_accepted":False}
    (OUT/"proposal-receipt.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    (REPORT/"proposal-receipt.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2))

if __name__=="__main__":main()
