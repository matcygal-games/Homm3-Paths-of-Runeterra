"""Assemble authored full-canvas PNG frames into native VCMI animation JSON.

This performs file assembly only. It neither synthesizes missing poses nor grants
visual acceptance to source images. Every source frame has an explicit checksum.
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import shutil

from common import json_bytes, read_json, sha256, write_json


def within(root: Path, relative: str) -> Path:
    from identity import safe_relative_name
    if not safe_relative_name(relative):
        raise ValueError(f"Invalid relative animation path: {relative!r}")
    result = (root / relative).resolve()
    if not result.is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes production root: {relative}")
    return result


def assemble(project: Path, recipe_path: Path, resume: bool = False, protected_outputs: dict | None = None) -> dict:
    from PIL import Image
    recipe = read_json(recipe_path)
    if recipe.get("recipe_type") != "vcmi_animation":
        raise ValueError(f"Unsupported animation recipe {recipe_path}")
    output_name = recipe["output_path"].replace("\\", "/")
    if not output_name.startswith("Content/Sprites/runeterra/demacia/") or not output_name.endswith(".json"):
        raise ValueError("Animation output must be a namespaced Content/Sprites/runeterra/demacia/...json path")
    output_root = project / "assets/generated"
    output = within(output_root, output_name)
    if not output.is_relative_to((output_root / "Content/Sprites/runeterra/demacia").resolve()):
        raise ValueError("Normalized animation output leaves the Demacia namespace")
    canvas = recipe["canvas"]
    pivot = recipe["pivot"]
    if len(canvas) != 2 or any(type(value) is not int or value <= 0 for value in canvas):
        raise ValueError("Animation canvas must contain two positive integer dimensions")
    if any(type(pivot.get(axis)) is not int for axis in ("x", "y")):
        raise ValueError("Animation pivot must be measured integer x/y metadata")
    sequences, copies, outputs, groups = [], [], [], set()
    if not recipe["groups"]:
        raise ValueError("Animation requires at least one authored group")
    for sequence in recipe["groups"]:
        group = sequence["group"]
        if type(group) is not int or group < 0 or group in groups:
            raise ValueError(f"Duplicate/invalid animation group {group}")
        groups.add(group)
        shadow = sequence.get("generateShadow", recipe.get("generateShadow", 0))
        overlay = sequence.get("generateOverlay", recipe.get("generateOverlay", 0))
        if type(shadow) is not int or shadow not in (0, 1, 2) or type(overlay) is not int or overlay not in (0, 1):
            raise ValueError("Invalid native shadow/overlay generation flags")
        frames = []
        for index, descriptor in enumerate(sequence["frames"]):
            source = within(project, descriptor["source"])
            if not source.is_relative_to((project / "assets/source").resolve()):
                producer_name = descriptor.get("generated_by")
                if not source.is_relative_to((project / "assets/generated").resolve()) or producer_name not in recipe.get("depends_on", []):
                    raise ValueError("Frames outside assets/source require an explicit generated-recipe dependency")
                producer = within(project, producer_name)
                if not producer.is_relative_to((project / "assets/recipes").resolve()):
                    raise ValueError("Generated-frame dependency must be a project asset recipe")
                producer_data = read_json(producer)
                if producer_data.get("output_path") != source.relative_to(project / "assets/generated").as_posix():
                    raise ValueError("Generated-frame producer does not export this frame")
            if source.suffix.lower() != ".png" or not source.is_file():
                raise ValueError(f"Authored PNG frame missing: {source}")
            checksum = sha256(source)
            if descriptor.get("sha256") != checksum:
                raise ValueError(f"Source frame checksum changed: {source}")
            with Image.open(source) as image:
                image.load()
                if list(image.size) != canvas:
                    raise ValueError(f"Frame canvas mismatch: {source}: {image.size} != {canvas}")
                if image.mode != "RGBA":
                    raise ValueError(f"Final frame must provide explicit RGBA alpha: {source}")
            name = f"{output.stem}-frames/g{group:02d}-f{index:03d}.png"
            destination = output.parent / name
            frames.append(name)
            copies.append((source, destination, checksum))
            if "overlay_source" in descriptor or "overlay_sha256" in descriptor:
                if overlay != 0:
                    raise ValueError("Explicit ownership sidecars require generateOverlay=0")
                overlay_source = within(project, descriptor.get("overlay_source", ""))
                if not overlay_source.is_relative_to((project / "assets/source").resolve()):
                    raise ValueError("Ownership overlay source must be under assets/source")
                if overlay_source.suffix.lower() != ".png" or not overlay_source.is_file():
                    raise ValueError(f"Authored ownership overlay PNG missing: {overlay_source}")
                overlay_checksum = sha256(overlay_source)
                if descriptor.get("overlay_sha256") != overlay_checksum:
                    raise ValueError(f"Ownership overlay source checksum changed: {overlay_source}")
                with Image.open(overlay_source) as mask:
                    mask.load()
                    if mask.mode != "RGBA" or list(mask.size) != canvas:
                        raise ValueError("Ownership overlay must be RGBA and match the full frame canvas")
                    if mask.getchannel("A").getbbox() is None:
                        raise ValueError("Ownership overlay is empty")
                sidecar = destination.with_name(destination.stem + "-OVERLAY.png")
                copies.append((overlay_source, sidecar, overlay_checksum))
            elif destination.with_name(destination.stem + "-OVERLAY.png").exists():
                raise ValueError("Undeclared ownership overlay already exists; preserve it and review removal explicitly")
        if not frames:
            raise ValueError(f"Animation group {group} has no authored frames")
        sequences.append({"group": group, "frames": frames,
                          "generateShadow": shadow, "generateOverlay": overlay})
    # Validate all inputs before mutating any output.
    basepath = output.parent.relative_to(output_root / "Content/Sprites").as_posix() + "/"
    definition = {"basepath": basepath, "sequences": sorted(sequences, key=lambda item: item["group"])}
    checksums = {destination.relative_to(output_root).as_posix(): checksum for _, destination, checksum in copies}
    checksums[output_name] = hashlib.sha256(json_bytes(definition)).hexdigest()
    for name, checksum in checksums.items():
        if name in (protected_outputs or {}) and protected_outputs[name] != checksum:
            raise ValueError(f"Recipe would replace accepted output {name}; preserve it and review the changed recipe separately")
    for source, destination, checksum in copies:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not (resume and destination.is_file() and sha256(destination) == checksum):
            shutil.copyfile(source, destination)
        outputs.append({"output_path": destination.relative_to(output_root).as_posix(), "sha256": checksum,
                        "source": source.relative_to(project).as_posix(), "dimensions": canvas})
    write_json(output, definition)
    outputs.append({"output_path": output_name, "sha256": sha256(output),
                    "source": output.relative_to(project).as_posix(), "dimensions": None})
    return {"ok": True, "errors": [], "warnings": ["Assembled authored frames; native visual and in-game acceptance remain pending."],
            "recipe": str(recipe_path), "recipe_sha256": sha256(recipe_path), "outputs": outputs,
            "pivot": pivot, "canvas": canvas, "frame_count": sum(len(item["frames"]) for item in sequences), "visual_approval_granted": False}
