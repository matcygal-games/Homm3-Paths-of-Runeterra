"""Crop 48 native pieces from one uniformly fitted genuine painted scene."""
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
    prompt = HERE / "actual-tool-prompt-v1.txt"
    faction_path = PROJECT / "content/factions.json"
    pieces = json.loads(faction_path.read_text(encoding="utf-8"))["piltover"]["puzzleMap"]["pieces"]
    if (len(pieces) != 48 or sorted(piece["index"] for piece in pieces) != list(range(1, 49))
            or {(piece["x"], piece["y"]) for piece in pieces} != {(7 + x * 74, 8 + y * 91) for y in range(6) for x in range(8)}):
        raise ValueError("Puzzle must retain all native authored positions and reveal orders")
    with Image.open(master) as source:
        resized = ImageOps.fit(source.convert("RGBA"), (592, 546), method=Image.Resampling.LANCZOS, centering=(.5, .5))
    native = HERE / "native"
    native.mkdir(exist_ok=True)
    resized.save(native / "resized-master.png", compress_level=9)
    recomposed = Image.new("RGBA", resized.size)
    rows = []
    # CTownHandler::loadPuzzle numbers filenames by array order. `index` is
    # reveal order, not the file suffix. Positions use the authored 7,8 origin.
    for number, piece in enumerate(pieces):
        x, y = piece["x"] - 7, piece["y"] - 8
        cropped = resized.crop((x, y, x + 74, y + 91))
        output = native / ("piece" + str(number).zfill(2) + ".png")
        cropped.save(output, compress_level=9)
        recomposed.paste(cropped, (x, y))
        recipe = {"recipe_type": "raster", "production_status": "painted-master-complete-unapproved",
                  "output_path": "Content/Sprites/runeterra/piltover/puzzle/" + output.name,
                  "canvas": [74, 91], "source": output.relative_to(PROJECT).as_posix(), "source_sha256": sha(output),
                  "source_canvas": [74, 91], "fit": "exact",
                  "generation": {"image_generation_used": True, "provider": "OpenAI built-in imagegen",
                      "model": "Not exposed by the tool", "prompt": prompt.read_text(encoding="utf-8"),
                      "painted_master": master.relative_to(PROJECT).as_posix(), "painted_master_sha256": sha(master),
                      "method": "Uniform aspect-preserving fit to592x546, then exact native74x91 crops; no drawing"},
                  "production_inputs": [{"path": path.relative_to(PROJECT).as_posix(), "sha256": sha(path)}
                                        for path in (master, prompt, Path(__file__), faction_path)],
                  "puzzle_placement": {"filename_number": number, "x": piece["x"], "y": piece["y"], "reveal_order": piece["index"]}}
        target = native / (output.stem + ".recipe.json")
        target.write_text(json.dumps(recipe, indent=2) + "\n", encoding="utf-8")
        rows.append({"recipe": target.relative_to(PROJECT).as_posix(), "source_sha256": sha(output)})
    if recomposed.tobytes() != resized.tobytes():
        raise ValueError("All48 puzzle crops fail exact RGBA recomposition")
    print(json.dumps({"status": "authored configuration", "recipes": rows,
                      "recomposition_rgba_equal": True, "resized_rgba_sha256": hashlib.sha256(resized.tobytes()).hexdigest(),
                      "visual_approval_granted": False}))


if __name__ == "__main__":
    main()
