"""Rebuild unapproved native town-map candidates from the preserved AI masters.

This is a format/scale production recipe, not an art-acceptance command. It never
writes the global asset manifest, staging mod, original game data, or runtime.
"""
from pathlib import Path
import hashlib
import io
import json
import sys

from PIL import Image, ImageDraw


PROJECT = Path(__file__).resolve().parents[4]
ROOT = Path(__file__).resolve().parent
SPRITES = PROJECT / "assets/source/Sprites/runeterra/demacia/town"
STATES = ("village", "fort", "citadel", "castle", "capitol")
sys.path.insert(0, str(PROJECT / "scripts"))
from owner_overlay import make_overlay


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fit(image, width, height):
    factor = min(width / image.width, height / image.height)
    size = (max(1, round(image.width * factor)), max(1, round(image.height * factor)))
    return image.resize(size, Image.Resampling.LANCZOS)


def cross(icon):
    """Original project-authored red spent-construction mark; no copied pixels."""
    draw = ImageDraw.Draw(icon)
    side = 14 if icon.height > 40 else 11
    x, y = icon.width - side - 1, icon.height - side - 2
    inset = 2
    lines = ((x + inset, y + inset, x + side - inset, y + side - inset),
             (x + side - inset, y + inset, x + inset, y + side - inset))
    for line in lines:
        draw.line(line, fill=(43, 23, 17, 255), width=5)
    for line in lines:
        draw.line(line, fill=(181, 41, 30, 255), width=3)
    for line in lines:
        draw.line((line[0], line[1] - 1, line[2], line[3] - 1), fill=(239, 116, 83, 255), width=1)


