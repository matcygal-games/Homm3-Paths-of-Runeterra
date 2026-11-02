"""Technical isolation/constant-density placement of painted quill releases."""
from pathlib import Path
import hashlib
import json
import runpy
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
PROJECT = ROOT / "runeterra-ixtal"
REPORT = ROOT / "build/reports/ixtal-implementation-20261026-v1/creature-art-t1-t3"
COMPONENTS = ROOT / "runeterra-piltover/assets/source/creatures/painted-v1/t5-t7/components.py"
parts_of = runpy.run_path(str(COMPONENTS))["components"]

# Authored actual atlas pixel observations. One density per full atlas, never
# per-pose alpha bounds fitting. Ground marks refer to torso/support projection.
UNITS = {
    "bristlehog": {"atlas":"shooting-atlas-v1.png", "scale":0.20,
        "roots":[[225,365],[580,365],[940,365],[1285,365],
                 [225,668],[580,668],[940,668],[1285,668],
                 [225,1008],[580,1008],[940,1008],[1285,1008]],
        "tips":[[1390,16],[1442,526],[1437,987]]},
    "thornbackBristlehog": {"atlas":"shooting-atlas-v2.png", "scale":0.21,
        "roots":[[225,378],[580,378],[940,378],[1285,378],
                 [225,687],[580,687],[940,687],[1285,687],
                 [225,1019],[580,1019],[940,1019],[1285,1019]],
        "tips":[[1393,12],[1445,510],[1441,995]]}
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path):
    return {"path":path.relative_to(PROJECT).as_posix(),"sha256":sha(path)}


def isolate(source, part):
    pixels = np.asarray(source).copy()
    mask = np.zeros(source.width * source.height, dtype=np.bool_)
    mask[part["pixels"]] = True
    pixels[~mask.reshape(source.height, source.width)] = 0
    return Image.fromarray(pixels).crop(tuple(part["box"]))


def main():
    REPORT.mkdir(parents=True,exist_ok=True)
    summary = []
    for identifier, settings in UNITS.items():
        master = HERE / identifier / settings["atlas"]
        image = Image.open(master).convert("RGBA")
        parts = [part for part in parts_of(image.getchannel("A"),threshold=32) if part["area"] > 1500]
        if len(parts) != 12:
            raise ValueError(f"{identifier}: expected twelve separate genuine painted poses, got {len(parts)}")
        rows = [[] for _ in range(3)]
        for part in parts:
            row = min(2,int((part["box"][1]+part["box"][3])/2 * 3 / image.height))
            rows[row].append(part)
        if any(len(row)!=4 for row in rows):
            raise ValueError(f"{identifier}: actual pose rows are not 3x4")
        parts = [part for row in rows for part in sorted(row,key=lambda p:p["box"][0])]
        records, measurements = [], []
        target_dir = HERE / "native" / identifier
        (target_dir / "battle").mkdir(parents=True,exist_ok=True)
        (target_dir / "isolated").mkdir(parents=True,exist_ok=True)
        for index, part in enumerate(parts):
            row, phase = divmod(index,4)
            group = 14+row
            direction = ("upper","middle","lower")[row]
            isolated = isolate(image,part)
            source_path = target_dir / "isolated" / f"shoot-{index:02}.png"
            isolated.save(source_path)
            size = tuple(round(value*settings["scale"]) for value in isolated.size)
            scaled = isolated.resize(size,Image.Resampling.LANCZOS)
            sx, sy = size[0]/isolated.width, size[1]/isolated.height
            box = part["box"]
            root = settings["roots"][index]
            paste = (round(197-(root[0]-box[0])*sx),round(266-(root[1]-box[1])*sy))
            native = Image.new("RGBA",(450,400))
            native.alpha_composite(scaled,paste)
            native_path = target_dir / "battle" / f"g{group}-f{phase:03}.png"
            native.save(native_path)
            pose = {"index":index,"group":group,"frame":phase,"source_frame":ref(source_path),
                    "source_box":box,"source_root":root,"nominal_scale":settings["scale"],
                    "pixel_grid_scale":[sx,sy],"native_paste":list(paste),"native_root":[197,266],
                    "native_frame":ref(native_path),"alpha_threshold":32}
            records.append(pose)
            if phase==3:
                tip = settings["tips"][row]
                pixel = image.getpixel(tuple(tip))
                if pixel[3] <128:
                    raise ValueError(f"{identifier}/{direction}: annotated actual quill tip is not visibly painted: {tip},{pixel}")
                point = [round(paste[0]+(tip[0]-box[0])*sx),round(paste[1]+(tip[1]-box[1])*sy)]
                offset = [point[0]-197,point[1]-265]
                measurement = {"direction":direction,"group":group,"release_frame_zero_based":3,
                    "native_tip_pixels":point,"original_tip_pixels":tip,"source_tip_rgba":list(pixel),
                    "native_origin_offset":offset,"source_frame":ref(source_path),"native_frame":ref(native_path),
                    "measurement":"Actual painted forward dorsal quill tip at fourth temporal pose. Physical flying quill remains a separate projectile, not a baked effect. Source geometry only; native trajectory pending."}
                measurements.append(measurement)
                marked = native.copy()
                draw = ImageDraw.Draw(marked)
                draw.line((point[0]-4,point[1],point[0]+4,point[1]),fill=(255,0,255,255))
                draw.line((point[0],point[1]-4,point[0],point[1]+4),fill=(255,0,255,255))
                marked.crop((132,170,272,280)).resize((560,440),Image.Resampling.NEAREST).save(REPORT/f"{identifier}-release-{direction}-annotated.png")
        placement = target_dir / "shoot-placement-v1.json"
        placement.write_text(json.dumps({"method":"One uniform source-atlas density; authored torso-ground roots; connected painted-pixel isolation at alpha32. No bbox fit, limb warp or drawn substitute.",
            "producer":ref(Path(__file__)),"components_helper":{"path":COMPONENTS.relative_to(ROOT).as_posix(),"sha256":sha(COMPONENTS)},
            "source_master":ref(master),"poses":records},indent=2)+"\n")
        measurement_path = target_dir / "shot-measurements-v1.json"
        measurement_path.write_text(json.dumps({"units":[{"id":identifier,"source_kind":"painted-native",
            "source_master":ref(master),"source_metadata":ref(placement),"measurements":measurements}],
            "acceptance":"Technical actual-source quill-tip measurements; native projectile playback, left-facing convention and motion acceptance remain pending."},indent=2)+"\n")
        summary.append({"id":identifier,"measurement":ref(measurement_path),"native_points":{m["direction"]:m["native_tip_pixels"] for m in measurements},
                        "offsets":{m["direction"]:m["native_origin_offset"] for m in measurements}})
    (REPORT / "quill-release-delivery-v1.json").write_text(json.dumps({"units":summary,"content_changed":False,"native_execution":"not observed"},indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
