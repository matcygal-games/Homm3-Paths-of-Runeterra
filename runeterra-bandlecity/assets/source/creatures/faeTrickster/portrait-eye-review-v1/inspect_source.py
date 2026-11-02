"""Read-only source measurement; diagnostics stay in the assigned new report."""
from pathlib import Path
import hashlib
import json

from PIL import Image, ImageDraw

PROJECT = Path(__file__).resolve().parents[5]
REPORT = PROJECT / "build/reports/five-town-audit-20261022/art-portrait-fix"


def main():
    source = PROJECT / "assets/source/creatures/faeTrickster/registered-v2/ui-map/large-source.png"
    image = Image.open(source).convert("RGBA")
    REPORT.mkdir(parents=True, exist_ok=True)
    sheet = Image.new("RGB", (832, 650), "#242424")
    zoom = image.resize((832, 592), Image.Resampling.NEAREST)
    sheet.paste(zoom, (0, 32), zoom)
    draw = ImageDraw.Draw(sheet)
    for x in range(0, 52, 2):
        draw.text((x * 16, 5), str(x), fill="white")
    for y in range(0, 37, 2):
        draw.text((1, 32 + y * 16), str(y), fill="white")
    sheet.save(REPORT / "source-coordinate-inspection.png")
    pixels = []
    for y in range(image.height):
        for x in range(image.width):
            r, g, b, a = image.getpixel((x, y))
            if a >= 128 and g >= r + 12 and b >= r + 6 and g >= 65:
                pixels.append({"xy": [x, y], "rgba": [r, g, b, a]})
    print(json.dumps({"source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                      "size": image.size, "alpha_bounds": image.getchannel("A").getbbox(),
                      "turquoise_threshold_pixels_not_semantic_by_themselves": pixels}, indent=2))


if __name__ == "__main__":
    main()
