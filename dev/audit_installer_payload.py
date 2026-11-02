"""Compare a V7 Mods directory with an installer payload without modifying either."""

import argparse
import hashlib
from pathlib import Path


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.digest()


def files(root):
    return {p.relative_to(root).as_posix(): p for p in root.rglob("*") if p.is_file()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--payload", type=Path, required=True)
    args = parser.parse_args()
    for path in (args.source, args.payload):
        if not path.is_dir():
            parser.error(f"directory not found: {path}")
    source, payload = files(args.source), files(args.payload)
    missing = sorted(source.keys() - payload.keys())
    extra = sorted(payload.keys() - source.keys())
    changed = []
    for name in sorted(source.keys() & payload.keys()):
        a, b = source[name], payload[name]
        if a.stat().st_size != b.stat().st_size or digest(a) != digest(b):
            changed.append(name)
    print(f"Source: {len(source)} files; payload: {len(payload)} files")
    for label, entries in (("Missing", missing), ("Extra", extra), ("Different", changed)):
        print(f"{label}: {len(entries)}")
        for name in entries:
            print(f"  {name}")
    return 1 if missing or extra or changed else 0


if __name__ == "__main__":
    raise SystemExit(main())
