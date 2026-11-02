"""BTA02 unselected portrait experiment. No selection, shared helper or stage writes.

Run with -B. --replay uses only frozen inputs and compiler; --compile-one is an
internal separate-process reproduction. All write destinations are jailed below.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile

from PIL import Image, ImageDraw, __version__ as pillow_version

SOURCE_ROOT = Path(__file__).resolve().parent
SOURCE = SOURCE_ROOT / "padded-v2"
PROJECT = SOURCE_ROOT.parents[4]
WORKSPACE = PROJECT.parent
REPORT = PROJECT / "build/reports/five-town-audit-20261022/art-portrait-fix/padded-v2"
PREFIX = "Content/Sprites/runeterra/bandlecity/creatures/faeTrickster/"
OWN = "assets/source/creatures/faeTrickster/portrait-eye-review-v1/padded-v2/"
ROI = [18, 0, 52, 37]
EYE = [42, 21, 45, 25]
CRACK = [40, 20, 47, 29]
EYE_POINTS = [(42, 21), (42, 23), (43, 23), (44, 23),
              (42, 24), (43, 24), (44, 24)]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def write(path, data):
    resolved = path.resolve()
    if not any(resolved.is_relative_to(root.resolve()) for root in (SOURCE, REPORT)):
        raise ValueError(f"Write outside assigned new paths: {path}")
    for parent in [path, *path.parents]:
        if parent.exists() and parent.is_symlink():
            raise ValueError(f"Redirected path refused: {parent}")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != data:
        raise ValueError(f"Preserve existing differing evidence: {path}")
    if not path.exists():
        path.write_bytes(data)


def png(image):
    stream = io.BytesIO()
    image.save(stream, "PNG", compress_level=9, optimize=False)
    return stream.getvalue()


def image(path):
    with Image.open(path) as opened:
        opened.load()
        return opened.convert("RGBA")


def compiler():
    path = REPORT / "compiler-root/scripts/faction_art_compile.py"
    spec = importlib.util.spec_from_file_location("portrait_frozen_compiler", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.create_compiler("bandlecity")


def protection_inventory():
    paths = set()
    for base in (PROJECT / "assets/source/creatures/faeTrickster",
                 PROJECT / "assets/generated" / PREFIX,
                 PROJECT / "build/Mods/runeterra-bandlecity" / PREFIX):
        for path in base.rglob("*"):
            if path.is_file() and not path.is_relative_to(SOURCE_ROOT) and "flight-size-review-v1" not in path.parts:
                paths.add(path)
    paths.update((PROJECT / "assets/recipes/creatures").glob("faeTrickster-*.json"))
    paths.add(PROJECT / "assets/manifest.json")
    return {p.relative_to(PROJECT).as_posix(): sha(p.read_bytes()) for p in sorted(paths)}


def prepare():
    write(REPORT / "protected-before.json", encoded(protection_inventory()))
    mappings = {
        "fae-large-source.png": "assets/source/creatures/faeTrickster/registered-v2/ui-map/large-source.png",
        "selected-large-recipe.json": "assets/recipes/creatures/faeTrickster-large.json",
        "selected-small-recipe.json": "assets/recipes/creatures/faeTrickster-small.json",
        "selected-large.png": "assets/generated/" + PREFIX + "large.png",
        "selected-small.png": "assets/generated/" + PREFIX + "small.png",
    }
    for unit in ("briarTrickster", "gladeGuardian", "elderGladeGuardian"):
        for size in ("large", "small"):
            mappings[f"{unit}-{size}.png"] = f"assets/generated/Content/Sprites/runeterra/bandlecity/creatures/{unit}/{size}.png"
    # Discover the actual selected map frame through its recipe, never guess it.
    map_recipe = json.loads((PROJECT / "assets/recipes/creatures/faeTrickster-map.json").read_text())
    mappings["selected-map.png"] = map_recipe["groups"][0]["frames"][0]["source"]
    pins = {}
    for name, relative in mappings.items():
        data = (PROJECT / relative).read_bytes()
        write(SOURCE / "inputs" / name, data)
        pins[relative] = {"sha256": sha(data), "snapshot": OWN + "inputs/" + name}
    data = (WORKSPACE / "scripts/faction_art_compile.py").read_bytes()
    write(REPORT / "compiler-root/scripts/faction_art_compile.py", data)
    pins["../scripts/faction_art_compile.py"] = {"sha256": sha(data), "snapshot": "build/reports/five-town-audit-20261022/art-portrait-fix/padded-v2/compiler-root/scripts/faction_art_compile.py"}
    write(SOURCE / "source-pins.json", encoded(pins))


def compose(source, roi):
    if (len(roi) != 4 or any(type(v) is not int for v in roi)
            or not 0 <= roi[0] < roi[2] <= source.width
            or not 0 <= roi[1] < roi[3] <= source.height):
        raise ValueError("Invalid portrait ROI")
    framed = Image.new("RGBA", (42, 46), (0, 0, 0, 0))
    framed.paste(source.crop(tuple(roi)), (4, 4))
    return framed


def recipes():
    master = image(SOURCE / "inputs/fae-large-source.png")
    framed = compose(master, ROI)
    data = png(framed)
    write(SOURCE / "portrait-framed-master.png", data)
    draft = {
        "recipe_type": "raster", "production_status": "painted-master-complete-unapproved",
        "status": "built-unreviewed", "selected": False, "unit": "faeTrickster",
        "source": OWN + "portrait-framed-master.png", "source_sha256": sha(data),
        "source_canvas": [42, 46], "size": [58, 64], "fit": "cover", "require_alpha": True,
        "output_path": PREFIX + "large.png", "visual_approval_granted": False,
        "generation": {"image_generation_used": False,
                       "method": "Lossless own-source ROI [18,0,52,37), raw RGBA paste at (4,4) on transparent 42x46; existing compiler performs uniform Lanczos cover. No recolor, paint, mirror or new pose."},
        "upstream_identity": {"source": OWN + "inputs/fae-large-source.png",
                              "sha256": sha((SOURCE / "inputs/fae-large-source.png").read_bytes()),
                              "roi": ROI, "paste_xy": [4, 4], "eye_rectangle": EYE,
                              "seed_crack_context_rectangle": CRACK},
        "acceptance": "UNSELECTED; actual human art review, native context and redistribution pending",
    }
    write(SOURCE / "large-draft.recipe.json", encoded(draft))
    small = copy.deepcopy(draft)
    small.update(size=[32, 32], fit="contain", output_path=PREFIX + "diagnostic-small.png",
                 diagnostic_only=True, selected_small_unchanged=True)
    write(SOURCE / "small-diagnostic.recipe.json", encoded(small))
    old = json.loads((SOURCE / "inputs/selected-large-recipe.json").read_text())
    old["source"] = OWN + "inputs/fae-large-source.png"
    old["output_path"] = PREFIX + "negative-old-center-cover.png"
    write(SOURCE / "negative-old.recipe.json", encoded(old))
    contain = copy.deepcopy(old)
    contain.update(fit="contain", output_path=PREFIX + "control-full-contain.png")
    write(SOURCE / "control-full-contain.recipe.json", encoded(contain))


def compile_one(label):
    if label not in ("run-a", "run-b"):
        raise ValueError("Only two named scoped reproductions are permitted")
    scratch = REPORT / label / "runeterra-bandlecity"
    module = compiler()
    expected = scratch / "assets/generated" / PREFIX / "large.png"
    if module.output_path(scratch, PREFIX + "large.png") != expected.resolve():
        raise RuntimeError("Actual compiler API cannot confine output; stopped before writes")
    for name in ("portrait-framed-master.png", "inputs/fae-large-source.png"):
        write(scratch / OWN / name, (SOURCE / name).read_bytes())
    selected = []
    for recipe_name in ("large-draft.recipe.json", "small-diagnostic.recipe.json",
                        "negative-old.recipe.json", "control-full-contain.recipe.json"):
        relative = "assets/recipes/" + recipe_name
        write(scratch / relative, (SOURCE / recipe_name).read_bytes())
        selected.append(relative)
    receipt = module.compile_recipes(scratch, selected, resume=True)
    write(REPORT / label / "compiler-receipt.json", encoded(receipt))
    if not receipt["ok"] or receipt["compiled_count"] != 4:
        raise RuntimeError(receipt)
    print(json.dumps({"run": label, "ok": receipt["ok"], "compiled": receipt["compiled_count"]}))


def fit_geometry(source_size, target, fit):
    ratio = (min if fit == "contain" else max)(target[0] / source_size[0], target[1] / source_size[1])
    scaled = [round(v * ratio) for v in source_size]
    offset = ([(target[i] - scaled[i]) // 2 for i in (0, 1)] if fit == "contain"
              else [-((scaled[i] - target[i]) // 2) for i in (0, 1)])
    actual = [scaled[i] / source_size[i] for i in (0, 1)]
    return {"ratio": ratio, "scaled": scaled, "offset": offset, "actual_xy_scale_after_rounding": actual,
            "visible_source_rectangle": [max(0, -offset[0] / actual[0]), max(0, -offset[1] / actual[1]),
                                         min(source_size[0], (target[0] - offset[0]) / actual[0]),
                                         min(source_size[1], (target[1] - offset[1]) / actual[1])]}


def stats(im):
    alpha = im.getchannel("A")
    return {"size": list(im.size), "mode": im.mode, "alpha_bounds": alpha.getbbox(),
            "body_bounds_alpha128": alpha.point(lambda a: 255 if a >= 128 else 0).getbbox(),
            "nonzero_alpha_pixels": sum(a > 0 for a in alpha.tobytes()),
            "alpha_mass": sum(alpha.tobytes()),
            "edge_alpha_mass": sum(im.getpixel((x, y))[3] for y in range(im.height) for x in range(im.width)
                                   if x in (0, im.width - 1) or y in (0, im.height - 1))}


def diagnostic_sheet(outputs):
    sheet = Image.new("RGB", (840, 400), "#272b28")
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 8), "BTA02 UNSELECTED | native-size pixels (1x); nearest enlargements below | no human approval", fill="white")
    cells = [("old 58x64", image(SOURCE / "inputs/selected-large.png")),
             ("ROI candidate", outputs["large.png"]), ("full contain control", outputs["control-full-contain.png"]),
             ("Briar selected", image(SOURCE / "inputs/briarTrickster-large.png")),
             ("Guardian selected", image(SOURCE / "inputs/gladeGuardian-large.png")),
             ("Elder selected", image(SOURCE / "inputs/elderGladeGuardian-large.png"))]
    for i, (label, im) in enumerate(cells):
        x = 12 + i * 137
        draw.text((x, 30), label, fill="white")
        sheet.paste(im, (x + 20, 51), im)
        enlarged = im.resize((116, 128), Image.Resampling.NEAREST)
        sheet.paste(enlarged, (x, 125), enlarged)
    draw.text((12, 268), "32x32: selected small | diagnostic ROI small | selected Briar / Guardian / Elder; adventure frame at right", fill="white")
    smalls = [image(SOURCE / "inputs/selected-small.png"), outputs["diagnostic-small.png"]]
    smalls += [image(SOURCE / f"inputs/{u}-small.png") for u in ("briarTrickster", "gladeGuardian", "elderGladeGuardian")]
    for i, im in enumerate(smalls):
        sheet.paste(im, (25 + i * 137, 294), im)
    adventure = image(SOURCE / "inputs/selected-map.png")
    sheet.paste(adventure, (720, 286), adventure)
    draw.text((12, 365), "Same source identity/material/light/pose; no battle/map/small selection change. Not a native game capture.", fill="white")
    write(REPORT / "native-before-after-family-comparison.png", png(sheet))


def verify(replay):
    module = compiler()
    checks = []

    def check(name, condition, detail=None):
        checks.append({"name": name, "passed": bool(condition), "detail": detail})

    outputs = {}
    hashes = {}
    for name in ("large.png", "diagnostic-small.png", "negative-old-center-cover.png", "control-full-contain.png"):
        a = REPORT / "run-a/runeterra-bandlecity/assets/generated" / PREFIX / name
        b = REPORT / "run-b/runeterra-bandlecity/assets/generated" / PREFIX / name
        check("independent-process-byte-identity:" + name, a.read_bytes() == b.read_bytes())
        outputs[name] = image(a)
        hashes[name] = sha(a.read_bytes())
    check("negative-old-exact-selected-output", (REPORT / "run-a/runeterra-bandlecity/assets/generated" / PREFIX / "negative-old-center-cover.png").read_bytes() == (SOURCE / "inputs/selected-large.png").read_bytes())
    src = image(SOURCE / "inputs/fae-large-source.png")
    framed = image(SOURCE / "portrait-framed-master.png")
    check("lossless-ROI-original-RGBA", framed.crop((4, 4, 38, 41)).tobytes() == src.crop(tuple(ROI)).tobytes())
    check("native-PNG-large-and-diagnostic-canvas", outputs["large.png"].size == (58, 64) and outputs["diagnostic-small.png"].size == (32, 32))
    check("transparent-frame-no-edge-appendage", stats(outputs["large.png"])["edge_alpha_mass"] == 0)
    old_geometry = fit_geometry((52, 37), (58, 64), "cover")
    visible = old_geometry["visible_source_rectangle"]
    old_retained = [p for p in EYE_POINTS if visible[0] <= p[0] + .5 < visible[2]]
    check("negative-cover-removes-eye-core", len(old_retained) < len(EYE_POINTS) and (43, 24) not in old_retained)
    check("candidate-retains-entire-eye-crack-ROI", ROI[0] <= CRACK[0] < CRACK[2] <= ROI[2] and ROI[1] <= CRACK[1] < CRACK[3] <= ROI[3])
    scratch = REPORT / "run-a/runeterra-bandlecity"
    recipe = json.loads((SOURCE / "negative-old.recipe.json").read_text())
    bad = copy.deepcopy(recipe)
    bad["crop"] = [-1, 0, 52, 37]
    try:
        module.raster_bytes(scratch, bad)
        rejected = False
    except module.CompileError as exc:
        rejected = str(exc)
    check("actual-compiler-invalid-ROI-rejected", bool(rejected), rejected)
    bad = copy.deepcopy(recipe)
    bad["source_canvas"] = [53, 37]
    try:
        module.raster_bytes(scratch, bad)
        rejected = False
    except module.CompileError as exc:
        rejected = str(exc)
    check("actual-compiler-invalid-source-camera-rejected", bool(rejected), rejected)
    try:
        module.output_path(PROJECT.parent / "wrong-project", PREFIX + "large.png")
        rejected = False
    except module.CompileError as exc:
        rejected = str(exc)
    check("actual-compiler-wrong-project-root-rejected", bool(rejected), rejected)
    try:
        write(PROJECT / "assets/recipes/SHOULD-NOT-WRITE.json", b"{}")
        rejected = False
    except ValueError as exc:
        rejected = str(exc)
    check("own-writer-active-selection-write-rejected-before-write", bool(rejected), rejected)
    pins = json.loads((SOURCE / "source-pins.json").read_text())
    check("frozen-input-pins", all(sha((PROJECT / p["snapshot"]).read_bytes()) == p["sha256"] for p in pins.values()))
    before = json.loads((REPORT / "protected-before.json").read_text())
    current = protection_inventory() if not replay else None
    changed = [name for name, checksum in before.items() if current.get(name) != checksum] if current is not None else None
    if not replay:
        check("original-sources-recipes-outputs-manifest-stage-byte-unchanged", not changed, {"files": len(before), "changed": changed})
        write(REPORT / "protected-after.json", encoded(current))
    metrics = {
        "status": "authored configuration", "art_status": "built-unreviewed", "selected": False,
        "human_review": "pending", "native_context": "not_run", "redistribution": "unresolved",
        "python": sys.version, "pillow": pillow_version, "eye_rectangle_source": EYE,
        "eye_pixels_source_RGBA": [{"xy": p, "rgba": src.getpixel(p)} for p in EYE_POINTS],
        "eye_core": {"xy": [43, 24], "rgba": src.getpixel((43, 24))},
        "seed_crack_context_rectangle": CRACK, "roi": ROI, "framed_canvas": [42, 46], "paste_xy": [4, 4],
        "old_geometry": old_geometry, "old_eye_pixel_centers_retained": old_retained,
        "candidate_geometry": fit_geometry((42, 46), (58, 64), "cover"),
        "candidate_eye_rectangle_output_continuous": [(EYE[0] - 14) * 58 / 42, (EYE[1] + 4) * 64 / 46,
                                                        (EYE[2] - 14) * 58 / 42, (EYE[3] + 4) * 64 / 46],
        "source_alpha": stats(src), "ROI_alpha": stats(src.crop(tuple(ROI))), "framed_alpha": stats(framed),
        "omitted_source_pixels_nonzero_alpha": stats(src)["nonzero_alpha_pixels"] - stats(src.crop(tuple(ROI)))["nonzero_alpha_pixels"],
        "outputs": {name: {"sha256": hashes[name], **stats(im)} for name, im in outputs.items()},
        "test_count": len(checks), "passed": sum(c["passed"] for c in checks), "checks": checks,
        "replay": replay, "live_protection_checked": not replay,
    }
    write(REPORT / ("replay-verification.json" if replay else "verification.json"), encoded(metrics))
    recipe_path = SOURCE / "large-draft.recipe.json"
    write(REPORT / "candidate-manifest.json", encoded({
        "id": "BTA02-fae-portrait-padded-v2", "entity": "faeTrickster", "role": "large-creature-portrait",
        "technical_state": "built-unreviewed", "selected": False,
        "source": {"path": OWN + "portrait-framed-master.png", "sha256": sha((SOURCE / "portrait-framed-master.png").read_bytes())},
        "recipe": {"path": OWN + "large-draft.recipe.json", "sha256": sha(recipe_path.read_bytes())},
        "output": {"path": "run-a/runeterra-bandlecity/assets/generated/" + PREFIX + "large.png", "sha256": hashes["large.png"]},
        "canvas": [58, 64], "alpha": stats(outputs["large.png"]),
        "provenance": "Own selected Fae seedpod RGBA crop and transparent framing only; no new image generation or original-game pixels",
        "dependencies": "source-pins.json; frozen existing faction_art_compile.py; Python 3.14.7; Pillow 12.3.0",
        "review": {"human": "pending", "native_context": "not_run", "release_accepted": False},
        "rights": "Unresolved upstream generated-art/Riot-derived subject rights; no redistribution approval"
    }))
    diagnostic_sheet(outputs)
    proof = Image.new("RGB", (840, 370), "#242424")
    draw = ImageDraw.Draw(proof)
    draw.text((8, 8), "Measured source eye (43,24) RGBA " + str(src.getpixel((43, 24))) + " | nearest pixels, no brightening", fill="white")
    for i, (label, im, rect) in enumerate([
        ("source crack [40,20,47,29)", src, (39, 19, 49, 30)),
        ("old output right edge", outputs["negative-old-center-cover.png"], (48, 32, 58, 43)),
        ("candidate eye/crack", outputs["large.png"], (33, 30, 48, 47))]):
        x = 12 + i * 275
        draw.text((x, 42), label, fill="white")
        zoom = im.crop(rect).resize(((rect[2] - rect[0]) * 16, (rect[3] - rect[1]) * 16), Image.Resampling.NEAREST)
        proof.paste(zoom, (x, 70), zoom)
    draw.text((8, 350), "Old cover excludes x43/44; candidate retains all original RGBA eye/seed pixels before uniform conversion.", fill="white")
    write(REPORT / "eye-crack-nearest-pixel-proof.png", png(proof))
    if not all(c["passed"] for c in checks):
        raise RuntimeError([c for c in checks if not c["passed"]])
    print(json.dumps({"tests": len(checks), "passed": metrics["passed"], "candidate_sha256": hashes["large.png"],
                      "protected_files": len(before), "replay": replay}, indent=2))


def archive():
    files = [p for p in SOURCE.rglob("*") if p.is_file()]
    files += [SOURCE_ROOT / "replay.py"]
    files += [SOURCE_ROOT / "README.md"]
    files += [REPORT / "compiler-root/scripts/faction_art_compile.py", REPORT / "protected-before.json"]
    files += [p for p in REPORT.glob("*.md") if p.is_file()]
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in sorted(files):
            member = path.relative_to(PROJECT.parent).as_posix()
            info = zipfile.ZipInfo(member, (2026, 10, 22, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(info, path.read_bytes())
    data = stream.getvalue()
    write(REPORT / "portrait-candidate-source.zip", data)
    with zipfile.ZipFile(io.BytesIO(data)) as bundle:
        assert bundle.testzip() is None
        members = {name: sha(bundle.read(name)) for name in bundle.namelist()}
    write(REPORT / "source-archive.json", encoded({"sha256": sha(data), "members": members,
          "status": "editable-unselected-development-source-only", "installable": False,
          "replay": "python -B runeterra-bandlecity/assets/source/creatures/faeTrickster/portrait-eye-review-v1/replay.py --replay"}))
    extracted = REPORT / "archive-replay"
    with zipfile.ZipFile(io.BytesIO(data)) as bundle:
        for name in bundle.namelist():
            destination = extracted / name
            if not destination.resolve().is_relative_to(extracted.resolve()):
                raise ValueError("Archive member escapes replay root")
            write(destination, bundle.read(name))
    helper = extracted / "runeterra-bandlecity/assets/source/creatures/faeTrickster/portrait-eye-review-v1/replay.py"
    subprocess.run([sys.executable, "-B", str(helper), "--replay"], check=True)
    nested_report = extracted / "runeterra-bandlecity/build/reports/five-town-audit-20261022/art-portrait-fix/padded-v2"
    nested = json.loads((nested_report / "replay-verification.json").read_text())
    original = json.loads((REPORT / "verification.json").read_text())
    assert nested["outputs"] == original["outputs"]
    write(REPORT / "archive-replay-result.json", encoded({"ok": True, "archive_sha256": sha(data),
          "zip_crc": "passed", "members": len(members), "replay_tests": nested["test_count"],
          "replay_passed": nested["passed"], "all_four_outputs_equal_original": True,
          "live_inputs_used_by_replay": False}))


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--compile-one", choices=["run-a", "run-b"])
    parser.add_argument("--archive-only", action="store_true")
    args = parser.parse_args()
    if args.compile_one:
        compile_one(args.compile_one)
        return
    if args.archive_only:
        archive()
        return
    if not args.replay:
        prepare()
    recipes()
    for label in ("run-a", "run-b"):
        subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()), "--compile-one", label], check=True)
    verify(args.replay)


if __name__ == "__main__":
    main()
