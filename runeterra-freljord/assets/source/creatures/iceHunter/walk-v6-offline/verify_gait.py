"""Bounded candidate-only anatomy/contact checks, including deliberate bad gaits.

This is not art acceptance, a game test, or a substitute for independent review.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

import author_cohort as author


def geometry_checks(records):
    failures = []
    for phase, joints in enumerate(records):
        for side, leg in joints["legs"].items():
            hip, knee, ankle = (np.array(leg[k]) for k in ("hip", "knee", "ankle"))
            if abs(np.linalg.norm(knee - hip) - leg["thigh_length"]) > 1e-7:
                failures.append(f"{phase}/{side}: thigh length changed")
            if abs(np.linalg.norm(ankle - knee) - leg["shin_length"]) > 1e-7:
                failures.append(f"{phase}/{side}: shin length changed")
            if (side == "near" and hip[1] >= 0) or (side == "far" and hip[1] <= 0):
                failures.append(f"{phase}/{side}: leg moved to the other hip attachment")
        for side, arm in joints["arms"].items():
            shoulder, elbow, wrist = (np.array(arm[k]) for k in ("shoulder", "elbow", "wrist"))
            if abs(np.linalg.norm(elbow - shoulder) - arm["upper_length"]) > 1e-7:
                failures.append(f"{phase}/{side}: upper arm length changed")
            if abs(np.linalg.norm(wrist - elbow) - arm["fore_length"]) > 1e-7:
                failures.append(f"{phase}/{side}: forearm length changed")
        if joints["bow"]["attachment_error"] > 1e-6:
            failures.append(f"{phase}: bow not attached to actual grip")
    for side, sign in (("near", 1), ("far", -1)):
        a = records[0]["legs"][side]["track_x"]
        b = records[3]["legs"][side]["track_x"]
        if not sign * a > .25 or not sign * b < -.25:
            failures.append(side + ": opposite contact ownership missing")
    for phase, side in ((1, "far"), (2, "far"), (4, "near"), (5, "near")):
        if records[phase]["legs"][side]["sole_lift"] < .15:
            failures.append(f"{phase}/{side}: swing foot lacks clearance")
    return failures


def main(attempt, cohort_attempt):
    if not attempt.isalnum():
        raise ValueError("alphanumeric report suffix required")
    report = author.REPORT / ("gait-checks-" + attempt + ".json")
    if report.exists():
        raise ValueError("preserve existing report")
    result = {"scope": "candidate-only analytical geometry and PNG inspection; no native/build/full suite",
              "status": "built-unreviewed", "human_visual_approval": False,
              "identity_contact_gate_passed": False, "production_ready": False,
              "author_source_sha256": author.digest(Path(author.__file__)),
              "verifier_source_sha256": author.digest(Path(__file__)), "units": {}, "errors": []}
    for unit in author.UNITS:
        veteran = unit == "veteranIceHunter"
        meshes, records = zip(*(author.author(i / 6, veteran) for i in range(6)))
        errors = geometry_checks(records)
        dense = []
        for sample in range(61):
            t = sample / 60
            mesh, joints = author.author(t, veteran)
            vertices = np.array(mesh.vertices)
            feet = {}
            for side in ("near", "far"):
                indices = {index for face, part in zip(mesh.faces, mesh.parts)
                           if part in (side + "_foot_instep", side + "_toe") for index in face}
                minimum = float(vertices[list(indices), 2].min())
                expected = joints["legs"][side]["sole_lift"]
                if minimum < -.001:
                    errors.append(f"sample{sample}/{side}: surfaced foot penetrates ground")
                if joints["legs"][side]["stance"] and abs(minimum) > .001:
                    errors.append(f"sample{sample}/{side}: actual sole does not touch ground")
                if not joints["legs"][side]["stance"] and minimum < expected - .01:
                    errors.append(f"sample{sample}/{side}: actual swing mesh lower than planned clearance")
                feet[side] = {"minimum_surface_z": minimum, "planned_sole_lift": expected,
                              "stance": joints["legs"][side]["stance"]}
            dense.append({"t": t, "feet": feet})
        first, _ = author.author(0, veteran)
        closure, _ = author.author(1, veteran)
        loop_error = float(np.abs(np.asarray(first.vertices) - np.asarray(closure.vertices)).max())
        if loop_error > 1e-8:
            errors.append("full surfaced mesh does not close at cycle end")
        slip = {}
        for side, start in (("near", 0), ("far", .5)):
            points = []
            for t in np.linspace(start, start + .49, 30):
                _, joints = author.author(float(t), veteran)
                p = np.asarray(joints["legs"][side]["contact_toe"])
                p[0] += joints["reference_root_world_x"]
                points.append(p)
            slip[side] = float(np.ptp(np.array(points), axis=0).max())
            if slip[side] > 1e-8:
                errors.append(side + ": planned stance foot slips against authored root displacement")
        # Negative controls prove phase/clearance/contact checks reject their target defects.
        repeated = [copy.deepcopy(records[0]) for _ in records]
        no_clearance = copy.deepcopy(list(records))
        no_clearance[1]["legs"]["far"]["sole_lift"] = 0
        detached = copy.deepcopy(list(records))
        detached[0]["bow"]["attachment_error"] = .17
        reversed_order = [copy.deepcopy(records[i]) for i in (0, 2, 1, 5, 4, 3)]
        controls = {"repeated_support_body_bob_rejected": bool(geometry_checks(repeated)),
                    "missing_swing_clearance_rejected": bool(geometry_checks(no_clearance)),
                    "detached_bow_rejected": bool(geometry_checks(detached)),
                    "incorrect_phase_order_rejected": bool(geometry_checks(reversed_order))}
        if not all(controls.values()):
            errors.append("negative control unexpectedly passed")
        candidate = author.candidate_root(unit) / ("diagnostic-" + cohort_attempt)
        receipt = json.loads((candidate / "receipt.json").read_text(encoding="utf-8"))
        if receipt["source_sha256"]["author_cohort.py"] != author.digest(Path(author.__file__)):
            errors.append("rendered cohort does not bind the currently checked authoring source")
        for frame in receipt["phases"]:
            if frame["joints"] != records[frame["phase"]]:
                errors.append("rendered phase/joint record differs from checked geometry")
        image_checks = []
        idlepath = author.PROJECT / "assets/source/creatures" / unit / "registered-v3/native/g02-f000.png"
        idle = Image.open(idlepath).convert("RGBA")
        idle_mask = np.asarray(idle)[:, :, 3] >= 128
        for frame in receipt["phases"]:
            path = author.PROJECT / frame["png"]
            image = Image.open(path).convert("RGBA")
            pixels = np.asarray(image)
            mask = pixels[:, :, 3] >= 128
            if image.size != (450, 400) or path.exists() and author.digest(path) != frame["png_sha256"]:
                errors.append("native canvas/hash changed: " + path.name)
            # This is a mismatch indicator, not a human/art quality metric.
            region = np.zeros_like(mask)
            region[185:238, 155:245] = True
            union = ((mask | idle_mask) & region).sum()
            iou = float(((mask & idle_mask) & region).sum() / max(1, union))
            image_checks.append({"phase": frame["phase"], "png_sha256": author.digest(path),
                                 "alpha128_bbox": frame["bounds_alpha128"], "upper_body_silhouette_iou_to_selected_idle": iou,
                                 "transparent_corners": not bool(mask[0, 0] or mask[-1, -1])})
        result["units"][unit] = {"mechanical_geometry_checks_pass": not errors, "failures": errors,
                                  "dense_surface_contact_samples": dense, "loop_max_vertex_error": loop_error,
                                  "authored_world_stance_slip": slip, "negative_controls": controls,
                                  "phase_records": list(records), "native_frame_checks": image_checks,
                                  "native_game_motion_verified": False,
                                  "selected_identity_match_verified": False,
                                  "note": "Analytical slip uses the authored stride/root relation only. Actual VCMI timing and both-facing motion remain untested. Silhouette IoU is not art approval."}
        result["errors"].extend(unit + ": " + e for e in errors)
    result["mechanical_geometry_checks_pass"] = not result["errors"]
    report.write_text(author.encoded(result), encoding="utf-8")
    print(json.dumps({"report": report.relative_to(author.PROJECT).as_posix(),
                      "geometry_pass": result["mechanical_geometry_checks_pass"], "errors": result["errors"],
                      "identity_gate": False, "production_ready": False}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt", default="attempt01")
    parser.add_argument("--cohort-attempt", default="attempt02")
    args = parser.parse_args()
    main(args.attempt, args.cohort_attempt)
