"""Record finite-pass visible proof, deterministic replay and preserved pins."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

import numpy as np
from PIL import Image,ImageDraw

import author_pass as current


def run():
    output=current.REPORT/"artifact-provenance-final.json"
    if output.exists():
        raise ValueError("preserve prior final proof")
    record={"status":"built-unreviewed","selected":False,"production_ready":False,
            "human_visual_approval":False,"identity_contract_pass":False,"cycle_expanded":False,
            "owned_paths_released":True,"reproduction":{},"frame_sha256":{},"contact_receipt_sha256":{},
            "raw_image_inspection_is_not_human_approval":True}
    comparison=Image.new("RGB",(875,332),(66,72,59))
    draw=ImageDraw.Draw(comparison)
    chainproof=Image.new("RGB",(1140,340),(66,72,59))
    chains=ImageDraw.Draw(chainproof)
    for row,unit in enumerate(current.original.UNITS):
        root=current.root_for(unit)/"contacts-finish"
        receipt=json.loads((root/"receipt.json").read_text())
        record["contact_receipt_sha256"][unit]=current.original.digest(root/"receipt.json")
        previous="identity-fit-approach2-reachfix" if unit=="veteranIceHunter" else "identity-fit-approach2"
        paths=[current.PROJECT/"assets/source/creatures"/unit/"registered-v3/native/g02-f000.png",
               current.original.candidate_root(unit)/previous/"g00-f000.png",
               current.root_for(unit)/"contacts/g00-f000.png",root/"g00-f000.png",root/"g00-f003.png"]
        labels=("selected idle","prior identity0","initial pass0","finished contact0","finished contact3")
        for col,(path,label) in enumerate(zip(paths,labels)):
            im=Image.open(path).convert("RGBA").crop((125,155,300,295))
            x,y=col*175,row*166
            draw.line((x,y+135,x+174,y+135),fill=(125,130,112))
            comparison.paste(im,(x,y+24),im)
            draw.text((x+2,y+3),label,fill="white")
        for col,frame in enumerate(receipt["phases"]):
            path=current.PROJECT/frame["png"]
            record["frame_sha256"][frame["png"]]=current.original.digest(path)
            im=Image.open(path).convert("RGBA").crop((150,180,245,280)).resize((285,300),Image.Resampling.NEAREST)
            x,y=(row*2+col)*285,25
            chainproof.paste(im,(x,y),im)
            chains.text((x+3,4),unit+" phase"+str(frame["phase"]),fill="white")
            for side,color in (("near",(70,220,245)),("far",(245,169,65))):
                leg=frame["joints"]["legs"][side]
                points=[]
                for key in ("hip","knee","ankle"):
                    px,py=current.fit.project(leg[key])
                    points.append((x+(px-150)*3,y+(py-180)*3))
                chains.line(points,fill=color,width=1)
                for px,py in points:
                    chains.ellipse((px-2,py-2,px+2,py+2),fill=color)
        destination=current.REPORT/"reproduction"/unit
        destination.mkdir(parents=True,exist_ok=False)
        materials,provenance=current.prepare_materials(unit,current.landmarks_for(unit),destination)
        mesh,joints=current.author(0,unit,current.landmarks_for(unit))
        image=current.fit.raster(mesh,materials)
        stream=io.BytesIO()
        image.save(stream,format="PNG")
        observed=hashlib.sha256(stream.getvalue()).hexdigest()
        expected=current.original.digest(root/"g00-f000.png")
        record["reproduction"][unit]={"phase":0,"sha256":observed,"recorded_sha256":expected,
                                     "byte_identical":observed==expected}
        archive=json.loads((root/"editable-inputs.json").read_text())
        if hashlib.sha256(archive["source_utf8"].encode()).hexdigest()!=receipt["source_sha256"]:
            raise ValueError("execution source archive mismatch")
    comparison.save(current.REPORT/"all-contacts-native-comparison.png")
    comparison.resize((2625,996),Image.Resampling.NEAREST).save(current.REPORT/"all-contacts-3x-diagnostic.png")
    chainproof.save(current.REPORT/"actual-sculpted-leg-chain-proof.png")
    frozen=json.loads((current.REPORT/"inputs-before.json").read_text())["files"]
    selected=json.loads((current.PROJECT/"build/reports/three-town-audit-20261022/walk-feasibility/selected-walk-inventory.json").read_text())["inputs"]
    for label,entries in (("prior_owned",frozen),("selected",selected)):
        changed=[]
        for name,expected in entries.items():
            file=Path(name)
            if not file.is_absolute():file=current.PROJECT.parent/file
            if not file.is_file() or current.original.digest(file)!=expected:changed.append(name)
        record[label+"_files_rechecked"]=len(entries)
        record[label+"_file_changes"]=changed
    verification=json.loads((current.REPORT/"verification-final.json").read_text())
    record["mechanical_pass"]=verification["mechanical_pass"]
    record["source_and_report_hashes"]={}
    for root in (current.root_for("iceHunter"),current.root_for("veteranIceHunter"),current.REPORT):
        for file in root.rglob("*"):
            if file.is_file():record["source_and_report_hashes"][file.relative_to(current.PROJECT).as_posix()]=current.original.digest(file)
    record["critical_report_hashes"]={name:current.original.digest(current.REPORT/name) for name in
                                      ("manual-production-handoff.json","verification-final.json","all-contacts-native-comparison.png")}
    record["limits"]="Source mechanics/replay are verified; identity remains failed/unaccepted, all12 selection gaps pending. This pass is complete and released with no further authoring active."
    output.write_text(current.original.encoded(record),encoding="utf-8")
    print(json.dumps({key:record[key] for key in ("mechanical_pass","production_ready","reproduction","prior_owned_files_rechecked",
                     "prior_owned_file_changes","selected_files_rechecked","selected_file_changes","critical_report_hashes")},indent=2))


if __name__=="__main__":
    run()
