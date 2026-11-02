"""Split an own painted puzzle cover using actual native placement metadata."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageOps

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", type=Path)
    args = parser.parse_args()
    master = HERE / "master-v2.png"
    if args.provider:
        if master.exists():
            raise SystemExit("Preserve existing master; version replacements")
        with Image.open(args.provider) as opened:
            image = opened.convert("RGBA")
            Image.frombytes("RGBA", image.size, image.tobytes()).save(master)
        save_json(HERE / "generation-v2.json", {
            "provider":"OpenAI built-in imagegen", "model":"Not exposed by tool",
            "provider_file_sha256":sha(args.provider), "master_sha256":sha(master),
            "prompt":"prompt-v2.txt", "prompt_sha256":sha(HERE / "prompt-v2.txt"),
            "visual_acceptance":"pending", "pixel_edit":"RGBA conversion and metadata removal only"
        })
    with Image.open(master) as image:
        native = ImageOps.fit(image.convert("RGBA"), (592,544), method=Image.Resampling.LANCZOS)
    native_path = HERE / "native-cover-v2.png"
    native.save(native_path)
    faction_path = PROJECT / "content/factions.json"
    puzzle = json.loads(faction_path.read_text(encoding="utf-8"))["ixtal"]["puzzleMap"]
    pieces = puzzle["pieces"]
    if len(pieces) != 48 or sorted(p["index"] for p in pieces) != list(range(1,49)):
        raise SystemExit("Exact48 distinct reveal positions required")
    coverage = bytearray(592*544)
    for number, placement in enumerate(pieces):
        x, y = placement["x"]-7, placement["y"]-8
        if x % 74 or y % 91:
            raise SystemExit("Authored puzzle placement changed; revise explicit split plan")
        width, height = min(74,592-x), min(91,544-y)
        if width <= 0 or height <= 0:
            raise SystemExit("Puzzle piece outside native map viewport")
        for row in range(y,y+height):
            for col in range(x,x+width):
                pos = row*592+col
                if coverage[pos]:
                    raise SystemExit("Overlapping puzzle cover pieces")
                coverage[pos] = 1
        source_name = native_path.relative_to(PROJECT).as_posix()
        recipe = {
            "recipe_type":"raster", "production_status":"painted-master-complete-unapproved",
            "output_path":"Content/Sprites/"+puzzle["prefix"]+f"{number:02d}.png",
            "canvas":[width,height], "source":source_name, "source_sha256":sha(native_path),
            "source_canvas":[592,544], "crop":[x,y,x+width,y+height], "fit":"exact",
            "generation":{"image_generation_used":True,"provider":"OpenAI built-in imagegen",
                          "model":"Not exposed by tool","prompt":(HERE/"prompt-v2.txt").read_text(encoding="utf-8").strip(),
                          "painted_master":master.relative_to(PROJECT).as_posix(),"painted_master_sha256":sha(master),
                          "method":"Uniform cover resize and exact rectangular native split; no drawing"},
            "production_inputs":[{"path":path.relative_to(PROJECT).as_posix(),"sha256":sha(path)}
                                 for path in (master,HERE/"prompt-v2.txt",HERE/"generation-v2.json",Path(__file__),faction_path)],
            "credits":{"author":"Runeterra project-directed painted image generation","license":"pending","redistribution":"unresolved"}
        }
        save_json(PROJECT/f"assets/recipes/puzzle/piece{number:02d}.json", recipe)
    if not all(coverage):
        raise SystemExit("Puzzle cover contains gaps")
    save_json(HERE/"native-split-v2.json", {
        "status":"authored configuration","pieces":48,"native_cover":[592,544],
        "covered_pixels":len(coverage),"overlaps":0,"gaps":0,
        "native_picture_offset":"CPuzzleWindow adds +1 to authored x, so authored7 starts at native map x8",
        "native_observation":"not_run","faction_sha256":sha(faction_path),"native_cover_sha256":sha(native_path)
    })
    print(json.dumps({"pieces":48,"coverage_pixels":len(coverage),"master_sha256":sha(master),"native_verified":False}))


if __name__ == "__main__":
    main()
