"""Technical whole-figure assembly from fresh painted T5 action sheets.

Only alpha-component isolation, uniform per-sheet scaling, cropping and fixed
root translation are used. No pose synthesis, mirroring or per-frame scaling.
"""
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SELF = Path(__file__).resolve()
W = next(parent for parent in SELF.parents if (parent / "AGENTS.md").is_file())
P = W / "runeterra-noxus"
S = SELF.parent.parent
N = SELF.parent
R = W / "build/reports/regional-crests-20261025-v1/noxus-t5-t6-art/assembly"
UNITS = {"crimsonDisciple": 79, "crimsonAdept": 84}
CONTRACTS = S / "authored-contracts-v1.json"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pin(path):
    return {"path": path.relative_to(P).as_posix(), "sha256": sha(path.read_bytes())}


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write(path, data):
    assert path.resolve().is_relative_to(N) or path.resolve().is_relative_to(R) or (
        path.resolve().is_relative_to(S / "recipes-v1")) or path == S / "candidate-selection-v1.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not isinstance(data, bytes):
        data = encoded(data)
    if path.exists() and path.read_bytes() != data:
        raise ValueError("Version immutable candidate output before changing it: " + str(path))
    path.write_bytes(data)


def png_bytes(image):
    stream = io.BytesIO()
    image.save(stream, format="PNG", compress_level=9, optimize=False)
    return stream.getvalue()


def alpha_components(alpha, threshold=128, minimum=500):
    """Four-connected run-length components, with exact opaque support runs."""
    parents, runs, previous = [], [], []
    def find(label):
        while parents[label] != label:
            parents[label] = parents[parents[label]]
            label = parents[label]
        return label
    def union(left, right):
        parents[find(right)] = find(left)
    for y, row in enumerate(alpha >= threshold):
        edge = np.diff(np.pad(row.astype(np.int8), (1, 1)))
        current = []
        for start, end in zip(np.where(edge == 1)[0], np.where(edge == -1)[0]):
            label = len(parents)
            parents.append(label)
            start, end = int(start), int(end)
            for old_start, old_end, old_label in previous:
                if old_end > start and end > old_start:
                    union(label, old_label)
            current.append((start, end, label))
            runs.append((y, start, end, label))
        previous = current
    grouped = {}
    for y, start, end, label in runs:
        group = grouped.setdefault(find(label), {"pixels": 0, "box": [start, y, end, y + 1], "runs": []})
        group["pixels"] += end - start
        box = group["box"]
        group["box"] = [min(box[0], start), min(box[1], y), max(box[2], end), max(box[3], y + 1)]
        group["runs"].append((y, start, end))
    return [group for group in grouped.values() if group["pixels"] >= minimum]


def ordered_components(image, columns, rows):
    array = np.asarray(image)
    components = alpha_components(array[:, :, 3])
    if len(components) != columns * rows:
        raise ValueError(f"Whole-figure component count {len(components)} != {columns * rows}; merged/missing body requires new painting")
    by_row = [[] for _ in range(rows)]
    for component in components:
        box = component["box"]
        if box[0] <= 1 or box[1] <= 1 or box[2] >= image.width - 1 or box[3] >= image.height - 1:
            raise ValueError("Whole figure intersects canvas boundary: " + str(box))
        row = min(rows - 1, int(((box[1] + box[3]) / 2) / (image.height / rows)))
        by_row[row].append(component)
    if any(len(row) != columns for row in by_row):
        raise ValueError("Whole-figure intended row counts disagree: " + str([len(row) for row in by_row]))
    return [component for row in by_row for component in sorted(row, key=lambda component: component["box"][0])]


def isolate(image, component):
    """Retain component RGB/alpha and four-pixel AA fringe; exclude neighbors."""
    box = component["box"]
    crop_box = [max(0, box[0] - 4), max(0, box[1] - 4), min(image.width, box[2] + 4), min(image.height, box[3] + 4)]
    core = Image.new("L", (crop_box[2] - crop_box[0], crop_box[3] - crop_box[1]), 0)
    draw = ImageDraw.Draw(core)
    for y, start, end in component["runs"]:
        draw.line((start - crop_box[0], y - crop_box[1], end - crop_box[0] - 1, y - crop_box[1]), fill=255)
    support = core.filter(ImageFilter.MaxFilter(9))
    crop = image.crop(crop_box)
    array = np.array(crop)
    keep = np.asarray(support) > 0
    # Other opaque figures must never be captured by a padded rectangular crop.
    local_core = np.asarray(core) > 0
    other_core = (array[:, :, 3] >= 128) & ~local_core
    if np.any(other_core):
        # Separate low-alpha fringes may meet although bodies are independent.
        # Attribute AA to the nearest opaque component, never a grid rectangle.
        own_distance = np.full(local_core.shape, 5, dtype=np.uint8)
        other_distance = np.full(local_core.shape, 5, dtype=np.uint8)
        own_distance[local_core] = 0
        other_distance[other_core] = 0
        growing_own = core
        growing_other = Image.fromarray(other_core.astype(np.uint8) * 255)
        for distance in range(1, 5):
            growing_own = growing_own.filter(ImageFilter.MaxFilter(3))
            growing_other = growing_other.filter(ImageFilter.MaxFilter(3))
            own_distance[(np.asarray(growing_own) > 0) & (own_distance == 5)] = distance
            other_distance[(np.asarray(growing_other) > 0) & (other_distance == 5)] = distance
        keep &= (own_distance < other_distance) | local_core
        support = Image.fromarray(keep.astype(np.uint8) * 255)
    array[~keep] = 0
    array[array[:, :, 3] == 0] = 0  # Hidden gutter RGB is not painted content.
    return Image.fromarray(array), support, crop_box


