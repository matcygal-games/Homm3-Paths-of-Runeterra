"""Technical alpha proposals for genuine lower Protector development paintings."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw

HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if p.name=="runeterra-ionia")
OUT=HERE/"lower-protector-contour-proposal-v2"
REPORT=PROJECT/"build/reports/complete-town-20261028-v1/physical-contract-v1-lower-protector-contour-proposal-v2"

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    plan=json.loads((HERE/"lower-protector-contour-proposal-v2.json").read_text())
    OUT.mkdir(exist_ok=False);REPORT.mkdir(parents=True,exist_ok=False)
    rows={}
    for state,item in plan["states"].items():
        source_path=PROJECT/item["source"];assert sha(source_path)==item["source_sha256"]
        source=Image.open(source_path).convert("RGBA")
        mask=Image.new("L",(800,374));d=ImageDraw.Draw(mask)
        for polygon in item["polygons"]:d.polygon([tuple(p)for p in polygon],fill=255)
        for rule in plan.get("bounded_matte_keys",[]):
            if rule["state"]!=state:continue
            x0,y0,x1,y1=rule["bounds"]
            for y in range(y0,y1):
                for x in range(x0,x1):
                    r,g,b,_=source.getpixel((x,y))
                    remove=(r>110 and b>r+12 and b>g+2)if rule["key"]=="bright-sky"else(r>130 and b>100 and r>g+40 and b>g+20)
                    if remove:mask.putpixel((x,y),0)
        path=OUT/(state+"-proposed-mask.png");mask.convert("RGBA").save(path)
        actor=source.copy();actor.putalpha(mask)
        scene=Image.new("RGBA",source.size,(45,45,45,255));scene.alpha_composite(actor)
        scene.convert("RGB").save(REPORT/(state+"-proposed-visible.png"))
        scene.convert("RGB").crop((620,85,790,165)).resize((1020,480),Image.Resampling.NEAREST).save(REPORT/(state+"-detail-6x.png"))
        rows[state]={"source":item["source"],"source_sha256":sha(source_path),"mask_path":path.relative_to(PROJECT).as_posix(),"mask_sha256":sha(path),"pixels":mask.histogram()[255],"bounds":mask.getbbox()}
    result={"status":"design proposal","masks":rows,"source_or_held_frames_modified":False,"art_owner_review_required":True,"physical_geometry_accepted":False,"release_accepted":False}
    (OUT/"proposal-receipt.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    (REPORT/"proposal-receipt.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps(result,indent=2))

if __name__=="__main__":main()
