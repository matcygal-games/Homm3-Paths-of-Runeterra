"""Technical creature-frame padding crops; never repaint a creature.

Keep every RGBA pixel in the reviewed visible-body rectangle and restore the
unchanged450x400canvas. This removes only distant alpha1..7 gutter noise, which
can otherwise move the native renderer's any-alpha shadow anchor. Originals,
all alpha>=8 pixels and a one-pixel antialias margin remain preserved.
"""
from pathlib import Path

from PIL import Image

from common import PROJECT, sha256


def crop_padding(source: Path, output: Path, project: Path = PROJECT) -> dict:
    project = Path(project).resolve()
    source, output = Path(source).resolve(), Path(output).resolve()
    root = (project / "assets/source/creatures").resolve()
    if not source.is_relative_to(root) or not output.is_relative_to(root):
        raise ValueError("Padding conversion stays inside project creature sources")
    if source.relative_to(root).parts[0] != output.relative_to(root).parts[0] or source == output:
        raise ValueError("Preserve the original and use a new path inside the same unit")
    with Image.open(source) as image:
        image.load()
        if image.mode != "RGBA" or image.size != (450, 400):
            raise ValueError("Padding crop requires an actual450x400RGBA native source frame")
        alpha = image.getchannel("A")
        visible = alpha.point(lambda value: 255 if value >= 8 else 0).getbbox()
        if visible is None:
            raise ValueError("No measurable creature body; do not invent an output")
        box = (max(0, visible[0] - 1), max(0, visible[1] - 1),
               min(450, visible[2] + 1), min(400, visible[3] + 1))
        original_bounds = alpha.getbbox()
        # Exact integer crop/paste, no mask extraction, color edits or resize.
        piece = image.crop(box)
        native = Image.new("RGBA", image.size)
        native.paste(piece, box[:2])
        if native.crop(box).tobytes() != piece.tobytes():
            raise ValueError("Padding conversion altered retained RGBA pixels")
        discarded = alpha.copy()
        discarded.paste(0, box)
        maximum_discarded = discarded.getextrema()[1]
        if maximum_discarded >= 8:
            raise ValueError("Refusing to discard visible creature pixels")
        removed = sum(discarded.histogram()[1:])
        after_bounds = native.getchannel("A").getbbox()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        with Image.open(output) as previous:
            if previous.mode != native.mode or previous.size != native.size or previous.tobytes() != native.tobytes():
                raise ValueError("Preserve previous padding conversion; select another explicit version")
    else:
        native.save(output)
    return {"source": source.relative_to(project).as_posix(), "source_sha256": sha256(source),
            "output": output.relative_to(project).as_posix(), "sha256": sha256(output),
            "native_canvas": [450, 400], "retained_rectangle": list(box),
            "alpha8_bounds": list(visible), "before_any_alpha_bounds": list(original_bounds),
            "after_any_alpha_bounds": list(after_bounds), "removed_nonzero_gutter_pixels": removed,
            "maximum_discarded_alpha": maximum_discarded, "retained_rgba_pixels_identical": True,
            "operation": "Exact visible-body bounding rectangle plus1pixel margin, cropped/pasted on original canvas. All alpha>=8 retained; no pixel edits within rectangle.",
            "visual_approval_granted": False, "active_assets_modified": False}
