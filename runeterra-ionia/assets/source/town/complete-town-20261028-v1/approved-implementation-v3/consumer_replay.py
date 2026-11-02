"""Replay the unchanged public layout consumer in an owned isolated fixture.

This is a technical evidence runner, not artwork generation or mod admission.
Mutations are authored separately against an exact frozen baseline; source and
generated pixels change together so a physical negative reaches real geometry
rather than merely failing an outdated frame checksum.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PROJECT = next(p for p in HERE.parents if p.name == "runeterra-ionia")
WORKSPACE = PROJECT.parent
sys.path.insert(0, str(WORKSPACE / "scripts"))
import faction_town_layout as layout
import faction_pipeline as fp
import faction_production as production


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def encoded(value) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def direct(root: Path, name: str) -> Path:
    if not isinstance(name, str) or "\\" in name:
        raise ValueError("Expected a direct portable fixture path")
    relative = Path(name)
    if relative.is_absolute() or any(part in ("", ".", "..") for part in relative.parts):
        raise ValueError("Unsafe fixture relative path")
    path = root / relative
    if not path.absolute().is_relative_to(root):
        raise ValueError("Fixture path escapes its verified root")
    current = root
    for part in relative.parts:
        current = current / part
        if current.exists() and (current.is_symlink() or getattr(current.lstat(), "st_file_attributes", 0) & 0x400):
            raise ValueError("Fixture mutation cannot use redirected files")
    return path


def fixture(root: Path) -> Path:
    root = root.absolute()
    if not root.is_relative_to(HERE) or root == HERE:
        raise ValueError("Replay fixture must be strictly within the owned physical subtree")
    current = root
    while current != HERE:
        if current.is_symlink() or getattr(current.lstat(), "st_file_attributes", 0) & 0x400:
            raise ValueError("Redirected physical fixture")
        current = current.parent
    return root


def inventory(root: Path) -> dict[str, str]:
    return {path.relative_to(root).as_posix(): sha(path)
            for path in sorted(root.rglob("*")) if path.is_file()}


def inspect(root: Path):
    content = {"factions": read(direct(root, "content/factions.json"))}
    errors, dependencies = layout.inspect(root, content, "ionia")
    return errors, sorted(dependencies)


def collect(root: Path):
    """Exercise the actual production collector; never create a package/stage."""
    pipeline=fp.Pipeline(root,"runeterra-ionia","ionia")
    declared=layout.dependency_paths(root)
    exported=production._current_town_layout_source_entries(pipeline,{})
    mismatches=[]
    for path in declared:
        member="runeterra-ionia/"+path.relative_to(root).as_posix()
        if exported.get(member)!=path.read_bytes():mismatches.append(member)
    helper=WORKSPACE/"scripts/faction_town_layout.py"
    if exported.get("scripts/faction_town_layout.py")!=helper.read_bytes():mismatches.append("scripts/faction_town_layout.py")
    return{"actual_api":"faction_production._current_town_layout_source_entries",
           "production_collector_sha256":sha(WORKSPACE/"scripts/faction_production.py"),
           "declared_dependency_count":len(declared),"exported_member_count":len(exported),
           "byte_mismatches":mismatches,"declared_dependency_bytes_exported_exactly":not mismatches,
           "scope":"Actual helper-declared contract closure; extra recursively copied authoring JSON references are recorded separately in the fixture inventory. No source package or game stage produced."}


@contextmanager
def changed(root: Path, mapping: dict[str, bytes]):
    """Change only enumerated existing fixture files, then restore exact bytes."""
    paths = {name: direct(root, name) for name in mapping}
    if any(not path.is_file() or path.stat().st_nlink != 1 for path in paths.values()):
        raise ValueError("Fixture mutation needs existing ordinary unaliased owned files")
    before = {name: path.read_bytes() for name, path in paths.items()}
    try:
        for name, value in mapping.items():
            paths[name].write_bytes(value)
        yield
    finally:
        for name, value in before.items():
            paths[name].write_bytes(value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = fixture(args.fixture)
    output = args.out.absolute()
    if not output.is_relative_to(PROJECT / "build/reports/complete-town-20261028-v1"):
        raise ValueError("Evidence output leaves the assigned unique report namespace")
    output.mkdir(parents=True, exist_ok=False)
    before = inventory(root)
    errors, dependencies = inspect(root)
    try:collector=collect(root)
    except(OSError,ValueError,KeyError,TypeError)as error:
        collector={"actual_api":"faction_production._current_town_layout_source_entries","errors":[str(error)],"declared_dependency_bytes_exported_exactly":False}
    result = {
        "status": "authored configuration",
        "consumer": {"path": "scripts/faction_town_layout.py", "sha256": sha(WORKSPACE / "scripts/faction_town_layout.py")},
        "baseline_errors": errors,
        "dependency_count": len(dependencies),
        "dependencies": [{"path": str(path.relative_to(root)), "sha256": sha(path)} for path in dependencies if path.is_file()],
        "actual_public_source_collector":collector,
        "fixture_inventory_before": before,
        "fixture_inventory_after": inventory(root),
        "fixture_unchanged": before == inventory(root),
        "native_town_visual_observed": False,
        "complete_mod_admission_claimed": False,
        "release_accepted": False,
    }
    (output / "receipt.json").write_bytes(encoded(result))
    print(json.dumps({"baseline_errors": errors, "dependency_count": len(dependencies),"source_collector_exact":collector["declared_dependency_bytes_exported_exactly"], "fixture_unchanged": result["fixture_unchanged"]}))
    return 0 if not errors and collector["declared_dependency_bytes_exported_exactly"] and result["fixture_unchanged"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
