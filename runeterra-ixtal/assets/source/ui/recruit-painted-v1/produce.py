"""Lossless metadata cleanup and deterministic native resizing of real painted art.

This script draws no artwork. Supply the actual provider PNG explicitly once.
Subsequent runs read the preserved clean RGBA master.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
WORKSPACE = PROJECT.parent
sys.path.insert(0, str(WORKSPACE / "scripts"))
import faction_art_compile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", type=Path)
    args = parser.parse_args()
    master = HERE / "master-v1.png"
    if args.provider:
        if master.exists():
            raise SystemExit("Preserved master exists; use a versioned cohort for replacement")
        with Image.open(args.provider) as opened:
            opened.load()
            clean = opened.convert("RGBA")
            # Fresh image object deliberately drops ancillary provider metadata.
            Image.frombytes("RGBA", clean.size, clean.tobytes()).save(master)
            write_json(HERE / "generation-v1.json", {
                "provider": "OpenAI built-in imagegen", "model": "Not exposed by tool",
                "provider_file_sha256": sha(args.provider), "master_sha256": sha(master),
                "dimensions": list(clean.size), "pixel_edit": "None; RGBA conversion and metadata removal only",
                "prompt": "prompt-v1.txt", "prompt_sha256": sha(HERE / "prompt-v1.txt"),
                "visual_acceptance": "pending", "redistribution": "pending"
            })
    with Image.open(master) as image:
        source_size = list(image.size)
    cohort = HERE.relative_to(PROJECT).as_posix()
    for height in (120, 130):
        recipe = {
            "recipe_type": "raster", "production_status": "painted-master-complete-unapproved",
            "output_path": f"Content/Sprites/runeterra/ixtal/ui/creatureBackground{height}.png",
            "canvas": [100, height], "source": cohort + "/master-v1.png",
            "source_sha256": sha(master), "source_canvas": source_size, "fit": "cover",
            "generation": {"image_generation_used": True, "provider": "OpenAI built-in imagegen",
                           "model": "Not exposed by tool", "prompt": (HERE / "prompt-v1.txt").read_text(encoding="utf-8").strip(),
                           "painted_master": cohort + "/master-v1.png", "method": "Uniform centered cover crop; no artwork drawing"},
            "production_inputs": [{"path": cohort + "/" + filename, "sha256": sha(HERE / filename)}
                                  for filename in ("prompt-v1.txt", "generation-v1.json", "produce.py")]
        }
        write_json(PROJECT / f"assets/recipes/ui/creatureBackground{height}.json", recipe)
        output, _ = faction_art_compile.raster_bytes(PROJECT, recipe)
        preview = HERE / f"native-{height}.png"
        preview.write_bytes(output)
    print(json.dumps({"master_sha256": sha(master), "recipes": 2, "native_previews": [120,130], "status": "authored configuration"}))


if __name__ == "__main__":
    main()
