"""Fail closed if the reviewed payload diverges from the selected V7 mod files."""
import hashlib
from pathlib import Path
import re
import sys


OMITTED = {
    "runeterra-bandlecity/build-metadata.json", "runeterra-bilgewater/build-metadata.json",
    "runeterra-demacia/CREDITS.md", "runeterra-demacia/README.md", "runeterra-demacia/build-metadata.json",
    "runeterra-freljord/build-metadata.json", "runeterra-ionia/build-metadata.json",
    "runeterra-ixtal/build-metadata.json", "runeterra-ixtal/docs/CREDITS.md",
    "runeterra-noxus/build-metadata.json", "runeterra-piltover/build-metadata.json",
    "runeterra-piltover/docs/CREDITS.md", "runeterra-shurima/build-metadata.json",
    "runeterra-targon/build-metadata.json", "runeterra-world/DEVELOPMENT.json",
    "runeterra-zaun/build-metadata.json",
}
PRIVATE = re.compile(rb"(?i)(?:[a-z]:[\\/]users[\\/]matcy|[a-z]:[\\/]runeterra|[a-z]:[\\/]e2e|matcy)")
TEXT = {".json", ".txt", ".md", ".lua", ".cfg", ".ini", ".xml", ".cmd", ".ps1"}


def collect(root):
    return {p.relative_to(root).as_posix(): p for p in root.rglob("*") if p.is_file()}


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.digest()


def main():
    source, app = map(Path, sys.argv[1:3])
    if (app / "Data").exists() or (app / "Mp3").exists():
        raise SystemExit("Original Data/Mp3 must not be in the payload")
    a, b = collect(source / "app" / "Mods"), collect(app / "Mods")
    if a.keys() - b.keys() != OMITTED or b.keys() - a.keys():
        raise SystemExit("V7 payload file inventory changed; inspect before rebuilding")
    for name in sorted(a.keys() & b.keys()):
        if a[name].stat().st_size != b[name].stat().st_size or digest(a[name]) != digest(b[name]):
            raise SystemExit("Payload differs from V7: " + name)
    for name, path in collect(app).items():
        if path.suffix.lower() in {".lod", ".snd", ".vid", ".h3s"}:
            raise SystemExit("Possible original game archive: " + name)
        if path.suffix.lower() in TEXT and PRIVATE.search(path.read_bytes()):
            raise SystemExit("Possible private path: " + name)
    print("Verified V7 mod hashes, the reviewed omission set and basic payload privacy.")


if __name__ == "__main__":
    main()
