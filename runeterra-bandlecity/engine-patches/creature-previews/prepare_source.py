"""Apply the exact optional-preview overlay after the fifth engine patch.

No source archives, builds, game data or native processes are accessed here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent
EXPECTED = frozenset({
    "client/widgets/MiscWidgets.cpp", "lib/CCreatureHandler.h",
    "lib/CCreatureHandler.cpp", "config/schemas/creature.json",
    "test/entity/CreaturePreviewTest.cpp", "test/CMakeLists.txt",
})


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def apply_overlay(destination: Path, patch_root: Path = ROOT) -> dict:
    destination = destination.resolve(strict=True)
    document = json.loads((patch_root / "changes.json").read_text(encoding="utf-8"))
    entries = document["files"]
    if document.get("schema") != 1 or {e["path"] for e in entries} != EXPECTED or len(entries) != len(EXPECTED):
        raise ValueError("Unexpected preview overlay selection")
    prepared = []
    for entry in entries:
        name = entry["path"]
        relative = PurePosixPath(name)
        if relative.is_absolute() or ".." in relative.parts or "\\" in name or ":" in name:
            raise ValueError("Unsafe overlay path")
        target = destination / name
        if not target.resolve().is_relative_to(destination):
            raise ValueError("Overlay destination escapes requested source")
        source = patch_root / "overlay" / name
        data = source.read_bytes()
        if sha(data) != entry["after_sha256"]:
            raise ValueError("Overlay hash mismatch: " + name)
        current = sha(target.read_bytes()) if target.exists() else None
        if current not in (entry["before_sha256"], entry["after_sha256"]):
            raise ValueError("Source baseline mismatch: " + name)
        prepared.append((target, data))
    # Verify the entire selection before writing any target.
    for target, data in prepared:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return {e["path"]: e["after_sha256"] for e in entries}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="Explicit disposable source tree already prepared through patch five")
    args = parser.parse_args()
    print(json.dumps(apply_overlay(args.destination), indent=2, sort_keys=True))
