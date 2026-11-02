"""Bounded technical visibility proposal from a genuine coast absence painting."""
from pathlib import Path
import hashlib
import json
from PIL import Image,ImageDraw,ImageChops

HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if p.name=="runeterra-ionia")
BASE=HERE.parent
OUT=HERE/"coast-underlap-proposal-v1"
REPORT=PROJECT/"build/reports/complete-town-20261028-v1/physical-contract-v1-coast-underlap-proposal-v1"

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    plan=json.loads((HERE/"coast-underlap-proposal-v1.json").read_text())
    absence=PROJECT/plan["source_painting"];foreground=PROJECT/plan["foreground_matte"]
    assert sha(absence)==plan["source_sha256"]
    assert sha(foreground)==plan["foreground_matte_sha256"]
    source=Image.open(absence).convert("RGBA")
    workshop=Image.open(foreground).getchannel("R")
    trace=Image.new("L",(800,374));ImageDraw.Draw(trace).polygon([tuple(p)for p in plan["polygon"]],fill=255)
    mask=ImageChops.multiply(trace,workshop)
    OUT.mkdir(exist_ok=False);REPORT.mkdir(parents=True,exist_ok=False)
    target=OUT/"hidden-main-pier-mask.png";mask.convert("RGBA").save(target)
    freeze=json.loads((BASE/"FRAME-FREEZE-v1.json").read_text())
    full=Image.open(BASE/"complete-native-v5-selected.png").convert("RGBA")
    patch=source.copy();patch.putalpha(mask)
    proof=full.copy();proof.alpha_composite(patch)
    fore=full.copy();fore.putalpha(workshop);proof.alpha_composite(fore)
    hidden_exact=proof.tobytes()==full.tobytes()
    facts={}
    for state in ("shipyard","ship"):
        oldmask=Image.open(HERE/"contour-proposal-v2"/(state+"-proposed-mask.png")).getchannel("R")
        oldvisible=full.copy();oldvisible.putalpha(oldmask)
        coast=Image.new("RGBA",(800,374));coast.alpha_composite(oldvisible);coast.alpha_composite(patch)
        # This contextual image is a proposal, not a selected frame or all-state replay.
        context=source.copy();context.alpha_composite(oldvisible);context.alpha_composite(patch)
        context.convert("RGB").save(REPORT/(state+"-workshop-absent-context.png"))
        neutral=Image.new("RGBA",(800,374),(45,45,45,255));neutral.alpha_composite(coast)
        neutral.convert("RGB").crop((0,180,200,280)).resize((1000,500),Image.Resampling.NEAREST).save(REPORT/(state+"-main-pier-detail-5x.png"))
        facts[state]={"old_visible_coast_changed":False,"hidden_new_painted_pixels":mask.histogram()[255],
                      "underlap_outside_foreground_matte":bool(ImageChops.subtract(mask,workshop).getbbox())}
    result={"status":"design proposal","source_painting":plan["source_painting"],"source_sha256":sha(absence),
            "foreground_matte_sha256":sha(foreground),"underlap_mask":{"path":target.relative_to(PROJECT).as_posix(),"sha256":sha(target),"bounds":mask.getbbox(),"pixels":mask.histogram()[255]},
            "local_complete_painting_visibility_unchanged":hidden_exact,
            "visibility_proof_scope":"Only local underlap hidden by exact foreground matte, using complete painting as control. Not an empty-terrain or actual all-state composition acceptance.",
            "coast_proposals":facts,"native_execution":False,"physical_foundation_acceptance":False,"frame_or_source_pixels_modified":False,"release_accepted":False}
    (OUT/"proposal-receipt.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    (REPORT/"proposal-receipt.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2))

if __name__=="__main__":main()
