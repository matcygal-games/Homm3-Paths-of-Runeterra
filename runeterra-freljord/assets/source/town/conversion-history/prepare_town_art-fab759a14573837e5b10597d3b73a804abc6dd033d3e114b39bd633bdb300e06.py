"""Assemble actual painted Freljord buildings without painting or accepting art.

Masters and their prompt/generation records stay immutable. This helper performs
uniform resampling, placement and alpha-derived technical mask/icon assembly.
It never removes painted backgrounds, invents buildings or publishes a stage.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import time

from PIL import Image, ImageChops, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
CANVAS = (800, 374)
ICON_SIZE = (150, 70)
PREFIX = "Content/Sprites/runeterra/freljord/"
GOLD = (225, 190, 80)
STATE = re.compile(r"[A-Za-z][A-Za-z0-9]*\Z")
VERSION = re.compile(r"buildings-v[1-9][0-9]*\Z")


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sha(path):
    return digest(Path(path).read_bytes())


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def relative(root, path):
    path = Path(path).resolve()
    if not path.is_relative_to(Path(root).resolve()):
        raise ValueError("Town art source escaped the Freljord project")
    return path.relative_to(Path(root).resolve()).as_posix()


def safe_source(root, name):
    if not isinstance(name, str) or not name.startswith("assets/source/town/") or "\\" in name:
        raise ValueError("Town source requires its own canonical source path")
    if any(part in ("", ".", "..") or part.endswith((".", " ")) or ":" in part for part in name.split("/")):
        raise ValueError("Unsafe town source path")
    path = (Path(root) / name).resolve()
    relative(root, path)
    return path


def png(image):
    stream = io.BytesIO()
    image.save(stream, format="PNG", compress_level=9, optimize=False)
    return stream.getvalue()


def load_rgba(path):
    with Image.open(path) as opened:
        opened.load()
        if opened.format != "PNG" or opened.mode != "RGBA":
            raise ValueError(f"Real RGBA PNG required: {path}")
        image = opened.copy()
    alpha = image.getchannel("A")
    if alpha.getbbox() is None or alpha.getextrema()[1] < 128:
        raise ValueError(f"Building has no visible opaque silhouette: {path}")
    if alpha.getextrema()[0] >= 128:
        raise ValueError(f"Transparent building required; opaque matte must be corrected with imagegen: {path}")
    return image


def place(image, rect, canvas=CANVAS):
    """Contain full painted alpha footprint, bottom-centred; never erase a halo."""
    x, y, width, height = rect
    if min(x, y) < 0 or min(width, height) <= 0 or x + width > canvas[0] or y + height > canvas[1]:
        raise ValueError("Building placement rectangle leaves the native canvas")
    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError("Cannot place an empty painted master")
    subject = image.crop(bbox)
    scale = min(width / subject.width, height / subject.height)
    size = (max(1, round(subject.width * scale)), max(1, round(subject.height * scale)))
    subject = subject.resize(size, Image.Resampling.LANCZOS)
    native = Image.new("RGBA", canvas)
    position = (x + (width - size[0]) // 2, y + height - size[1])
    native.alpha_composite(subject, position)
    return native, {"alpha_bbox": list(bbox), "source_canvas": list(image.size),
                    "uniform_scale": scale, "upscaled": scale > 1,
                    "placed_size": list(size), "placed_origin": list(position),
                    "rect": list(rect), "canvas": list(canvas),
                    "alpha_treatment": "Preserved painted RGBA, including any soft halo; no threshold erasure/background removal"}


def masks(native):
    silhouette = native.getchannel("A").point(lambda value: 255 if value >= 128 else 0)
    if silhouette.getbbox() is None:
        raise ValueError("Native building has no alpha128 click silhouette")
    area = Image.new("RGBA", native.size, (255, 255, 255, 0))
    area.putalpha(silhouette)
    outline = ImageChops.subtract(silhouette.filter(ImageFilter.MaxFilter(3)), silhouette)
    border = Image.new("RGBA", native.size, GOLD + (0,))
    border.putalpha(outline)
    return area, border


def icon(image):
    # The construction icon contains only this independently painted subject.
    return place(image, [2, 2, ICON_SIZE[0]-4, ICON_SIZE[1]-4], ICON_SIZE)[0]


def generation(root, folder, master, record, conversion):
    prompt_path = folder / "prompt.txt"
    if not prompt_path.is_file() or not prompt_path.read_text(encoding="utf-8").strip():
        raise ValueError(f"Missing exact painted prompt: {prompt_path}")
    prompt = prompt_path.read_text(encoding="utf-8")
    if record.get("prompt") != prompt:
        raise ValueError(f"Prompt record and prompt.txt disagree: {folder}")
    if record.get("tool") != "image_gen.imagegen":
        raise ValueError("Town master requires truthful imagegen generation provenance")
    if record.get("master_sha256") != sha(master):
        raise ValueError("Painted town master changed from its generation record")
    return {"image_generation_used": True, "tool": "image_gen.imagegen",
            "provider": "OpenAI built-in imagegen", "model": record.get("model") or "not exposed by built-in tool",
            "model_id_exposed": False, "prompt": prompt,
            "painted_master": relative(root, master), "painted_master_sha256": sha(master),
            "generation_record": relative(root, folder / "generation.json"),
            "conversion": conversion, "visual_approval_granted": False,
            "references": [{"path": relative(root, path), "sha256": sha(path)}
                           for path in (master, prompt_path, folder / "generation.json")]}


def native_ids(root, names):
    library = Path(root).parent / "vcmi-develop/vcmi-develop/config/buildingsLibrary.json"
    text = library.read_text(encoding="utf-8")
    found = {name: int(index) for name, index in re.findall(r'"(\w+)"\s*:\s*\{\s*"id"\s*:\s*(\d+)', text)}
    missing = set(names) - found.keys()
    if missing:
        raise ValueError(f"Buildings absent from actual native ID library: {sorted(missing)}")
    return {name: found[name] for name in names}


def state_plan(root, state, version="buildings-v1"):
    root = Path(root).resolve()
    if not STATE.fullmatch(state) or not VERSION.fullmatch(version):
        raise ValueError("Unknown or unsafe building/version identifier")
    faction = read(root / "content/factions.json")["freljord"]
    if state not in faction["town"]["buildings"]:
        raise ValueError(f"Unregistered Freljord building state: {state}")
    layout_path = root / "design/building-layout.json"
    layout = read(layout_path)
    sites = [site for site in layout["sites"] if state in site["states"]]
    if len(sites) != 1 or layout.get("canvas") != list(CANVAS):
        raise ValueError("Building state needs one explicit native layout site")
    site = sites[0]
    rect = site["rect"]
    if state == "grail":
        # Its explicitly documented shared plot needs a small ornament, not a
        # second full hall. This is placement, not invented painted geometry.
        rect = [rect[0] + rect[2] - 34, rect[1] + 4, 30, 58]
    folder = safe_source(root, f"assets/source/town/{version}/{state}")
    master, record_path = folder / "master.png", folder / "generation.json"
    if not master.is_file() or not record_path.is_file():
        raise FileNotFoundError(f"Real painted master/provenance missing: {folder}")
    record = read(record_path)
    image = load_rgba(master)
    native, conversion = place(image, rect)
    area, border = masks(native)
    gen = generation(root, folder, master, record, conversion)
    selection = {"master_sha256": sha(master), "layout_sha256": sha(layout_path),
                 "generation_sha256": sha(record_path), "prompt_sha256": sha(folder / "prompt.txt"),
                 "helper_sha256": sha(Path(__file__)), "rect": rect}
    revision = digest(encoded(selection))[:16]
    derived = folder / f"prepared-{revision}"
    sources = {"layer": derived / "layer.png", "area": derived / "area.png",
               "border": derived / "border.png", "icon": derived / "icon.png"}
    files = {sources["layer"]: png(native), sources["area"]: png(area),
             sources["border"]: png(border), sources["icon"]: png(icon(image))}
    credits = {"author":"Project-directed OpenAI built-in imagegen; deterministic technical conversion",
               "license":None,"redistribution":"unresolved; release prohibited"}
    common = {"status":"painted-candidate", "visual_approval_granted":False,
              "production_status":"painted-master-complete-unapproved", "canvas":list(CANVAS),
              "require_alpha":True,"credits":credits,
              "acceptance":"Technical assembly only. Painted alpha/ground, native composition/clicks and rights remain pending.",
              "inputs":[{"path":relative(root,layout_path),"sha256":sha(layout_path)}]}
    descriptor = {"source":relative(root,sources["layer"]), "source_sha256":digest(files[sources["layer"]]),
                  "sha256":digest(files[sources["layer"]]),"source_canvas":list(CANVAS)}
    layer = {**common,"generation":gen,"recipe_type":"vcmi_animation","pivot":{"x":0,"y":0},
             "output_path":f"{PREFIX}town/structures/{state}.json",
             "groups":[{"group":0,"generateShadow":0,"generateOverlay":0,"frames":[descriptor]}]}
    recipes = {root / f"assets/recipes/town/structures/{state}-animation.json":layer}
    for role in ("area","border"):
        path = sources[role]
        mask_gen = {"image_generation_used":False,
                    "method":"alpha128 silhouette" if role == "area" else "One-pixel 8-connected gold outer edge of alpha128 silhouette",
                    "references":[{"path":relative(root,sources["layer"]),"sha256":digest(files[sources["layer"]])}],
                    "painted_source_provenance":gen}
        recipes[root / f"assets/recipes/town/structures/{state}-{role}.json"] = {
            **common,"production_status":"derived-technical-mask-complete","generation":mask_gen,
            "recipe_type":"raster","fit":"exact","source":relative(root,path),
            "source_sha256":digest(files[path]),"source_canvas":list(CANVAS),
            "output_path":f"{PREFIX}town/structures/{state}_{role}.png"}
    receipt = {"state":state,"site":site["id"],"selection":selection,"conversion":conversion,
               "native_alpha128_bbox":list(area.getchannel("A").getbbox()),
               "prepared_icon":relative(root,sources["icon"]),"icon_sha256":digest(files[sources["icon"]]),
               "native_icon_size":list(ICON_SIZE),
               "sources":{relative(root,p):digest(data) for p,data in files.items()},
               "recipes":{relative(root,p):digest(encoded(value)) for p,value in recipes.items()},
               "status":"authored configuration","visual_approval_granted":False,
               "soft_alpha_review":"Pending. Input alpha preserved; this helper does not prove absence of painted halo/ground tile."}
    files[derived / "preparation.json"] = encoded(receipt)
    return files, recipes, receipt


def write_immutable(path, data):
    path = Path(path)
    if path.is_file() and path.read_bytes() != data:
        raise ValueError(f"Prepared source revision already differs; preserve and investigate: {path}")
    if not path.exists():
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(data)


def guard_acceptance(root, recipes):
    manifest = Path(root) / "assets/manifest.json"
    if not manifest.is_file():
        return
    accepted = {entry["output_path"] for entry in read(manifest).get("assets",[]) if entry.get("status") == "accepted"}
    if any(recipe["output_path"] in accepted for recipe in recipes.values()):
        raise ValueError("Accepted town output requires separate explicit review; preserve its source recipe")


def select_recipes(root, recipes):
    guard_acceptance(root,recipes)
    for path,value in recipes.items():
        data = encoded(value)
        if path.is_file() and path.read_bytes() != data:
            old = path.read_bytes()
            history = Path(root) / "assets/source/town/recipe-history" / (digest(old) + ".json")
            write_immutable(history,old)
        path.parent.mkdir(parents=True,exist_ok=True)
        if not path.is_file() or path.read_bytes() != data:
            path.write_bytes(data)


def icon_recipe(root, receipts):
    root = Path(root)
    buildings = read(root / "content/factions.json")["freljord"]["town"]["buildings"]
    by_state = {entry["state"]:entry for entry in receipts}
    if len(by_state) != len(receipts) or set(by_state) != set(buildings):
        raise ValueError("All current native building states need real prepared icons; no filler or borrowed frame is allowed")
    ids = native_ids(root,buildings)
    frames = []
    for state in sorted(buildings,key=ids.get):
        entry = by_state[state]
        source = safe_source(root,entry["prepared_icon"])
        if not source.is_file() or sha(source) != entry["icon_sha256"]:
            raise ValueError(f"Prepared building icon missing/changed: {state}")
        frames.append({"building":state,"frame":ids[state],"source":entry["prepared_icon"],
                       "source_sha256":entry["icon_sha256"],"sha256":entry["icon_sha256"],"source_canvas":list(ICON_SIZE)})
    return {"recipe_type":"indexed_animation","production_status":"painted-master-complete-unapproved",
            "status":"painted-candidate","visual_approval_granted":False,
            "canvas":list(ICON_SIZE),"require_alpha":True,
            "output_path":f"{PREFIX}town/buildingIcons.json","frames":frames,
            "generation":{"image_generation_used":False,
                          "method":"150x70 uniformly contained crops of own independently painted building masters. Exact native sparse building IDs retained; no filled gaps or reference pixels."},
            "credits":{"author":"Project own imagegen masters and deterministic crop assembly", "license":None,
                       "redistribution":"unresolved; release prohibited"},
            "dimensions_basis":{"native_reference":"runeterra-demacia/references/frames/hallcstl/g00-f000.png",
                                "reference_sha256":"d6a9bcb61ecf1ee349ccad7d33d3324a21f09187942c8629c147ca3afd3f5028",
                                "use":"Dimensions only; no licensed reference pixels copied"}}


def composition(root, destination):
    root,destination = Path(root),Path(destination)
    background = root / "assets/source/town/background-v1/native.png"
    if not background.is_file():
        return {"generated":False,"reason":"Own painted background native image missing"}
    with Image.open(background) as opened:
        if opened.size != CANVAS:
            raise ValueError("Own background must already match native town canvas")
        base = opened.convert("RGBA")
    layout = read(root / "design/building-layout.json")
    structures = read(root / "content/factions.json")["freljord"]["town"]["structures"]
    record = {"generated":True,"status":"authored configuration","visual_approval_granted":False,
              "background_sha256":sha(background),"compositions":{}}
    destination.mkdir(parents=True,exist_ok=True)
    for upgraded,label in ((False,"partial-base"),(True,"partial-upgraded")):
        image = base.copy()
        selected,missing = [],[]
        for site in layout["sites"]:
            if not site["land"]:
                continue
            options = [state for state in site["states"] if state != "grail"]
            state = options[-1] if upgraded else options[0]
            recipe_path = root / f"assets/recipes/town/structures/{state}-animation.json"
            if not recipe_path.is_file():
                missing.append(state)
                continue
            recipe = read(recipe_path)
            descriptor = recipe["groups"][0]["frames"][0]
            source = safe_source(root,descriptor["source"])
            if not source.is_file() or sha(source) != descriptor["source_sha256"]:
                raise ValueError(f"Current selected town layer is missing/stale: {state}")
            selected.append((state,source))
        for state,source in sorted(selected,key=lambda pair:structures[pair[0]]["z"]):
            with Image.open(source) as opened:
                if opened.mode != "RGBA" or opened.size != CANVAS:
                    raise ValueError("Current selected native layer geometry changed")
                image.alpha_composite(opened)
        path = destination / (label + ".png")
        write_immutable(path,png(image))
        record["compositions"][label] = {"path":relative(root,path),"sha256":sha(path),
                                             "selected_states":[state for state,_ in selected],"missing_states":missing,
                                             "complete":not missing}
    return record


def prepare(root=ROOT, states=None, version="buildings-v1", *, all_icons=False, previews=True):
    root = Path(root).resolve()
    all_states = read(root / "content/factions.json")["freljord"]["town"]["buildings"]
    requested = sorted(all_states if states is None else states)
    plans,missing = [],[]
    for state in requested:
        try:
            plans.append(state_plan(root,state,version))
        except FileNotFoundError as exc:
            missing.append({"state":state,"reason":str(exc)})
    recipes = {path:value for _,values,_ in plans for path,value in values.items()}
    guard_acceptance(root,recipes)
    for files,_,_ in plans:
        for path,data in files.items():
            if path.is_file() and path.read_bytes() != data:
                raise ValueError(f"Prepared source revision is no longer immutable: {path}")
    for files,_,_ in plans:
        for path,data in files.items():
            write_immutable(path,data)
    select_recipes(root,recipes)
    receipts = [receipt for _,_,receipt in plans]
    icon_status = "not requested"
    if all_icons:
        if missing or set(requested) != set(all_states):
            icon_status = "blocked: all 36 real state masters and icons are required"
        else:
            recipe = icon_recipe(root,receipts)
            select_recipes(root,{root / "assets/recipes/town/buildingIcons.json":recipe})
            icon_status = "authored configuration"
    report_dir = root / ("build/reports/town-art/prepared-" + str(time.time_ns()))
    report = {"status":"authored configuration","version":version,"prepared_states":receipts,
              "missing":missing,"building_icons":icon_status,"visual_approval_granted":False,
              "scope":"Technical resampling and silhouette derivation only; no stage, painting, background removal, native game or art acceptance"}
    if previews:
        report["composition"] = composition(root,report_dir)
    report["ok"] = not missing and not icon_status.startswith("blocked")
    report_dir.mkdir(parents=True,exist_ok=True)
    write_immutable(report_dir / "report.json",encoded(report))
    return report,report_dir / "report.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state",nargs="+",help="Only these exact authored building states")
    parser.add_argument("--version",default="buildings-v1",help="Explicit immutable painted source version")
    parser.add_argument("--icons",action="store_true",help="Require all native building icons and exact sparse ID assembly")
    parser.add_argument("--no-preview",action="store_true")
    args = parser.parse_args()
    try:
        report,path = prepare(states=args.state,version=args.version,all_icons=args.icons,previews=not args.no_preview)
        print(json.dumps({"ok":report["ok"],"prepared":len(report["prepared_states"]),"missing":report["missing"],
                          "building_icons":report["building_icons"],"report":str(path)},indent=2))
        return 0 if report["ok"] else 2
    except (OSError,ValueError,KeyError) as exc:
        print("Town art preparation failed: " + str(exc),file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