def support_x(component):
    box = component["box"]
    strips = [(start, end) for y, start, end in component["runs"] if y >= box[3] - max(3, round((box[3] - box[1]) * .04))]
    return (min(start for start, _ in strips) + max(end for _, end in strips) - 1) / 2


def calibrator(sheet):
    return {"general-v1": 10, "melee-v1": 0, "shoot-v1": 0,
            "defend-death-v1": 4, "defend-death-v2": 4, "auxiliary-v1": 0, "cast-v1": 0}[sheet]


def sheet_layout(sheet):
    if sheet == "general-v1":
        return 6, 4
    if sheet.startswith("defend-death"):
        return 6, 2
    if sheet == "shoot-v1":
        return 8, 3
    if sheet == "auxiliary-v1":
        return 4, 2
    return 6, 3


def assemble_sheet(unit, sheet, target_height):
    path = S / unit / sheet / "raw-generated.png"
    image = Image.open(path).convert("RGBA")
    columns, rows = sheet_layout(sheet)
    components = ordered_components(image, columns, rows)
    index = calibrator(sheet)
    control = components[index]
    camera_scale = target_height / (control["box"][3] - control["box"][1])
    control_center = (index % columns + .5) * image.width / columns
    common_x_offset = support_x(control) - control_center
    records = []
    frames = []
    for index, component in enumerate(components):
        crop, mask, crop_box = isolate(image, component)
        # One scalar applies to every pixel of every pose in this entire sheet.
        dimensions = [round(crop.width * camera_scale), round(crop.height * camera_scale)]
        scaled = crop.resize(dimensions, Image.Resampling.LANCZOS)
        is_aux = sheet == "auxiliary-v1"
        canvas = (96, 64) if is_aux and index < 6 else (64, 64) if is_aux else (450, 400)
        root = (64, 60) if is_aux and index < 6 else (32, 60) if is_aux else (197, 266)
        source_root = ((index % columns + .5) * image.width / columns + common_x_offset, component["box"][3] - 1)
        destination = (round(root[0] - (source_root[0] - crop_box[0]) * camera_scale),
                       round(root[1] - (source_root[1] - crop_box[1]) * camera_scale))
        if destination[0] < 0 or destination[1] < 0 or destination[0] + scaled.width > canvas[0] or destination[1] + scaled.height > canvas[1]:
            raise ValueError(f"Complete figure would be cropped by native canvas: {unit}/{sheet}/{index}: {destination}, {scaled.size}, {canvas}")
        output = Image.new("RGBA", canvas, (0, 0, 0, 0))
        output.alpha_composite(scaled, destination)
        outpath = N / unit / sheet / f"pose-{index:03d}.png"
        maskpath = N / unit / sheet / f"pose-{index:03d}-aa-support.png"
        write(outpath, png_bytes(output))
        write(maskpath, png_bytes(mask))
        record = {"index": index, "source": pin(path), "component_core_bbox": component["box"],
            "component_core_pixels": component["pixels"], "extraction_crop": crop_box,
            "aa_support_mask": pin(maskpath), "uniform_sheet_scale": camera_scale,
            "source_root": list(source_root), "native_root": list(root), "native_canvas": list(canvas),
            "destination": list(destination), "scaled_whole_figure_size": dimensions,
            "native": pin(outpath), "native_visible_bbox": list(output.getbbox()),
            "alpha_core_opacity_correction": "none; original alpha retained before uniform resize",
            "no_mirror_stretch_warp_or_pose_generation": True}
        records.append(record)
        frames.append(output)
    registration = {"unit": unit, "sheet": sheet, "source": pin(path), "source_dimensions": list(image.size),
        "columns": columns, "rows": rows, "component_count": len(components), "calibration_pose_index": calibrator(sheet),
        "calibration_height": control["box"][3] - control["box"][1], "target_native_body_height": target_height,
        "uniform_sheet_scale": camera_scale, "common_source_x_root_offset": common_x_offset,
        "root_policy": "One source-cell horizontal camera with idle/guard foot calibration; actual opaque foot/corpse baseline per genuine pose. Whole components cross cell boundaries without clipping.",
        "frames": records}
    registration_path = N / unit / sheet / "registration.json"
    write(registration_path, registration)
    # A finite native-scale contact sheet, not a substitute for action playback.
    cellw, cellh = (112, 80) if sheet == "auxiliary-v1" else (132, 112)
    board = Image.new("RGB", (columns * cellw, rows * cellh), (58, 54, 51))
    draw = ImageDraw.Draw(board)
    for index, frame in enumerate(frames):
        box = frame.getbbox()
        visible = frame.crop(box)
        x = index % columns * cellw + (cellw - visible.width) // 2
        y = index // columns * cellh + cellh - visible.height - 7
        board.paste(visible, (x, y), visible)
        draw.text((index % columns * cellw + 2, index // columns * cellh + 2), str(index), fill="white")
    write(R / unit / (sheet + "-native.png"), png_bytes(board))
    return registration_path, records


def portraits(unit):
    path = S / unit / "identity-v1/raw-generated.png"
    image = Image.open(path).convert("RGBA")
    # Explicit independent identity head/shoulder crops, never old guided pixels.
    crop = [350, 10, 990, 716] if unit == "crimsonDisciple" else [295, 10, 935, 716]
    results = []
    for role, size in (("large", (58, 64)), ("small", (32, 32))):
        box = crop if role == "large" else [crop[0] + 45, 15, crop[2] - 25, 585]
        selected = image.crop(box)
        ratio = min(size[0] / selected.width, size[1] / selected.height)
        resized = selected.resize((round(selected.width * ratio), round(selected.height * ratio)), Image.Resampling.LANCZOS)
        result = Image.new("RGBA", size, (0, 0, 0, 0))
        result.alpha_composite(resized, ((size[0] - resized.width) // 2, (size[1] - resized.height) // 2))
        destination = N / unit / "portraits" / (role + ".png")
        write(destination, png_bytes(result))
        results.append({"role": role, "source": pin(path), "crop": box, "fit": "uniform contain",
                        "native_canvas": list(size), "native": pin(destination)})
    regpath = N / unit / "portraits/registration.json"
    write(regpath, results)
    return regpath, results


def group_sources(sheet_records):
    general = sheet_records["general-v1"]
    death_name = next(name for name in sheet_records if name.startswith("defend-death"))
    death = sheet_records[death_name]
    groups = {0: general[:6], 1: general[6:10], 2: [general[10]], 3: general[12:16],
              4: death[:4], 5: death[6:12], 7: general[18:22], 8: list(reversed(general[18:22])), 22: [death[11]]}
    for row, group in enumerate((11, 12, 13)):
        groups[group] = sheet_records["melee-v1"][row * 6:(row + 1) * 6]
    for row, group in enumerate((14, 15, 16)):
        groups[group] = sheet_records["shoot-v1"][row * 8:(row + 1) * 8]
    if "cast-v1" in sheet_records:
        for row, group in enumerate((30, 31, 32)):
            groups[group] = sheet_records["cast-v1"][row * 6:(row + 1) * 6]
    return groups


def main():
    contract = json.loads(CONTRACTS.read_text(encoding="utf-8"))
    all_units, all_inputs, missing = {}, {CONTRACTS: sha(CONTRACTS.read_bytes()), SELF: sha(SELF.read_bytes())}, []
    for unit, height in UNITS.items():
        sheets = ["general-v1", "melee-v1", "shoot-v1", "defend-death-v2" if unit == "crimsonAdept" else "defend-death-v1", "auxiliary-v1"]
        if unit == "crimsonAdept":
            sheets.append("cast-v1")
        registered, sheet_records = [], {}
        for sheet in sheets:
            path = S / unit / sheet / "raw-generated.png"
            if not path.is_file():
                missing.append(path.relative_to(P).as_posix())
                continue
            for input_path in sorted(path.parent.iterdir()):
                if input_path.is_file():
                    all_inputs[input_path] = sha(input_path.read_bytes())
            regpath, records = assemble_sheet(unit, sheet, 45 if sheet == "auxiliary-v1" else height)
            registered.append(regpath)
            sheet_records[sheet] = records
        regpath, portrait_records = portraits(unit)
        registered.append(regpath)
        for path in sorted((S / unit / "identity-v1").iterdir()):
            if path.is_file():
                all_inputs[path] = sha(path.read_bytes())
        for role, definition in contract["units"][unit].items():
            record = definition["before_recipe"]
            path = P / record["path"]
            assert sha(path.read_bytes()) == record["sha256"]
            all_inputs[path] = record["sha256"]
        all_units[unit] = {"registrations": [pin(path) for path in registered], "sheets": sheet_records,
                           "portraits": portrait_records, "native_body_height": height}
    if missing:
        write(R / "partial-input-state.json", {"status": "authored configuration", "complete": False,
            "missing_fresh_sources": missing, "assembled_sheets": {unit: list(info["sheets"]) for unit, info in all_units.items()},
            "no_complete_recipes_or_selection_written": True})
        print(json.dumps({"complete": False, "missing_fresh_sources": missing}, indent=2))
        return 2
    # Inputs are directly pinned in EVERY selected recipe, including all twelve
    # live consumed templates, not hidden behind a transitive JSON document.
    dependencies = {path.relative_to(P).as_posix(): checksum for path, checksum in all_inputs.items()}
    for info in all_units.values():
        for record in info["registrations"]:
            dependencies[record["path"]] = record["sha256"]
        for records in info["sheets"].values():
            for record in records:
                for key in ("native", "aa_support_mask"):
                    dependencies[record[key]["path"]] = record[key]["sha256"]
        for record in info["portraits"]:
            dependencies[record["native"]["path"]] = record["native"]["sha256"]
    selection = {"status": "authored configuration", "candidate_only": True,
        "fresh_independent_painted_2d_sources": True, "old_guided_pixels_consumed": False,
        "producer": pin(SELF), "authored_contract": pin(CONTRACTS), "units": {},
        "visual_approval_granted": False, "runtime_verified": False, "release_accepted": False}
    for unit, info in all_units.items():
        groups = group_sources(info["sheets"])
        recipes = []
        general_path = S / unit / "general-v1/raw-generated.png"
        generation = {"image_generation_used": True, "provider": "OpenAI built-in imagegen", "model": "not exposed by tool",
            "painted_master": general_path.relative_to(P).as_posix(), "painted_master_sha256": sha(general_path.read_bytes()),
            "prompt": (general_path.parent / "prompt.txt").read_text(encoding="utf-8"),
            "method": "Fresh independent painted identity and genuine action sheets; whole-figure alpha extraction, one uniform camera scalar per sheet and source-foot registration only; no posing/mirroring/stretching.",
            "technical_producer": pin(SELF), "registrations": info["registrations"], "old_guided_pixels_consumed": False}
        for role, definition in contract["units"][unit].items():
            recipe = json.loads((P / definition["before_recipe"]["path"]).read_text(encoding="utf-8"))
            for obsolete in ("guide_definition", "painted_cohort_manifest", "focused_action_derivation", "focused_map_derivation"):
                recipe.pop(obsolete, None)
            recipe.update(generation=generation, production_status="painted-master-complete-unapproved",
                          status="built-unreviewed", visual_approval_granted=False)
            recipe["dependencies"] = [{"path": name, "sha256": checksum} for name, checksum in sorted(dependencies.items())]
            if role == "battle":
                for group in recipe["groups"]:
                    sources = groups[group["group"]]
                    assert len(sources) == len(group["frames"])
                    group["frames"] = [{"source": record["native"]["path"], "source_sha256": record["native"]["sha256"],
                        "sha256": record["native"]["sha256"], "source_canvas": [450, 400]} for record in sources]
            elif role == "map":
                sources = info["sheets"]["auxiliary-v1"][:6]
                recipe["groups"][0]["frames"] = [{"source": record["native"]["path"], "source_sha256": record["native"]["sha256"],
                    "sha256": record["native"]["sha256"], "source_canvas": [96, 64]} for record in sources]
            else:
                record = next(record for record in info["portraits"] if record["role"] == role) if role in ("large", "small") else info["sheets"]["auxiliary-v1"][6 if role == "attackLeft" else 7]
                recipe.update(source=record["native"]["path"], source_sha256=record["native"]["sha256"], source_canvas=record["native_canvas"], fit="exact")
                recipe.pop("crop", None)
                recipe.pop("crop_sha256", None)
            destination = S / "recipes-v1" / f"{unit}-{role}.json"
            write(destination, recipe)
            recipes.append(pin(destination))
        selection["units"][unit] = {"registrations": info["registrations"], "recipes": recipes,
            "native_body_height": info["native_body_height"], "battle_frame_slots": sum(len(records) for records in groups.values()),
            "map_frame_slots": 6, "group_sources": {str(group): [record["native"] for record in records] for group, records in groups.items()}}
    for path, expected in all_inputs.items():
        assert sha(path.read_bytes()) == expected, "Source changed during assembly: " + str(path)
    write(S / "candidate-selection-v1.json", selection)
    print(json.dumps({"complete": True, "units": {unit: {"battle_frame_slots": info["battle_frame_slots"],
        "map_frame_slots": info["map_frame_slots"]} for unit, info in selection["units"].items()},
        "direct_dependencies_per_recipe": len(dependencies), "selection": pin(S / "candidate-selection-v1.json")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
