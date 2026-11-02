"""Finite contact-fit verification only; never promotes identity or selected art."""
from __future__ import annotations

import ast
import copy
import json
from pathlib import Path

import numpy as np
from PIL import Image

import author_cohort as original
import identity_fit as first
import identity_fit_second as second
import verify_gait as prior_checks


def leg_triangles(mesh):
    allowed = ("thigh", "knee_cap", "shaped_calf_boot", "boot_cuff", "foot_instep", "toe", "boot_binding")
    vertices = np.asarray(mesh.vertices)
    return np.array([vertices[list(face)] for face, part in zip(mesh.faces, mesh.parts)
                     if any(part.startswith(side + "_" + name) for side in ("near", "far") for name in allowed)])


def run():
    output = first.REPORT / "verification-final.json"
    if output.exists():
        raise ValueError("preserve verification history")
    result = {"status":"built-unreviewed","human_visual_approval":False,"identity_pass":False,
              "production_ready":False,"cycle_expanded":False,"identity_fit_approaches":2,
              "native_game_test":False,"full_suite":False,"cases":{},"errors":[]}
    for approach in (1,2):
        for unit in original.UNITS:
            suffix = "identity-fit-approach" + str(approach)
            reachfix = approach == 2 and unit == "veteranIceHunter"
            if reachfix:
                suffix += "-reachfix"
            root = original.candidate_root(unit) / suffix
            receipt = json.loads((root / "receipt.json").read_text())
            landmarks = receipt["landmarks"]
            def author(t):
                return first.author(t,unit,landmarks,1) if approach == 1 else second.author(t,unit,landmarks)
            errors, contacts, records = [], [], []
            mesh0 = None
            max_leg_error = 0.0
            for sample in range(61):
                t = sample / 60
                mesh,joints = author(t)
                old_mesh,_ = original.author(t,unit == "veteranIceHunter")
                old_tri, new_tri = leg_triangles(old_mesh), leg_triangles(mesh)
                if old_tri.shape != new_tri.shape:
                    errors.append(f"{sample}: leg topology changed")
                else:
                    max_leg_error = max(max_leg_error,float(np.abs(old_tri-new_tri).max()))
                vertices = np.asarray(mesh.vertices)
                feet = {}
                for side in ("near","far"):
                    indices = {index for face,part in zip(mesh.faces,mesh.parts)
                               if part in (side+"_foot_instep",side+"_toe") for index in face}
                    minimum = float(vertices[list(indices),2].min())
                    planned = joints["legs"][side]
                    if minimum < -.001 or (planned["stance"] and abs(minimum) > .001):
                        errors.append(f"{sample}/{side}: surfaced ground contact failed")
                    if not planned["stance"] and minimum < planned["sole_lift"]-.01:
                        errors.append(f"{sample}/{side}: surfaced swing clearance failed")
                    feet[side] = {"min_z":minimum,"stance":planned["stance"],"planned_lift":planned["sole_lift"]}
                for side,arm in joints["arms"].items():
                    s,e,w = (np.array(arm[key]) for key in ("shoulder","elbow","wrist"))
                    if abs(np.linalg.norm(e-s)-arm["upper_length"])>1e-7 or abs(np.linalg.norm(w-e)-arm["fore_length"])>1e-7:
                        errors.append(f"{sample}/{side}: arm length changed")
                if joints["bow"]["attachment_error"] > 1e-7:
                    errors.append(f"{sample}: actual bow grip detached")
                contacts.append({"t":t,"feet":feet})
                if sample in (0,10,20,30,40,50):
                    records.append(joints)
                if sample == 0:
                    mesh0 = vertices
                if sample == 60:
                    closure = float(np.abs(mesh0-vertices).max())
            errors.extend(prior_checks.geometry_checks(records))
            if max_leg_error > 0:
                errors.append("proven old leg geometry changed")
            if closure > 1e-8:
                errors.append("full fitted surface does not close at t1")
            repeated = [copy.deepcopy(records[0]) for _ in records]
            no_clearance = copy.deepcopy(records)
            no_clearance[1]["legs"]["far"]["sole_lift"] = 0
            detached = copy.deepcopy(records)
            detached[0]["bow"]["attachment_error"] = .2
            controls = {"repeated_support_rejected":bool(prior_checks.geometry_checks(repeated)),
                        "no_clearance_rejected":bool(prior_checks.geometry_checks(no_clearance)),
                        "detached_bow_rejected":bool(prior_checks.geometry_checks(detached)),
                        "bad_order_rejected":bool(prior_checks.geometry_checks([records[i] for i in (0,2,1,5,4,3)]))}
            if not all(controls.values()):
                errors.append("a negative control passed")
            frame_checks = []
            for frame in receipt["phases"]:
                path = original.PROJECT / frame["png"]
                image = Image.open(path).convert("RGBA")
                mask = np.asarray(image)[:,:,3] >= 128
                y,x = np.where(mask)
                unclipped = bool(len(x) and x.min()>150 and x.max()<244 and y.min()>180 and y.max()<279)
                phase_mesh,phase_joints = author(frame["phase"]/6)
                if phase_joints != frame["joints"]:
                    errors.append("checked pose differs from rendered receipt")
                if image.size != (450,400) or original.digest(path) != frame["sha256"] or not unclipped:
                    errors.append("native canvas/hash/clip failed: "+path.name)
                frame_checks.append({"phase":frame["phase"],"sha256":original.digest(path),
                                     "alpha128_bbox":[int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)],
                                     "unclipped_in_fixed_render_region":unclipped})
            key = unit+"/"+suffix
            result["cases"][key] = {"mechanical_checks_pass":not errors,"errors":errors,
                                    "original_leg_vertex_max_error":max_leg_error,"full_surface_loop_max_error":closure,
                                    "dense_pose_count":61,"dense_surface_contacts":contacts,"negative_controls":controls,
                                    "native_contact_frames":frame_checks,"receipt_sha256":original.digest(root/"receipt.json"),
                                    "authoring_inputs_retained":(root/"authoring-inputs.json").is_file(),
                                    "identity_match_not_approved":True}
            result["errors"].extend(key+": "+error for error in errors)
    before = json.loads((first.REPORT/"inputs-before.json").read_text())
    changed = []
    for path,expected in before["old_files"].items():
        source = Path(path)
        if not source.is_absolute():
            source = original.PROJECT.parent/source
        if not source.is_file() or original.digest(source) != expected:
            changed.append(path)
    result["prior_owned_files_rechecked"] = len(before["old_files"])
    result["prior_owned_files_changed"] = changed
    inventory = json.loads((original.PROJECT/"build/reports/three-town-audit-20261022/walk-feasibility/selected-walk-inventory.json").read_text())
    changed = []
    for path,expected in inventory["inputs"].items():
        source = Path(path)
        if not source.is_absolute():
            source = original.PROJECT.parent/source
        if not source.is_file() or original.digest(source) != expected:
            changed.append(path)
    result["selected_inputs_rechecked"] = len(inventory["inputs"])
    result["selected_inputs_changed"] = changed
    for file in Path(__file__).parent.glob("*identity*.py"):
        ast.parse(file.read_text())
    result["mechanical_checks_pass"] = not result["errors"]
    result["source_preservation_pass"] = not result["prior_owned_files_changed"] and not changed
    result["source_hashes"] = {file.relative_to(original.PROJECT).as_posix():original.digest(file)
                               for file in (Path(__file__),Path(first.__file__),Path(second.__file__),Path(original.__file__))}
    output.write_text(original.encoded(result),encoding="utf-8")
    print(json.dumps({"report":output.relative_to(original.PROJECT).as_posix(),"mechanics":result["mechanical_checks_pass"],
                      "prior_owned_files":result["prior_owned_files_rechecked"],"prior_owned_changes":result["prior_owned_files_changed"],
                      "selected_inputs":result["selected_inputs_rechecked"],"selected_changes":changed,
                      "errors":result["errors"],"identity_pass":False,"production_ready":False}))


if __name__ == "__main__":
    run()
