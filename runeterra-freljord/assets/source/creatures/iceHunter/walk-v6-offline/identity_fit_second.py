"""Second and final finite identity-fit approach; only opposite contact renders.

Preserves approach1 and the pre-existing pass. Uses the actual selected holding
cell's saved source camera to sample own painted master color onto real surfaces.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import numpy as np
from PIL import Image

import author_cohort as original
import identity_fit as fit

HERE = Path(__file__).resolve().parent


def master_patch(master, holding, native_rect, resolution):
    bbox = holding["source_bbox"]
    anchor = holding["source_camera_anchor"]
    scale = holding["uniform_camera_scale"]
    size = (round((bbox[2] - bbox[0]) * scale), round((bbox[3] - bbox[1]) * scale))
    origin = (round(197 - (anchor[0] - bbox[0]) * scale), round(266 - (anchor[1] - bbox[1]) * scale))
    sx, sy = size[0] / (bbox[2] - bbox[0]), size[1] / (bbox[3] - bbox[1])
    width, height = native_rect[2] - native_rect[0], native_rect[3] - native_rect[1]
    affine = (1 / resolution / sx, 0, bbox[0] + (native_rect[0] - origin[0]) / sx,
              0, 1 / resolution / sy, bbox[1] + (native_rect[1] - origin[1]) / sy)
    return master.transform((round(width * resolution), round(height * resolution)),
                            Image.Transform.AFFINE, affine, Image.Resampling.BICUBIC)


def author(t, unit, landmarks):
    mesh, joints = fit.author(t, unit, landmarks, 2)
    remove = {"reference_fitted_actual_bow", "actual_bow_string", "actual_arrow_fletching"}
    mesh = fit.subset(mesh, lambda part: part not in remove)
    for i, part in enumerate(mesh.parts):
        if part in ("near_thigh", "far_thigh"):
            mesh.materials[i] = "own_upper_leg"
        elif part.startswith(("near_", "far_")) and any(key in part for key in ("knee_cap", "boot", "foot_instep", "_toe")):
            mesh.materials[i] = "own_boot"

    move = fit.body_transform(t)
    shoulders = original.Surface()
    for side in ("near", "far"):
        point = landmarks[side + "_arm"][0]
        depth = .25 if side == "near" else -.015
        shoulders.oval(fit.unproject(point[0], point[1] - 1.2, depth), (.105, .075, .070),
                       "source_upperbody", "fitted_" + side + "_pauldron")
    fit.append_reference(mesh, shoulders, fit.posed_copy(shoulders, move))

    bow = original.Surface()
    points = [fit.unproject(*xy, -.015) for xy in landmarks["bow"]]
    bow.cord(points, .027, "source_upperbody", "fitted_thicker_actual_bow")
    bow.cord([points[0], points[-1]], .0035, "source_upperbody", "fitted_actual_bow_string")
    rest_hand = fit.unproject(*landmarks["far_arm"][2], -.015)
    actual_hand = np.array(joints["arms"]["far"]["wrist"])
    offset = actual_hand - rest_hand
    fit.append_reference(mesh, bow, fit.posed_copy(bow, lambda point: point + offset))
    handle = points[landmarks["bow_grip_index"]] + offset
    joints["bow"] = {"handle": handle.tolist(), "hand_side": "far",
                     "attachment_error": float(np.linalg.norm(handle - actual_hand))}
    arrows = original.Surface()
    for tip in landmarks["arrow_tips"]:
        top = fit.unproject(*tip, -.10)
        arrows.oval(top, (.045, .022, .080), "source_upperbody", "fitted_painted_fletching", sides=10, rows=6)
    fit.append_reference(mesh, arrows, fit.posed_copy(arrows, move))
    return mesh, joints


def run(unit, reachfix=False):
    start = time.perf_counter()
    root = original.candidate_root(unit) / ("identity-fit-approach2" + ("-reachfix" if reachfix else ""))
    root.mkdir(exist_ok=False)
    report = fit.REPORT / unit / root.name
    report.mkdir(parents=True, exist_ok=False)
    configpath = HERE / ("identity-fit-second-reachfix-landmarks.json" if reachfix else "identity-fit-second-landmarks.json")
    landmarks = json.loads(configpath.read_text())[unit]
    reference = original.PROJECT / "assets/source/creatures" / unit / "registered-v3/native/g02-f000.png"
    evidencepath = reference.parents[1] / "production-evidence-v2.json"
    evidence = json.loads(evidencepath.read_text())
    holding = next(row for row in evidence["source_cells"] if row["group"] == 2 and row["frame"] == 0)
    masterpath = original.PROJECT / holding["master"]
    if original.digest(masterpath) != holding["master_sha256"]:
        raise ValueError("own selected master hash changed")
    master = Image.open(masterpath).convert("RGBA")
    color = fit.fill_texture(master_patch(master, holding, fit.TEXTURE_CROP, 4))
    Image.fromarray(color.astype(np.uint8)).save(root / "source-upperbody-rgb.png")
    config = json.loads((original.candidate_root(unit) / "cohort.json").read_text())
    materials = original.materials(config, root)
    materials["source_upperbody"] = {"pixels": color}
    for name, rect in (("own_upper_leg", landmarks["upper_leg_texture_patch"]),
                       ("own_boot", landmarks["boot_texture_patch"])):
        patch = master_patch(master, holding, rect, 4)
        rgb = fit.fill_texture(patch)
        patch = Image.fromarray(rgb.astype(np.uint8)).resize((64,64), Image.Resampling.BICUBIC)
        patch.save(root / "materials" / (name + ".png"))
        materials[name] = {"pixels": np.asarray(patch, float)}
    with (root / "materials.mtl").open("a", encoding="ascii") as file:
        file.write("\nnewmtl source_upperbody\nKd 1 1 1\nmap_Kd source-upperbody-rgb.png\n")
        for name in ("own_upper_leg", "own_boot"):
            file.write("\nnewmtl " + name + "\nKd 1 1 1\nmap_Kd materials/" + name + ".png\n")
    frames, records = [], []
    for phase in (0,3):
        mesh,joints = author(phase / 6,unit,landmarks)
        output = root / f"g00-f{phase:03d}.png"
        fit.raster(mesh, materials).save(output)
        mesh.export_obj(root / f"phase{phase}.obj")
        frames.append(output)
        records.append({"phase": phase,"png": output.relative_to(original.PROJECT).as_posix(),
                        "sha256": original.digest(output),"mesh_sha256": original.digest(root / f"phase{phase}.obj"),
                        "triangles": len(mesh.faces),"joints": joints})
    original.contact_sheet(unit,frames,report / "selected-idle-versus-identity-fit-native.png",root.name)
    inputs = [reference,evidencepath,masterpath,Path(__file__),HERE / "identity_fit.py",configpath,
              Path(original.__file__)]
    receipt = {"unit":unit,"approach":2,"execution_correction":reachfix,"status":"built-unreviewed","selected":False,
               "production_ready":False,"human_visual_approval":False,"independent_review_pass":False,
               "canvas":[450,400],"pivot":[197,266],"only_contact_phases_rendered":[0,3],
               "method":"Revised measured hood/arm/mantle/equipment surfaces, actual selected master holding cell camera UV transfer at4x material resolution, own painted brown boot material on unchanged real v6 legs. No sprite cutout limbs or alpha-defined ground contacts.",
               "source_texture_crop":list(fit.TEXTURE_CROP),"holding_cell_camera":holding,
               "seconds":time.perf_counter()-start,"landmarks":landmarks,"phases":records,
               "inputs":{path.relative_to(original.PROJECT).as_posix():original.digest(path) for path in inputs},
               "limits":["Second and final allowed contact-fit approach; no automatic cycle expansion or art acceptance", "Baked one-view color transfer still needs native-scale independent identity and seam inspection", "No native gameplay or both-facing validation"]}
    for folder in (root,report):
        (folder / "receipt.json").write_text(original.encoded(receipt),encoding="utf-8")
    (root / "authoring-inputs.json").write_text(original.encoded({"source":Path(__file__).read_text(),
                                                                "fit_source":(HERE/"identity_fit.py").read_text(),
                                                                "landmarks":landmarks}),encoding="utf-8")
    print(json.dumps({"unit":unit,"approach":2,"seconds":receipt["seconds"],
                      "receipt_sha256":original.digest(root / "receipt.json")}))


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("unit",choices=original.UNITS)
    parser.add_argument("--reachfix",action="store_true")
    args=parser.parse_args()
    run(args.unit,args.reachfix)
