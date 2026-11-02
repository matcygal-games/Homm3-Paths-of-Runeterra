"""Native static map conversion of real painted regional sites; no artwork drawing."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
SITES = ("ionianSpiritWillow", "bandlePortalGrove", "shurimanCaravanserai", "bilgewaterSmugglersCove")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True)+"\n",encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("site", choices=SITES)
    parser.add_argument("--provider", type=Path)
    args = parser.parse_args()
    folder = HERE / args.site
    folder.mkdir(parents=True, exist_ok=True)
    version = "v2" if args.site == "ionianSpiritWillow" else "v1"
    master = folder / f"master-{version}.png"
    prompt = folder / f"prompt-{version}.txt"
    if args.provider:
        if master.exists():
            raise SystemExit("Preserve painted master; version any replacement")
        with Image.open(args.provider) as opened:
            image = opened.convert("RGBA")
            Image.frombytes("RGBA",image.size,image.tobytes()).save(master)
        save_json(folder/f"generation-{version}.json",{
            "provider":"OpenAI built-in imagegen","model":"Not exposed by tool",
            "provider_file_sha256":sha(args.provider),"master_sha256":sha(master),
            "prompt":prompt.name,"prompt_sha256":sha(prompt),
            "pixel_edit":"RGBA conversion and metadata removal only","visual_acceptance":"pending",
            "reference_scope":"Original H3 native map controls inspected for scale/style; official lore subjects inform original artwork, no copied card pixels"
        })
    with Image.open(master) as opened:
        image = opened.convert("RGBA")
    box = image.getchannel("A").point(lambda alpha:255 if alpha>=8 else 0).getbbox()
    if box is None or box[0]<=0 or box[1]<=0 or box[2]>=image.width or box[3]>=image.height:
        raise SystemExit("Painted whole silhouette missing or cut at provider image boundary")
    sprite=image.crop(box)
    sprite.thumbnail((88,88),Image.Resampling.LANCZOS)
    position=((96-sprite.width)//2,94-sprite.height)
    native=Image.new("RGBA",(96,96))
    native.alpha_composite(sprite,position)
    native_path=folder/f"native-{version}.png"
    native.save(native_path)
    source=native_path.relative_to(PROJECT).as_posix()
    generation={"image_generation_used":True,"provider":"OpenAI built-in imagegen","model":"Not exposed by tool",
                "prompt":prompt.read_text(encoding="utf-8").strip(),"painted_master":master.relative_to(PROJECT).as_posix(),
                "painted_master_sha256":sha(master),"method":"Whole alpha crop, uniform reduction, fixed96x96mapcanvas; no drawing"}
    recipe={"recipe_type":"vcmi_animation","production_status":"painted-master-complete-unapproved",
            "output_path":f"Content/Sprites/runeterra/world/sites/{args.site}/map.json",
            "canvas":[96,96],"pivot":{"x":48,"y":94},"generation":generation,
            "groups":[{"group":0,"generateShadow":1,"generateOverlay":0,"frames":[{
                "frame":0,"source":source,"source_sha256":sha(native_path),"sha256":sha(native_path),"source_canvas":[96,96]}]}],
            "production_inputs":[{"path":path.relative_to(PROJECT).as_posix(),"sha256":sha(path)}
                                 for path in (master,prompt,folder/f"generation-{version}.json",Path(__file__))],
            "credits":{"author":"Runeterra project-directed painted image generation","license":"pending","redistribution":"unresolved"}}
    save_json(PROJECT/f"assets/recipes/sites/{args.site}.json",recipe)
    save_json(folder/f"calibration-{version}.json",{
        "source_box":list(box),"source_canvas":list(image.size),"native_canvas":[96,96],"native_position":list(position),
        "native_size":list(sprite.size),"native_frame_sha256":sha(native_path),
        "template_mask":["VVV","BBV","BAV"],"visitable_offset":[1,0],
        "footing":"Bottomcenter land approach is within active lower-middle32px tile; actual scene observation remains pending",
        "shadow_policy":"Native generateShadow1 projection; own material/contact shading preserved. No arbitrary or empty-SHADOW substitute. Native shadow appearance/doubling remains unobserved.",
        "native_execution":"not_run","visual_acceptance":"pending"})
    print(json.dumps({"site":args.site,"master_sha256":sha(master),"native_size":list(sprite.size),"recipe":1,"status":"authored configuration"}))


if __name__ == "__main__":
    main()
