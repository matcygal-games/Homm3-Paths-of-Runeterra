"""Technical native diagnostic assembly only; no painting or canonical writes."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[3]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

def main():
    plan = read(PROJECT / "assets/source/town/painted-v3/selection.json")
    entries, checks = [], []
    board = Image.new("RGB", (4 * 192, 5 * 212), (48, 52, 55))
    draw = ImageDraw.Draw(board)
    for row, old in enumerate(plan["adventure"]):
        state = old["state"]
        folder = ROOT / state
        master = folder / "master.png"
        image = Image.open(master).convert("RGBA")
        if image.size != (1536, 1024):
            raise ValueError(f"Unexpected atlas canvas: {state}: {image.size}")
        # Measure the actual transparent row gutter rather than assuming a
        # 512-pixel row stride. The Capitol edit retained a shorter row layout;
        # 512 clips lower-row flags and leaks their tips into the upper row.
        # These are whole-atlas crops; individual frames are never repainted.
        cell_height = {"capitol": 502, "castle": 506}.get(state, 512)
        entry = deepcopy(old)
        entry.pop("atlas_crop", None)
        entry.update(master=master.relative_to(PROJECT).as_posix(), master_sha256=sha(master),
                     provenance=(folder / "generation.json").relative_to(PROJECT).as_posix(),
                     cell_size=[768, cell_height])
        if cell_height != 512:
            entry["atlas_crop"] = [0, 0, 1536, cell_height * 2]
        frames = []
        for index in range(4):
            col, cell_row = index % 2, index // 2
            cell = image.crop((col * 768, cell_row * cell_height, (col + 1) * 768, (cell_row + 1) * cell_height))
            mask = cell.getchannel("A").point(lambda value: 255 if value >= 128 else 0)
            bounds = mask.getbbox()
            edge = {"top": sum(v >= 128 for v in cell.getchannel("A").crop((0, 0, 768, 1)).getdata()),
                    "bottom": sum(v >= 128 for v in cell.getchannel("A").crop((0, cell_height - 1, 768, cell_height)).getdata()),
                    "left": sum(v >= 128 for v in cell.getchannel("A").crop((0, 0, 1, cell_height)).getdata()),
                    "right": sum(v >= 128 for v in cell.getchannel("A").crop((767, 0, 768, cell_height)).getdata())}
            scale = entry["camera_scale"]
            tile = cell.resize((round(768 * scale), round(cell_height * scale)), Image.Resampling.LANCZOS)
            offset = [entry["native_anchor"][a] - round(entry["source_anchor"][a] * scale) for a in range(2)]
            native = Image.new("RGBA", (192, 192))
            native.alpha_composite(tile, tuple(offset))
            target = folder / f"review-frame-{index}.png"
            native.save(target)
            board.paste(native, (col * 192 + (index // 2) * 384, row * 212 + 20), native)
            frames.append({"path": target.relative_to(PROJECT).as_posix(), "sha256": sha(target),
                           "source_alpha_bounds": bounds, "source_opaque_edge_pixels": edge,
                           "native_alpha_bounds": native.getchannel("A").point(lambda a: 255 if a >= 128 else 0).getbbox(),
                           "scale": scale, "offset": offset})
        draw.text((5, row * 212 + 4), state + " - four native candidate frames", fill="white")
        entries.append(entry)
        checks.append({"state": state, "master_sha256": sha(master), "frames": frames})
    board.save(ROOT / "native-adventure-review.png")
    icon_master = ROOT / "icons/master.png"
    icons = []
    icon_board = Image.new("RGB", (4 * 160, 140), (48, 52, 55))
    icon_draw = ImageDraw.Draw(icon_board)
    for index, old in enumerate(plan["icons"]):
        entry = deepcopy(old)
        entry.update(master=icon_master.relative_to(PROJECT).as_posix(), master_sha256=sha(icon_master),
                     provenance=(ROOT / "icons/generation.json").relative_to(PROJECT).as_posix())
        crop = Image.open(icon_master).convert("RGBA").crop(tuple(entry["crop"]))
        for size_name, size in (("large", (58, 64)), ("small", (48, 32))):
            picture = crop.copy()
            picture.thumbnail(size, Image.Resampling.LANCZOS)
            native = Image.new("RGBA", size)
            native.alpha_composite(picture, ((size[0] - picture.width) // 2, size[1] - picture.height))
            target = ROOT / "icons" / f"review-{entry['state']}-{entry['mode']}-{size_name}.png"
            native.save(target)
            icon_board.paste(native, (index * 160 + (0 if size_name == "large" else 70), 40), native)
        icon_draw.text((index * 160 + 3, 5), entry["state"] + " " + entry["mode"], fill="white")
        icons.append(entry)
    icon_board.save(ROOT / "native-icon-review.png")
    write(ROOT / "handoff.json", {"status": "authored configuration", "adventure": entries, "icons": icons,
                                   "checks": checks, "native_adventure_board_sha256": sha(ROOT / "native-adventure-review.png"),
                                   "native_icon_board_sha256": sha(ROOT / "native-icon-review.png"),
                                   "row_geometry_basis": "Measured transparent gutters: Capitol 502, Castle 506, other states 512. Castle right edges contain one/three soil-tip pixels, inspected as footing only; no roof, wall or flag cuts.",
                                   "canonical_recipes_written": False, "final_art_acceptance": False})
    print(json.dumps({"adventure": len(entries), "icons": len(icons), "handoff": str(ROOT / 'handoff.json'),
                      "source_edge_findings": {r["state"]: [f["source_opaque_edge_pixels"] for f in r["frames"]] for r in checks}}))

if __name__ == "__main__":
    main()
