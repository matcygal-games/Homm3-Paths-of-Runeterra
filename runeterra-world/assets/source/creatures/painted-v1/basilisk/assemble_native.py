"""Register complete painted neutral basilisk poses; no drawing, rigging or invented actions."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageOps

HERE = Path(__file__).resolve().parent
PROJECT = next(path for path in HERE.parents if path.name == "runeterra-world")
UNIT_IDS = ("wildBasilisk",)
FIDGET = (0, 1, 1, 2, 2, 3, 3)
GROUPS = {
    0: ("movement", (4, 5, 6, 7, 8, 9)),
    1: ("movement", FIDGET), 2: ("movement", (0,)),
    3: ("movement", (0, 10, 0)), 4: ("movement", (11,)),
    5: ("combat", (12, 13, 14, 15)),
    7: ("movement", (0, 12, 13)),
    8: ("movement", (13, 12, 0)),
    11: ("combat", (0, 1, 2, 3)),
    12: ("combat", (4, 5, 6, 7)),
    13: ("combat", (8, 9, 10, 11)), 22: ("combat", (15,)),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return path.relative_to(PROJECT).as_posix()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def render(row, annotation, root=(220, 266), canvas=(450, 400), multiplier=1., mirror=False):
    """Only uniform whole-pose reduction and translation about annotated anatomy."""
    source = PROJECT / row["image"]
    if sha(source) != row["sha256"] or sha(PROJECT / row["source"]) != row["source_sha256"]:
        raise ValueError("Painted source/extraction changed: " + row["image"])
    if annotation["source"] != row["source"] or annotation["source_sha256"] != row["source_sha256"]:
        raise ValueError("Projected root annotations refer to another source")
    point = annotation["projected_roots"][row["index"]]
    scale = annotation["scale"] * multiplier
    with Image.open(source) as opened:
        actor = opened.convert("RGBA")
    local_root = [point[axis] - row["crop"][axis] for axis in (0, 1)]
    actor = actor.resize((max(1, round(actor.width * scale)), max(1, round(actor.height * scale))), Image.Resampling.LANCZOS)
    offset = [root[axis] - round(local_root[axis] * scale) for axis in (0, 1)]
    if mirror:
        actor = ImageOps.mirror(actor)
        offset[0] = root[0] - (actor.width - 1 - round(local_root[0] * scale))
    bbox = actor.getchannel("A").point(lambda value: 255 if value >= 8 else 0).getbbox()
    if bbox is None or any(offset[a] + bbox[a] < 0 or offset[a] + bbox[a+2] > canvas[a] for a in (0, 1)):
        raise ValueError("Whole actor would clip the native canvas: " + row["image"])
    final = Image.new("RGBA", canvas, (0, 0, 0, 0))
    final.alpha_composite(actor, tuple(offset))
    return final, {"source": row["image"], "source_sha256": row["sha256"], "source_index": row["index"],
                   "source_root": point, "source_crop": row["crop"], "cohort_scale": annotation["scale"],
                   "role_scale_multiplier": multiplier, "native_root": list(root), "offset": offset,
                   "mirror": mirror, "visible_alpha_threshold": 8}


def build(identifier):
    if identifier not in UNIT_IDS:
        raise ValueError("An explicitly owned neutral basilisk identifier is required before writes")
    roots_path, ledger_path = HERE / "pose-roots-v1.json", HERE / "generation-ledger-v1.json"
    roots = json.loads(roots_path.read_text(encoding="utf-8"))
    if roots["native_canvas"] != [450, 400] or roots["native_root"] != [220, 266]:
        raise ValueError("Native projected-root contract changed")
    annotations = roots["units"][identifier]
    index_path = HERE / identifier / "isolated-source-map-v1.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))["cohorts"]
    expected = {"movement": 16, "combat": 16}
    if set(index) != set(expected):
        raise ValueError("Unexpected or missing genuine source cohort")
    for kind, count in expected.items():
        if len(index[kind]) != count or len(annotations[kind]["projected_roots"]) != count:
            raise ValueError("Complete source cohort and explicit roots required: " + kind)
    master, portrait = [HERE / identifier / name for name in ("identity-master-v1.png", "portrait-v1.png")]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    master_entry = next(row for row in ledger["entries"] if row["source"] == relative(master))
    if sha(master) != master_entry["sha256"]:
        raise ValueError("Identity master generation pin changed")
    dependencies = {master, portrait, roots_path, ledger_path, index_path, Path(__file__), HERE / "extract_sources.py"}
    for rows in index.values():
        for row in rows:
            dependencies.update((PROJECT / row["source"], PROJECT / row["image"]))
    selection = HERE / "selected-cohorts-v1.json"
    if selection.exists():
        dependencies.add(selection)
    common = {"production_status": "painted-master-complete-unapproved",
        "generation": {**deepcopy(master_entry["generation"]), "painted_master": relative(master),
            "painted_master_sha256": sha(master), "action_source_ledger": relative(ledger_path),
            "action_source_ledger_sha256": sha(ledger_path),
            "method": "Complete genuine painted pose resampling about explicit projected roots; no per-pose density fitting, drawing, warping or invented animation"},
        "production_inputs": [{"path": relative(path), "sha256": sha(path)} for path in sorted(dependencies)]}
    native = HERE / "native" / identifier
    recipes = PROJECT / "assets/recipes/creatures/basilisk" / identifier
    native.mkdir(parents=True, exist_ok=True)
    registration, recipe_paths = [], []

    def descriptor(path, frame, canvas):
        return {"frame": frame, "source": relative(path), "source_sha256": sha(path), "source_canvas": list(canvas)}

    def save_pixels(path, image):
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path, compress_level=9)

    def save_recipe(role, recipe):
        path = recipes / (role + ".json")
        write_json(path, dict(deepcopy(common), **recipe))
        recipe_paths.append(relative(path))

    groups = dict(GROUPS)
    battle = []
    for group, (kind, order) in sorted(groups.items()):
        frames = []
        for position, source_index in enumerate(order):
            row = index[kind][source_index]
            image, record = render(row, annotations[kind])
            path = native / "battle" / f"g{group:02d}-f{position:03d}.png"
            save_pixels(path, image)
            frames.append(descriptor(path, position, image.size))
            record.update(group=group, frame=position, native_frame=relative(path), sha256=sha(path))
            registration.append(record)
        battle.append({"group": group, "frames": frames, "generateShadow": 2, "generateOverlay": 0})
    prefix = "Content/Sprites/runeterra/world/creatures/" + identifier + "/"
    save_recipe("battle", {"recipe_type": "vcmi_animation", "canvas": [450, 400], "pivot": {"x": 220, "y": 266},
                           "output_path": prefix + "battle.json", "groups": battle})
    map_frames = []
    for frame, source_index in enumerate(FIDGET):
        image, record = render(index["movement"][source_index], annotations["movement"], (72, 56), (96, 64), .5, True)
        if image.getchannel("A").point(lambda v: 255 if v >= 8 else 0).getbbox()[0] < 32:
            raise ValueError("Adventure actor exceeds configured right-two-column mask")
        path = native / "map" / f"g00-f{frame:03d}.png"
        save_pixels(path, image)
        map_frames.append(descriptor(path, frame, image.size))
        registration.append(dict(record, role="map", frame=frame, native_frame=relative(path), sha256=sha(path)))
    save_recipe("map", {"recipe_type": "vcmi_animation", "canvas": [96, 64], "pivot": {"x": 72, "y": 56},
        "output_path": prefix + "map.json", "groups": [{"group": 0, "frames": map_frames, "generateShadow": 2, "generateOverlay": 0}]})
    for role, mirror in (("attackLeft", False), ("attackRight", True)):
        image, record = render(index["movement"][0], annotations["movement"], (40, 56), (64, 64), .5, mirror)
        path = native / (role + ".png")
        save_pixels(path, image)
        registration.append(dict(record, role=role, native_frame=relative(path), sha256=sha(path)))
        save_recipe(role, {"recipe_type": "raster", "canvas": [64, 64], "source": relative(path),
            "source_sha256": sha(path), "source_canvas": [64, 64], "fit": "exact", "output_path": prefix + role + ".png"})
    with Image.open(portrait) as opened:
        image = opened.convert("RGBA")
    for role, size in (("large", (58, 64)), ("small", (32, 32))):
        path = native / (role + ".png")
        save_pixels(path, ImageOps.fit(image, size, Image.Resampling.LANCZOS))
        save_recipe(role, {"recipe_type": "raster", "canvas": list(size), "source": relative(path),
            "source_sha256": sha(path), "source_canvas": list(size), "fit": "exact", "output_path": prefix + role + ".png"})
    write_json(native / "registration.json", {"status": "authored configuration", "id": identifier, "recipes": recipe_paths,
        "frames": registration, "method": roots["method"], "visual_approval_granted": False,
        "shadow": "Native generateShadow2 grounded-body projection; actual native playback/contact review remains pending",
        "turn": "g7 right-to-front then engine facing flip then g8 front-to-new-facing; no double mirror"})
    return recipe_paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unit", nargs="+", choices=UNIT_IDS, default=list(UNIT_IDS))
    args = parser.parse_args()
    recipes = []
    for identifier in args.unit:
        recipes.extend(build(identifier))
    print(json.dumps({"status": "authored configuration", "recipes": recipes, "visual_approval_granted": False}))


if __name__ == "__main__":
    main()
