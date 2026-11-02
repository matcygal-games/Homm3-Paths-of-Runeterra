"""Assemble sparse native HALL icon frames without inventing missing artwork.

Each frame number is a canonical BuildingID, rather than the icon's position in
this recipe. PNGs remain separately generated resources with verified producers.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re

from animation import within
from common import json_bytes, read_json, sha256


CANVAS = [150, 70]
PREFIX = "Content/Sprites/runeterra/demacia/"
# BuildingIDBase::Type in lib/constants/EntityIdentifiers.h: standard buildings,
# seven creature levels with five upgrades, then the reserved eighth level.
BUILDING_IDS = frozenset(range(72)) | frozenset(range(150, 156))
PIVOT = {"x": 0, "y": 0, "basis": "Native HALL construction icon top-left"}


def _checksum(value, label):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError(f"{label} requires a canonical SHA256 checksum")
    return value


def assemble(project: Path, recipe_path: Path, resume: bool = False, protected_outputs: dict | None = None) -> dict:
    """Write only an indexed JSON animation; never copy or fill icon frames."""
    from PIL import Image
    from raster import convert as verify_raster

    project = Path(project).resolve()
    recipe = read_json(recipe_path)
    if recipe.get("recipe_type") != "indexed_animation":
        raise ValueError("Expected indexed_animation recipe")
    if recipe.get("canvas") != CANVAS:
        raise ValueError("HALL icon animation requires the native150x70 canvas")
    pivot = recipe.get("pivot", PIVOT)
    if not isinstance(pivot, dict) or any(type(pivot.get(axis)) is not int or pivot[axis] != 0 for axis in ("x", "y")):
        raise ValueError("HALL icon pivot must be integer x0,y0")
    output_name = recipe.get("output_path")
    if not isinstance(output_name, str) or not output_name.startswith(PREFIX) or not output_name.endswith(".json"):
        raise ValueError("Indexed animation output must be a private Demacian JSON resource")
    generated_root = (project / "assets/generated").resolve()
    output = within(generated_root, output_name)
    private_root = (generated_root / PREFIX).resolve()
    if not output.is_relative_to(private_root):
        raise ValueError("Indexed animation output leaves the private Demacia namespace")
    descriptors = recipe.get("frames")
    if not isinstance(descriptors, list) or not descriptors:
        raise ValueError("Indexed animation needs explicitly authored frames")
    dependencies = recipe.get("depends_on")
    if not isinstance(dependencies, list) or any(not isinstance(value, str) for value in dependencies):
        raise ValueError("Indexed animation requires explicit producer depends_on entries")
    images, seen, producers, source_hashes = [], set(), {}, {}
    for descriptor in descriptors:
        if not isinstance(descriptor, dict):
            raise ValueError("Indexed frame must be an explicit frame/source descriptor")
        frame = descriptor.get("frame")
        if type(frame) is not int or frame not in BUILDING_IDS or frame in seen:
            raise ValueError(f"Duplicate or noncanonical BuildingID frame: {frame!r}")
        seen.add(frame)
        source = within(project, descriptor.get("source", ""))
        if not source.is_relative_to(private_root) or source.suffix != ".png":
            raise ValueError("HALL icon source must be a generated PNG in the private Demacia namespace")
        source_name = source.relative_to(generated_root).as_posix()
        expected = _checksum(descriptor.get("sha256"), "HALL icon")
        if not source.is_file() or sha256(source) != expected:
            raise ValueError("Generated HALL icon missing or checksum changed")
        if source_name in (protected_outputs or {}) and protected_outputs[source_name] != expected:
            raise ValueError(f"Indexed animation would reference changed accepted output {source_name}")
        with Image.open(source) as image:
            image.load()
            if image.format != "PNG" or image.mode != "RGBA" or list(image.size) != CANVAS:
                raise ValueError("HALL icon must actually be a PNG with RGBA150x70 geometry")
        producer_name = descriptor.get("generated_by")
        producer = within(project, producer_name)
        if not producer.is_relative_to((project / "assets/recipes").resolve()) or producer_name not in dependencies:
            raise ValueError("HALL icon producer requires a project recipe and explicit depends_on entry")
        producer_sha = _checksum(descriptor.get("producer_sha256"), "HALL icon producer")
        if not producer.is_file() or sha256(producer) != producer_sha:
            raise ValueError("HALL icon producer missing or checksum changed")
        production = read_json(producer)
        if production.get("recipe_type") != "raster" or production.get("output_path") != source_name:
            raise ValueError("Declared raster producer does not export this HALL icon")
        if production.get("canvas", production.get("size")) != CANVAS:
            raise ValueError("HALL raster producer must export the native150x70 canvas")
        producers[producer_name] = (producer, producer_sha, source_name, expected)
        source_hashes[source_name] = expected
        images.append({"group": 0, "frame": frame, "file": source_name[len("Content/Sprites/"):]})
    definition = {"basepath": "", "images": sorted(images, key=lambda item: item["frame"])}
    payload = json_bytes(definition)
    checksum = hashlib.sha256(payload).hexdigest()
    if output_name in (protected_outputs or {}) and protected_outputs[output_name] != checksum:
        raise ValueError(f"Indexed animation would replace accepted output {output_name}; review changed frame bindings separately")
    # A forged PNG with an updated descriptor checksum must still match its real
    # producer. Protecting the output makes reproduction fail before any write;
    # the normal case is a no-op that preserves every generated PNG's timestamp.
    for producer_name, (producer, producer_sha, source_name, expected) in sorted(producers.items()):
        verified = verify_raster(project, producer, resume=True, protected_outputs={source_name: expected})
        if (verified.get("canvas") != CANVAS or len(verified["outputs"]) != 1 or
                verified["outputs"][0]["sha256"] != expected):
            raise ValueError(f"HALL icon differs from its declared producer's actual export: {producer_name}")
    output.parent.mkdir(parents=True, exist_ok=True)
    if not (resume and output.is_file() and sha256(output) == checksum):
        output.write_bytes(payload)
    return {"ok": True, "errors": [], "warnings": ["Indexed authored icons assembled; native visual acceptance remains pending."],
            "recipe": str(recipe_path), "recipe_sha256": sha256(recipe_path), "canvas": CANVAS[:], "pivot": pivot,
            "frame_count": len(images), "frame_ids": sorted(seen), "referenced_frame_sha256": source_hashes,
            "producer_sha256": {name: value[1] for name, value in sorted(producers.items())},
            "outputs": [{"output_path": output_name, "source": output.relative_to(project).as_posix(),
                         "sha256": checksum, "dimensions": None}], "visual_approval_granted": False}
