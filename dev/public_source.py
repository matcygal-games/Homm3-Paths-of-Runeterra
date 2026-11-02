"""Prepare a fresh, reviewed source tree without copying private Git history.

Planning is read-only. A successful export preserves admitted source bytes and
does not establish third-party rights, gameplay acceptance or GPL compliance.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import zlib

from .publication_audit import TEXT_EXTENSIONS, contains_local_path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_ROOT_FILES = {
    ".editorconfig", ".gitattributes", ".gitignore", "README.md", "LICENSE",
    "NOTICE.md", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "SECURITY.md",
    "CHANGELOG.md", "pyproject.toml", "requirements.txt", "requirements-dev.txt",
}
PUBLIC_TREES = {".github", "dev", "tests", "docs", "issues", "installer", "paths-of-runeterra", "vendor"}
PRIVATE_PARTS = {".git", ".codex", ".kilo", ".tools", ".venv", "__pycache__",
                 "build", "dist", "reports", "prompts", "references", "cache", "caches",
                 "saves", "logs", "node_modules"}
BLOCKED_SUFFIXES = {".lod", ".snd", ".vid", ".h3s", ".exe", ".dll", ".pdb", ".lib", ".obj", ".dmp", ".pyc", ".zip", ".7z"}
RETIRED_SCENE = re.compile(r"(?i)\.blend[0-9~@]*$")
MAX_METADATA = 4 * 1024 * 1024
SOURCE_TEXT_EXTENSIONS = TEXT_EXTENSIONS | {".c", ".cc", ".cpp", ".h", ".hpp", ".cmake", ".rst", ".iss", ".lock", ".properties", ".sh", ".svg", ".lua"}
PRIVATE_PATH = re.compile(r"(?i)(?:[a-z]:[/\\]users[/\\][^/\\\s\"']+|/(?:home|users)/[^/\s\"']+)")


def _redirect(info):
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def direct(path: Path, *, file=False):
    """Refuse aliased ancestors before reading a selected source or output."""
    path = Path(path).absolute()
    for item in reversed((path, *path.parents)):
        try:
            info = item.lstat()
        except FileNotFoundError:
            continue
        if _redirect(info):
            raise ValueError("Linked source/output path refused: " + str(item))
        if item != path and not stat.S_ISDIR(info.st_mode):
            raise ValueError("Non-directory ancestor refused: " + str(item))
        if item == path and file and (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1):
            raise ValueError("Source must be a regular, single-link file: " + str(item))
    return path


def exclusion(name):
    if not isinstance(name, str) or not name or "\\" in name or ":" in name or any(part in {"", ".", ".."} for part in name.split("/")):
        return "invalid relative path"
    parts = Path(name).parts
    if not parts or Path(name).is_absolute() or any(p in {".", ".."} for p in parts):
        return "invalid relative path"
    if parts[0] == "matt_dev":
        return "private developer archive"
    if any(part.casefold() in PRIVATE_PARTS for part in parts):
        return "local, generated or historical material"
    if Path(name).name.casefold() in {"local-paths.json", "dirs.json", ".env"} or Path(name).name.startswith(".env."):
        return "local settings"
    if name in PUBLIC_ROOT_FILES:
        return None
    if len(parts) == 1:
        return "not a public root source file"
    if parts[0] not in PUBLIC_TREES and not re.fullmatch(r"runeterra-[a-z]+(?:-[a-z]+)*", parts[0]):
        return "not a public source tree"
    if any(parts[index] == "assets" and parts[index + 1] in {"compiled", "generated"}
           for index in range(len(parts) - 1)):
        return "derived assets"
    return None


def _unpack_metadata(raw):
    decoder = zlib.decompressobj()
    result = decoder.decompress(raw, MAX_METADATA + 1)
    if len(result) > MAX_METADATA or decoder.unconsumed_tail or not decoder.eof:
        raise ValueError("Compressed PNG metadata exceeds limit or is incomplete")
    return result


def png_private_metadata(path):
    """Inspect standard PNG textual metadata without altering image pixels."""
    with path.open("rb") as source:
        if source.read(8) != b"\x89PNG\r\n\x1a\n":
            raise ValueError("Invalid PNG signature")
        while True:
            header = source.read(8)
            if len(header) != 8:
                raise ValueError("Incomplete PNG chunk header")
            length, kind = int.from_bytes(header[:4], "big"), header[4:]
            if kind in {b"tEXt", b"zTXt", b"iTXt"}:
                if length > MAX_METADATA:
                    raise ValueError("PNG text metadata exceeds limit")
                raw = source.read(length)
                if len(raw) != length:
                    raise ValueError("Incomplete PNG metadata")
                if kind == b"tEXt":
                    text = raw
                elif kind == b"zTXt":
                    _, value = raw.split(b"\0", 1)
                    if not value or value[0] != 0:
                        raise ValueError("Unsupported compressed PNG text")
                    text = _unpack_metadata(value[1:])
                else:
                    keyword, value = raw.split(b"\0", 1)
                    if len(value) < 2 or value[0] not in (0, 1) or value[1] != 0:
                        raise ValueError("Invalid international PNG text")
                    language, translated, text = value[2:].split(b"\0", 2)
                    text = _unpack_metadata(text) if value[0] else text
                    text = keyword + b" " + language + b" " + translated + b" " + text
                normalized = text.decode("utf-8", errors="replace").replace("\\\\", "/").replace("\\", "/")
                if PRIVATE_PATH.search(normalized):
                    return True
            else:
                source.seek(length, os.SEEK_CUR)
            if len(source.read(4)) != 4:
                raise ValueError("Incomplete PNG chunk")
            if kind == b"IEND":
                return False


def candidates(root):
    result = subprocess.run(["git", "-c", "core.longpaths=true", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                            cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    if result.stderr:
        raise ValueError("Git inventory warnings require review before export")
    return sorted({os.fsdecode(value) for value in result.stdout.split(b"\0") if value})


def _has_retired_art_import(path):
    """Inspect producer code without importing or executing it."""
    try:
        syntax = ast.parse(path.read_text(encoding="utf-8-sig"))
    except (SyntaxError, UnicodeError) as error:
        raise ValueError("Python source could not be inspected") from error
    for node in ast.walk(syntax):
        modules = ([value.name for value in node.names] if isinstance(node, ast.Import)
                   else [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
        if any(name.split(".", 1)[0] in {"bpy", "bpy_extras", "bmesh", "mathutils", "blenderproc", "pyrender", "trimesh"} for name in modules):
            return True
    return False


def plan(root=ROOT, *, names=None, progress=None):
    root = direct(Path(root))
    admitted, excluded, blocked = [], [], []
    listed = candidates(root) if names is None else sorted(set(names))
    for index, name in enumerate(listed, 1):
        if progress is not None and index % 1000 == 0:
            progress(index, len(listed))
        reason = exclusion(name)
        if reason:
            excluded.append({"path": name, "reason": reason})
            continue
        path = root / name
        try:
            direct(path, file=True)
            if RETIRED_SCENE.search(path.name):
                raise ValueError("Retired 3D scene files are forbidden in public source")
            if path.suffix.casefold() in BLOCKED_SUFFIXES:
                raise ValueError("Binary/game archive requires a separate reviewed distribution")
            if (path.suffix.casefold() in SOURCE_TEXT_EXTENSIONS or name in PUBLIC_ROOT_FILES or path.name in {"LICENSE", "COPYING", "NOTICE"}) and contains_local_path(path):
                raise ValueError("Text contains a workstation user-directory path")
            if path.suffix.casefold() == ".py" and _has_retired_art_import(path):
                raise ValueError("Retired 3D artwork producer is forbidden in public source")
            if path.suffix.casefold() == ".png" and png_private_metadata(path):
                raise ValueError("PNG metadata contains a workstation user-directory path")
            with path.open("rb") as source:
                digest = hashlib.file_digest(source, "sha256").hexdigest()
            admitted.append({"path": name, "sha256": digest, "size": path.stat().st_size})
        except (OSError, ValueError, zlib.error) as error:
            blocked.append({"path": name, "reason": str(error)})
    present = {item["path"] for item in admitted}
    for required in ("README.md", "LICENSE", "NOTICE.md", "CONTRIBUTING.md"):
        if required not in present:
            blocked.append({"path": required, "reason": "Required contributor/license document is not admitted"})
    return {"format_version": 1, "eligible": not blocked, "admitted": admitted, "excluded": excluded,
            "blocked": blocked, "scope": "Source inventory/privacy admission only; rights, corresponding engine source, secrets and gameplay require separate review. No Git history is exported."}


def export(root, destination, inventory):
    root = direct(Path(root))
    destination = direct(Path(destination))
    if not inventory.get("eligible") or inventory.get("blocked"):
        raise ValueError("Public source inventory is blocked; no output was created")
    if destination == root or root.is_relative_to(destination):
        raise ValueError("Destination overlaps or contains source workspace")
    if destination.is_relative_to(root) and not destination.is_relative_to(root / "matt_dev"):
        raise ValueError("An in-workspace export must be inside ignored local storage")
    if destination.exists():
        raise ValueError("Destination already exists; existing output is never replaced")
    selected = inventory.get("admitted", [])
    if not isinstance(selected, list) or any(not isinstance(item, dict) or exclusion(item.get("path")) is not None for item in selected):
        raise ValueError("Invalid source inventory")
    current = plan(root, names=[item["path"] for item in selected])
    if not current["eligible"] or current["admitted"] != selected:
        raise ValueError("Source inventory changed or failed current admission")
    # Bind the plan to source bytes before creating an output. Validate again
    # while copying; unexpected changes leave an explicitly incomplete tree.
    for item in inventory["admitted"]:
        path = direct(root / item["path"], file=True)
        with path.open("rb") as source:
            if hashlib.file_digest(source, "sha256").hexdigest() != item["sha256"]:
                raise ValueError("Source changed after planning: " + item["path"])
    destination.mkdir(parents=True, exist_ok=False)
    marker = destination / "INCOMPLETE.json"
    marker.write_text('{"status":"incomplete source export"}\n', encoding="utf-8")
    for item in inventory["admitted"]:
        path = direct(root / item["path"], file=True)
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != item["sha256"]:
            raise ValueError("Source changed during export; output marked incomplete: " + item["path"])
        target = destination / item["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        direct(target)
        with target.open("xb") as output:
            output.write(raw)
    (destination / "PUBLIC_SOURCE_MANIFEST.json").write_text(json.dumps(inventory, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    marker.unlink()
    return destination


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="source repository; defaults to this checkout")
    parser.add_argument("--output", type=Path, help="new destination for an admitted source tree")
    parser.add_argument("--write", action="store_true", help="export only if every selected file passes; default is read-only planning")
    args = parser.parse_args(argv)
    if args.write and args.output is None:
        parser.error("--write requires --output")
    try:
        inventory = plan(args.root, progress=lambda done, total: print(f"Source inventory: {done}/{total} paths", file=sys.stderr))
        print(json.dumps(inventory, indent=2, ensure_ascii=True))
        if args.write:
            export(args.root, args.output, inventory)
        return 0 if inventory["eligible"] else 1
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print("Public source preparation failed: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
