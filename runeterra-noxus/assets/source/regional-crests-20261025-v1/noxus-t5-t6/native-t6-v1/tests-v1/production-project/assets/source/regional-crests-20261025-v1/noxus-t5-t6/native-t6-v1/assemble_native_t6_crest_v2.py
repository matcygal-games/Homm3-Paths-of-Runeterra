"""Technical whole-figure assembly from fresh painted T6 broad-cleaver action sheets.

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
R = W / "build/reports/regional-crests-20261025-v1/noxus-t5-t6-art/assembly-t6"
UNITS = {"minotaurReckoner": 99, "veteranMinotaur": 106}
CAMERA_CONTRACT = N / "camera-contract-t6-v1.json"
CONTRACTS = S / "authored-contracts-v1.json"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pin(path):
    return {"path": path.relative_to(P).as_posix(), "sha256": sha(path.read_bytes())}


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write(path, data):
    assert path.resolve().is_relative_to(N) or path.resolve().is_relative_to(R) or (
        path.resolve().is_relative_to(S / "recipes-t6-v1/crest-v2")) or path == S / "candidate-selection-t6-v1-crest-v2.json"
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
    return json.loads(CAMERA_CONTRACT.read_text(encoding="utf-8"))["calibration_pose_index"][sheet]


def sheet_layout(sheet):
    return tuple(json.loads(CAMERA_CONTRACT.read_text(encoding="utf-8"))["sheet_layouts"][sheet])


def cohort_master(unit, sheet):
    directory = S / unit / sheet
    for name in ("cleanmaster.png", "master.png"):
        if (directory / name).is_file():
            return directory / name
    return directory / "cleanmaster.png"


def cohort_inputs(unit, sheet):
    directory = S / unit / sheet
    return [cohort_master(unit, sheet), directory / "prompt-as-sent.txt", directory / "generation.json"]


def validate_actual_cohort(unit, sheet):
    master, sent_prompt, generation_path = cohort_inputs(unit, sheet)
    generation = json.loads(generation_path.read_text(encoding="utf-8"))
    assert generation["image_generation_used"] is True
    assert generation["model_id_exposed"] is False
    assert generation["old_guided_action_frames_used_as_inputs"] is False
    assert generation["painted_master"] == master.relative_to(P).as_posix()
    assert generation["painted_master_sha256"] == sha(master.read_bytes())
    assert generation["prompt_file"] == pin(sent_prompt)
    assert generation["prompt"].strip() == sent_prompt.read_text(encoding="utf-8").strip()
    with Image.open(master) as image:
        assert image.mode == "RGBA" and not image.info
        assert sha(image.tobytes()) == generation["decoded_rgba_sha256"]


def assemble_sheet(unit, sheet, target_height):
    path = cohort_master(unit, sheet)
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
    registration_path = N / unit / sheet / "registration-t6-v1.json"
    write(registration_path, registration)
    # A finite native-scale contact sheet, not a substitute for action playback.
    cellw = max(112, max(frame.getbbox()[2] - frame.getbbox()[0] for frame in frames) + 18)
    cellh = max(80, max(frame.getbbox()[3] - frame.getbbox()[1] for frame in frames) + 28)
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
    path = cohort_master(unit, "identity-v1")
    image = Image.open(path).convert("RGBA")
    # Explicit independent identity head/shoulder crops, never old guided pixels.
    crop = [160, 0, 1110, 1048]  # Fresh bull head, horns, crest and shoulder; no old portrait pixels.
    results = []
    for role, size in (("large", (58, 64)), ("small", (32, 32))):
        box = crop if role == "large" else [160, 0, 1110, 730]
        selected = image.crop(box)
        ratio = min(size[0] / selected.width, size[1] / selected.height)
        resized = selected.resize((round(selected.width * ratio), round(selected.height * ratio)), Image.Resampling.LANCZOS)
        result = Image.new("RGBA", size, (0, 0, 0, 0))
        result.alpha_composite(resized, ((size[0] - resized.width) // 2, (size[1] - resized.height) // 2))
        destination = N / unit / "portraits/crest-v2" / (role + ".png")
        write(destination, png_bytes(result))
        results.append({"role": role, "source": pin(path), "crop": box, "fit": "uniform contain",
                        "native_canvas": list(size), "native": pin(destination)})
    regpath = N / unit / "portraits/crest-v2/registration-t6-v1.json"
    write(regpath, results)
    return regpath, results


def group_sources(sheet_records):
    general = sheet_records["general-v1"]
    death_name = next(name for name in sheet_records if name.startswith("defend-death"))
    death = sheet_records[death_name]
    groups = {0: general[:6], 1: general[6:10], 2: [general[10]], 3: general[12:16],
              4: death[:4], 5: death[6:12], 7: general[18:22], 8: list(reversed(general[18:22])), 22: [death[11]]}
    for row, group in enumerate((11, 12, 13)):
        groups[group] = sheet_records[next(name for name in sheet_records if name.startswith("melee-"))][row * 6:(row + 1) * 6]
    if any(name.startswith("cleave-") for name in sheet_records):
        for row, group in enumerate((40, 41, 42)):
            groups[group] = sheet_records[next(name for name in sheet_records if name.startswith("cleave-"))][row * 6:(row + 1) * 6]
    return groups


def collect_live_public_lineage(all_inputs):
    """Pin public own-painted artistic ancestors without loading private refs."""
    pending = [path for path in all_inputs if path.name == "generation.json"]
    visited = set()
    while pending:
        generation_path = pending.pop()
        if generation_path in visited:
            continue
        visited.add(generation_path)
        generation = json.loads(generation_path.read_text(encoding="utf-8"))
        def inspect(node):
            if isinstance(node, dict):
                for field in ("public_pixel_equivalent", "input"):
                    equivalent = node.get(field)
                    if not isinstance(equivalent, dict) or "path" not in equivalent:
                        continue
                    name = equivalent["path"]
                    ancestor = (P / name).resolve()
                    if not ancestor.is_relative_to((P / "assets/source").resolve()):
                        raise ValueError("Public painted ancestor outside own source root: " + name)
                    assert sha(ancestor.read_bytes()) == equivalent["sha256"], "Public painted ancestor changed: " + name
                    with Image.open(ancestor) as master:
                        assert master.mode == "RGBA" and not master.info, "Public artistic input must be a clean own RGBA master: " + name
                    all_inputs[ancestor] = equivalent["sha256"]
                    if ancestor.is_relative_to(S.resolve()):
                        unit, cohort = ancestor.parent.parent.name, ancestor.parent.name
                        validate_actual_cohort(unit, cohort)
                        for path in cohort_inputs(unit, cohort):
                            all_inputs[path] = sha(path.read_bytes())
                        pending.append(ancestor.parent / "generation.json")
                    else:
                        # Exact source-owner-declared independent standing input.
                        # Read its public hash/header only; never consume old
                        # guided action pixels or execute a historical producer.
                        assert ancestor.name == "master-original.png" and ancestor.parent.name == "painted-imagegen-v1"
                        assert ancestor.parent.parent.name in UNITS
                for key, value in node.items():
                    if key not in ("public_pixel_equivalent", "input"):
                        inspect(value)
            elif isinstance(node, list):
                for value in node:
                    inspect(value)
        inspect(generation.get("input_references", []))


def main():
    contract = json.loads(CONTRACTS.read_text(encoding="utf-8"))
    camera = json.loads(CAMERA_CONTRACT.read_text(encoding="utf-8"))
    assert camera["battle"]["body_height"] == UNITS
    map_height = camera["adventure"]["body_height"]
    all_units, all_inputs, missing = {}, {CONTRACTS: sha(CONTRACTS.read_bytes()), SELF: sha(SELF.read_bytes()), CAMERA_CONTRACT: sha(CAMERA_CONTRACT.read_bytes())}, []
    for unit, height in UNITS.items():
        sheets = camera["selected_sheets"][unit]
        registered, sheet_records = [], {}
        for sheet in sheets:
            path = cohort_master(unit, sheet)
            required = cohort_inputs(unit, sheet)
            absent = [required_path for required_path in required if not required_path.is_file()]
            if absent:
                missing.extend(required_path.relative_to(P).as_posix() for required_path in absent)
                continue
            if sheet == "auxiliary-v1" and map_height is None:
                missing.append(CAMERA_CONTRACT.relative_to(P).as_posix() + "#adventure/body_height")
                continue
            validate_actual_cohort(unit, sheet)
            for input_path in required:
                all_inputs[input_path] = sha(input_path.read_bytes())
            regpath, records = assemble_sheet(unit, sheet, map_height if sheet == "auxiliary-v1" else height)
            registered.append(regpath)
            sheet_records[sheet] = records
        portrait_records = []
        identity_required = cohort_inputs(unit, "identity-v1")
        identity_absent = [path for path in identity_required if not path.is_file()]
        if identity_absent:
            missing.extend(path.relative_to(P).as_posix() for path in identity_absent)
        else:
            validate_actual_cohort(unit, "identity-v1")
            regpath, portrait_records = portraits(unit)
            registered.append(regpath)
            for path in identity_required:
                all_inputs[path] = sha(path.read_bytes())
        for role, definition in contract["units"][unit].items():
            record = definition["before_recipe"]
            path = P / record["path"]
            assert sha(path.read_bytes()) == record["sha256"]
            all_inputs[path] = record["sha256"]
        all_units[unit] = {"registrations": [pin(path) for path in registered], "sheets": sheet_records,
                           "portraits": portrait_records, "native_body_height": height}
    if missing:
        write(R / ("partial-input-state-" + sha(encoded(missing))[:12] + ".json"), {"status": "authored configuration", "complete": False,
            "missing_fresh_sources": missing, "assembled_sheets": {unit: list(info["sheets"]) for unit, info in all_units.items()},
            "no_complete_recipes_or_selection_written": True})
        print(json.dumps({"complete": False, "missing_fresh_sources": missing}, indent=2))
        return 2
    selected_generation_records = [pin(path) for path in sorted(all_inputs) if path.name == "generation.json"]
    assert len(selected_generation_records) == 11
    collect_live_public_lineage(all_inputs)
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
        "producer": pin(SELF), "authored_contract": pin(CONTRACTS), "camera_contract": pin(CAMERA_CONTRACT), "units": {},
        "actual_generation_records": [pin(path) for path in sorted(all_inputs) if path.name == "generation.json"],
        "selected_generation_records": selected_generation_records,
        "live_standing_identity_inputs": [pin(path) for path in sorted(all_inputs) if path.name == "master-original.png"],
        "public_lineage_ancestors_are_live_inputs": True,
        "clean_metadata_free_masters_only": True,
        "visual_approval_granted": False, "runtime_verified": False, "release_accepted": False}
    for unit, info in all_units.items():
        groups = group_sources(info["sheets"])
        recipes = []
        general_path = cohort_master(unit, "general-v1")
        actual_generation_path = general_path.parent / "generation.json"
        generation = json.loads(actual_generation_path.read_text(encoding="utf-8"))
        assert generation["image_generation_used"] is True and generation["model_id_exposed"] is False
        generation["painted_master"] = general_path.relative_to(P).as_posix()
        generation["painted_master_sha256"] = sha(general_path.read_bytes())
        assert generation["prompt"].strip() == (general_path.parent / "prompt-as-sent.txt").read_text(encoding="utf-8").strip()
        generation["prompt_file"] = pin(general_path.parent / "prompt-as-sent.txt")
        generation["prompt_sha256"] = sha((general_path.parent / "prompt-as-sent.txt").read_bytes())
        if not isinstance(generation.get("model"), str) or not generation["model"].strip():
            generation["model"] = "not exposed by builtin imagegen"
        generation["actual_generation_record"] = pin(actual_generation_path)
        generation["consumed_generation_records"] = [pin(path) for path in sorted(all_inputs) if path.name == "generation.json"]
        generation["native_assembly_producer"] = pin(SELF)
        generation["registrations"] = info["registrations"]
        generation["old_guided_pixels_consumed"] = False
        for role, definition in contract["units"][unit].items():
            recipe = json.loads((P / definition["before_recipe"]["path"]).read_text(encoding="utf-8"))
            for obsolete in ("guide_definition", "painted_cohort_manifest", "focused_action_derivation", "focused_map_derivation", "native_registration", "technical_registration", "registration_evidence", "native_measurement"):
                recipe.pop(obsolete, None)
            recipe.update(generation=generation, production_status="painted-master-complete-unapproved",
                          status="built-unreviewed", visual_approval_granted=False)
            recipe["dependencies"] = [{"path": name, "sha256": checksum} for name, checksum in sorted(dependencies.items())]
            recipe["native_registration"] = {"registrations": info["registrations"], "camera_contract": pin(CAMERA_CONTRACT), "battle_root": [197, 266]}
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
            destination = S / "recipes-t6-v1/crest-v2" / f"{unit}-{role}.json"
            write(destination, recipe)
            recipes.append(pin(destination))
        selection["units"][unit] = {"registrations": info["registrations"], "recipes": recipes,
            "native_body_height": info["native_body_height"], "battle_frame_slots": sum(len(records) for records in groups.values()),
            "map_frame_slots": 6, "group_sources": {str(group): [record["native"] for record in records] for group, records in groups.items()}}
    for path, expected in all_inputs.items():
        assert sha(path.read_bytes()) == expected, "Source changed during assembly: " + str(path)
    write(S / "candidate-selection-t6-v1-crest-v2.json", selection)
    print(json.dumps({"complete": True, "units": {unit: {"battle_frame_slots": info["battle_frame_slots"],
        "map_frame_slots": info["map_frame_slots"]} for unit, info in selection["units"].items()},
        "direct_dependencies_per_recipe": len(dependencies), "selection": pin(S / "candidate-selection-t6-v1-crest-v2.json")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