def main():
    records = []
    crops = {}
    sources = {}
    background_path = PROJECT / "assets/source/town/background-candidates/terrain-v2-native.png"
    background = Image.open(background_path).convert("RGBA")
    mask_config = json.loads((ROOT / "ownership-mask-v1.json").read_text(encoding="utf-8"))
    for state in STATES:
        master = ROOT / state / "master-v1.png"
        source = Image.open(master).convert("RGBA")
        # The generated masters contain isolated nearly-transparent dust outside
        # the actual silhouette. Use opacity16 only to choose the crop rectangle;
        # preserve all alpha values inside it, rather than binarizing the sprite.
        bounds = source.getchannel("A").point(lambda alpha: 255 if alpha >= 16 else 0).getbbox()
        if bounds is None:
            raise ValueError(f"Empty master: {master}")
        crop = source.crop(bounds)
        crops[state] = crop
        sources[state] = master
        scaled = fit(crop, 178, 150)
        position = (14 + (178 - scaled.width) // 2, 192 - scaled.height)
        native = Image.new("RGBA", (192, 192), (0, 0, 0, 0))
        native.alpha_composite(scaled, position)
        buffer = io.BytesIO()
        native.save(buffer, format="PNG")
        if hashlib.sha256(buffer.getvalue()).hexdigest() != mask_config["frame_sha256"][state]:
            raise ValueError(f"{state}: native frame changed; remeasure its explicit ownership polygons before replacing outputs")
        source_native = ROOT / state / "native-v1.png"
        source_native.parent.mkdir(parents=True, exist_ok=True)
        native.save(source_native)
        output = SPRITES / "map" / f"{state}.png"
        output.parent.mkdir(parents=True, exist_ok=True)
        native.save(output)
        owner_layer, owner_metadata = make_overlay(native, mask_config["polygons"][state], blue_excess=mask_config["blue_excess"])
        owner_output = output.with_name(output.stem + "-OVERLAY.png")
        owner_layer.save(owner_output)
        owner_layer.save(ROOT / state / "ownership-overlay-v1.png")
        animation = SPRITES / "map" / f"{state}.json"
        write_json(animation, {"basepath": "runeterra/demacia/town/map/", "sequences": [{
            "group": 0, "frames": [f"{state}.png"], "generateShadow": 0, "generateOverlay": 0}]})
        records.append({"state": state, "role": "adventure-map town", "status": "generated-unreviewed",
                        "master": str(master.relative_to(PROJECT)).replace("\\", "/"), "master_sha256": digest(master),
                        "crop_alpha_threshold": 16, "crop": list(bounds), "resample": "Pillow LANCZOS",
                        "canvas": [192, 192], "scaled_size": list(scaled.size), "position": list(position),
                        "alpha_bbox": list(native.getbbox()), "output": str(output.relative_to(PROJECT)).replace("\\", "/"),
                        "output_sha256": digest(output), "animation": str(animation.relative_to(PROJECT)).replace("\\", "/"),
                        "animation_sha256": digest(animation), "required_groups": {"0": 1},
                        "owner_overlay": str(owner_output.relative_to(PROJECT)).replace("\\", "/"),
                        "owner_overlay_sha256": digest(owner_output), "owner_mask": owner_metadata})
        write_json(PROJECT / "assets/recipes" / f"adventure-{state}-animation.json", {
            "recipe_type": "vcmi_animation", "output_path": f"Content/Sprites/runeterra/demacia/town/map/{state}.json",
            "canvas": [192, 192], "pivot": {"x": 176, "y": 176,
                "basis": "192px native canvas bottom-right anchor tile center; visible gate alignment remains provisional."},
            "generateShadow": 0, "generateOverlay": 0,
            "groups": [{"group": 0, "frames": [{"source": output.relative_to(PROJECT).as_posix(), "sha256": digest(output),
                "overlay_source": owner_output.relative_to(PROJECT).as_posix(), "overlay_sha256": digest(owner_output)}]}]})
    for state, master_state in (("village", "village"), ("fort", "castle")):
        for size_name, dimensions in (("large", (58, 64)), ("small", (48, 32))):
            width, height = dimensions
            backdrop_crop = (150, 0, 490, 374) if size_name == "large" else (0, 0, 561, 374)
            backdrop = background.crop(backdrop_crop).resize(dimensions, Image.Resampling.LANCZOS)
            subject = fit(crops[master_state], width - 2, height - 3)
            backdrop.alpha_composite(subject, ((width - subject.width) // 2, height - subject.height - 1))
            for built in (False, True):
                icon = backdrop.copy()
                if built:
                    cross(icon)
                variant = "built" if built else "normal"
                output = SPRITES / "icons" / f"{state}_{variant}_{size_name}.png"
                output.parent.mkdir(parents=True, exist_ok=True)
                icon.save(output)
                write_json(PROJECT / "assets/recipes" / f"adventure-icon-{state}-{variant}-{size_name}.json", {
                    "recipe_type": "raster", "output_path": "Content/Sprites/" + output.relative_to(PROJECT / "assets/source/Sprites").as_posix(),
                    "source": output.relative_to(PROJECT).as_posix(), "source_sha256": digest(output),
                    "fit": "stretch", "size": list(dimensions),
                    "pivot": {"x": 0, "y": 0, "basis": "Static town UI icon top-left; reference native dimensions."}})
                records.append({"role": "town interface state icon", "status": "generated-unreviewed",
                                "state": state, "variant": variant, "dimensions": list(dimensions),
                                "subject_master": str(sources[master_state].relative_to(PROJECT)).replace("\\", "/"),
                                "background_master": str(background_path.relative_to(PROJECT)).replace("\\", "/"),
                                "background_sha256": digest(background_path), "background_crop": list(backdrop_crop),
                                "spent_construction_mark": "project-authored red cross" if built else None,
                                "output": str(output.relative_to(PROJECT)).replace("\\", "/"), "output_sha256": digest(output)})
    # Native-size private reference board; original pixels remain in references.
    sheet = Image.new("RGB", (5 * 208, 470), (41, 46, 44))
    draw = ImageDraw.Draw(sheet)
    for index, state in enumerate(STATES):
        draw.text((index * 208 + 8, 8), f"Demacia: {state}", fill=(235, 235, 220))
        sprite = Image.open(ROOT / state / "native-v1.png").convert("RGBA")
        sheet.paste(sprite, (index * 208 + 8, 24), sprite)
    for index, name in enumerate(("avccast0", "avccasx0", "avccasz0")):
        draw.text((index * 208 + 8, 230), f"Original: {name}", fill=(235, 235, 220))
        sprite = Image.open(PROJECT / "references/frames" / name / "g00-f000.png").convert("RGBA")
        sheet.paste(sprite, (index * 208 + 8, 246), sprite)
    for index, state in enumerate(("village", "fort")):
        x = (index + 3) * 208 + 8
        draw.text((x, 230), f"Demacia icons: {state}", fill=(235, 235, 220))
        for built in (False, True):
            variant = "built" if built else "normal"
            for size_name, y in (("large", 255), ("small", 335)):
                icon = Image.open(SPRITES / "icons" / f"{state}_{variant}_{size_name}.png").convert("RGBA")
                sheet.paste(icon, (x + (75 if built else 0), y), icon)
    comparison = PROJECT / "references/demacia-adventure-native-comparison-v1.png"
    sheet.save(comparison)
    write_json(ROOT / "recipe-v1.json", {"version": 1, "status": "generated-unreviewed", "records": records,
                                        "comparison_sheet": str(comparison.relative_to(PROJECT)).replace("\\", "/"),
                                        "accepted": False, "limitations": [
                                            "Architecture is static; group0 frame0 is intentional and is not creature animation scaffolding.",
                                            "The town mask and click/entrance alignment require actual adventure-map rendering and movement checks.",
                                            "Two front cloth panels have explicit grayscale-alpha owner-color sidecars; native runtime rendering is not yet observed.",
                                            "Generated masters contain faint alpha dust; crop geometry ignores opacity below16 but does not flatten retained alpha.",
                                            "Native contrast, angle, scale, terrain contact and all8 state icons still require visual acceptance.",
                                            "No generated output is marked approved and no global asset-manifest entry is changed."]})
    print(json.dumps({"ok": True, "status": "generated-unreviewed", "town_states": 5, "state_icons": 8,
                      "recipe": str(ROOT / "recipe-v1.json"), "comparison_sheet": str(comparison)}))


if __name__ == "__main__":
    main()
