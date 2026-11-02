"""Technical composition of genuine painted terrain; no procedural scene art."""
from pathlib import Path
import hashlib
import json
from PIL import Image

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assemble():
    background = Image.open(HERE / "background-master-v2.png").convert("RGBA")
    background = background.resize((800, 374), Image.Resampling.LANCZOS)
    # The generated local shore supplies genuine new snow and inlet pixels.
    # The eleven-pixel upper offset registers its little inlet to the dock.
    shore = Image.open(HERE / "shore-master.png").convert("RGBA")
    shore = shore.resize((100, 180), Image.Resampling.LANCZOS)
    alpha = Image.new("L", shore.size)
    alpha.putdata([
        round(255 * min(1, x / 10, y / 8, (179-y) / 8))
        for y in range(180) for x in range(100)
    ])
    shore.putalpha(alpha)
    background.alpha_composite(shore, (700, 112))

    # Crop only the empty black letterbox around the imagegen-painted street.
    # Keep the painted snow/road itself; no threshold removes its interior.
    lane = Image.open(HERE / "foreground-path-master.png").convert("RGBA")
    lane = lane.crop((0, 299, 2170, 450))
    lane = lane.resize((800, 56), Image.Resampling.LANCZOS)
    alpha = Image.new("L", lane.size)
    alpha.putdata([round(255 * min(1, y / 18))
                   for y in range(56) for x in range(800)])
    lane.putalpha(alpha)
    background.alpha_composite(lane, (0, 318))
    background.save(HERE / "background-native-v3.png", compress_level=9)

    names = ["background-master-v1.png", "background-master-v2.png",
             "foreground-path-master.png", "shore-master.png",
             "foreground-path-edit-target.png", "shore-edit-target.png",
             "prepaint-plan.json", "prepaint-building-road-plan.png",
             "planned-water.png", "prompt-v1.txt", "prompt-v2.txt",
             "prompt-foreground.txt", "prompt-shore.txt", "assemble.py"]
    record = {
        "status": "authored configuration",
        "tool": "image_gen.imagegen",
        "provider": "OpenAI built-in imagegen",
        "workflow": "Painted2D image generation and local painted image edits",
        "derived_from_blender": False,
        "native_canvas": [800, 374],
        "technical_conversion": [
            "Uniform wide-scene resampling to 800x374",
            "Uniform 100x180 shore-patch resampling and bounded edge composition",
            "Crop generated letterbox and place the painted 800x56 front street with eighteen-pixel edge transition",
            "Opaque RGBA PNG encoding"
        ],
        "source_files": {name: sha(HERE/name) for name in names},
        "output": "background-native-v3.png",
        "output_sha256": sha(HERE / "background-native-v3.png"),
        "art_acceptance": False,
        "native_verified": False,
        "release_accepted": False,
    }
    (HERE / "generation.json").write_text(
        json.dumps(record, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(record["output_sha256"])


if __name__ == "__main__":
    assemble()
