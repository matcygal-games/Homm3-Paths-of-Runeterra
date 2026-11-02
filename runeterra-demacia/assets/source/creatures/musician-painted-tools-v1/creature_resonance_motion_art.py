"""Source-only musician painted atlas recovery and measured native exports.

The retained creative PNGs are immutable. Three reviewed row-overlap atlases
need integer ROI repacking before equal-cell export. This never synthesizes a
pose, rescales a frame independently, or modifies active game assets.
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from creature_family_motion_art import (calibrate_generation, export_generation,
                                      proof, sha, write)
from creature_padding import crop_padding


UNITS = ("resonanceAdept", "harmonicWarden")
GROUPS = (1, 3, 4, 5, 7, 8, 11, 12, 13, 14, 16)
# Manually observed hair top / full boot sole in the first real returned pose.
# These are one camera per complete atlas, never per-frame fitting.
LANDMARKS = {
    "resonanceAdept": {1: (107, 596), 3: (148, 554), 4: (156, 595),
        5: (82, 525), 7: (95, 599), 8: (89, 606), 11: (63, 517),
        12: (112, 495), 13: (107, 493), 14: (49, 428), 16: (35, 426)},
    "harmonicWarden": {1: (128, 616), 3: (123, 554), 4: (146, 600),
        5: (84, 533), 7: (143, 589), 8: (62, 611), 11: (91, 496),
        12: (87, 495), 13: (86, 492), 14: (35, 439), 16: (44, 422)},
}


def repack_overlap(project: Path, unit: str, group: int) -> dict:
    """Recover complete real poses across an otherwise empty row gutter.

    Each original column has two visibly disjoint alpha>=8 runs. Reviewed split
    y540 lies between them (nearest lower head y551). Exact crops retain all
    visible pixels and one pixel of antialiasing. Faint distant alpha1..7 is
    documented, not reconstructed into an invented figure.
    """
    folder = project / "assets/source/creatures" / unit / "musician-rig-v6"
    source_record = folder / f"paint-action-g{group:02}-atlas-v1-generation.json"
    record = json.loads(source_record.read_text())
    source = project / record["output"]
    if record["layout"] != [3, 2] or record["returned_dimensions"] != [1536, 1024] or sha(source) != record["output_sha256"]:
        raise ValueError("Reviewed ROI recovery only applies to its exact original 3x2 atlas")
    frames = []
    with Image.open(source) as original:
        original.load()
        packed = Image.new("RGBA", original.size)
        for index in range(6):
            col, row = index % 3, index // 3
            owner = (col * 512, 0 if row == 0 else 540,
                     (col + 1) * 512, 540 if row == 0 else 1024)
            region = original.crop(owner)
            mask = region.getchannel("A").point(lambda value: 255 if value >= 8 else 0)
            body = mask.getbbox()
            if body is None:
                raise ValueError("Reviewed source pose missing")
            rect = [owner[0] + max(0, body[0] - 1), owner[1] + max(0, body[1] - 1),
                    owner[0] + min(region.width, body[2] + 1), owner[1] + min(region.height, body[3] + 1)]
            piece = original.crop(rect)
            if piece.width > 504 or piece.height > 504:
                raise ValueError("Complete real pose cannot fit with a transparent safety margin")
            destination = [(512 - piece.width) // 2, (512 - piece.height) // 2]
            cell = Image.new("RGBA", (512, 512))
            cell.paste(piece, destination)
            recovered = cell.crop((destination[0], destination[1], destination[0]+piece.width, destination[1]+piece.height))
            if recovered.tobytes() != piece.tobytes():
                raise ValueError("ROI repack altered retained RGBA pixels")
            discarded = region.getchannel("A")
            discarded.paste(0, (rect[0]-owner[0], rect[1]-owner[1], rect[2]-owner[0], rect[3]-owner[1]))
            if discarded.getextrema()[1] >= 8:
                raise ValueError("ROI recovery would omit visible source pixels")
            packed.paste(cell, (col*512, row*512))
            frames.append({"index": index, "reviewed": True, "neighbor_pixels_absent": True,
                "owner_rectangle": list(owner), "source_rectangle": rect,
                "destination_offset": destination,
                "source_to_repacked_translation": [destination[0]-(rect[0]-col*512), destination[1]-(rect[1]-row*512)],
                "retained_rgba_identical": True, "maximum_discarded_alpha": discarded.getextrema()[1],
                "crop_pixel_sha256": __import__("hashlib").sha256(piece.tobytes()).hexdigest(),
                "basis": "Viewed original atlas: first-row soles cross y512 into empty gutter; split y540 is above every lower-row head and below every first-row sole. Complete subject and1px antialias margin recovered without resizing."})
    target = folder / f"paint-action-g{group:02}-atlas-v2.png"
    if target.exists():
        with Image.open(target) as previous:
            if previous.mode != "RGBA" or previous.size != packed.size or previous.tobytes() != packed.tobytes():
                raise ValueError("Preserve previous source repack")
    else:
        packed.save(target)
    result = {**record, "version": 2, "output": target.relative_to(project).as_posix(), "output_sha256": sha(target),
        "atlas_repack": {"source_generation_record": proof(project, source_record), "source": proof(project, source),
            "frames": frames, "inverse_translation_required": True,
            "operation": "Exact integer crop/paste of reviewed complete RGBA source rectangles; no resize, paint or pose synthesis. Original generated source retained."},
        "status": "Technical source repack; native continuity and renderer review pending"}
    write(folder / f"paint-action-g{group:02}-atlas-v2-generation.json", result)
    return result


def export_remaining(project: Path) -> dict:
    project = project.resolve()
    results = []
    for unit in UNITS:
        folder = project / "assets/source/creatures" / unit / "musician-rig-v6"
        for group in GROUPS:
            repacked = group == 5 or (unit == "resonanceAdept" and group == 11)
            if repacked:
                record = repack_overlap(project, unit, group)
            else:
                version = 2 if unit == "resonanceAdept" and group == 14 else 1
                record = json.loads((folder/f"paint-action-g{group:02}-atlas-v{version}-generation.json").read_text())
            generation = folder/f"paint-action-g{group:02}-atlas-v{record['version']}-generation.json"
            head, ground = LANDMARKS[unit][group]
            first_delta = record["atlas_repack"]["frames"][0]["source_to_repacked_translation"] if repacked else [0, 0]
            head += first_delta[1]; ground += first_delta[1]
            camera = calibrate_generation(project, generation, reference_index=0, head_top_y=head,
                ground_y=ground, root_x=record["returned_cell"][0]/2+first_delta[0],
                target_height=80 if unit == "resonanceAdept" else 84,
                basis="Manually observed first-pose hair top and complete boot sole in the actual returned atlas. One uniform camera for every source cell; whole-cell center is the explicit common horizontal pivot. Repacked inputs use exact first-pose ROI translation. No raw-to-painted geometry equivalence is asserted.")
            camera_path = folder/f"paint-action-g{group:02}-camera-v1.json"
            placements = None
            if repacked:
                effective_scale = round(record["returned_cell"][0]*camera["scale"])/record["returned_cell"][0]
                placements = [{"index": row["index"],
                    "native_translation": [round((first_delta[axis]-row["source_to_repacked_translation"][axis])*effective_scale) for axis in (0, 1)],
                    "reviewed": True, "basis": "Inverse technical ROI packing translation relative to the measured first-cell camera, rounded once to integer native pixels. Entire frame only; fixed source scale retained.",
                    "evidence": [proof(project, generation)]} for row in record["atlas_repack"]["frames"]]
            exported = export_generation(project, generation, camera_path, placements=placements)
            results.append({"unit": unit, "group": group, "generation": proof(project, generation),
                "camera": proof(project, camera_path), "export": proof(project, folder/f"paint-action-g{group:02}-native-export-v1{'-placement-v1' if placements else ''}.json"),
                "frames": len(exported["frames"]), "source_repacked": repacked})
    result = {"units": list(UNITS), "actions": results, "active_assets_modified": False,
              "visual_approval_granted": False, "status": "Initial whole-atlas native exports; measured row-layout corrections and full native motion review remain required."}
    write(project/"assets/source/creatures/musician-remaining-native-exports-v1.json", result)
    return result


def foot_landmark(image: Image.Image) -> tuple[float, int]:
    """Observed sole-band extent, used only for reviewed whole-frame placement."""
    alpha = image.getchannel("A")
    visible = alpha.point(lambda value: 255 if value >= 8 else 0)
    bounds = visible.getbbox()
    if bounds is None:
        raise ValueError("No real subject for placement measurement")
    feet = visible.crop((0, bounds[3]-8, image.width, bounds[3])).getbbox()
    return (feet[0]+feet[2])/2, bounds[3]


def finalize_sources(project: Path) -> dict:
    """Assemble explicit diagnostic candidates, retaining known visual issues.

    Sole-band measurements address returned row-layout translation only. They
    never establish anatomical equivalence with the raw rig or art acceptance.
    Death uses only the raw guide's relative ground projection, without trying
    to align an instrument's horizontal extent to a person's foot.
    """
    project = project.resolve()
    all_groups = (0, 1, 2, 3, 4, 5, 7, 8, 11, 12, 13, 14, 15, 16)
    measurements = []
    sources = {}
    for unit in UNITS:
        folder = project/"assets/source/creatures"/unit/"musician-rig-v6"
        raw = json.loads((folder/"raw-native-review-v1.json").read_text())
        raw_standing = next(row for row in raw["frames"] if row["group"] == 2)
        raw_sole = foot_landmark(Image.open(project/raw_standing["output"]))
        idle = json.loads((folder/"paint-action-g02-native-export-v1-placement-v1.json").read_text())
        painted_sole = foot_landmark(Image.open(project/idle["frames"][0]["output"]))
        for group in all_groups:
            initial = folder/f"paint-action-g{group:02}-native-export-v1-placement-v1.json"
            if not initial.exists():
                initial = folder/f"paint-action-g{group:02}-native-export-v1.json"
            exported = json.loads(initial.read_text())
            sources[unit, group] = (initial, exported)
            rows = []
            for row in exported["frames"]:
                native = Image.open(project/row["output"])
                current = foot_landmark(native)
                raw_row = next(value for value in raw["frames"] if value["group"] == group and value["index"] == row["index"])
                rig_sole = foot_landmark(Image.open(project/raw_row["output"]))
                expected_y = 267+rig_sole[1]-raw_sole[1]
                dx = 0 if group in (0, 2, 5) else round(painted_sole[0]+rig_sole[0]-raw_sole[0]-current[0])
                dy = 0 if group in (0, 2) else expected_y-current[1]
                rows.append({"index": row["index"], "observed_painted_sole_band_center": list(current),
                    "guide_sole_band_center": list(rig_sole), "expected_guide_relative_floor_y": expected_y,
                    "additional_whole_frame_translation": [dx, dy],
                    "source": proof(project, project/row["output"]), "raw_guide": proof(project, project/raw_row["output"]),
                    "reviewed": True,
                    "basis": "Actual native opaque composites viewed. Complete returned rows drift vertically and stationary boots drift horizontally. Explicit integer translation follows the guide's relative sole projection; no scale, body fitting or pose warp. Foot alignment is not evidence of head/body continuity. Walk and calm-standing retain prior measured placement; corpse horizontal motion retained."})
            measurements.append({"unit": unit, "group": group, "initial_export": proof(project, initial), "frames": rows})
    evidence = project/"references/prototypes/musician-rig/painted-complete-placement-measurements-v1.json"
    write(evidence, {"measurements": measurements, "visual_approval_granted": False,
        "open_issue": "Resonance Adept g00f005 still has roughly5px body-height drift; matching boots does not resolve it."})
    units = []
    for unit in UNITS:
        folder = project/"assets/source/creatures"/unit/"musician-rig-v6"
        actions = []; groups = []
        for group in all_groups:
            initial, exported = sources[unit, group]
            row_measurements = next(value for value in measurements if value["unit"] == unit and value["group"] == group)
            placements = []
            for row, measure in zip(exported["frames"], row_measurements["frames"]):
                base = row["placement"]["native_translation"]
                correction = measure["additional_whole_frame_translation"]
                placements.append({"index": row["index"], "native_translation": [base[i]+correction[i] for i in (0, 1)],
                    "reviewed": True, "basis": measure["basis"], "evidence": [proof(project, evidence)]})
            final = export_generation(project, project/exported["generation_record"]["path"],
                project/exported["camera_record"]["path"], version=2, placements=placements, placement_version=2)
            converted = []
            for row in final["frames"]:
                output = folder/"native-battle-candidate-v1"/f"g{group:02}-f{row['index']:03}.png"
                converted.append({"index": row["index"], **crop_padding(project/row["output"], output, project)})
            group_frames = [{"source": row["output"], "sha256": row["sha256"]} for row in converted]
            groups.append({"group": group, "frames": group_frames})
            actions.append({"group": group, "generation": exported["generation_record"], "camera": exported["camera_record"],
                "placement": final["placement_record"], "export": proof(project, folder/f"paint-action-g{group:02}-native-export-v2-placement-v2.json"),
                "converted_frames": converted, "actual_pose_indices": list(range(len(converted))),
                "intentional_source_holds": final["source_holds"]})
        corpse = next(row for row in groups if row["group"] == 5)["frames"][-1]
        groups.append({"group": 22, "frames": [corpse]})
        recipe = {"recipe_type": "animation", "output_path": f"Content/Sprites/runeterra/demacia/creatures/{unit}/battle.json",
            "canvas": [450, 400], "groups": groups, "generateShadow": 1, "generateOverlay": 1,
            "source_status": "Source-only diagnostic candidate; not active or visually accepted",
            "credits": "Original own volumetric rig/poses and generated painted finish. Installed original Castle resources are private style comparisons only.",
            "acceptance": "No final art, native gameplay, or release acceptance. Known Adept final-walk body-height drift remains open.",
            "active_assets_modified": False, "visual_approval_granted": False}
        recipe_path = folder/"battle-candidate-v1.recipe.json"
        write(recipe_path, recipe)
        units.append({"id": unit, "blend": proof(project, folder/f"{unit}-musician-rig-v6.blend"),
            "raw_pose_metadata": proof(project, folder/"musician-production-v6.json"), "actions": actions,
            "candidate_recipe": proof(project, recipe_path), "groups": {str(row["group"]):len(row["frames"]) for row in groups},
            "actual_source_pose_cells": 75, "pose_count_note": "Count includes genuine ready/recovery holds; it is not75unique physical poses.", "corpse": "g22 explicitly reuses actual final painted g05 corpse",
            "open_issues": ["Adeptg00f005 roughly5px head/body-height drift remains open"] if unit == "resonanceAdept" else [],
            "status": "Source-only diagnostic candidate; actual renderer grounding, mirrored action and release timing still pending"})
    result = {"units": units, "placement_evidence": proof(project, evidence),
              "active_assets_modified": False, "visual_approval_granted": False}
    write(project/"assets/source/creatures/musician-painted-battle-candidates-v1.json", result)
    return result


def painted_emission_report(project: Path) -> dict:
    """Manual visible wooden-rim landmarks, measured on final source PNGs."""
    project=project.resolve()
    points={"resonanceAdept": ((216,226),(215,227),(215,226)),
            "harmonicWarden": ((216,221),(215,224),(215,226))}
    complete=json.loads((project/"assets/source/creatures/musician-painted-battle-candidates-v1.json").read_text())
    content=json.loads((project/"content/creatures.json").read_text())
    units=[]
    for unit in UNITS:
        folder=project/"assets/source/creatures"/unit/"musician-rig-v6"
        row=next(value for value in complete["units"] if value["id"]==unit)
        measurements=[]
        for group,direction,point in zip((14,15,16),("upper","middle","lower"),points[unit]):
            action=next(value for value in row["actions"] if value["group"]==group)
            generation=json.loads((project/action["generation"]["path"]).read_text())
            native=action["converted_frames"][4]
            missile=content[unit]["graphics"]["missile"]
            offsets=missile["offset"]
            measurements.append({"group":group,"direction":direction,"source_kind":"painted-native",
                "release_frame_zero_based":4,"one_based_climax":5,
                "native_emitter_pixels":list(point),
                "landmark":"Manually selected top rim of the forward wooden resonator face, over its central crest; visible on the actual final painted native PNG, not copied from rig coordinates.",
                "source_frame":proof(project,project/generation["output"]),
                "native_frame":{"path":native["output"],"sha256":native["sha256"]},
                "source_pose_metadata":row["raw_pose_metadata"],"generation_record":action["generation"],
                "camera":action["camera"],"placement":action["placement"],"export":action["export"],
                "padding_conversion":{key:native[key] for key in ("source","source_sha256","output","sha256","retained_rectangle","retained_rgba_pixels_identical")},
                "proposed_offset":{"x":point[0]-197,"y":point[1]-265},
                "configured_offset_snapshot":{"x":offsets[direction+"X"],"y":offsets[direction+"Y"]},
                "configured_one_based_climax_snapshot":missile["attackClimaxFrame"],
                "configured_facing_right_origin_snapshot":[197+offsets[direction+"X"],265+offsets[direction+"Y"]],
                "proposed_native_facing_right_origin":list(point),
                "proposed_native_facing_left_formula":[247-(point[0]-197),point[1]],
                "native_renderer_verified":False})
        units.append({"id":unit,"source_kind":"painted-native","blend":row["blend"],
            "blend_role":"Original editable pose-guide provenance only; imagegen painted pixels are not evaluated geometry and are measured separately.",
            "measurements":measurements})
    result={"source_kind":"painted-native","units":units,
        "measurement_board":proof(project,project/"references/prototypes/musician-rig/painted-release-emitter-review-v1.png"),
        "native_formula":{"facing_right_x":"197+offsetX","facing_left_x":"247-offsetX","y":"265+offsetY",
            "release":"One-based configured5 emits at zero-based4 after native group frame-count clamp."},
        "limitations":["Source PNG landmarks only. Actual VCMI projectile attachment, mirrored left-facing origin and release timing remain unobserved for these candidates.",
            "Left-facing anchor247-offsetX is not a strict449-x bitmap landmark mirror; actual stack placement/rendering must be observed before accepting attachment.",
            "Adept directional instrument pitch is subtle at native size; measured painted rim Y is226/227/226 rather than the raw rig's monotonic222/226/230. Do not replace measured points with inferred raw geometry."],
        "active_content_modified":False,"visual_approval_granted":False}
    write(project/"assets/source/creatures/musician-painted-projectile-landmarks-v1.json",result)
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--finalize", action="store_true")
    args = parser.parse_args()
    result = export_remaining(args.project)
    if args.finalize:
        result = finalize_sources(args.project)
        painted_emission_report(args.project)
        print(json.dumps({"units": len(result["units"]), "frames": sum(sum(row["groups"].values()) for row in result["units"])}))
    else:
        print(json.dumps({"groups": len(result["actions"]), "frames": sum(row["frames"] for row in result["actions"])}))
