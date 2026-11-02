"""Bounded changed-surface/contact/IK checks; never final visual acceptance."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import numpy as np
from PIL import Image

import author_pass as current
import verify_gait as original_checks


def surface_failure(vertices, foot_ids, leg_ids, planned):
    foot_min=float(vertices[list(foot_ids),2].min())
    leg_min=float(vertices[list(leg_ids),2].min())
    return (leg_min<-.001 or (planned["stance"] and abs(foot_min)>.001)
            or (not planned["stance"] and foot_min<planned["sole_lift"]-.001))


def run(label):
    output=current.REPORT/(label+".json")
    if output.exists():
        raise ValueError("preserve previous verification")
    result={"status":"built-unreviewed","human_visual_approval":False,"production_ready":False,
            "source_sha256":current.original.digest(Path(current.__file__)),"cases":{},"errors":[]}
    for unit in current.original.UNITS:
        landmarks=current.landmarks_for(unit)
        records=[]
        errors=[]
        dense=[]
        before=None
        actual_stance_points={"near":[],"far":[]}
        for sample in range(61):
            t=sample/60
            mesh,joints=current.author(t,unit,landmarks)
            _,old_joints=current.previous.author(t,unit,landmarks)
            if joints["legs"]!=old_joints["legs"] or joints["arms"]!=old_joints["arms"]:
                errors.append(f"{sample}: fixed IK chains changed")
            vertices=np.asarray(mesh.vertices)
            feet={}
            for side in ("near","far"):
                foot_ids={i for face,part in zip(mesh.faces,mesh.parts) if part==side+"_sculpt_foot" for i in face}
                all_leg_ids={i for face,part in zip(mesh.faces,mesh.parts) if part.startswith(side+"_sculpt_") for i in face}
                min_foot=float(vertices[list(foot_ids),2].min())
                min_leg=float(vertices[list(all_leg_ids),2].min())
                planned=joints["legs"][side]
                if min_leg<-.001 or (planned["stance"] and abs(min_foot)>.001):
                    errors.append(f"{sample}/{side}: surfaced grounded contact failed")
                if not planned["stance"] and min_foot<planned["sole_lift"]-.001:
                    errors.append(f"{sample}/{side}: surfaced swing clearance failed")
                toe=np.array(joints["sculpt_surface_contacts"][side]["actual_sole_toe_vertex"])
                # Confirm the tested contact really exists in the new surfaced sole.
                if np.linalg.norm(vertices[list(foot_ids)]-toe,axis=1).min()>1e-9:
                    errors.append(f"{sample}/{side}: declared contact is not a sole vertex")
                if planned["stance"]:
                    world_toe=toe.copy()
                    world_toe[0]+=joints["reference_root_world_x"]
                    actual_stance_points[side].append((sample,world_toe))
                feet[side]={"minimum_foot_z":min_foot,"minimum_whole_leg_z":min_leg,"stance":planned["stance"]}
            if joints["bow"]["attachment_error"]>1e-8:
                errors.append(f"{sample}: actual bow curve node detached")
            if sample in (0,10,20,30,40,50):
                records.append(joints)
            if sample==0:before=vertices
            if sample==60:
                closure=float(np.abs(vertices-before).max())
            dense.append({"t":t,"feet":feet})
        errors.extend(original_checks.geometry_checks(records))
        if closure>1e-8:errors.append("new complete mesh loop does not close")
        slip={}
        for side,start in (("near",0),("far",30)):
            points=[point for sample,point in actual_stance_points[side] if start<=sample<start+30]
            slip[side]=float(np.ptp(np.array(points),axis=0).max())
            if slip[side]>1e-8:errors.append(side+" actual sole-toe stance slips")
        repeated=[copy.deepcopy(records[0]) for _ in records]
        no_clearance=copy.deepcopy(records);no_clearance[1]["legs"]["far"]["sole_lift"]=0
        detached=copy.deepcopy(records);detached[0]["bow"]["attachment_error"]=.2
        controls={"repeated_support_rejected":bool(original_checks.geometry_checks(repeated)),
                  "no_swing_clearance_rejected":bool(original_checks.geometry_checks(no_clearance)),
                  "detached_grip_rejected":bool(original_checks.geometry_checks(detached)),
                  "bad_phase_order_rejected":bool(original_checks.geometry_checks([records[i] for i in (0,2,1,5,4,3)]))}
        test_mesh,test_joints=current.author(0,unit,landmarks)
        test_vertices=np.asarray(test_mesh.vertices)
        foot_ids={i for face,part in zip(test_mesh.faces,test_mesh.parts) if part=="near_sculpt_foot" for i in face}
        leg_ids={i for face,part in zip(test_mesh.faces,test_mesh.parts) if part.startswith("near_sculpt_") for i in face}
        below=test_vertices.copy();below[list(foot_ids),2]-=.04
        floating=test_vertices.copy();floating[list(foot_ids),2]+=.04
        altered_end=before.copy();altered_end[0,0]+=.02
        controls.update({"surface_penetration_rejected":surface_failure(below,foot_ids,leg_ids,test_joints["legs"]["near"]),
                         "floating_stance_surface_rejected":surface_failure(floating,foot_ids,leg_ids,test_joints["legs"]["near"]),
                         "broken_mesh_loop_rejected":float(np.abs(altered_end-before).max())>1e-8})
        if not all(controls.values()):errors.append("negative control unexpectedly passed")
        frame_checks=[]
        for mode in ("contacts-finish","cohort"):
            root=current.root_for(unit)/mode
            if not (root/"receipt.json").is_file():continue
            receipt=json.loads((root/"receipt.json").read_text())
            for frame in receipt["phases"]:
                path=current.PROJECT/frame["png"]
                im=Image.open(path).convert("RGBA")
                mask=np.asarray(im)[:,:,3]>=128
                y,x=np.where(mask)
                unclipped=bool(len(x) and x.min()>150 and x.max()<244 and y.min()>180 and y.max()<279)
                if im.size!=(450,400) or not unclipped or current.original.digest(path)!=frame["sha256"]:
                    errors.append(mode+" native PNG/canvas/clip mismatch")
                _,joints=current.author(frame["phase"]/6,unit,landmarks)
                if joints!=frame["joints"]:errors.append(mode+" rendered phase differs from checked pose")
                if receipt["source_sha256"]!=current.original.digest(current.__file__):
                    errors.append(mode+" rendered source pin differs")
                frame_checks.append({"mode":mode,"phase":frame["phase"],"sha256":frame["sha256"],
                                     "alpha128_bbox":[int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)],"unclipped":unclipped})
        result["cases"][unit]={"mechanical_pass":not errors,"errors":errors,"fixed_ik_chain_change":False,
                               "surface_sculpt_changed":True,"dense_pose_samples":dense,"loop_max_vertex_error":closure,
                               "actual_sole_vertex_stance_slip":slip,"negative_controls":controls,"frame_checks":frame_checks,
                               "native_gameplay_verified":False,"art_pass_claimed":False}
        result["errors"].extend(unit+": "+error for error in errors)
    before=json.loads((current.REPORT/"inputs-before.json").read_text())
    changed=[]
    for name,expected in before["files"].items():
        file=Path(name)
        if not file.is_absolute():file=current.PROJECT.parent/file
        if not file.is_file() or current.original.digest(file)!=expected:changed.append(name)
    result["prior_files_rechecked"]=len(before["files"])
    result["prior_file_changes"]=changed
    inventory=json.loads((current.PROJECT/"build/reports/three-town-audit-20261022/walk-feasibility/selected-walk-inventory.json").read_text())
    changed=[]
    for name,expected in inventory["inputs"].items():
        file=Path(name)
        if not file.is_absolute():file=current.PROJECT.parent/file
        if not file.is_file() or current.original.digest(file)!=expected:changed.append(name)
    result["selected_inputs_rechecked"]=len(inventory["inputs"])
    result["selected_input_changes"]=changed
    result["mechanical_pass"]=not result["errors"]
    result["preservation_pass"]=not result["prior_file_changes"] and not changed
    output.write_text(current.original.encoded(result),encoding="utf-8")
    print(json.dumps({"report":output.relative_to(current.PROJECT).as_posix(),"mechanical_pass":result["mechanical_pass"],
                      "preservation_pass":result["preservation_pass"],"errors":result["errors"],"art_pass_claimed":False}))


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("label",choices=("geometry-preflight","verification-final"))
    run(parser.parse_args().label)
