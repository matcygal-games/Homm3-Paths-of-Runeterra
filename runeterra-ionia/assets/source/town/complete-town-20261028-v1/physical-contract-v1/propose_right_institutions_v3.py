"""Technical separated-institution alpha proposals from actual V6 source pixels."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw

HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if p.name=="runeterra-ionia")
OUT=HERE/"right-institutions-contour-proposal-v3"
REPORT=PROJECT/"build/reports/complete-town-20261028-v1/physical-contract-v1-right-institutions-contour-proposal-v3"

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    plan=json.loads((HERE/"right-institutions-contour-proposal-v3.json").read_text())
    source_path=PROJECT/plan["source"];assert sha(source_path)==plan["source_sha256"]
    source=Image.open(source_path).convert("RGBA")
    OUT.mkdir(exist_ok=False);REPORT.mkdir(parents=True,exist_ok=False)
    rows={}
    for site in ("protector","gateway"):
        mask=Image.new("L",(800,374));d=ImageDraw.Draw(mask)
        for polygon in plan[site+"_polygons"]:d.polygon([tuple(p)for p in polygon],fill=255)
        for rule in plan.get("bounded_matte_keys",[]):
            if rule["site"]!=site:continue
            x0,y0,x1,y1=rule["bounds"]
            for y in range(y0,y1):
                for x in range(x0,x1):
                    r,g,b,_=source.getpixel((x,y))
                    remove=(b>r+18 and b>g+2)if rule["key"]=="blue-sky"else((r>g+35 and b>g+20)if rule["key"]=="pink-leaves-only"else((r>g+35 and b>g+20)or(g>r+12 and g>b+8)))
                    if remove:mask.putpixel((x,y),0)
        path=OUT/(site+"-proposed-mask.png");mask.convert("RGBA").save(path)
        actor=source.copy();actor.putalpha(mask)
        scene=Image.new("RGBA",source.size,(45,45,45,255));scene.alpha_composite(actor)
        scene.convert("RGB").save(REPORT/(site+"-proposed-visible.png"))
        box=(610,45,800,175)if site=="protector"else(650,164,795,247)
        crop=scene.convert("RGB").crop(box)
        crop.resize((crop.width*4,crop.height*4),Image.Resampling.NEAREST).save(REPORT/(site+"-detail-4x.png"))
        rows[site]={"path":path.relative_to(PROJECT).as_posix(),"sha256":sha(path),"pixels":mask.histogram()[255],"bounds":mask.getbbox()}
    result={"status":"design proposal","source":plan["source"],"source_sha256":sha(source_path),"masks":rows,
            "source_or_held_frames_modified":False,"art_owner_review_required":True,"physical_geometry_accepted":False,"release_accepted":False}
    (OUT/"proposal-receipt.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    (REPORT/"proposal-receipt.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps(result,indent=2))

if __name__=="__main__":main()
