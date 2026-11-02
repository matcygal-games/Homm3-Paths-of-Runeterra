"""Build the reviewed V7 manual ZIP, without changing any input or game files.

Only Python's standard library is used. Failed builds leave their .partial file
for inspection; no files are deleted and existing outputs are never overwritten.
"""
from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import zipfile


ROOT = Path(__file__).absolute().parents[2]
ARCHIVE_ROOT = "Paths-of-Runeterra/"
SOURCE_MANIFEST_SHA256 = "6008ba797e83ad48d31fbaf69c42d2cc07fa839016001622b58d837010153865"
REVIEWED_MANIFEST_SHA256 = "6df782b2e5c7c803ad124d6224cac6c2e8c0be3593cc24b96461d01d632606b2"
RESTORE = (
    "runeterra-demacia/CREDITS.md",
    "runeterra-ixtal/docs/CREDITS.md",
    "runeterra-piltover/docs/CREDITS.md",
)
OMITTED = frozenset({
    "runeterra-bandlecity/build-metadata.json", "runeterra-bilgewater/build-metadata.json",
    "runeterra-demacia/CREDITS.md", "runeterra-demacia/README.md", "runeterra-demacia/build-metadata.json",
    "runeterra-freljord/build-metadata.json", "runeterra-ionia/build-metadata.json",
    "runeterra-ixtal/build-metadata.json", "runeterra-ixtal/docs/CREDITS.md",
    "runeterra-noxus/build-metadata.json", "runeterra-piltover/build-metadata.json",
    "runeterra-piltover/docs/CREDITS.md", "runeterra-shurima/build-metadata.json",
    "runeterra-targon/build-metadata.json", "runeterra-world/DEVELOPMENT.json",
    "runeterra-zaun/build-metadata.json",
})
RUNTIME = {"VCMI_client.exe": 2, "VCMI_server.exe": 1, "VCMI_lib.dll": 19}
EIGHTH_PATCH = (
    "installer/manual/engine-patches/0008-invalidate-cached-task-batch.patch",
    "35d79532d92e8fcc53e4bcdc4453ccce1ee8ee30b09a55d0c1abb02c28440a05",
)
TEXT = {".json", ".txt", ".md", ".lua", ".cfg", ".ini", ".xml", ".cmd", ".ps1",
        ".py", ".h", ".yml", ".yaml", ".html", ".csv", ".patch"}
PRIVATE = re.compile(rb"(?i)(?:[a-z]:[\\/]users[\\/](?!runneradmin(?:[\\/]|$))|"
                     rb"[a-z]:[\\/](?:runeterra|e2e)|matcy|/home/|/Users/(?!runneradmin/))")
BAD_PARTS = {"user", "saves", "saved games", "logs", "cache", "__pycache__", ".git"}
BAD_EXTENSIONS = {".lod", ".snd", ".vid", ".h3s", ".vsgm1", ".vcgm1", ".h3c", ".sav", ".log", ".pdb", ".pyc"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=True, sort_keys=True) + "\n").encode("utf-8")


def safe_name(name: str) -> str:
    """Reject Windows aliases as well as ZIP traversal, before normalization."""
    if (not isinstance(name, str) or not name or "\\" in name or name.startswith("/")
            or any(ord(c) < 32 for c in name)):
        raise ValueError("Unsafe relative member name")
    for part in name.split("/"):
        if (not part or part in {".", ".."} or part.endswith((" ", "."))
                or re.search(r'[:*?<>|\"]', part)
                or re.fullmatch(r"(?i)(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", part)):
            raise ValueError("Unsafe relative member name: " + name)
    if PurePosixPath(name).is_absolute():
        raise ValueError("Absolute member name")
    return name


def direct(path: Path) -> None:
    """Check ancestors without resolve(), which would hide links."""
    for part in reversed((path, *path.parents)):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("Linked or reparse path refused")
        if stat.S_ISREG(info.st_mode) and info.st_nlink != 1:
            raise ValueError("Hardlinked input/output refused")


def clean_path(path: Path) -> Path:
    if ".." in path.parts or any(p.endswith((" ", ".")) for p in path.parts):
        raise ValueError("Ambiguous filesystem path refused")
    path = path.absolute()
    direct(path)
    # Resolve existing Windows spelling to detect short-name / SUBST aliases.
    # resolve() is only called after the explicit reparse checks above.
    ancestor = path
    while not ancestor.exists():
        if ancestor == ancestor.parent:
            raise ValueError("No existing filesystem ancestor")
        ancestor = ancestor.parent
    if os.path.normcase(str(ancestor.resolve())) != os.path.normcase(str(ancestor)):
        raise ValueError("Aliased filesystem path refused")
    return path


