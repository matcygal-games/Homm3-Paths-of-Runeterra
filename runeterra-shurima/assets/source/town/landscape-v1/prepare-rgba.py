"""Lossless native RGBA derivative of this directory's own painted master."""
from pathlib import Path
import hashlib
import json
from PIL import Image

ROOT = Path(__file__).resolve().parent
source, destination = ROOT / "master.png", ROOT / "native-rgba.png"
with Image.open(source) as image:
    if image.size != (800, 374):
        raise ValueError("Expected the pinned native-size terrain master")
    original = image.convert("RGB").tobytes()
    image.convert("RGBA").save(destination)
with Image.open(destination) as image:
    assert image.mode == "RGBA" and image.size == (800, 374)
    assert image.convert("RGB").tobytes() == original
record = {"status": "authored configuration", "operation": "lossless RGB to opaque RGBA format conversion; RGB pixel bytes unchanged",
          "source": source.name, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
          "output": destination.name, "output_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
          "canvas": [800, 374], "alpha": 255, "visual_approval_granted": False}
(ROOT / "rgba-conversion.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
