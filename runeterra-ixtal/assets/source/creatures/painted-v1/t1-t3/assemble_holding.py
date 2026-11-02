"""Deterministic whole-painting placement only; no character/crest painting."""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
REPORT = ROOT / "build/reports/ixtal-implementation-20261026-v1/creature-art-t1-t3"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    contract = json.loads((HERE / "holding_registration.json").read_text())
    REPORT.mkdir(parents=True, exist_ok=True)
    records = []
    board = Image.new("RGB", (780, 540), (53, 50, 43))
    draw = ImageDraw.Draw(board)
    for index, (identifier, entry) in enumerate(contract["units"].items()):
        master = HERE / entry["master"]
        source = Image.open(master).convert("RGBA")
        # Remove only effectively transparent isolated color noise from provider
        # alpha; retain actual painted semitransparent edge pixels.
        alpha = source.getchannel("A").point(lambda value: 0 if value < 4 else value)
        source.putalpha(alpha)
        scale = entry["scale"]
        scaled = source.resize(tuple(round(value * scale) for value in source.size), Image.Resampling.LANCZOS)
        root = entry["source_root"]
        placement = (round(197 - root[0] * scale), round(266 - root[1] * scale))
        native = Image.new("RGBA", tuple(contract["canvas"]))
        native.alpha_composite(scaled, placement)
        target = HERE / identifier / "native-holding-right.png"
        native.save(target)
        left = native.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        # Mirroring is an alternate facing of the same pose, never an action.
        left.save(HERE / identifier / "native-holding-left.png")
        crop = native.crop((137, 156, 277, 286))
        x, y = (index % 3) * 260, (index // 3) * 270
        draw.text((x + 10, y + 6), identifier, fill=(238, 224, 189))
        board.paste(crop, (x + 40, y + 22), crop)
        enlarged = crop.resize((280, 260), Image.Resampling.NEAREST)
        board.paste(enlarged, (x - 5, y + 15), enlarged)
        # Separate native crop below enlarged inspection; enlarged copy is only
        # a preview, never a selected battle texture.
        board.paste(crop, (x + 110, y + 130), crop)
        records.append({"id":identifier,"master":master.relative_to(HERE).as_posix(),
                        "master_sha256":sha(master),"native":target.relative_to(HERE).as_posix(),
                        "native_sha256":sha(target),"canvas":list(native.size),
                        "alpha_bbox":list(native.getbbox()),"root":[197,266],"scale":scale,
                        "source_root":root,"paste":list(placement),"status":"source preview; native/motion/art acceptance pending"})
    preview = REPORT / "holding-native-crops-v1.png"
    board.save(preview)
    (REPORT / "holding-conversion-v1.json").write_text(json.dumps({
        "status":"authored configuration", "producer":HERE.relative_to(ROOT).as_posix()+"/assemble_holding.py",
        "producer_sha256":sha(Path(__file__)),"contract_sha256":sha(HERE / "holding_registration.json"),
        "preview":preview.relative_to(ROOT).as_posix(),"preview_sha256":sha(preview),"units":records,
        "limitations":["Identity holding poses only; distinct action cohorts still required.",
                        "Source-native comparison and enlarged inspection do not establish actual game placement or final art acceptance."]}, indent=2)+"\n")
    print(json.dumps({"units":len(records),"preview":preview.relative_to(ROOT).as_posix(),"source_bytes":sum(p.stat().st_size for p in HERE.rglob('*') if p.is_file())}))


if __name__ == "__main__":
    main()
