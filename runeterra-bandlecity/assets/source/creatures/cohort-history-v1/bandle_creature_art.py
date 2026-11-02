"""Register delivered painted Bandle troop atlases; never synthesize artwork.

Only own source exports, recipes and creature review reports are writable here.
The coordinator alone compiles/stages/publishes. All outputs remain unapproved.
Run with the project Pillow environment: python scripts/bandle_creature_art.py.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from statistics import median
import sys

from PIL import Image, ImageDraw

PROJECT = Path(__file__).resolve().parents[1]
WORKSPACE = PROJECT.parent
PREFIX = "Content/Sprites/runeterra/bandlecity/"
UNITS = {
    "yordleScout": (48, None, 0), "scoutPatrol": (48, None, 0),
    "faeTrickster": (48, "fly", 2), "briarTrickster": (48, "fly", 2),
    "mechPilot": (88, None, 0), "advancedMech": (88, None, 0),
    "puffcapTrapper": (48, "shoot", 6), "masterTrapper": (48, "shoot", 6),
    "portalMage": (54, "cast", 3), "gladeMagus": (54, "cast", 3),
    "bandleGunner": (62, "shoot", 3), "bandleBombardier": (62, "shoot", 4),
    "gladeGuardian": (94, "flycast", 5), "elderGladeGuardian": (94, "flycast", 5),
}
NAMES = list(UNITS)
SHOOTERS = ("puffcapTrapper", "masterTrapper", "bandleGunner", "bandleBombardier")
ACCEPTANCE = "built-unreviewed; all-action/native playback, artistic and redistribution acceptance pending"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: dict) -> None:
    allowed = [PROJECT / "assets/source/creatures", PROJECT / "assets/source/projectiles",
               PROJECT / "assets/recipes/creatures", PROJECT / "assets/recipes/projectiles",
               PROJECT / "build/reports/art-review/creatures"]
    if not any(path.resolve().is_relative_to(root.resolve()) for root in allowed):
        raise ValueError(f"Not an owned output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return path.relative_to(PROJECT).as_posix()


def save(image: Image.Image, path: Path) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG", compress_level=9, optimize=False)
    return {"source": rel(path), "source_sha256": sha(path), "sha256": sha(path),
            "source_canvas": list(image.size)}


def generation(folder: Path) -> dict:
    master = folder / ("action-atlas.png" if "creatures" in folder.parts else "master.png")
    response = json.loads((folder / "tool-response.json").read_text(encoding="utf-8"))
    prompt = (folder / "prompt.txt").read_text(encoding="utf-8").rstrip("\n")
    image = Image.open(master)
    if image.mode != "RGBA" or image.getchannel("A").getextrema()[0] != 0:
        raise ValueError(f"Actual transparent RGBA master required: {master}")
    data = {"provider": "OpenAI built-in imagegen", "model": "not exposed by built-in tool",
            "image_generation_used": True, "prompt": prompt,
            "painted_master": rel(master), "painted_master_sha256": sha(master),
            "source_canvas": list(image.size), "prompt_sha256": sha(folder / "prompt.txt"),
            "tool_response_sha256": sha(folder / "tool-response.json"),
            "original_generated_path": response["original_generated_path"],
            "status": "authored configuration", "native_playback": "not_run",
            "native_visual_review": "pending", "release_accepted": False,
            "transparent_background_requested": True, "alpha_preserved": True}
    reference = response.get("identity_reference")
    if reference:
        data["references"] = [{"path": reference, "sha256": sha(PROJECT / reference),
                               "role": "own subject identity reference, not pose source"}]
    write(folder / "generation.json", data)
    return data


def layout(image: Image.Image, rows: int) -> tuple[list[int], list[dict]]:
    """Measure low-alpha row gutters; one camera/anchor for each entire row.

    The tool does not guarantee requested canvas or square cells. Do not assume
    either. The crop boundaries are evidence, not changes to source alpha.
    """
    alpha = image.getchannel("A")
    counts = [sum(v > 30 for v in alpha.crop((0, y, image.width, y + 1)).get_flattened_data())
              for y in range(image.height)]
    bounds = [0]
    pitch = image.height / rows
    for row in range(1, rows):
        target = round(pitch * row)
        candidates = range(max(bounds[-1] + 1, round(target - pitch * .24)),
                           min(image.height, round(target + pitch * .24)))
        low = min(counts[y] for y in candidates)
        # Pick the centre of the longest low-alpha gutter near the expected row.
        good = [y for y in candidates if counts[y] <= low + 2]
        runs = []
        for y in good:
            if runs and y == runs[-1][-1] + 1:
                runs[-1].append(y)
            else:
                runs.append([y])
        gutter = min(runs, key=lambda run: (-len(run), abs(median(run) - target)))
        bounds.append(round(median(gutter)))
    bounds.append(image.height)
    records = []
    for row in range(rows):
        bottoms = []
        boxes = []
        for col in range(6):
            box = [round(col * image.width / 6), bounds[row],
                   round((col + 1) * image.width / 6), bounds[row + 1]]
            cell = image.crop(box)
            bbox = cell.getchannel("A").point(lambda v: 255 if v > 30 else 0).getbbox()
            if bbox is None:
                raise ValueError(f"Empty painted cell row={row}, col={col}")
            bottoms.append(bbox[3])
            boxes.append(box)
        records.append({"row": row, "crop_boxes": boxes,
                        "shared_anchor": [image.width / 12, median(bottoms)],
                        "boundary_alpha_pixels": [counts[bounds[row]], counts[min(image.height - 1, bounds[row + 1] - 1)]],
                        "camera": "one row cohort; never per-frame bbox recentering"})
    return bounds, records


def register_atlas(unit: str, version: str, rows: int, height: int) -> tuple[dict, dict]:
    folder = PROJECT / f"assets/source/creatures/{unit}/{version}"
    provenance = generation(folder)
    image = Image.open(folder / "action-atlas.png").copy()
    _, row_records = layout(image, rows)
    reference_row, reference_col = (1, 4) if version == "master-v1" else (0, 0)
    ref = image.crop(row_records[reference_row]["crop_boxes"][reference_col])
    bbox = ref.getchannel("A").point(lambda v: 255 if v > 30 else 0).getbbox()
    scale = height / (bbox[3] - bbox[1])
    output = {}
    measured = []
    for record in row_records:
        row = record["row"]
        anchor_x, anchor_y = record["shared_anchor"]
        for col, crop in enumerate(record["crop_boxes"]):
            cell = image.crop(crop)
            target = (max(1, round(cell.width * scale)), max(1, round(cell.height * scale)))
            resized = cell.resize(target, Image.Resampling.LANCZOS)
            canvas = Image.new("RGBA", (450, 400))
            # One native combat pivot, one scale per atlas, one anchor per row.
            offset = (225 - round(anchor_x * scale), 270 - round(anchor_y * scale))
            canvas.alpha_composite(resized, offset)
            destination = PROJECT / f"assets/source/creatures/{unit}/registered-v1/{version}/r{row:02}-c{col:02}.png"
            descriptor = save(canvas, destination)
            output[row, col] = descriptor
            measured.append({"row": row, "column": col, "crop": crop,
                             "scale": scale, "offset": list(offset), **descriptor})
    registration = {"unit": unit, "source": provenance["painted_master"],
                    "source_sha256": provenance["painted_master_sha256"],
                    "canvas": [450, 400], "pivot": {"x": 225, "y": 270},
                    "native_subject_height_target": height, "scale": scale,
                    "row_cameras": row_records, "frames": measured,
                    "source_alpha_modified": False, "per_frame_fitting": False,
                    "status": "authored configuration", "acceptance": ACCEPTANCE}
    write(folder / "registration.json", registration)
    return output, provenance


def base_recipe(unit: str, name: str, provenance: dict) -> dict:
    return {"unit": unit, "output_path": PREFIX + f"creatures/{unit}/{name}",
            "production_status": "painted-master-complete-unapproved",
            "status": "built-unreviewed", "generation": provenance,
            "credits": {"author": "Original project art: OpenAI built-in imagegen; technical assembly: Codex",
                        "license": "not reviewed", "redistribution": "unresolved; release prohibited"},
            "visual_approval_granted": False, "acceptance": ACCEPTANCE}


def groups_for(unit: str, master: dict, supplement: dict | None) -> dict:
    def row(source: dict, number: int, columns=range(6)):
        return [source[number, column] for column in columns]
    turn_row = 3 if unit == "bandleBombardier" else 4
    groups = {
        0: ("leaf-wing-flight" if "Trickster" in unit or "Guardian" in unit else "physical-ground-gait", row(master, 0)),
        1: ("four-pose-fidget-held-1-2-2-2-native-ticks", row(master, 1, [0, 1, 1, 2, 2, 3, 3])),
        2: ("anchored-idle", row(master, 1, [4])),
        3: ("hit-recoil", row(master, 2, range(3))),
        4: ("defensive-brace", row(master, 2, range(3, 6))),
        5: ("progressive-collapse", row(master, 3)),
        7: ("turn-front", row(master, turn_row, range(3))),
        8: ("turn-back", row(master, turn_row, range(3, 6))),
        11: ("melee-up", row(master, 5)),
        12: ("melee-front", row(master, 6)),
        13: ("melee-down", row(master, 7)),
    }
    if supplement:
        kind = UNITS[unit][1]
        if kind == "shoot":
            for index in range(3):
                groups[14 + index] = (f"physical-shoot-{'up front down'.split()[index]}", row(supplement, index))
            if "Trapper" in unit:
                for index in range(3):
                    groups[11 + index] = (f"held-jar-melee-{'up front down'.split()[index]}", row(supplement, index + 3))
            if unit == "bandleBombardier":
                groups[5] = ("repaired-progressive-crew-and-cannon-collapse", row(supplement, 3))
        if kind in ("cast", "flycast"):
            for index in range(3):
                groups[30 + index] = (f"native-action-cast-{'up front down'.split()[index]}", row(supplement, index))
        if kind in ("fly", "flycast"):
            start = 3 if kind == "flycast" else 0
            groups[20] = ("physical-wing-takeoff", row(supplement, start))
            groups[21] = ("physical-wing-landing", row(supplement, start + 1))
    return groups


def convert_unit(unit: str) -> dict:
    height, _, rows = UNITS[unit]
    master, provenance = register_atlas(unit, "master-v1", 8, height)
    supplement = None
    if rows:
        supplement, supplement_provenance = register_atlas(unit, "supplement-v1", rows, height)
        provenance["supplemental_generation_records"] = [supplement_provenance]
    provenance["technical_method"] = "Measured row-cohort registration; unmodified alpha, one uniform scale per atlas and shared native pivot. No pose synthesis or per-frame tight fitting."
    groups = groups_for(unit, master, supplement)
    battle = {**base_recipe(unit, "battle.json", provenance), "recipe_type": "vcmi_animation",
              "canvas": [450, 400], "pivot": {"x": 225, "y": 270},
              "generateShadow": 1, "generateOverlay": 1,
              "groups": [{"group": group, "action": action, "frames": frames}
                         for group, (action, frames) in sorted(groups.items())],
              "timing": {"fidget_seconds_at_native_10fps": .7, "fidget_pose_holds": [1, 2, 2, 2],
                         "probability_multiplier_in_content": .1, "controlled_native_elapsed_review": "not_run"}}
    write(PROJECT / f"assets/recipes/creatures/{unit}-battle.json", battle)
    native = PROJECT / f"assets/source/creatures/{unit}/registered-v1/ui-map"
    map_frames = []
    # Native map uses independently cropped real gait poses with ONE fixed crop
    # and scale, not still-frame translations; no directional spin is claimed.
    envelope = None
    for desc in groups[0][1]:
        box = Image.open(PROJECT / desc["source"]).getchannel("A").getbbox()
        envelope = box if envelope is None else (min(envelope[0], box[0]), min(envelope[1], box[1]),
                                                 max(envelope[2], box[2]), max(envelope[3], box[3]))
    ratio = min(52 / (envelope[2] - envelope[0]), 43 / (envelope[3] - envelope[1]))
    for index, desc in enumerate(groups[0][1]):
        crop = Image.open(PROJECT / desc["source"]).crop(envelope)
        crop = crop.resize((max(1, round(crop.width * ratio)), max(1, round(crop.height * ratio))), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (96, 64)); canvas.alpha_composite(crop, ((96 - crop.width) // 2, 58 - crop.height))
        map_frames.append(save(canvas, native / f"map-{index:03}.png"))
    map_recipe = {**base_recipe(unit, "map.json", provenance), "recipe_type": "vcmi_animation", "canvas": [96, 64],
                  "pivot": {"x": 48, "y": 58}, "generateShadow": 2, "generateOverlay": 1,
                  "groups": [{"group": 0, "action": "painted-gait", "frames": map_frames}]}
    write(PROJECT / f"assets/recipes/creatures/{unit}-map.json", map_recipe)
    idle = Image.open(PROJECT / master[1, 4]["source"])
    idle = idle.crop(idle.getchannel("A").getbbox())
    # UI crops can fit per icon; animation frames above cannot.
    portrait = idle.crop((0, 0, idle.width, max(1, round(idle.height * .78))))
    attack = Image.open(PROJECT / groups[12][1][3]["source"])
    attack = attack.crop(attack.getchannel("A").getbbox())
    resources = [("large", portrait, [58, 64], "cover"), ("small", portrait, [32, 32], "contain"),
                 ("attackRight", attack, [64, 64], "contain"),
                 ("attackLeft", attack.transpose(Image.Transpose.FLIP_LEFT_RIGHT), [64, 64], "contain")]
    for name, image, canvas, fit in resources:
        descriptor = save(image, native / f"{name}-source.png")
        recipe = {**base_recipe(unit, name + ".png", provenance), "recipe_type": "raster", "size": canvas,
                  "fit": fit, "require_alpha": True, **descriptor}
        if name == "attackLeft":
            recipe["technical_note"] = "UI-only documented mirror of genuine own painted attack; no independently painted left action claimed"
        write(PROJECT / f"assets/recipes/creatures/{unit}-{name}.json", recipe)
    unique = {group: len({desc["sha256"] for desc in frames}) for group, (_, frames) in groups.items()}
    if any(count < (1 if group == 2 else 2) for group, count in unique.items()):
        raise ValueError(f"Insufficient real distinct painted poses: {unit}: {unique}")
    record = {"unit": unit, "resources": 6, "group_frames": {str(g): len(v[1]) for g, v in groups.items()},
              "distinct_frame_hashes": unique, "battle_recipe_sha256": sha(PROJECT / f"assets/recipes/creatures/{unit}-battle.json"),
              "status": "authored configuration", "native_playback": "not_run", "visual_approval": "pending"}
    write(PROJECT / f"assets/source/creatures/{unit}/registered-v1/action-inventory.json", record)
    return record


def convert_projectile(unit: str) -> dict:
    folder = PROJECT / f"assets/source/projectiles/{unit}/master-v1"
    provenance = generation(folder)
    image = Image.open(folder / "master.png").copy()
    image = image.crop(image.getchannel("A").getbbox())
    ratio = min(18 / image.width, 18 / image.height)
    image = image.resize((max(1, round(image.width * ratio)), max(1, round(image.height * ratio))), Image.Resampling.LANCZOS)
    frames = []
    angles = [90, 45, 0, -45, -90]
    for index, angle in enumerate(angles):
        rotated = image.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
        canvas = Image.new("RGBA", (48, 48))
        canvas.alpha_composite(rotated, ((48 - rotated.width) // 2, (48 - rotated.height) // 2))
        frames.append(save(canvas, folder / f"direction-{index:02}.png"))
    provenance["conversion"] = {"frame_angles": angles, "animation_in_time": False,
                                "method": "Uniformly downsample original own painted master, technically rotate for native angle selections"}
    recipe = {"output_path": PREFIX + f"projectiles/{unit}.json", "role": "projectile-animation",
              "recipe_type": "vcmi_animation", "canvas": [48, 48], "pivot": {"x": 24, "y": 24},
              "generateShadow": 0, "generateOverlay": 0, "generation": provenance,
              "production_status": "painted-master-complete-unapproved", "visual_approval_granted": False,
              "groups": [{"group": 0, "frames": frames}], "acceptance": ACCEPTANCE}
    write(PROJECT / f"assets/recipes/projectiles/{unit}.json", recipe)
    return {"unit": unit, "frame_angles": angles, "recipe_sha256": sha(PROJECT / f"assets/recipes/projectiles/{unit}.json")}


def report_sheets() -> list[dict]:
    report = PROJECT / "build/reports/art-review/creatures/v1"
    report.mkdir(parents=True, exist_ok=True)
    sheet = Image.new("RGBA", (1000, 1040), (68, 68, 68, 255)); draw = ImageDraw.Draw(sheet)
    draw.text((12, 8), "Bandle City | own unreviewed art | native pixels (1x) | no native execution / no final approval", fill="white")
    originals = ["cpkman", "cpegas", "cigole", "chcbow", "cmage", "clcbow", "ctree"]
    for line in range(7):
        top = 40 + line * 140
        for variant in range(2):
            unit = NAMES[line * 2 + variant]
            recipe = json.loads((PROJECT / f"assets/recipes/creatures/{unit}-battle.json").read_text())
            idle = next(g for g in recipe["groups"] if g["group"] == 2)["frames"][0]
            frame = Image.open(PROJECT / idle["source"])
            crop = frame.crop((145, 155, 310, 280))
            x = 170 + variant * 220
            sheet.alpha_composite(crop, (x, top + 8))
            draw.text((x, top), unit, fill="white")
        original = WORKSPACE / f"runeterra-freljord/references/native-v1-03be6110fba70717/{originals[line]}.def.png"
        image = Image.open(original).convert("RGBA")
        sheet.alpha_composite(image.crop((145, 155, 310, 280)), (680, top + 8))
        draw.text((680, top), f"native {originals[line]} (reference)", fill="white")
    results = [save(sheet, report / "all14-native-profiles.png")]
    for line in range(7):
        image = Image.new("RGBA", (1060, 340), (68, 68, 68, 255)); draw = ImageDraw.Draw(image)
        draw.text((10, 5), "Native 1x | selected true poses | all-action quality / native playback / rights pending", fill="white")
        for variant in range(2):
            unit = NAMES[line * 2 + variant]
            recipe = json.loads((PROJECT / f"assets/recipes/creatures/{unit}-battle.json").read_text())
            groups = {g["group"]: g["frames"] for g in recipe["groups"]}
            selected = [(2, 0), (0, 0), (0, 2), (12, 2), (12, 3), (5, 0), (5, 3), (5, 5)]
            for col, (group, index) in enumerate(selected):
                frame = Image.open(PROJECT / groups[group][index]["source"])
                image.alpha_composite(frame.crop((150, 150, 280, 285)), (10 + col * 130, 43 + variant * 145))
                draw.text((14 + col * 130, 28 + variant * 145), f"g{group}/f{index}", fill="white")
            draw.text((10, 18 + variant * 145), unit, fill=(255, 215, 140))
        results.append(save(image, report / f"line-{line + 1:02}-native-selected-actions.png"))
    return results


def main() -> int:
    if PROJECT.name != "runeterra-bandlecity":
        raise ValueError("Own Bandle City project root required")
    records = [convert_unit(unit) for unit in NAMES]
    projectiles = [convert_projectile(unit) for unit in SHOOTERS]
    report = {"status": "authored configuration", "technical_candidate": "built-unreviewed",
              "units": records, "projectiles": projectiles, "recipes": 88,
              "native_playback": "not_run", "final_art_acceptance": "pending", "release_accepted": False,
              "sheets": report_sheets(), "script_sha256": sha(Path(__file__)),
              "notes": ["Original masters retained byte-for-byte; generated source alpha is never removed or repainted",
                        "Metadata completeness does not grant artistic acceptance; inspect source gutters, limb continuity, shadows and gait",
                        "Bombardier omitted death in base atlas: turns use actual row3; death uses supplemental row3",
                        "Trapper held-jar melee uses supplemental rows3/4/5, not initial throwing-like rows",
                        "Native fixed pivot225,270; per-atlas uniform scale, shared row anchors, no individual frame fitting",
                        "Fidget four genuine poses held1/2/2/2 native ticks =0.7s at10fps; native elapsed verification pending"]}
    write(PROJECT / "build/reports/art-review/creatures/v1/technical-source-inventory.json", report)
    print(json.dumps({"units": len(records), "projectiles": len(projectiles), "recipes": 88,
                      "report": "build/reports/art-review/creatures/v1/technical-source-inventory.json",
                      "final_art_acceptance": "pending"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
