"""Uniform crops of the actual painted recruitment scene; no artwork drawing."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageOps

HERE = Path(__file__).resolve().parent
PROJECT = next(path for path in HERE.parents if path.name == "runeterra-piltover")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    master = HERE / "master-v1.png"
    prompt = HERE / "piltover_recruit_background_v1-actual-prompt.txt"
    with Image.open(master) as source:
        original = source.convert("RGBA")
    native = HERE / "native"
    native.mkdir(exist_ok=True)
    rows = []
    for height in (120, 130):
        output = native / ("creatureBackground" + str(height) + ".png")
        ImageOps.fit(original, (100, height), method=Image.Resampling.LANCZOS, centering=(.5, .5)).save(output, compress_level=9)
        recipe = {"recipe_type": "raster", "production_status": "painted-master-complete-unapproved",
                  "output_path": "Content/Sprites/runeterra/piltover/ui/" + output.name,
                  "canvas": [100, height], "source": output.relative_to(PROJECT).as_posix(),
                  "source_sha256": sha(output), "source_canvas": [100, height], "fit": "exact",
                  "generation": {"image_generation_used": True, "provider": "OpenAI built-in imagegen",
                      "model": "Not exposed by the tool", "prompt": prompt.read_text(encoding="utf-8"),
                      "painted_master": master.relative_to(PROJECT).as_posix(), "painted_master_sha256": sha(master),
                      "method": "Uniform aspect-preserving centered cover crop of actual painted 2D master; no drawing"},
                  "production_inputs": [{"path": path.relative_to(PROJECT).as_posix(), "sha256": sha(path)}
                                        for path in (master, prompt, Path(__file__))]}
        target = native / (output.stem + ".recipe.json")
        target.write_text(json.dumps(recipe, indent=2) + "\n", encoding="utf-8")
        rows.append({"recipe": target.relative_to(PROJECT).as_posix(), "source_sha256": sha(output)})
    print(json.dumps({"status": "authored configuration", "recipes": rows, "visual_approval_granted": False}))


if __name__ == "__main__":
    main()
