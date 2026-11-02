"""Derive native town click/highlight masks from a verified building frame.

The silhouette uses the same alpha128 boundary as SDLImageShared::isTransparent.
No rectangle, ellipse, inferred building bounds, or replacement art is generated.
"""
from __future__ import annotations

import hashlib
import io
from pathlib import Path
import re

from animation import within
from common import read_json, sha256


CANVAS = [800, 374]
STRUCTURES = "Content/Sprites/runeterra/demacia/town/structures/"
GOLD = (225, 190, 80, 255)


def _checksum(value, label):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError(f"{label} requires a canonical SHA256 checksum")
    return value


def convert(project: Path, recipe_path: Path, resume: bool = False, protected_outputs: dict | None = None) -> dict:
    """Export two full-canvas RGBA resources without granting art approval."""
    from PIL import Image, ImageChops, ImageFilter
    from raster import convert as verify_raster

    project = Path(project).resolve()
    recipe = read_json(recipe_path)
    if recipe.get("recipe_type") != "town_masks":
        raise ValueError("Expected town_masks recipe")
    if recipe.get("canvas") != CANVAS:
        raise ValueError("Town masks require the actual800x374 native town canvas")
    source = within(project, recipe["source"])
    generated_root = (project / "assets/generated").resolve()
    if not source.is_relative_to(generated_root):
        raise ValueError("Town mask input must be a declared generated building frame")
    input_sha = _checksum(recipe.get("source_sha256"), "Building frame")
    if not source.is_file() or sha256(source) != input_sha:
        raise ValueError("Generated building frame missing or checksum changed")
    producer_name = recipe.get("generated_by")
    producer = within(project, producer_name)
    if not producer.is_relative_to((project / "assets/recipes").resolve()):
        raise ValueError("Building producer must be a declared project asset recipe")
    if not isinstance(recipe.get("depends_on"), list) or producer_name not in recipe["depends_on"]:
        raise ValueError("Building producer requires an explicit depends_on entry")
    producer_sha = _checksum(recipe.get("producer_sha256"), "Building producer")
    if not producer.is_file() or sha256(producer) != producer_sha:
        raise ValueError("Building producer recipe missing or checksum changed")
    production = read_json(producer)
    source_name = source.relative_to(generated_root).as_posix()
    if production.get("recipe_type") != "raster" or production.get("output_path") != source_name:
        raise ValueError("Declared producer does not export this building frame")
    if production.get("canvas") != CANVAS:
        raise ValueError("Building producer must export the native800x374 town canvas")
    if not source_name.startswith(STRUCTURES) or not source_name.endswith("-frame.png"):
        raise ValueError("Building frame must use the canonical Demacia town structure path")
    building = source_name[len(STRUCTURES):-len("-frame.png")]
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", building):
        raise ValueError("Building frame must have a single canonical building identifier")
    destinations = {}
    for role in ("area", "border"):
        name = recipe.get("output_" + role)
        if name != STRUCTURES + building + "_" + role + ".png":
            raise ValueError(f"Town {role} output must match this building's canonical namespaced path")
        destination = within(generated_root, name)
        if not destination.is_relative_to((generated_root / STRUCTURES).resolve()):
            raise ValueError("Town mask output leaves the Demacia structure namespace")
        destinations[role] = (name, destination)
    pivot = production.get("pivot", {})
    if (not isinstance(pivot, dict) or any(type(pivot.get(axis)) is not int for axis in ("x", "y")) or
            not 0 <= pivot["x"] < CANVAS[0] or not 0 <= pivot["y"] < CANVAS[1]):
        raise ValueError("Town frame producer requires a measured native integer pivot")
    if "pivot" in recipe and recipe["pivot"] != pivot:
        raise ValueError("Town masks must preserve the building producer's pivot")
    with Image.open(source) as frame:
        frame.load()
        if frame.mode != "RGBA" or list(frame.size) != CANVAS:
            raise ValueError("Generated building frame must actually be RGBA800x374")
        alpha = frame.getchannel("A")
        silhouette = alpha.point(lambda value: 255 if value >= 128 else 0)
    bounds = silhouette.getbbox()
    if bounds is None:
        raise ValueError("Building frame has no opaque silhouette at alpha128")
    if silhouette.getextrema() == (255, 255):
        raise ValueError("Opaque full-canvas frame is not a transparent building silhouette")
    area = Image.new("RGBA", tuple(CANVAS), (255, 255, 255, 0))
    area.putalpha(silhouette)
    # One pixel outside the opaque silhouette, including transparent arch/yard
    # boundaries. It never fills the building or changes the full frame geometry.
    outline = ImageChops.subtract(silhouette.filter(ImageFilter.MaxFilter(3)), silhouette)
    border = Image.new("RGBA", tuple(CANVAS), GOLD[:3] + (0,))
    border.putalpha(outline)
    payloads = {}
    for role, image in (("area", area), ("border", border)):
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        payload = buffer.getvalue()
        checksum = hashlib.sha256(payload).hexdigest()
        name, destination = destinations[role]
        if name in (protected_outputs or {}) and protected_outputs[name] != checksum:
            raise ValueError(f"Town mask recipe would replace accepted output {name}; review the changed frame separately")
        payloads[role] = (payload, checksum)
    # Reproduce the declared raster producer with its generated output protected
    # by the expected frame hash. Matching output is a no-op under resume=True;
    # a forged/stale frame fails before the producer can mutate anything.
    verified = verify_raster(project, producer, resume=True, protected_outputs={source_name: input_sha})
    if len(verified["outputs"]) != 1 or verified["outputs"][0]["sha256"] != input_sha:
        raise ValueError("Building frame differs from the declared producer's actual export")
    outputs = []
    for role in ("area", "border"):
        name, destination = destinations[role]
        payload, checksum = payloads[role]
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not (resume and destination.is_file() and sha256(destination) == checksum):
            destination.write_bytes(payload)
        outputs.append({"output_path": name, "source": destination.relative_to(project).as_posix(),
                        "sha256": checksum, "dimensions": CANVAS[:], "role": "town-" + role})
    clipped = bounds[0] == 0 or bounds[1] == 0 or bounds[2] == CANVAS[0] or bounds[3] == CANVAS[1]
    return {"ok": True, "recipe": str(recipe_path), "recipe_sha256": sha256(recipe_path),
            "canvas": CANVAS[:], "pivot": pivot, "outputs": outputs, "source_sha256": input_sha,
            "producer_sha256": producer_sha, "alpha_threshold": 128, "silhouette_bbox": list(bounds),
            "border_width": 1, "border_color": list(GOLD), "border_connectivity": 8,
            "outline_clipped_at_canvas_edge": clipped,
            "warnings": ["The building touches a native canvas edge; its outer outline is clipped at that boundary."] if clipped else [],
            "visual_approval_granted": False}