def inventory(root: Path) -> dict[str, Path]:
    root = clean_path(root)
    if not root.is_dir():
        raise ValueError("Expected input directory")
    result: dict[str, Path] = {}
    folded: dict[str, str] = {}
    for current, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            path = Path(current) / name
            direct(path)
            relative = safe_name(path.relative_to(root).as_posix())
            key = relative.casefold()
            if key in folded:
                raise ValueError("Case-colliding input path: " + relative)
            folded[key] = relative
            if path.is_file():
                result[relative] = path
            elif not path.is_dir():
                raise ValueError("Non-regular input refused")
    return result


def checked_read(path: Path) -> bytes:
    direct(path)
    if not path.is_file():
        raise ValueError("Expected regular input file")
    with path.open("rb") as stream:
        before = os.fstat(stream.fileno())
        data = stream.read()
        after = os.fstat(stream.fileno())
    direct(path)
    now = path.stat()
    if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino) or (
            after.st_size, after.st_mtime_ns, after.st_ino) != (now.st_size, now.st_mtime_ns, now.st_ino):
        raise ValueError("Input changed while reading")
    return data


def load_json(path: Path) -> object:
    def pairs(rows):
        result = {}
        for key, value in rows:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result
    return json.loads(checked_read(path).decode("utf-8-sig"), object_pairs_hook=pairs)


