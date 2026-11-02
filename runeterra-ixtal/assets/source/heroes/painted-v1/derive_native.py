"""Replay fixed technical crops of actual painted sources; never generates art."""
from pathlib import Path
import argparse
import hashlib
import json
from PIL import Image, ImageOps

BASE = Path(__file__).resolve().parent
PROJECT = BASE.parents[3]
IDS = ("qiyana", "nidalee", "neeko", "milio", "skarner", "malphite", "zyra", "inessa", "mara", "lupe", "lune", "aliayQunlan", "mivasim", "chiuqeslan", "bayal")
# Separate native horizontal portrait framing; no anatomy/face repainting.
SMALL_Y = {"qiyana": .13, "nidalee": .18, "neeko": .16, "milio": .16,
           "skarner": .27, "malphite": .26, "zyra": .17}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def dump(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def replay(portraits_only=False):
    outputs = []
    for key in IDS:
        folder = BASE / key
        kinds = [("portrait", "master.png", "generation-request.json", (("large",(58,64)),("small",(48,32))))]
        if not portraits_only:
            kinds.append(("specialty", "specialty-master.png", "specialty-generation-request.json", (("specialtyLarge",(44,44)),("specialtySmall",(32,32)))))
        for kind, filename, request_name, roles in kinds:
            master = folder / filename
            request = json.loads((folder / request_name).read_text(encoding="utf-8"))
            with Image.open(master) as opened:
                opened.load()
                image = opened.convert("RGBA")
            request["status"] = "painted-master-complete-unapproved"
            request["master_sha256"] = sha(master)
            request["master_dimensions"] = list(image.size)
            dump(folder / request_name, request)
            for role, size in roles:
                crop = None
                if role == "small":
                    height = min(image.height, round(image.width / 1.5))
                    top = min(round(image.height * SMALL_Y.get(key, .16)), image.height - height)
                    crop = (0, top, image.width, top + height)
                    native = image.crop(crop).resize(size, Image.Resampling.LANCZOS)
                else:
                    native = ImageOps.fit(image, size, Image.Resampling.LANCZOS, centering=(.5,.5))
                target = folder / (role + ".png")
                native.save(target)
                source = target.relative_to(PROJECT).as_posix()
                generation = {"image_generation_used":True, "provider":request["provider"], "model":"not exposed",
                              "prompt":request["prompt"], "painted_master":master.relative_to(PROJECT).as_posix(),
                              "painted_master_sha256":sha(master), "master_canvas":list(image.size),
                              "derivation":"Fixed original painted source face crop and LANCZOS resize" if crop else "Fixed centered original painted source crop and LANCZOS resize",
                              "small_source_crop":list(crop) if crop else None,
                              "producer":"assets/source/heroes/painted-v1/derive_native.py"}
                recipe = {"recipe_type":"raster", "production_status":"painted-master-complete-unapproved",
                          "canvas":list(size), "output_path":f"Content/Sprites/runeterra/ixtal/heroes/{key}/{role}.png",
                          "source":source, "source_sha256":sha(target), "source_canvas":list(size), "fit":"exact",
                          "generation":generation}
                dump(folder / (role + ".recipe.json"), recipe)
                outputs.append({"id":key, "kind":kind, "role":role, "path":source, "sha256":sha(target),
                                "canvas":list(size), "mode":"RGBA", "master":generation["painted_master"],
                                "master_sha256":generation["painted_master_sha256"], "recipe":(folder / (role+".recipe.json")).relative_to(PROJECT).as_posix()})
    result = {"status":"painted-master-complete-unapproved", "faction":"runeterra-ixtal:ixtal", "outputs":outputs,
              "verification_boundary":"Actual imagegen-painted masters and deterministic technical crops. No final art, runtime, rights or release acceptance."}
    dump(BASE / ("portrait-output-index.json" if portraits_only else "native-output-index.json"), result)
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--portraits-only", action="store_true")
    args = parser.parse_args()
    print("Replayed", len(replay(args.portraits_only)["outputs"]), "own native painted hero candidate surfaces.")
