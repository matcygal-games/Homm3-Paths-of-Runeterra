"""Reconstruct patched VCMI source from pinned public upstream repositories.

This prepares editable source only. It never builds or launches the game, reads
licensed game data, or claims to reproduce an existing runtime binary.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys


ROOT = Path(__file__).absolute().parents[1]
UPSTREAM = "https://github.com/vcmi/vcmi.git"
COMMIT = "725ae80c42929ebbf6ccd620b38bd45ac32644c2"
SUBMODULES = (
    ("dependencies", "https://github.com/vcmi/vcmi-dependencies.git", "68f3f22614a3b17c80aa603b0c013181db845048"),
    ("test/googletest", "https://github.com/google/googletest", "b514bdc898e2951020cbdca1304b75f5950d1f59"),
)
PATCHES = (
    ("runeterra-freljord/engine-patches/0001-track-requested-connection-closures.patch", "fda36a1cf4aa5742de3f6a108610cea2ac16996c5226bb0a8685979c6c99395a"),
    ("runeterra-freljord/engine-patches/0002-stop-unoccupiable-escapes-and-exhausted-chains.patch", "9410fb047a1c102f8397b180933918186cf192796a2c93a39c584899fdb8fbad"),
    ("runeterra-freljord/engine-patches/0003-keep-local-games-off-lan-listeners.patch", "3f894f73627b92435a2abc6dea3ba54d31ae8331f3a99ae772d3a6b32bade212"),
    ("runeterra-bandlecity/engine-patches/ai-turn-lifecycle/0004-ai-turn-lifecycle.patch", "2cc42f37d47c6c688eaa1b0e270dae04e08e4a5641d47dca1359829bcc56eb3a"),
    ("runeterra-bandlecity/engine-patches/hero-loss-replanning/0005-hero-loss-replanning.patch", "8d68b29eb585e1078f0a5f4d9a11c3364566754d46ed4f2268a64df0c131cb21"),
    ("runeterra-bandlecity/engine-patches/creature-previews/0006-creature-preview-animation.patch", "de16af95207cde32efd1188ce536f4cf65a694fe55d17ce37c4e952c3e8e0b10"),
    ("runeterra-bandlecity/engine-patches/creature-previews/0007-preview-legacy-crop.patch", "2183f1d264b3faf838f9d9087cc3a818ee4551a5c9b0869ffc9faf012cbd5b0a"),
    ("installer/manual/engine-patches/0008-invalidate-cached-task-batch.patch", "35d79532d92e8fcc53e4bcdc4453ccce1ee8ee30b09a55d0c1abb02c28440a05"),
    ("installer/manual/engine-patches/0009-preserve-hero-last-stack.patch", "8a5873618348d90ad311e98395ee42ffe9409a9497c28eb92b40368a48fc6658"),
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _direct(path: Path) -> None:
    for component in reversed((path, *path.parents)):
        try:
            info = component.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("Linked source/output component refused: " + str(component))
        if stat.S_ISREG(info.st_mode) and info.st_nlink != 1:
            raise ValueError("Hardlinked source file refused: " + str(component))


def destination(workspace: Path, output: Path) -> Path:
    workspace = workspace.absolute()
    output = output if output.is_absolute() else workspace / output
    # Check spelling before Path.resolve could hide aliases or traversal.
    if ".." in output.parts or any(part.endswith((" ", ".")) for part in output.parts):
        raise ValueError("Ambiguous output path refused")
    output = output.absolute()
    try:
        relative = output.relative_to(workspace)
    except ValueError as error:
        raise ValueError("Output must be a new child of local build storage") from error
    if len(relative.parts) < 2 or relative.parts[0] not in ("build", "matt_dev"):
        raise ValueError("Output must be a new child of local build storage")
    _direct(output)
    if output.exists():
        raise ValueError("Existing output refused: " + str(output))
    return output


def _patch_paths(data: bytes) -> tuple[str, ...]:
    result = set()
    for line in data.splitlines():
        if not line.startswith((b"--- ", b"+++ ")):
            continue
        raw = line[4:].split(b"\t", 1)[0]
        if raw == b"/dev/null":
            continue
        if not raw.startswith((b"a/", b"b/")):
            raise ValueError("Patch must use literal a/ and b/ paths")
        name = raw[2:].decode("utf-8", errors="strict")
        path = PurePosixPath(name)
        if (not name or path.is_absolute() or "\\" in name
                or any(part in ("", ".", "..", ".git") or part.endswith((" ", "."))
                       or re.search(r'[:*?<>|\"]', part) for part in name.split("/"))):
            raise ValueError("Unsafe patch path: " + name)
        result.add(name)
    if not result or b"new file mode 120000" in data:
        raise ValueError("Empty or linked patch refused")
    return tuple(sorted(result))


def checked_patches(workspace: Path) -> tuple[tuple[str, bytes, tuple[str, ...]], ...]:
    rows = []
    for name, expected in PATCHES:
        path = workspace / name
        _direct(path)
        data = path.read_bytes()
        if sha(data) != expected:
            raise ValueError("Patch hash mismatch: " + name)
        # Review diffs contain both CRLF and LF context. Public upstream is
        # checked out with LF; normalize only this disposable application copy.
        canonical = data.replace(b"\r\n", b"\n")
        rows.append((name, canonical, _patch_paths(canonical)))
    return tuple(rows)


def git_environment() -> dict[str, str]:
    # Keep caller Git worktree/config/filters/hooks from redirecting this owned
    # reconstruction. No global configuration or credential files are changed.
    env = {key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
               GIT_TERMINAL_PROMPT="0", GIT_PAGER="cat")
    return env


def git(arguments: list[str], cwd: Path, data: bytes | None = None) -> bytes:
    command = ["git", "-c", "core.autocrlf=false", "-c", "core.hooksPath=",
               "-c", "core.attributesFile=", "-c", "init.templateDir=",
               "-c", "protocol.file.allow=never", *arguments]
    result = subprocess.run(command, cwd=cwd, env=git_environment(), input=data,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=600)
    if result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace")[-3000:]
        raise RuntimeError("Git source preparation failed: " + detail.strip())
    return result.stdout


def apply_patch(source: Path, data: bytes) -> tuple[str, ...]:
    paths = _patch_paths(data)
    for name in paths:
        _direct(source / name)
    git(["apply", "--check", "--whitespace=nowarn", "-"], source, data)
    git(["apply", "--whitespace=nowarn", "-"], source, data)
    return paths


def reconstruct(output: Path, *, workspace: Path = ROOT) -> dict:
    workspace = workspace.absolute()
    target = destination(workspace, output)
    patches = checked_patches(workspace)  # Fail before creating/fetching anything.
    target.mkdir(parents=True)
    state = target / "PATHS-SOURCE-INCOMPLETE.json"
    state.write_text(json.dumps({"scope": "source reconstruction only", "complete": False}) + "\n", encoding="utf-8")
    git(["init", "--quiet"], target)
    git(["fetch", "--depth=1", UPSTREAM, COMMIT], target)
    git(["checkout", "--quiet", "--detach", "FETCH_HEAD"], target)
    if git(["rev-parse", "HEAD"], target).decode().strip() != COMMIT:
        raise ValueError("Upstream commit differs from pinned source")
    for name, url, commit in SUBMODULES:
        configured = git(["config", "--file", ".gitmodules", "--get", "submodule." + name + ".url"], target).decode().strip()
        if configured != url:
            raise ValueError("Upstream submodule URL differs from pinned source: " + name)
        entry = git(["ls-tree", "HEAD", "--", name], target).decode().split()
        if len(entry) < 3 or entry[0] != "160000" or entry[2] != commit:
            raise ValueError("Upstream submodule commit differs: " + name)
    git(["submodule", "update", "--init", "--depth=1", "--", *(row[0] for row in SUBMODULES)], target)
    for name, _url, commit in SUBMODULES:
        if git(["rev-parse", "HEAD"], target / name).decode().strip() != commit:
            raise ValueError("Fetched submodule commit differs: " + name)
    patch_records = []
    for name, data, _paths in patches:
        print("Applying " + Path(name).name, flush=True)
        touched = apply_patch(target, data)
        patch_records.append({"path": name, "sha256": dict(PATCHES)[name],
                              "lf_application_sha256": sha(data), "changed_paths": list(touched)})
    license_file = target / "license.txt"
    _direct(license_file)
    if b"GNU GENERAL PUBLIC LICENSE" not in license_file.read_bytes():
        raise ValueError("Upstream GPL notice missing")
    changed = sorted({name for item in patch_records for name in item["changed_paths"]})
    record = {"schema": 1, "status": "authored configuration", "complete": True,
              "scope": "editable source reconstruction; no compiler, tests, game or binary reproduction",
              "upstream": {"url": UPSTREAM, "commit": COMMIT},
              "submodules": [{"path": name, "url": url, "commit": commit} for name, url, commit in SUBMODULES],
              "line_endings": "LF checkout and normalized patch application; historical CRLF archives unchanged",
              "patches": patch_records, "upstream_license_sha256": sha(license_file.read_bytes()),
              "changed_source_sha256": {name: sha((target / name).read_bytes()) for name in changed}}
    (target / "PATHS-SOURCE.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    state.unlink()
    return record


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("build/engine-source"), help="new directory under build/")
    args = parser.parse_args(argv)
    try:
        record = reconstruct(args.output)
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(str(error), file=sys.stderr)
        return 2
    print("Prepared pinned public source with " + str(len(record["patches"])) + " patches; no build or game launched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
