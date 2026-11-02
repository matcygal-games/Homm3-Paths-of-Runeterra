"""Convert real painted projectile masters into five native angles; no drawing."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
ANGLES = (90, 45, 0, -45, -90)
PAIRS = {"quill": ("bristlehog", "thornbackBristlehog"), "stone": ("stoneshaper", "axiomStoneshaper")}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=PAIRS)
    parser.add_argument("--provider", type=Path)
    args = parser.parse_args()
    folder = HERE / args.kind
    folder.mkdir(parents=True, exist_ok=True)
    master = folder / "master-v1.png"
    prompt = folder / "prompt-v1.txt"
    if args.provider:
        if master.exists():
            raise SystemExit("Version existing painted cohorts instead of overwriting")
        with Image.open(args.provider) as opened:
            opened.load()
            image = opened.convert("RGBA")
            Image.frombytes("RGBA", image.size, image.tobytes()).save(master)
        save_json(folder / "generation-v1.json", {
            "provider": "OpenAI built-in imagegen", "model": "Not exposed by tool",
            "provider_file_sha256": sha(args.provider), "master_sha256": sha(master),
            "prompt": "prompt-v1.txt", "prompt_sha256": sha(prompt),
            "pixel_edit": "RGBA conversion and metadata removal only", "visual_acceptance": "pending"
        })
    with Image.open(master) as opened:
        image = opened.convert("RGBA")
    alpha = image.getchannel("A")
    box = alpha.point(lambda a: 255 if a >= 8 else 0).getbbox()
    if box is None:
        raise SystemExit("No actual projectile pixels")
    sprite = image.crop(box)
    limit = (28, 8) if args.kind == "quill" else (16, 12)
    sprite.thumbnail(limit, Image.Resampling.LANCZOS)
    frames = []
    for index, angle in enumerate(ANGLES):
        rotated = sprite.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
        target = Image.new("RGBA", (32, 32))
        target.alpha_composite(rotated, ((32-rotated.width)//2, (32-rotated.height)//2))
        name = folder / f"g00-f{index:03d}.png"
        target.save(name)
        checksum = sha(name)
        frames.append({"frame": index, "source": name.relative_to(PROJECT).as_posix(),
                       "source_sha256": checksum, "sha256": checksum, "source_canvas": [32,32]})
    inputs = [{"path": path.relative_to(PROJECT).as_posix(), "sha256": sha(path)}
              for path in (master, prompt, folder / "generation-v1.json", Path(__file__))]
    for unit in PAIRS[args.kind]:
        recipe = {
            "recipe_type": "vcmi_animation", "production_status": "painted-master-complete-unapproved",
            "output_path": f"Content/Sprites/runeterra/ixtal/projectiles/{unit}.json",
            "canvas": [32,32], "pivot": {"x":16,"y":16}, "groups": [{"group":0, "frames":frames, "generateShadow":0, "generateOverlay":0}],
            "generation": {"image_generation_used":True, "provider":"OpenAI built-in imagegen",
                           "model":"Not exposed by tool", "prompt":prompt.read_text(encoding="utf-8").strip(),
                           "painted_master": master.relative_to(PROJECT).as_posix(),
                           "painted_master_sha256":sha(master),
                           "method":"Complete alpha crop, uniform native reduction and native angle rotations; no drawing"},
            "production_inputs": inputs,
            "painted_projectile_crop": {"source":master.relative_to(PROJECT).as_posix(), "source_sha256":sha(master), "crop":list(box)},
            "credits":{"author":"Runeterra project-directed painted image generation", "license":"pending", "redistribution":"unresolved"}
        }
        save_json(PROJECT / f"assets/recipes/projectiles/{unit}.json", recipe)
    print(json.dumps({"kind":args.kind,"master_sha256":sha(master),"actual_crop":list(box),"angles":ANGLES,"status":"authored configuration","native_trajectory":"not_run"}))


if __name__ == "__main__":
    main()
