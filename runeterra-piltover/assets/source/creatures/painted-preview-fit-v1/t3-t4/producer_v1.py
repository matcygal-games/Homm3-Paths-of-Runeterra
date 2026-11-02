"""Register genuine whole painted actors into native canvases, without drawing."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageOps

HERE = Path(__file__).resolve().parent
PROJECT = next(path for path in HERE.parents if path.name == "runeterra-piltover")
FIDGET = (0,1,1,2,2,3,3)
UNIT_IDS = ("freightHandler", "armouredHandler", "academyArtificer", "academyArbalist")
GROUPS = {0: ("movement", (4,5,6,7,8,9)), 1: ("movement", FIDGET), 2: ("movement", (0,)),
          3: ("movement", (10,0)), 4: ("movement", (11,)), 5: ("combat", (12,13,14,15)),
          7: ("movement", (0,12,13)), 8: ("movement", (13,12,0)),
          11: ("combat", (0,1,2,3)), 12: ("combat", (4,5,6,7)), 13: ("combat", (8,9,10,11)),
          22: ("combat", (15,))}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return path.relative_to(PROJECT).as_posix()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def render(row, annotation, root, canvas, multiplier=1., mirror=False):
    source = PROJECT / row["image"]
    if sha(source) != row["sha256"] or sha(PROJECT / row["source"]) != row["source_sha256"]:
        raise ValueError("Painted extraction cohort changed: " + row["image"])
    point = annotation["roots"][row["index"]]
    scale = annotation["scale"] * multiplier
    with Image.open(source) as opened:
        actor = opened.convert("RGBA")
    local = (point[0] - row["crop"][0], point[1] - row["crop"][1])
    scaled = (max(1, round(actor.width * scale)), max(1, round(actor.height * scale)))
    actor = actor.resize(scaled, Image.Resampling.LANCZOS)
    offset = (root[0] - round(local[0] * scale), root[1] - round(local[1] * scale))
    if mirror:
        actor = ImageOps.mirror(actor)
        offset = (root[0] - (actor.width - 1 - round(local[0] * scale)), offset[1])
    bounds = actor.getchannel("A").point(lambda value: 255 if value >= 8 else 0).getbbox()
    if bounds is None or not (0 <= offset[0] + bounds[0] < offset[0] + bounds[2] <= canvas[0]
                             and 0 <= offset[1] + bounds[1] < offset[1] + bounds[3] <= canvas[1]):
        raise ValueError("Whole painted actor would clip its native canvas: " + row["image"])
    final = Image.new("RGBA", tuple(canvas), (0,0,0,0))
    final.alpha_composite(actor, offset)
    return final, {"source": row["image"], "source_sha256": row["sha256"], "source_root": point,
                   "cohort_scale": annotation["scale"], "role_scale_multiplier": multiplier,
                   "native_root": list(root), "offset": list(offset), "mirror": mirror}


def build(identifier, roots):
    if identifier not in UNIT_IDS or identifier not in roots["units"]:
        raise ValueError("An explicitly owned low-tier unit identity is required before source access")
    folder = HERE / identifier
    index_path = folder / "isolated-source-map-v1.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))["cohorts"]
    config = roots["units"][identifier]
    ledger_path = HERE / "generation-ledger-v1.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    for cohort in ("movement", "combat"):
        if len(index.get(cohort, [])) != 16 or len(config.get(cohort, {}).get("roots", [])) != 16:
            raise ValueError("Complete genuine source cohort/manual root annotations required: " + identifier + "/" + cohort)
    for cohort, records in index.items():
        if config.get(cohort, {}).get("source") != records[0]["source"] or config[cohort].get("source_sha256") != records[0]["source_sha256"]:
            raise ValueError("Manual anatomical-root annotations are not bound to this exact selected source: " + identifier + "/" + cohort)
    native = HERE / "native" / identifier
    native.mkdir(parents=True, exist_ok=True)
    master, portrait = folder / "master-v1.png", folder / "portrait-v1.png"
    receipts, recipes = [], []
    master_entry = next(row for row in ledger["entries"] if row["source"] == relative(master))
    if master_entry["sha256"] != sha(master):
        raise ValueError("Master generation ledger changed")
    dependencies = [master, portrait, index_path, HERE / "pose-roots-v1.json", Path(__file__), HERE / "extract_sources.py",
                    ledger_path, HERE / "selected-cohorts-v1.json", HERE / "generation-prompts-v1.json"]
    dependencies += sorted({PROJECT / row["source"] for rows in index.values() for row in rows})
    common = {"production_status": "painted-master-complete-unapproved", "generation": {
        "image_generation_used": True, "provider": "OpenAI built-in imagegen", "model": "Not exposed by the tool",
        "prompt": master_entry["generation"]["prompt"],
        "action_source_ledger": relative(ledger_path), "action_source_ledger_sha256": sha(ledger_path),
        "painted_master": relative(master), "painted_master_sha256": sha(master),
        "method": "Whole-source uniform cohort resampling and root registration only; no rigging, rendering, limb warping or invented poses"},
        "production_inputs": [{"path": relative(path), "sha256": sha(path)} for path in dependencies]}
    def descriptor(path, position, size):
        return {"frame": position, "source": relative(path), "sha256": sha(path), "source_sha256": sha(path), "source_canvas": size}
    def save_recipe(role, recipe):
        path = native / (role + ".recipe.json")
        write_json(path, dict(deepcopy(common), **recipe))
        recipes.append(relative(path))
    groups = dict(GROUPS)
    if "shoot" in config:
        if len(index.get("shoot", [])) != 18 or len(config["shoot"].get("roots", [])) != 18:
            raise ValueError("Shooter requires complete genuine directional sources and manual roots")
        groups.update({14:("shoot",tuple(range(6))),15:("shoot",tuple(range(6,12))),16:("shoot",tuple(range(12,18)))})
    frames, registration, measured = [], [], []
    for group, (cohort, order) in sorted(groups.items()):
        sequence = []
        for position, source_index in enumerate(order):
            source_row = index[cohort][source_index]
            pixels, receipt = render(source_row, config[cohort], (197,265), (450,400))
            path = native / "battle" / (f"g{group:02d}-f{position:03d}.png")
            path.parent.mkdir(exist_ok=True)
            pixels.save(path, compress_level=9)
            sequence.append(descriptor(path, position, [450,400]))
            receipt.update(group=group, frame=position, native_frame=relative(path), sha256=sha(path))
            registration.append(receipt)
            if group in (14,15,16) and position == 3:
                tip = config[cohort]["release_tips"][group - 14]
                point = [receipt["offset"][axis] + round((tip[axis] - source_row["crop"][axis]) * config[cohort]["scale"]) for axis in (0,1)]
                measured.append({"direction": ("upper","middle","lower")[group-14], "group": group,
                    "release_frame_zero_based": 3, "native_tip_pixels": point,
                    "source_frame": {"path": relative(PROJECT / source_row["image"]), "sha256": source_row["sha256"]},
                    "native_frame": {"path": relative(path), "sha256": sha(path)}, "original_tip_pixels": tip})
        frames.append({"group": group, "frames": sequence, "generateShadow": 2, "generateOverlay": 0})
    save_recipe("battle", {"recipe_type":"vcmi_animation", "output_path":f"Content/Sprites/runeterra/piltover/creatures/{identifier}/battle.json",
                "canvas":[450,400], "pivot":{"x":197,"y":265}, "groups":frames})
    map_frames = []
    for position, source_index in enumerate(FIDGET):
        pixels, receipt = render(index["movement"][source_index], config["movement"], (80,60), (96,64), config["map_scale_multiplier"], mirror=True)
        bbox = pixels.getchannel("A").point(lambda value:255 if value>=8 else 0).getbbox()
        if bbox[0] < 32:
            raise ValueError("Adventure alpha exceeds its configured right-two-column footprint")
        path = native / "map" / f"g00-f{position:03d}.png"
        path.parent.mkdir(exist_ok=True)
        pixels.save(path, compress_level=9)
        map_frames.append(descriptor(path, position, [96,64]))
    save_recipe("map", {"recipe_type":"vcmi_animation", "output_path":f"Content/Sprites/runeterra/piltover/creatures/{identifier}/map.json",
                "canvas":[96,64], "pivot":{"x":80,"y":60}, "groups":[{"group":0,"frames":map_frames,"generateShadow":2,"generateOverlay":0}]})
    for name, mirrored in (("attackLeft",False),("attackRight",True)):
        pixels, receipt = render(index["combat"][6], config["combat"], (32,60), (64,64), config["encounter_scale_multiplier"], mirror=mirrored)
        path = native / (name + ".png")
        pixels.save(path, compress_level=9)
        save_recipe(name, {"recipe_type":"raster", "output_path":f"Content/Sprites/runeterra/piltover/creatures/{identifier}/{name}.png",
                    "canvas":[64,64], "source":relative(path), "source_sha256":sha(path), "source_canvas":[64,64], "fit":"exact"})
    with Image.open(portrait) as opened:
        pixels = opened.convert("RGBA")
    for name, size in (("large",(58,64)),("small",(32,32))):
        path = native / (name + ".png")
        ImageOps.fit(pixels,size,Image.Resampling.LANCZOS).save(path,compress_level=9)
        save_recipe(name, {"recipe_type":"raster", "output_path":f"Content/Sprites/runeterra/piltover/creatures/{identifier}/{name}.png",
                    "canvas":list(size), "source":relative(path), "source_sha256":sha(path), "source_canvas":list(size), "fit":"exact"})
    write_json(native / "registration.json", {"status":"authored configuration", "unit":identifier,"frames":registration,
                "method":roots["method"], "visual_approval_granted":False,"recipes":recipes})
    if measured:
        write_json(native / "shot-measurements-v1.json", {"units":[{"id":identifier,"source_kind":"painted-native",
              "source_master":{"path":index["shoot"][0]["source"],"sha256":index["shoot"][0]["source_sha256"]},"measurements":measured}]})
        measurement_path = native / "shot-measurements-v1.json"
        write_json(native / "emission-contract-candidate.json", {"id":identifier,"measurement":{"path":relative(measurement_path),"sha256":sha(measurement_path)},
            "release_frame_zero_based":3,"native_points":{row["direction"]:row["native_tip_pixels"] for row in measured},
            "configured_missile":{"attackClimaxFrame":4,"offset":{row["direction"]+axis:row["native_tip_pixels"][number]-(197,265)[number]
                for row in measured for number,axis in enumerate(("X","Y"))}}})
    return {"unit":identifier,"recipes":recipes,"battle_frames":len(registration),"shoot_measurements":len(measured)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unit", nargs="+", choices=UNIT_IDS, required=True)
    args = parser.parse_args()
    roots = json.loads((HERE / "pose-roots-v1.json").read_text(encoding="utf-8"))
    rows = [build(unit, roots) for unit in args.unit]
    print(json.dumps({"status":"authored configuration","units":rows,"visual_approval_granted":False}))


if __name__ == "__main__":
    main()
