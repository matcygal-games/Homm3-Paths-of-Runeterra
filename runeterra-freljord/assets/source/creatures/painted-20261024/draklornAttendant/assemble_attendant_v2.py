"""Own painted-source placement; actual shared strict plan, report-only output.

No artwork synthesis, per-pose fitting, alpha threshold, active recipes, manifest,
staging or native execution. All visible poses come from retained imagegen PNGs.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
from PIL import Image, ImageDraw

SOURCE = Path(__file__).resolve().parent
PROJECT = next(p for p in SOURCE.parents if p.name == "runeterra-freljord")
REPORT = PROJECT / "build/reports/painted-draklorn-attendant-20261024-v1"
sys.path.insert(0, str(PROJECT.parent / "scripts"))
import faction_art_compile

ROOT = [780, 930]
BATTLE_ROOT = [193, 266]
BATTLE_SCALE = .108
MAP_ROOT = [48, 60]
MAP_SCALE = .034
ATTACK_SCALE = .026
PORTRAIT_CROP = [400, 0, 1250, 980]
POSES = {"standing": "standing-v1", **{name: name + "-v1" for name in (
    "walk-contact-a", "walk-down-a", "walk-pass-a", "walk-contact-b", "walk-down-b", "walk-pass-b",
    "fidget", "hit", "defend", "death-kneel", "death-fall", "death-rest", "turn-front", "turn-back",
    "melee-prepare", "melee-up", "melee-front", "melee-down")}}
POSES.update({name:name+"-v2" for name in ("death-kneel","death-fall","death-rest")})
# Explicit manual anatomical ground-contact annotations, authorized by root.
# Same .108 scale/camera in every frame; translations never derive from alpha
# bounds, and no individual figure is resized. Source masters remain untouched.
GROUND_REGISTRATION = {
    "death-kneel":{"source_contact_point":[1080,908],"source_shift":[0,22],"landmark":"Planted front boot sole beside grounded knee; target floor930"},
    "death-fall":{"source_contact_point":[945,798],"source_shift":[0,132],"landmark":"Supporting near forearm/glove where body contacts ground; target floor930"},
    "death-rest":{"source_contact_point":[910,800],"source_shift":[0,130],"landmark":"Resting near glove/lower robe contact plane; target floor930"},
}
REQUIRED = {"0": 6, "1": 2, "2": 1, "3": 2, "4": 1, "5": 3, "7": 1, "8": 1, "11": 2, "12": 2, "13": 2}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded(value))


def descriptor(path):
    with Image.open(path) as im:
        canvas = list(im.size)
    return {"source": path.relative_to(PROJECT).as_posix(), "source_sha256": sha(path), "source_canvas": canvas}


def place(image, size, scale, root, source_shift=(0,0)):
    work = image.transform(tuple(s * 4 for s in size), Image.Transform.AFFINE,
        (1/(scale*4), 0, ROOT[0]-root[0]/scale-source_shift[0], 0, 1/(scale*4), ROOT[1]-root[1]/scale-source_shift[1]),
        resample=Image.Resampling.BICUBIC, fillcolor=(0,0,0,0))
    return work.resize(size, Image.Resampling.LANCZOS)


def border(image):
    a=image.getchannel("A")
    return max(a.crop(b).getextrema()[1] for b in ((0,0,image.width,1), (0,image.height-1,image.width,image.height),
        (0,0,1,image.height), (image.width-1,0,image.width,image.height)))


def groups():
    result={0:["walk-contact-a","walk-down-a","walk-pass-a","walk-contact-b","walk-down-b","walk-pass-b"],
            1:["standing"]*2+["fidget"]*4+["standing"]*2,
            2:["standing"], 3:["hit","hit","standing"], 4:["defend"],
            5:["death-kneel","death-fall","death-rest"], 7:["turn-front"], 8:["turn-back"]}
    for g, direction in ((11,"up"),(12,"front"),(13,"down")):
        result[g]=["standing","melee-prepare","melee-"+direction,"melee-"+direction,"melee-prepare","standing"]
    return result


def review_sheets(out, natives):
    rows=[]
    for group,names in groups().items():
        for start in range(0,len(names),6):
            rows.append((group,start,names[start:start+6]))
    for facing in ("right","left"):
        for scale in (1,2):
            tile=(265*scale,165*scale)
            sheet=Image.new("RGB",(tile[0]*6,tile[1]*len(rows)),(62,61,58))
            draw=ImageDraw.Draw(sheet)
            for row,(group,start,names) in enumerate(rows):
                for col,name in enumerate(names):
                    if name not in natives:
                        continue
                    native=natives[name]
                    if facing=="left":
                        native=native.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                    crop=native.crop((90,120,355,285))
                    if scale!=1:
                        crop=crop.resize(tile,Image.Resampling.NEAREST)
                    point=(col*tile[0],row*tile[1])
                    sheet.paste(crop,point,crop.getchannel("A"))
                    draw.text((point[0]+3,point[1]+3),f"g{group} f{start+col} {name}",fill="white")
            sheet.save(out/f"all-actions-{facing}-{scale}x.png")
    board=Image.new("RGB",(1060,165*((len(natives)+3)//4)),(62,61,58))
    draw=ImageDraw.Draw(board)
    for index,(name,native) in enumerate(natives.items()):
        point=((index%4)*265,(index//4)*165)
        crop=native.crop((90,120,355,285))
        board.paste(crop,point,crop.getchannel("A"))
        draw.text((point[0]+3,point[1]+3),name,fill="white")
    board.save(out/"unique-poses-native-1x.png")


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--preview",action="store_true")
    args=parser.parse_args()
    pins={path:sha(path) for path in (PROJECT/"assets/manifest.json",PROJECT/"content/creatures.json",
                                    Path(__file__),Path(faction_art_compile.__file__))}
    missing=[stem for stem in POSES.values() if not (SOURCE/(stem+".png")).is_file()]
    if missing and not args.preview:
        raise RuntimeError("Incomplete real-source packet; no recipes or compile: "+str(missing))
    out=REPORT/(("preview-" if args.preview else "conversion-")+str(time.time_ns()))
    out.mkdir(parents=True)
    native_dir=SOURCE/"native-v2"
    native_dir.mkdir(exist_ok=True)
    natives,paths,lineage={},{},[]
    for pose,stem in POSES.items():
        source=SOURCE/(stem+".png")
        if not source.is_file():
            continue
        with Image.open(source) as opened:
            if opened.mode!="RGBA" or not (1516<=opened.width<=1556 and 1004<=opened.height<=1044):
                raise RuntimeError("Unexpected master mode/canvas; never fit body: "+str(source))
            master=opened.copy()
        if border(master)>=128 and not args.preview:
            raise RuntimeError("Substantial source-edge alpha; inspect/repair clipping: "+str(source))
        registration=GROUND_REGISTRATION.get(pose,{"source_shift":[0,0],"landmark":"Unchanged source ground registration"})
        native=place(master,(450,400),BATTLE_SCALE,BATTLE_ROOT,registration["source_shift"])
        destination=native_dir/(stem+".png")
        native.save(destination,compress_level=9)
        natives[pose],paths[pose]=native,destination
        lineage.append({"pose":pose,"master":descriptor(source),"native":descriptor(destination),
                        "manual_ground_registration":registration,
                        "source_border_alpha_max":border(master),"native_border_alpha_max":border(native),
                        "native_alpha_bounds":native.getchannel("A").getbbox()})
    review_sheets(out,natives)
    requests=[]
    for path in sorted((SOURCE/"requests").glob("*.json")):
        req=json.loads(path.read_text(encoding="utf-8"))
        requests.append({"request":path.relative_to(PROJECT).as_posix(),"request_sha256":sha(path),
                         "reference_sha256":{ref:sha(PROJECT/ref) for ref in req["referenced_image_paths"]}})
    ledger=SOURCE/("generation-ledger-"+out.name+".json")
    save(ledger,{"status":"authored configuration","provider":"OpenAI built-in imagegen","model":"not exposed by tool",
                 "requests":requests,"selected_sources":lineage,"no_3d_inputs":True,"visual_approval_granted":False})
    result={"status":"authored configuration","preview_only":args.preview,"missing":missing,"source_lineage":lineage,
            "source_root":ROOT,"battle_root":BATTLE_ROOT,"battle_scale":BATTLE_SCALE,"native_canvas":[450,400],
            "group_counts":{str(g):len(names) for g,names in groups().items()},"required_groups":REQUIRED,
            "holding":"one static group2 frame; no continuous moving idle",
            "fidget_timing":"group1 MOUSEON uses10fps;8frames=.8s, with genuine equipment-check pose held briefly",
            "melee_timing":"native currentFrame*2>=count;6frame groups hold actualcontact atindex3",
            "per_pose_opaque_body_fit":False,"alpha_threshold":False,"runtime_verified":False,
            "manual_ground_registration":GROUND_REGISTRATION,
            "anatomy_concern":"Fall/rest human anatomy remains visibly longer than upright human; manual ground translations cure placement only, not proportions. Native artistic review pending.",
            "visual_approval_granted":False,"release_accepted":False,"strict_compiler_receipts":[],"output_sha256":{}}
    if not args.preview:
        resources=SOURCE/"resources-v1"
        resources.mkdir(exist_ok=True)
        with Image.open(SOURCE/"standing-v1.png") as im:
            standing=im.copy()
        map_image=place(standing,(64,64),MAP_SCALE,MAP_ROOT)
        map_image.save(resources/"map-000.png",compress_level=9)
        # Dedicated fixed icon scale uses a genuine physical up-strike; this
        # keeps its complete blade in64px and retains native anchor48,60.
        with Image.open(SOURCE/(POSES["melee-up"]+".png")) as im:
            attack=place(im,(64,64),ATTACK_SCALE,MAP_ROOT)
        attack.save(resources/"attackRight.png",compress_level=9)
        attack.transform((64,64),Image.Transform.AFFINE,(-1,0,96,0,1,0),resample=Image.Resampling.NEAREST).save(resources/"attackLeft.png",compress_level=9)
        for role,size in (("large",(58,64)),("small",(32,32))):
            crop=standing.crop(PORTRAIT_CROP)
            ratio=min(size[0]/crop.width,size[1]/crop.height)
            crop=crop.resize((round(crop.width*ratio),round(crop.height*ratio)),Image.Resampling.LANCZOS)
            icon=Image.new("RGBA",size,(0,0,0,0))
            icon.alpha_composite(crop,((size[0]-crop.width)//2,(size[1]-crop.height)//2))
            icon.save(resources/(role+".png"),compress_level=9)
        generation={"image_generation_used":True,"provider":"OpenAI built-in imagegen; original painted2D",
                    "model":"not exposed by tool","prompt":"Exact portable requests in ownedunit requests/ JSON leaves",
                    "painted_master":(SOURCE/"standing-v1.png").relative_to(PROJECT).as_posix(),
                    "painted_master_sha256":sha(SOURCE/"standing-v1.png"),"provenance":ledger.relative_to(PROJECT).as_posix(),
                    "provenance_sha256":sha(ledger),"producer_source":Path(__file__).relative_to(PROJECT).as_posix(),
                    "producer_source_sha256":sha(Path(__file__)),"method":"Fixed variant affine; native64map root48,60; no per-pose bodyfit or alpha threshold"}
        common={"status":"authored configuration","production_status":"painted-master-complete-unapproved",
                "unit":"draklornAttendant","generation":generation,"visual_approval_granted":False,
                "credits":{"author":"Project-directed built-in imagegen and technical2D assembly","license":None,"redistribution":"unresolved; release prohibited"},
                "acceptance":"Technical conversion only; native visuals/motion/rights/release remain pending"}
        recipes={"battle":{**common,"recipe_type":"vcmi_animation","canvas":[450,400],"pivot":{"x":193,"y":266},
                            "generateShadow":0,"generateOverlay":1,
                            "groups":[{"group":g,"frames":[descriptor(paths[name]) for name in names]} for g,names in groups().items()]},
                 "map":{**common,"recipe_type":"vcmi_animation","canvas":[64,64],"pivot":{"x":48,"y":60},
                         "generateShadow":0,"generateOverlay":1,"groups":[{"group":0,"frames":[descriptor(resources/"map-000.png")]}]}}
        for role in ("large","small","attackLeft","attackRight"):
            desc=descriptor(resources/(role+".png"))
            recipes[role]={**common,"recipe_type":"raster","fit":"exact","size":desc["source_canvas"],"require_alpha":True,**desc}
        compiler=faction_art_compile.create_compiler("freljord")
        for role,recipe in recipes.items():
            ext=".json" if role in ("map","battle") else ".png"
            recipe["output_path"]="Content/Sprites/runeterra/freljord/creatures/draklornAttendant/"+role+ext
            path=out/"recipes"/(role+".json")
            save(path,recipe)
            first,receipt=compiler.plan(PROJECT,path)
            second,_=compiler.plan(PROJECT,path)
            if first!=second:
                raise RuntimeError("Actual shared strict plan is not byte deterministic")
            result["strict_compiler_receipts"].append(receipt)
            for label,outputs in (("compiled-a",first),("compiled-b",second)):
                for relative,data in outputs.items():
                    destination=out/label/relative
                    destination.parent.mkdir(parents=True,exist_ok=True)
                    destination.write_bytes(data)
            result["output_sha256"].update({name:hashlib.sha256(data).hexdigest() for name,data in first.items()})
        result.update({"map_root":MAP_ROOT,"map_scale":MAP_SCALE,"map_canvas":[64,64],"attack_scale":ATTACK_SCALE,
                       "attack_source":"melee-up","attack_mirror":"x'=96-x aroundroot48; full64canvas, no bodyfit",
                       "portrait_fixed_crop":PORTRAIT_CROP})
    if any(sha(path)!=pin for path,pin in pins.items()):
        raise RuntimeError("Guarded compiler/producer/manifest/content changed; invalidate attempt")
    result["guarded_input_sha256"]={path.relative_to(PROJECT.parent).as_posix():pin for path,pin in pins.items()}
    result["guarded_inputs_unchanged"]=True
    save(out/("partial-inspection.json" if args.preview else "technical-conversion.json"),result)
    print(json.dumps({"report":out.relative_to(PROJECT).as_posix(),"selected_masters":len(lineage),"missing":missing,
                      "recipes":len(result["strict_compiler_receipts"]),"compiled_files":len(result["output_sha256"])},indent=2))


if __name__=="__main__":
    main()
