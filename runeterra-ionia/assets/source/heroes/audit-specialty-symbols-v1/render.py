"""Small unselected UI material-relief study, not a production converter."""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parents[4]
REPORT = ROOT / "runeterra-ionia/build/reports/six-town-audit-20261022/specialty-symbol-candidates-v1"
SIZE = 352
SCALE = SIZE / 100
MATERIALS = {
    "bronze": (168, 122, 61), "ivory": (207, 200, 161),
    "steel": (155, 177, 180), "teal": (44, 100, 91),
    "rose": (143, 67, 68), "blue": (54, 120, 165),
    "violet": (111, 79, 138), "wood": (126, 79, 43),
    "dark": (30, 40, 37), "skin": (151, 116, 80),
}


def raster(hero, seed):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:SIZE, 0:SIZE] / SCALE
    grain = rng.normal(0, 1.8, (SIZE, SIZE))
    grain += 1.6 * np.sin(xx * 1.1 + yy * 0.6)
    canvas = Image.new("RGBA", (SIZE, SIZE))

    def layer(kind, coords, material, width=1):
        mask = Image.new("L", (SIZE, SIZE))
        draw = ImageDraw.Draw(mask)
        pts = [(x * SCALE, y * SCALE) for x, y in coords]
        if kind == "polygon":
            draw.polygon(pts, fill=255)
        elif kind == "ellipse":
            draw.ellipse((*pts[0], *pts[1]), fill=255)
        elif kind == "ring":
            draw.ellipse((*pts[0], *pts[1]), outline=255, width=round(width * SCALE))
        elif kind == "line":
            draw.line(pts, fill=255, width=round(width * SCALE), joint="curve")
        else:
            raise ValueError(kind)
        # A shallow material relief, not an assertion of painterly authorship.
        relief = np.asarray(mask.filter(ImageFilter.GaussianBlur(1.1 * SCALE)), dtype=float) / 255
        gy, gx = np.gradient(relief)
        shade = 0.84 - gx * 9 - gy * 10 + 0.09 * (1 - (xx + yy) / 200)
        base = np.array(MATERIALS[material], dtype=float)
        color = base[None, None, :] * np.clip(shade[:, :, None], 0.38, 1.45)
        color += grain[:, :, None]
        if material in ("bronze", "steel"):
            color += (3 * np.sin(xx * 2 + yy * .15))[:, :, None]
        rgba = np.zeros((SIZE, SIZE, 4), dtype=np.uint8)
        rgba[:, :, :3] = np.clip(color, 0, 255).astype(np.uint8)
        rgba[:, :, 3] = np.asarray(mask)
        shadow = Image.new("RGBA", (SIZE, SIZE), (5, 4, 3, 0))
        shifted = Image.new("L", (SIZE, SIZE))
        shifted.paste(mask.filter(ImageFilter.GaussianBlur(0.5 * SCALE)), (3, 4))
        shadow.putalpha(shifted.point(lambda a: round(a * .7)))
        canvas.alpha_composite(shadow)
        canvas.alpha_composite(Image.fromarray(rgba))

    def poly(pts, mat): layer("polygon", pts, mat)
    def ellipse(box, mat): layer("ellipse", box, mat)
    def line(pts, mat, width): layer("line", pts, mat, width)
    def ring(box, mat, width): layer("ring", box, mat, width)

    def seal(value):
        ellipse([(61, 63), (92, 92)], "bronze")
        ellipse([(64, 66), (89, 89)], "dark")
        line([(67, 77), (74, 77)], "ivory", 2.4)
        line([(70.5, 73.5), (70.5, 80.5)], "ivory", 2.4)
        if value == 1:
            line([(79, 74), (82, 71), (82, 84)], "ivory", 2.4)
            line([(78, 84), (86, 84)], "ivory", 2.2)
        else:
            line([(77, 74), (79, 71), (84, 71), (86, 74), (85, 77), (78, 84), (87, 84)], "ivory", 2.4)

    def torso(color):
        poly([(30, 42), (43, 35), (55, 35), (67, 45), (62, 78), (31, 78)], color)
        poly([(33, 43), (43, 40), (57, 73), (50, 78)], "ivory")
        ellipse([(40, 18), (58, 39)], "skin")
        poly([(40, 20), (42, 17), (55, 17), (59, 24), (40, 24)], "dark")
        line([(32, 69), (61, 69)], "bronze", 4)
        ellipse([(21, 78), (29, 86)], "bronze")
        ellipse([(33, 78), (41, 86)], "steel")

    # Fixed plaque and margin, not copied from the original UN icon background.
    poly([(8, 5), (91, 5), (95, 10), (95, 91), (91, 95), (8, 95), (5, 91), (5, 10)], "wood")
    poly([(9, 9), (91, 9), (91, 91), (9, 91)], "dark")
    if hero == "karma":
        ring([(18, 14), (36, 32)], "bronze", 3)
        poly([(50, 18), (37, 43), (38, 50), (44, 57), (55, 57), (62, 49), (62, 43)], "blue")
        poly([(22, 60), (75, 60), (66, 76), (34, 76)], "bronze")
        ellipse([(27, 58), (71, 65)], "blue")
        line([(38, 80), (62, 80)], "ivory", 4)
        seal(1)
    elif hero in ("irelia", "leeSin", "xayah"):
        torso("rose" if hero == "irelia" else "teal")
        if hero == "irelia":
            line([(66, 78), (77, 40)], "wood", 5)
            poly([(72, 52), (73, 26), (83, 16), (82, 45)], "steel")
            line([(68, 54), (84, 58)], "bronze", 4)
            line([(34, 56), (60, 63)], "rose", 6)
        elif hero == "leeSin":
            line([(74, 16), (70, 83)], "wood", 6)
            line([(73, 25), (72, 40)], "ivory", 7)
            line([(72, 66), (71, 75)], "ivory", 7)
        else:
            line([(72, 17), (82, 28), (87, 48), (83, 66), (72, 79)], "wood", 5)
            line([(72, 17), (72, 79)], "ivory", 1.6)
            line([(65, 47), (89, 47)], "steel", 2)
    elif hero == "shen":
        poly([(22, 22), (37, 16), (42, 27), (57, 27), (63, 16), (78, 22), (72, 69), (50, 86), (28, 69)], "bronze")
        poly([(29, 27), (36, 24), (41, 34), (59, 34), (64, 24), (71, 27), (66, 63), (50, 76), (34, 63)], "steel")
        for y in (46, 57, 68):
            line([(34, y), (50, y + 5), (66, y)], "ivory", 3)
        for x in (27, 72): ellipse([(x - 2, 28), (x + 2, 32)], "ivory")
    elif hero == "akali":
        poly([(17, 73), (32, 59), (43, 69), (61, 52), (84, 73), (84, 82), (17, 82)], "teal")
        poly([(20, 37), (34, 24), (49, 21), (65, 25), (81, 37), (66, 48), (50, 53), (33, 48)], "bronze")
        poly([(25, 37), (38, 29), (50, 27), (64, 31), (76, 37), (63, 44), (50, 47), (36, 44)], "ivory")
        ellipse([(41, 28), (59, 46)], "teal")
        ellipse([(46, 31), (54, 43)], "dark")
    elif hero == "masterYi":
        line([(22, 47), (17, 61), (23, 74), (39, 81), (58, 79), (72, 68)], "bronze", 5)
        poly([(37, 59), (68, 19), (82, 14), (78, 30), (46, 67)], "steel")
        line([(34, 58), (49, 71)], "bronze", 5)
        line([(39, 68), (27, 81)], "wood", 6)
        line([(45, 59), (76, 24)], "ivory", 1.5)
    elif hero == "wukong":
        line([(46, 48), (36, 81)], "bronze", 5)
        for box in ([(25, 19), (49, 43)], [(49, 19), (73, 43)], [(25, 43), (49, 67)], [(49, 43), (73, 67)]):
            ellipse(box, "teal")
        line([(48, 42), (34, 28)], "bronze", 2)
        line([(49, 42), (63, 28)], "bronze", 2)
        line([(48, 44), (34, 57)], "bronze", 2)
        line([(49, 44), (63, 57)], "bronze", 2)
        seal(1)
    elif hero == "ahri":
        poly([(36, 22), (63, 22), (64, 34), (76, 49), (73, 70), (64, 82), (35, 82), (26, 70), (23, 49), (35, 34)], "bronze")
        poly([(39, 34), (60, 34), (69, 51), (66, 69), (59, 75), (39, 75), (32, 66), (31, 51)], "blue")
        line([(36, 23), (64, 23)], "ivory", 6)
        line([(31, 52), (68, 52)], "ivory", 3)
        line([(38, 66), (60, 66)], "bronze", 3)
    elif hero == "yasuo":
        for y in (29, 41, 53):
            line([(17, y), (38, y), (45, y + 4)], "blue", 3.5)
        poly([(46, 20), (68, 20), (63, 57), (79, 65), (80, 75), (44, 77), (34, 70), (43, 56)], "wood")
        poly([(46, 23), (63, 23), (60, 49), (43, 52)], "ivory")
        for y in (31, 39, 47): line([(44, y), (63, y + 3)], "bronze", 2)
        line([(36, 73), (79, 78)], "bronze", 5)
        seal(1)
    elif hero == "yone":
        poly([(22, 16), (53, 38), (40, 44), (58, 61), (32, 50), (40, 40), (19, 29)], "violet")
        line([(70, 17), (57, 25), (51, 39), (52, 55), (61, 72), (78, 81)], "bronze", 7)
        line([(72, 22), (63, 31), (61, 44)], "ivory", 3)
        line([(51, 51), (34, 69), (25, 72)], "violet", 4)
    elif hero == "syndra":
        poly([(20, 17), (62, 38), (47, 45), (76, 70), (38, 57), (46, 47), (19, 32)], "violet")
        poly([(70, 50), (73, 64), (86, 60), (80, 73), (87, 82), (75, 79), (68, 89), (66, 77), (53, 77), (63, 68), (57, 57)], "ivory")
        line([(29, 26), (51, 39)], "rose", 3)
    elif hero == "hwei":
        ring([(23, 17), (77, 71)], "bronze", 5)
        ring([(35, 29), (65, 59)], "ivory", 3)
        line([(18, 78), (74, 25)], "wood", 5)
        poly([(65, 25), (82, 18), (76, 37), (72, 28)], "steel")
        line([(19, 71), (28, 78)], "ivory", 4)
        seal(2)
    elif hero == "rakan":
        line([(31, 18), (31, 84)], "wood", 5)
        ellipse([(26, 12), (36, 22)], "bronze")
        poly([(35, 23), (60, 26), (80, 19), (74, 43), (79, 58), (58, 64), (35, 57)], "rose")
        line([(39, 29), (58, 33), (72, 29)], "ivory", 3)
        line([(39, 52), (57, 57), (73, 52)], "bronze", 3)
        seal(1)
    elif hero == "sett":
        ellipse([(24, 20), (76, 77)], "bronze")
        poly([(43, 53), (43, 25), (50, 12), (57, 25), (57, 53), (50, 62)], "steel")
        line([(50, 23), (50, 53)], "ivory", 2)
        line([(35, 60), (65, 60)], "bronze", 6)
        line([(50, 62), (50, 82)], "wood", 7)
        seal(1)
    else:
        raise ValueError(hero)
    return canvas


def main():
    recipe = json.loads((SOURCE / "recipe.json").read_text(encoding="utf-8"))
    out = REPORT / "renders"
    out.mkdir(parents=True, exist_ok=True)
    for entry in recipe["heroes"]:
        hero = entry["id"]
        seed = recipe["presentation"]["seed"]
        master = raster(hero, seed)
        master.save(out / f"{hero}-study-master.png")
        for label, size in (("large", 44), ("small", 32)):
            native(master, size).save(out / f"{hero}-{label}.png")
    print("Rendered 15 unselected material studies, each at 352, 44 and 32 pixels; production quality blocked.")


def native(master, size):
    data = np.array(master.resize((size, size), Image.Resampling.LANCZOS))
    data[data[:, :, 3] <= 4] = 0
    return Image.fromarray(data)


if __name__ == "__main__":
    main()
