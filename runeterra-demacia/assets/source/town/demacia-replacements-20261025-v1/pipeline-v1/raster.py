"""Reproduce declared crop/scale/canvas exports from authored master artwork."""
from __future__ import annotations

import hashlib
import io
from pathlib import Path

from animation import within
from common import read_json, sha256


def convert(project: Path, recipe_path: Path, resume: bool = False, protected_outputs: dict | None = None) -> dict:
    from PIL import Image
    recipe = read_json(recipe_path)
    if recipe.get("recipe_type") != "raster":
        raise ValueError("Expected raster recipe")
    source = within(project, recipe["source"])
    if not source.is_relative_to((project / "assets/source").resolve()):
        raise ValueError("Raster master must be under assets/source")
    if not source.is_file() or sha256(source) != recipe["source_sha256"]:
        raise ValueError("Raster source missing or checksum changed")
    name = recipe["output_path"]
    if not name.startswith("Content/Sprites/runeterra/demacia/") or not name.endswith(".png"):
        raise ValueError("Raster output must be a private Demacian PNG resource")
    destination = within(project / "assets/generated", name)
    size = recipe["size"]
    if len(size) != 2 or any(type(v) is not int or v <= 0 for v in size):
        raise ValueError("Raster size needs two positive integers")
    with Image.open(source) as original:
        original.load()
        if recipe.get("require_alpha") and (original.mode != "RGBA" or original.getextrema()[3][0] == 255):
            raise ValueError("Transparent export requires real source alpha; no background removal is inferred")
        picture = original.convert("RGBA")
    if "crop" in recipe:
        box = recipe["crop"]
        if (len(box) != 4 or any(type(v) is not int for v in box) or
                not (0 <= box[0] < box[2] <= picture.width and 0 <= box[1] < box[3] <= picture.height)):
            raise ValueError("Crop must be explicitly within the authored master")
        picture = picture.crop(tuple(box))
    box = recipe.get("content_box", [0, 0, *size])
    if (len(box) != 4 or any(type(v) is not int or v < 0 for v in box) or
            not box[2] or not box[3] or box[0] + box[2] > size[0] or box[1] + box[3] > size[1]):
        raise ValueError("Content box must fit the native output (x,y,width,height)")
    render_size = box[2:]
    fit = recipe.get("fit", "stretch")
    if fit == "contain":
        picture.thumbnail(tuple(render_size), Image.Resampling.LANCZOS)
    elif fit == "stretch":
        if abs(picture.width / picture.height - render_size[0] / render_size[1]) > 0.01:
            raise ValueError("Stretch would distort aspect ratio; declare a crop or contain fit")
        picture = picture.resize(tuple(render_size), Image.Resampling.LANCZOS)
    else:
        raise ValueError(f"Unknown raster fit: {fit}")
    if "background" in recipe:
        background = recipe["background"]
        background_path = within(project, background["source"])
        if not background_path.is_relative_to((project / "assets/source").resolve()):
            raise ValueError("Background must be an authored master under assets/source")
        if not background_path.is_file() or sha256(background_path) != background["sha256"]:
            raise ValueError("Authored background missing or checksum changed")
        with Image.open(background_path) as image:
            layer = image.convert("RGBA").resize(tuple(size), Image.Resampling.LANCZOS)
    else:
        layer = Image.new("RGBA", tuple(size))
    y = box[1] + ((box[3] - picture.height) // 2 if "content_box" in recipe else box[3] - picture.height)
    layer.alpha_composite(picture, (box[0] + (box[2] - picture.width) // 2, y))
    picture = layer
    if "canvas" in recipe:
        canvas, position = recipe["canvas"], recipe["position"]
        if (len(canvas) != 2 or len(position) != 2 or
                any(type(v) is not int or v < 0 for v in [*canvas, *position]) or
                not all(canvas) or position[0] + picture.width > canvas[0] or position[1] + picture.height > canvas[1]):
            raise ValueError("Raster placement leaves declared native canvas")
        layer = Image.new("RGBA", tuple(canvas))
        layer.alpha_composite(picture, tuple(position))
        picture = layer
    buffer = io.BytesIO()
    picture.save(buffer, format="PNG")
    payload = buffer.getvalue()
    checksum = hashlib.sha256(payload).hexdigest()
    if name in (protected_outputs or {}) and protected_outputs[name] != checksum:
        raise ValueError("Raster recipe would replace accepted artwork; review the changed source separately")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not (resume and destination.is_file() and sha256(destination) == checksum):
        destination.write_bytes(payload)
    return {"ok": True, "recipe": str(recipe_path), "recipe_sha256": sha256(recipe_path),
            "canvas": list(picture.size), "pivot": recipe.get("pivot", {"x": None, "y": None, "basis": "not applicable to static UI/terrain"}),
            "outputs": [{"output_path": name, "source": destination.relative_to(project).as_posix(),
                         "sha256": checksum, "dimensions": list(picture.size)}],
            "visual_approval_granted": False}