def digest_map(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError("Invalid file hash map")
    folded = set()
    for name, digest in value.items():
        safe_name(name)
        if name.casefold() in folded or not isinstance(digest, str) or not re.fullmatch("[0-9a-f]{64}", digest):
            raise ValueError("Invalid or case-colliding file hash map")
        folded.add(name.casefold())
    return value


def scan(name: str, data: bytes, *, payload: bool = False) -> None:
    safe_name(name)
    parts = PurePosixPath(name).parts
    if payload and (parts[0].casefold() in {"data", "mp3"} or any(p.casefold() in BAD_PARTS for p in parts)
                    or PurePosixPath(name).suffix.casefold() in BAD_EXTENSIONS
                    or name.casefold() in {"config/dirs.json", "config/settings.json", "config/modsettings.json"}):
        raise ValueError("Private, game-data or user-profile member refused: " + name)
    if (PurePosixPath(name).suffix.lower() in TEXT or parts[-1].upper() in {"COPYING", "LICENSE", "COPYRIGHT"}) and PRIVATE.search(data):
        raise ValueError("Private path in text member: " + name)


@dataclass(frozen=True)
class Entry:
    name: str
    digest: str
    size: int
    source: Path | None = None
    data: bytes | None = None

    def read(self) -> bytes:
        data = checked_read(self.source) if self.source is not None else self.data
        if data is None or len(data) != self.size or sha(data) != self.digest:
            raise ValueError("Admitted member changed before ZIP write: " + self.name)
        return data


class Package:
    def __init__(self):
        self.entries: dict[str, Entry] = {}
        self.folded: set[str] = set()
        self.directories: set[str] = set()

    def add(self, name: str, *, path: Path | None = None, data: bytes | None = None,
            expected: str | None = None, payload: bool = False) -> None:
        name = safe_name(name)
        key = name.casefold()
        # Also reject file-vs-directory collisions, e.g. app and app/foo.
        ancestors = {p.as_posix().casefold() for p in PurePosixPath(name).parents if p.as_posix() != "."}
        if key in self.folded or key in self.directories or ancestors & self.folded:
            raise ValueError("Duplicate or conflicting package member: " + name)
        content = checked_read(path) if path is not None else data
        if content is None:
            raise ValueError("Missing package member data")
        digest = sha(content)
        if expected is not None and digest != expected:
            raise ValueError("Input SHA-256 mismatch: " + name)
        scan(name[4:] if payload and name.startswith("app/") else name, content, payload=payload)
        self.entries[name] = Entry(name, digest, len(content), path, None if path else content)
        self.folded.add(key)
        self.directories.update(ancestors)


def sanitize_contract(raw: object, source_hash: str, source_files: dict[str, str], *, count: int = 79) -> dict:
    if (not isinstance(raw, dict) or raw.get("build") != "Paths of Runeterra V7"
            or raw.get("vcmi") != "1.8.0" or raw.get("sourceManifestSha256") != source_hash
            or not isinstance(raw.get("requiredFiles"), list) or len(raw["requiredFiles"]) != count):
        raise ValueError("V7 game contract does not match source manifest")
    rows = []
    seen = set()
    for row in raw["requiredFiles"]:
        if not isinstance(row, dict):
            raise ValueError("Invalid game contract row")
        name = safe_name(row.get("relative"))
        if (name.casefold() in seen or len(name.split("/")) != 2 or name.split("/")[0] not in {"Data", "Mp3"}
                or row.get("sha256") != source_files.get("app/" + name)):
            raise ValueError("Unsafe, duplicate or mismatched game contract row")
        seen.add(name.casefold())
        rows.append({"relative": name, "sha256": row["sha256"]})
    return {"build": raw["build"], "vcmi": raw["vcmi"], "sourceManifestSha256": source_hash,
            "requiredFiles": sorted(rows, key=lambda r: r["relative"])}


def constants(path: Path, names: set[str]) -> dict:
    """Read source pins without executing repository Python."""
    module = ast.parse(checked_read(path).decode("utf-8-sig"))
    result = {}
    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in names:
                    result[target.id] = ast.literal_eval(node.value)
    if result.keys() != names:
        raise ValueError("Engine source pin constants missing")
    return result


def validate_inventory(selected: dict, reviewed: dict[str, str], source_files: dict[str, str],
                       *, expected_count: int = 20338, omitted: frozenset[str] = OMITTED) -> None:
    if len(reviewed) != expected_count or selected.keys() != reviewed.keys():
        raise ValueError("Reviewed app inventory changed")
    source_mods = {n[9:] for n in source_files if n.startswith("app/Mods/")}
    selected_mods = {n[5:] for n in selected if n.startswith("Mods/")}
    if source_mods - selected_mods != omitted or selected_mods - source_mods:
        raise ValueError("Reviewed V7 mod omission set changed")
    for name in reviewed:
        original = source_files.get("app/" + name)
        if original is None or (original != reviewed[name] and name not in RUNTIME):
            raise ValueError("Reviewed payload differs from source V7: " + name)


def admit(profile: Path, payload: Path, contract: Path, *, workspace: Path = ROOT) -> tuple[Package, dict]:
    profile, payload, contract = map(clean_path, (profile, payload, contract))
    manifest_path = profile / "manifest.json"
    manifest_data = checked_read(manifest_path)
    if sha(manifest_data) != SOURCE_MANIFEST_SHA256:
        raise ValueError("Selected V7 source manifest SHA-256 differs from reviewed pin")
    if checked_read(profile / "manifest.sha256").decode("ascii").strip() != SOURCE_MANIFEST_SHA256:
        raise ValueError("V7 manifest hash sidecar mismatch")
    source_files = digest_map(load_json(manifest_path)["files"])
    hashes_path = workspace / "installer/manual/payload.lock.json"
    if sha(checked_read(hashes_path)) != REVIEWED_MANIFEST_SHA256:
        raise ValueError("Reviewed payload manifest differs from audit pin")
    reviewed = digest_map(load_json(hashes_path))
    selected = inventory(payload)
    validate_inventory(selected, reviewed, source_files)
    package = Package()
    privacy = []
    for name in sorted(selected):
        old = source_files.get("app/" + name)
        package.add("app/" + name, path=selected[name], expected=reviewed[name], payload=True)
        if name in RUNTIME:
            original = checked_read(profile / "app" / name)
            current = checked_read(selected[name])
            if sha(original) != old:
                raise ValueError("Original runtime differs from V7 manifest")
            provenance = privacy_provenance(original, current, RUNTIME[name])
            privacy.append({"path": "app/" + name, "v7_sha256": old,
                            "packaged_sha256": reviewed[name], **provenance})
    for name in RESTORE:
        package.add("app/Mods/" + name, path=profile / "app/Mods" / name,
                    expected=source_files["app/Mods/" + name], payload=True)
    for name in ("setup.ps1", "setup.cmd", "launch.cmd", "README.txt"):
        package.add(name, path=workspace / "installer/manual" / name)
    safe_contract = sanitize_contract(load_json(contract), SOURCE_MANIFEST_SHA256, source_files)
    package.add("game-contract.json", data=json_bytes(safe_contract))
    licenses = workspace / "installer/manual/licenses"
    license_manifest = load_json(licenses / "sources.json")
    if not isinstance(license_manifest, dict) or len(license_manifest.get("files", [])) != 12:
        raise ValueError("The recorded license texts and attribution records are required")
    expected_license_names = {"sources.json"}
    for row in license_manifest["files"]:
        name = safe_name(row["file"])
        if "/" in name or name in expected_license_names:
            raise ValueError("Unsafe or duplicate licence source")
        expected_license_names.add(name)
        package.add("licenses/" + name, path=licenses / name, expected=row["sha256"])
        if package.entries["licenses/" + name].size != row["bytes"]:
            raise ValueError("Licence size differs from source record")
    if inventory(licenses).keys() != expected_license_names:
        raise ValueError("Unexpected licence inventory")
    font_records = load_json(licenses / "font-records.json")
    for row in font_records["fonts"]:
        if reviewed.get(row["file"]) != row["sha256"]:
            raise ValueError("Font notice hash differs from bundled font")
    package.add("licenses/sources.json", path=licenses / "sources.json")
    pins = constants(workspace / "dev/engine_source.py", {"UPSTREAM", "COMMIT", "SUBMODULES", "PATCHES"})
    if len(pins["PATCHES"]) != 9 or pins["PATCHES"][-2] != EIGHTH_PATCH:
        raise ValueError("Expected the nine-patch reconstruction chain")
    patches = []
    for name, digest in pins["PATCHES"]:
        safe_name(name)
        member = "source/engine-patches/" + PurePosixPath(name).name
        package.add(member, path=workspace / name, expected=digest)
        patches.append({"path": member, "sha256": digest})
    notice = {"status": "source proof pending", "upstream": {"url": pins["UPSTREAM"], "commit": pins["COMMIT"]},
              "submodules": [{"path": n, "url": u, "commit": c} for n, u, c in pins["SUBMODULES"]],
              "patches": patches, "binary_sha256": {n: reviewed[n] for n in RUNTIME},
              "scope": "Known engine patches and source pins are supplied for inspection. These materials do not establish complete corresponding source, the exact build inputs for the bundled binaries, or reproducible binaries. Dependency source and distribution review remains pending. No public redistribution rights clearance is asserted."}
    package.add("source/ENGINE-SOURCE-NOTICE.json", data=json_bytes(notice))
    package.add("THIRD-PARTY-NOTICES.txt", data=(
        "Paths of Runeterra V7 - third-party notices\n\n"
        "This fan project includes VCMI and third-party dependencies. Preserve app/license.txt, "
        "app/licenses and the regional mod credits. Additional unmodified official licence texts "
        "and their URL/SHA-256 records are in licenses/. FFmpeg's notice identifies applicable "
        "licensing options; including licence texts is not proof of dependency build configuration "
        "or source compliance. Noto Sans and Noto Serif use the SIL Open Font License.\n\n"
        "Heroes III game archives and music are not included. A compatible separately owned "
        "installation is required. League of Legends and Runeterra names and characters belong "
        "to Riot Games; Heroes of Might and Magic belongs to its rights holders. This unofficial "
        "fan project is not endorsed by those rights holders.\n\n"
        "Known modified-engine patches and source pins are in source/. Complete corresponding "
        "source and binary reproduction have not been established; source proof and public "
        "distribution rights review remain pending.\n").encode("utf-8"))
    metadata = {"schema": 1, "build": "Paths of Runeterra V7", "source_manifest_sha256": SOURCE_MANIFEST_SHA256,
                "reviewed_app_files": len(reviewed), "restored_credit_files": len(RESTORE),
                "remaining_v7_mod_omissions": sorted(OMITTED - set(RESTORE)),
                "runtime_privacy_provenance": privacy}
    return package, metadata


def privacy_provenance(original: bytes, current: bytes, expected_count: int) -> dict:
    """Verify only exact private ASCII path strings were replaced, never edit them."""
    if len(original) != len(current):
        raise ValueError("Runtime privacy copy size changed")
    # Entire NUL-terminated paths, rather than arbitrary binary spans, were scrubbed.
    paths = list(re.finditer(rb"(?i)[a-z]:[\\/](?:[^\x00\r\n]*?(?:matcy|runeterra|e2e))[^\x00\r\n]*", original))
    result = bytearray(original)
    count = 0
    for match in paths:
        raw = match.group()
        if PRIVATE.search(raw):
            result[match.start():match.end()] = b"C:\\build" + b"\0" * (len(raw) - len(b"C:\\build"))
            count += 1
    if count != expected_count or bytes(result) != current:
        raise ValueError("Runtime differs beyond reviewed path privacy replacements")
    if PRIVATE.search(current):
        raise ValueError("Private paths remain in runtime")
    return {"method": "ASCII private build paths replaced by C:\\build with NUL padding; all other bytes unchanged",
            "replacement_count": count, "bytes": len(current)}


def output_path(output: Path, inputs: tuple[Path, ...]) -> Path:
    output = clean_path(output)
    if output.suffix.lower() != ".zip":
        raise ValueError("Output must be an explicit new .zip path")
    if os.name == "nt" and (not output.drive or output.drive.startswith("\\\\")):
        raise ValueError("Output must use a writable local drive")
    for source in inputs:
        source = clean_path(source)
        if output == source or output.is_relative_to(source) or source.is_relative_to(output.parent):
            raise ValueError("Output overlaps an input tree")
    for path in (output, output.with_suffix(output.suffix + ".partial"), output.with_suffix(output.suffix + ".SHA256SUMS")):
        direct(path)
        if path.exists():
            raise ValueError("Existing output or companion refused")
    return output


def verify_archive(path: Path, expected: dict[str, Entry]) -> None:
    with zipfile.ZipFile(path, "r") as archive:
        names = archive.namelist()
        if len(names) != len(set(n.casefold() for n in names)) or set(names) != {ARCHIVE_ROOT + n for n in expected}:
            raise ValueError("ZIP inventory differs from admitted package")
        for name, entry in expected.items():
            member = ARCHIVE_ROOT + safe_name(name)
            data = archive.read(member)  # Also verifies each member's CRC.
            if len(data) != entry.size or sha(data) != entry.digest:
                raise ValueError("ZIP member SHA-256 mismatch: " + name)
        manifest = json.loads(archive.read(ARCHIVE_ROOT + "PACKAGE-MANIFEST.json"))
        rows = manifest["files"]
        actual = {n: {"sha256": e.digest, "bytes": e.size} for n, e in expected.items()
                  if n != "PACKAGE-MANIFEST.json"}
        if rows != actual:
            raise ValueError("Embedded package manifest differs from ZIP members")


def write_archive(package: Package, metadata: dict, output: Path) -> dict:
    metadata = dict(metadata)
    metadata["files"] = {n: {"sha256": e.digest, "bytes": e.size} for n, e in sorted(package.entries.items())}
    package.add("PACKAGE-MANIFEST.json", data=json_bytes(metadata))
    output.parent.mkdir(parents=True, exist_ok=True)
    direct(output.parent)
    partial = output.with_suffix(output.suffix + ".partial")
    # Exclusive creation reserves the build output without replacing anything.
    with partial.open("xb") as stream:
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9, allowZip64=True) as archive:
            for name, entry in sorted(package.entries.items()):
                data = entry.read()  # Recheck admission hash immediately before writing.
                member = zipfile.ZipInfo(ARCHIVE_ROOT + name, date_time=(2026, 10, 31, 0, 0, 0))
                member.create_system = 3
                member.external_attr = (stat.S_IFREG | 0o644) << 16
                member.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(member, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        stream.flush()
        os.fsync(stream.fileno())
    verify_archive(partial, package.entries)
    with partial.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    direct(output)
    if output.exists():
        raise ValueError("Output appeared during build; partial retained")
    if os.name == "nt":
        partial.rename(output)  # Windows rename is atomic and refuses existing targets.
    else:
        # Non-Windows test use: exclusive final creation; retain partial by design.
        os.link(partial, output)
    sums = output.with_suffix(output.suffix + ".SHA256SUMS")
    with sums.open("x", encoding="ascii", newline="\n") as stream:
        stream.write(digest + "  " + output.name + "\n")
    return {"archive": output.name, "sha256": digest, "files": len(package.entries),
            "bytes": output.stat().st_size, "verified": True}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, type=Path, help="Original reviewed V7 profile (manifest and credits only)")
    parser.add_argument("--payload", required=True, type=Path, help="Reviewed staged app directory")
    parser.add_argument("--game-contract", required=True, type=Path, help="Reviewed compatibility contract")
    parser.add_argument("--output", required=True, type=Path, help="New ZIP path on a writable local drive")
    args = parser.parse_args(argv)
    try:
        target = output_path(args.output, (args.profile, args.payload, args.game_contract, ROOT / "installer/manual"))
        package, metadata = admit(args.profile, args.payload, args.game_contract)
        print(json.dumps(write_archive(package, metadata, target), indent=2))
    except (ValueError, OSError, KeyError, TypeError, zipfile.BadZipFile) as error:
        print("Manual ZIP build refused: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
