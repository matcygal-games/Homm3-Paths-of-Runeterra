"""Fixed-root technical assembly of delivered painted 2D priest masters only.

No drawing, pose invention, alpha thresholding, per-pose fitting, staging or
manifest mutation. Compile with the actual shared strict compiler plan twice
into report-only trees. Incomplete source sets fail before recipe production.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
from PIL import Image, ImageDraw, ImageOps

PROJECT = next(parent for parent in Path(__file__).resolve().parents
               if parent.name == "runeterra-shurima" and (parent / "content").is_dir())
REPORT = PROJECT / "build/reports/painted-priests-actions-20261024-v1"
OUTPUT = REPORT
sys.path.insert(0, str(PROJECT.parent / "scripts"))
import faction_art_compile

SOURCE_ROOT = [740, 1140]
BATTLE_ROOT = [193, 266]
BATTLE_SCALE = .068
MAP_SCALE = .04
MAP_ROOT = [64, 60]
PORTRAIT_CROP = [350, 100, 1110, 950]
POSES = {
    "walk-contact-a": "walk-contact-a-v1", "walk-down-a": "walk-down-a-v1",
    "walk-pass-a": "walk-pass-a-v1", "walk-contact-b": "walk-contact-b-v1",
    "walk-down-b": "walk-down-b-v1", "walk-pass-b": "walk-pass-b-v1",
    "fidget": "fidget-look-v1", "hit": "hit-recoil-v1", "defend": "defend-brace-v1",
    "death-kneel": "death-kneel-v3", "death-fall": "death-fall-v3", "death-rest": "death-rest-v1",
    "turn-front": "turn-front-v1", "turn-back": "turn-back-v1",
    "melee-up": "melee-up-v1", "melee-front": "melee-front-v1", "melee-down": "melee-down-v1",
    "shoot-load": "shoot-load-v1",
    "shoot-aim-up": "shoot-aim-up-v1", "shoot-aim-front": "shoot-aim-front-v1", "shoot-aim-down": "shoot-aim-down-v1",
    "shoot-release-up": "shoot-release-up-v2", "shoot-release-front": "shoot-release-front-v2", "shoot-release-down": "shoot-release-down-v2",
    "cast-prepare": "cast-prepare-v2", "cast-up": "cast-up-v1", "cast-front": "cast-front-v1", "cast-down": "cast-down-v1",
}


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded(value))


def fixed_place(image, canvas, scale, root):
    # One recorded transform, independent of opaque bounds and action pose.
    # Supersample this same affine before one uniform downsample so miniature
    # cloth/metal details are filtered, rather than sparsely sampled.
    sample = 4
    work = image.transform(tuple(value * sample for value in canvas), Image.Transform.AFFINE,
        (1 / (scale * sample), 0, SOURCE_ROOT[0] - root[0] / scale,
         0, 1 / (scale * sample), SOURCE_ROOT[1] - root[1] / scale),
        resample=Image.Resampling.BICUBIC, fillcolor=(0, 0, 0, 0))
    return work.resize(canvas, Image.Resampling.LANCZOS)


def descriptor(path):
    with Image.open(path) as opened:
        size = list(opened.size)
    return {"source": path.relative_to(PROJECT).as_posix(), "source_sha256": sha(path), "source_canvas": size}


def border_alpha(image):
    alpha = image.getchannel("A")
    return max(alpha.crop(box).getextrema()[1] for box in (
        (0, 0, image.width, 1), (0, image.height - 1, image.width, image.height),
        (0, 0, 1, image.height), (image.width - 1, 0, image.width, image.height)))


def portrait(image, size):
    cropped = image.crop(PORTRAIT_CROP)
    ratio = min(size[0] / cropped.width, size[1] / cropped.height)
    resized = cropped.resize((round(cropped.width * ratio), round(cropped.height * ratio)), Image.Resampling.LANCZOS)
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    out.alpha_composite(resized, ((size[0] - resized.width) // 2, (size[1] - resized.height) // 2))
    return out


def sequences():
    groups = {0: ["walk-contact-a", "walk-down-a", "walk-pass-a", "walk-contact-b", "walk-down-b", "walk-pass-b"],
              1: ["standing", "fidget", "standing"], 2: ["standing"], 3: ["hit", "standing"],
              4: ["defend"], 5: ["death-kneel", "death-fall", "death-rest"],
              7: ["turn-front"], 8: ["turn-back"]}
    for index, direction in enumerate(("up", "front", "down")):
        # Native MeleeAttackAnimation triggers HIT at currentFrame*2>=count.
        # Six frames hit at index3: hold the real contact across indices2/3.
        groups[11 + index] = ["standing", "defend", "melee-" + direction,
                              "melee-" + direction, "defend", "standing"]
        # Native ShootingAnimation::getAttackClimaxFrame returns configured - 1.
        # Content frame 4 therefore means zero-based index 3: physical release.
        groups[14 + index] = ["standing", "shoot-load", "shoot-aim-" + direction,
                              "shoot-release-" + direction, "standing"]
        groups[30 + index] = ["cast-prepare", "cast-" + direction, "standing"]
    return groups


def sheet(unit, natives, groups, scale):
    tile = (180 * scale, 155 * scale)
    rows = len(groups)
    out = Image.new("RGB", (tile[0] * 7, tile[1] * rows), (62, 61, 58))
    draw = ImageDraw.Draw(out)
    for row, (group, names) in enumerate(sorted(groups.items())):
        for col, name in enumerate(names):
            fixed_crop = natives[name].crop((110, 130, 290, 285))
            if scale != 1:
                fixed_crop = fixed_crop.resize(tile, Image.Resampling.NEAREST)
            point = (col * tile[0], row * tile[1])
            out.paste(fixed_crop, point, fixed_crop.getchannel("A"))
            draw.text((point[0] + 3, point[1] + 3), f"g{group} f{col} {name}", fill=(238, 231, 208))
    out.save(OUTPUT / f"{unit}-all-actions-{scale}x.png")


def unique_sheet(unit, natives):
    keys = list(natives)
    out = Image.new("RGB", (900, ((len(keys) + 4) // 5) * 155), (62, 61, 58))
    draw = ImageDraw.Draw(out)
    for index, name in enumerate(keys):
        point = ((index % 5) * 180, (index // 5) * 155)
        cropped = natives[name].crop((110, 130, 290, 285))
        out.paste(cropped, point, cropped.getchannel("A"))
        draw.text((point[0] + 3, point[1] + 3), name, fill=(238, 231, 208))
    out.save(OUTPUT / f"{unit}-unique-poses-1x.png")


def main():
    global OUTPUT
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true", help="Inspect existing fixed-root sources without claiming source closure")
    args = parser.parse_args()
    guarded_inputs = [PROJECT / "assets/manifest.json", PROJECT / "content/creatures.json",
                      Path(faction_art_compile.__file__), Path(__file__)]
    guarded_start = {str(path): sha(path) for path in guarded_inputs}
    if not args.preview:
        missing = []
        for unit in ("sunPriest", "highPriest"):
            root = PROJECT / "assets/source/creatures/painted-v2" / unit
            for stem in ("standing-v2", *POSES.values()):
                if not (root / (stem + ".png")).is_file():
                    missing.append((root / (stem + ".png")).relative_to(PROJECT).as_posix())
        if missing:
            raise RuntimeError("Incomplete pair; no recipe or compiler write permitted: " + ", ".join(missing))
    OUTPUT = REPORT / (("preview-" if args.preview else "conversion-") + str(time.time_ns()))
    OUTPUT.mkdir()
    compiler = faction_art_compile.create_compiler("shurima")
    manifest = json.loads((PROJECT / "assets/manifest.json").read_text(encoding="utf-8"))
    receipts, all_outputs, lineages = [], {}, {}
    for unit in ("sunPriest", "highPriest"):
        source = PROJECT / "assets/source/creatures/painted-v2" / unit
        masters = {"standing": source / ("standing-v2.png")}
        masters.update({key: source / (name + ".png") for key, name in POSES.items()})
        missing = [path.relative_to(PROJECT).as_posix() for path in masters.values() if not path.is_file()]
        if missing and not args.preview:
            raise RuntimeError("Missing real painted action sources: " + ", ".join(missing))
        natives, lineage, native_paths = {}, [], {}
        native_dir = source / "native-v1"
        native_dir.mkdir(exist_ok=True, parents=True)
        for name, path in masters.items():
            if not path.is_file():
                continue
            with Image.open(path) as opened:
                # Builtin output occasionally varies the transparent canvas.
                # Physical coordinates use the identical absolute affine;
                # actual canvas dimensions are recorded, never fit to nominal.
                if opened.mode != "RGBA" or not (1310 <= opened.width <= 1350 and 1162 <= opened.height <= 1202):
                    raise RuntimeError(f"Unexpected generated canvas/mode {path}: {opened.size}/{opened.mode}; never fit opaque body")
                master = opened.copy()
            source_edge = border_alpha(master)
            if not args.preview and source_edge >= 128:
                raise RuntimeError(f"Source has substantial alpha at its canvas edge; inspect/repair clipping before complete compilation: {path}")
            native = fixed_place(master, (450, 400), BATTLE_SCALE, BATTLE_ROOT)
            natives[name] = native
            destination = native_dir / (path.stem + ".png")
            native.save(destination, compress_level=9)
            native_paths[name] = destination
            lineage.append({"pose": name, "master": descriptor(path), "native": descriptor(destination),
                            "source_border_alpha_max": source_edge,
                            "source_canvas_matches_nominal": master.size == (1330, 1182),
                            "native_border_alpha_max": border_alpha(native),
                            "native_alpha_bounds": list(native.getchannel("A").getbbox())})
        available_groups = {group: names for group, names in sequences().items() if all(name in natives for name in names)}
        sheet(unit, natives, available_groups, 1)
        sheet(unit, natives, available_groups, 2)
        unique_sheet(unit, natives)
        request_records = []
        for request_path in sorted((source / "requests").glob("*.json")):
            request = json.loads(request_path.read_text(encoding="utf-8"))
            request_records.append({"request": request_path.relative_to(PROJECT).as_posix(),
                "request_sha256": sha(request_path),
                "reference_sha256": {ref: sha(PROJECT / ref) for ref in request["referenced_image_paths"]},
                "output": descriptor(source / (request_path.stem + ".png")) if (source / (request_path.stem + ".png")).is_file() else None})
        ledger_path = source / ("generation-ledger-" + OUTPUT.name + ".json")
        save_json(ledger_path, {"status": "authored configuration",
            "provider": "OpenAI built-in imagegen", "model": "not exposed by tool",
            "requests": request_records, "selected_pose_sources": lineage,
            "parent_requests": [record for path in sorted(source.glob("*-request*.json"))
                                for record in [{"source": path.relative_to(PROJECT).as_posix(), "sha256": sha(path)}]],
            "no_3d_inputs": True, "visual_approval_granted": False})
        lineages[unit] = {"sources": lineage, "missing": missing}
        if args.preview:
            continue
        resources = source / "resources-v1"
        resources.mkdir(exist_ok=True)
        with Image.open(masters["standing"]) as opened:
            standing = opened.copy()
        with Image.open(masters["melee-front"]) as opened:
            melee = opened.copy()
        fixed_place(standing, (96, 64), MAP_SCALE, MAP_ROOT).save(resources / "map-000.png", compress_level=9)
        attack = fixed_place(melee, (96, 64), MAP_SCALE, MAP_ROOT)
        attack.save(resources / "attackRight.png", compress_level=9)
        # Mirror complete canvas about the documented root x64, never alpha bounds.
        attack.transform((96, 64), Image.Transform.AFFINE, (-1, 0, 2 * MAP_ROOT[0], 0, 1, 0),
                         resample=Image.Resampling.NEAREST).save(resources / "attackLeft.png", compress_level=9)
        for role, size in (("large", (58, 64)), ("small", (32, 32))):
            portrait(standing, size).save(resources / (role + ".png"), compress_level=9)
        generation = {"image_generation_used": True, "provider": "OpenAI built-in imagegen; pure painted 2D sources",
                      "model": "not exposed by tool", "prompt": "Exact portable requests in the unit requests/ JSON leaves, plus preserved standing/walk request JSON. No 3D sources.",
                      "painted_master": masters["standing"].relative_to(PROJECT).as_posix(),
                      "painted_master_sha256": sha(masters["standing"]),
                      "method": "One fixed .068 battle transform and .04 adventure transform. No per-pose opaque-body fit, alpha threshold, pose synthesis or silhouette normalization.",
                      "provenance": ledger_path.relative_to(PROJECT).as_posix(),
                      "provenance_sha256": sha(ledger_path),
                      "producer_source": Path(__file__).relative_to(PROJECT).as_posix(),
                      "producer_source_sha256": sha(Path(__file__))}
        common = {"production_status": "painted-master-complete-unapproved", "status": "authored configuration",
                  "unit": unit, "generation": generation, "visual_approval_granted": False,
                  "credits": {"author": "Project-directed built-in imagegen; technical 2D assembly", "license": None,
                              "redistribution": "unresolved; release prohibited"},
                  "acceptance": "Technical conversion only; genuine source actions require native visual/motion and rights review."}
        recipes = {"battle": {**common, "recipe_type": "vcmi_animation", "canvas": [450, 400],
                    "pivot": {"x": 193, "y": 266}, "generateShadow": 0, "generateOverlay": 1,
                    "groups": [{"group": group, "frames": [descriptor(native_paths[name]) for name in names]}
                               for group, names in sorted(sequences().items())]},
                   "map": {**common, "recipe_type": "vcmi_animation", "canvas": [96, 64],
                    "pivot": {"x": 64, "y": 60}, "generateShadow": 0, "generateOverlay": 1,
                    "groups": [{"group": 0, "frames": [descriptor(resources / "map-000.png")]}]}}
        for role in ("attackLeft", "attackRight", "large", "small"):
            desc = descriptor(resources / (role + ".png"))
            recipes[role] = {**common, "recipe_type": "raster", "fit": "exact", "size": desc["source_canvas"],
                             "require_alpha": True, **desc}
        required = next(a["required_groups"] for a in manifest["assets"] if a["output_path"].endswith(f"/{unit}/battle.json"))
        actual = {str(group): len(names) for group, names in sequences().items()}
        if any(actual.get(group, 0) < count for group, count in required.items()):
            raise RuntimeError("Current manifest group requirements not satisfied")
        for role, recipe in recipes.items():
            extension = ".json" if role in ("map", "battle") else ".png"
            recipe["output_path"] = f"Content/Sprites/runeterra/shurima/creatures/{unit}/{role}{extension}"
            recipe_path = PROJECT / "assets/recipes/creatures/painted-v2" / unit / (role + ".json")
            save_json(recipe_path, recipe)
            save_json(OUTPUT / "recipe-snapshots" / unit / (role + ".json"), recipe)
            first, receipt = compiler.plan(PROJECT, recipe_path)
            second, _ = compiler.plan(PROJECT, recipe_path)
            if first != second:
                raise RuntimeError("Strict compiler plan was not byte-deterministic")
            for folder, outputs in (("compiled-a", first), ("compiled-b", second)):
                for relative, data in outputs.items():
                    destination = OUTPUT / folder / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(data)
            all_outputs.update({relative: hashlib.sha256(data).hexdigest() for relative, data in first.items()})
            receipts.append(receipt)
    guarded_end = {str(path): sha(path) for path in guarded_inputs}
    if guarded_end != guarded_start:
        raise RuntimeError("Guarded producer/compiler/manifest/creature input changed during run; invalidate this attempt")
    result = {"status": "authored configuration", "source_lineage": lineages, "battle_scale": BATTLE_SCALE,
              "source_root": SOURCE_ROOT, "battle_root": BATTLE_ROOT, "map_scale": MAP_SCALE, "map_root": MAP_ROOT,
              "affine_filter": "4x fixed affine supersample, uniform Lanczos downsample; unchanged source alpha, no thresholds",
              "portrait_fixed_crop": PORTRAIT_CROP, "per_pose_body_fit": False, "alpha_threshold": False,
              "preview_only": args.preview, "strict_compiler_receipts": receipts, "output_sha256": all_outputs,
              "producer_sha256": sha(Path(__file__)), "compiler_sha256": sha(Path(faction_art_compile.__file__)),
              "guarded_inputs_unchanged": True,
              "shooting_configured_climax": 4, "shooting_zero_based_release_index": 3,
              "melee_frame_count": 6, "melee_zero_based_hit_index": 3,
              "manifest_sha256": sha(PROJECT / "assets/manifest.json"),
              "creature_definitions_sha256": sha(PROJECT / "content/creatures.json"),
              "runtime_verified": False, "visual_approval_granted": False, "release_accepted": False}
    save_json(OUTPUT / ("partial-inspection.json" if args.preview else "technical-conversion.json"), result)
    print(json.dumps({"preview_only": args.preview, "recipes": len(receipts), "compiled_files": len(all_outputs),
                      "missing": {unit: len(value["missing"]) for unit, value in lineages.items()},
                      "report": OUTPUT.relative_to(PROJECT).as_posix()}, indent=2))


if __name__ == "__main__":
    main()
