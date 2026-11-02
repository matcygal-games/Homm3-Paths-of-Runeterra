"""Project paths, deterministic writes, and the comment syntax used by VCMI JSON."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import shutil
import zipfile

PROJECT = Path(__file__).resolve().parents[1]
WORKSPACE = PROJECT.parent
VCMI = WORKSPACE / "vcmi-develop" / "vcmi-develop"
MOD_ID = "runeterra-demacia"
STAGE = PROJECT / "build" / "Mods" / MOD_ID
REPORTS = PROJECT / "build" / "reports"
COLLECTIONS = {"factions": "faction", "creatures": "creature", "heroClasses": "heroClass",
               "heroes": "hero", "spells": "spell", "artifacts": "artifact"}


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json_bytes(value)
    if not path.is_file() or path.read_bytes() != payload:
        path.write_bytes(payload)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_jsonc(text: str) -> object:
    # Preserve strings, including URLs and escaped quotes, while removing comments.
    out = []
    i = 0
    quoted = False
    while i < len(text):
        char = text[i]
        if quoted:
            out.append(char)
            if char == "\\" and i + 1 < len(text):
                i += 1
                out.append(text[i])
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
            out.append(char)
        elif text[i:i + 2] == "//":
            end = text.find("\n", i)
            i = len(text) if end < 0 else end
            out.append("\n")
            continue
        elif text[i:i + 2] == "/*":
            end = text.find("*/", i + 2)
            if end < 0:
                raise ValueError("Unterminated JSON comment")
            out.append(" " * (end + 2 - i))
            i = end + 2
            continue
        else:
            out.append(char)
        i += 1
    if quoted:
        raise ValueError("Unterminated JSON string")
    clean = "".join(out)
    out, i, quoted = [], 0, False
    while i < len(clean):
        char = clean[i]
        if quoted:
            out.append(char)
            if char == "\\" and i + 1 < len(clean):
                i += 1
                out.append(clean[i])
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
            out.append(char)
        elif char == ",":
            j = i + 1
            while j < len(clean) and clean[j].isspace():
                j += 1
            if j >= len(clean) or clean[j] not in "]}":
                out.append(char)
        else:
            out.append(char)
        i += 1
    return json.loads("".join(out))


def read_json(path: Path) -> object:
    return parse_jsonc(path.read_text(encoding="utf-8-sig"))


def merge(base: dict, overrides: dict) -> dict:
    result = dict(base)
    for key, value in overrides.items():
        result[key] = merge(result[key], value) if isinstance(value, dict) and isinstance(result.get(key), dict) else value
    return result


def zip_files(path: Path, files: dict[str, bytes], preserve_unchanged: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    target = io.BytesIO() if preserve_unchanged else path
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    if preserve_unchanged:
        payload = target.getvalue()
        if not path.is_file() or path.read_bytes() != payload:
            path.write_bytes(payload)


def tree_hash(path: Path) -> str:
    digest = hashlib.sha256()
    for file in sorted(p for p in path.rglob("*") if p.is_file()):
        digest.update(file.relative_to(path).as_posix().encode("utf-8"))
        digest.update(bytes.fromhex(sha256(file)))
    return digest.hexdigest()


def reset_owned_build_directory(path: Path) -> None:
    target = path.resolve()
    build_root = (PROJECT / "build").resolve()
    if target == build_root or not target.is_relative_to(build_root):
        raise ValueError(f"Refusing to reset directory outside a project build child: {target}")
    marker = target / ".runeterra-owned.json"
    if target.exists():
        if not marker.is_file() or read_json(marker).get("mod_id") != MOD_ID:
            raise ValueError(f"Unowned build directory preserved: {target}")
        shutil.rmtree(target)
    target.mkdir(parents=True)
    write_json(marker, {"mod_id": MOD_ID})
