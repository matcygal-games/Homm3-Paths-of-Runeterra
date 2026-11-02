"""Checked entry to separately supplied maintainer scripts.

Importing this public module needs no private authoring archive. Script names are
relative to the workspace's logical scripts directory, including in source bundles
that still supply an ordinary public scripts directory.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path
import re
import stat
import sys

ROOT = Path(__file__).absolute().parents[1]


def _direct(path):
    for component in reversed((path, *path.parents)):
        try:
            info = component.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("Authoring path traverses a symlink/reparse component: " + str(component))
        if stat.S_ISREG(info.st_mode) and info.st_nlink != 1:
            raise ValueError("Hardlinked authoring source refused: " + str(component))


def _identity(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_nlink)


def load_layout(*, root=ROOT):
    """Checked-load the optional bridge and activate its narrow import hook."""
    root = Path(root)
    if ".." in root.parts or (root.drive and not root.is_absolute()):
        raise ValueError("Authoring workspace must be a direct non-traversing path")
    root = root.absolute()
    logical = root / "scripts" / "authoring_layout.py"
    public = logical.parent
    _direct(public)
    physical = logical if public.exists() else root / "matt_dev" / "scripts" / logical.name
    _direct(physical)
    if not physical.is_file():
        raise FileNotFoundError("Required maintainer authoring bridge is missing: " + str(logical)
                                + "; supply the separate maintainer authoring tools")
    before = physical.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise ValueError("Authoring bridge must be a direct regular file")
    with physical.open("rb") as source:
        opened = os.fstat(source.fileno())
        if _identity(opened) != _identity(before):
            raise ValueError("Authoring bridge changed before its owned handle opened")
        data = source.read()
        after_handle = os.fstat(source.fileno())
        after = physical.lstat()
        _direct(physical)
        selected = logical if public.exists() else root / "matt_dev" / "scripts" / logical.name
        if (_identity(after_handle) != _identity(opened)
                or after_handle.st_ctime_ns != opened.st_ctime_ns
                or _identity(after) != _identity(opened)
                or after.st_ctime_ns != before.st_ctime_ns
                or len(data) != opened.st_size or selected != physical):
            raise ValueError("Authoring bridge changed while reading its owned handle")
    spec = importlib.util.spec_from_loader("_dev_checked_authoring_layout", loader=None,
                                          origin=str(logical))
    module = importlib.util.module_from_spec(spec)
    module.__file__ = str(logical)
    exec(compile(data, str(logical), "exec"), module.__dict__)
    module._LAYOUT_MODULE = module
    return module


def _name(name):
    raw = os.fspath(name)
    if not isinstance(raw, str) or not raw or "\\" in raw:
        raise ValueError("Authoring script requires a normalized relative name")
    for part in raw.split("/"):
        if (not part or part in (".", "..") or part.endswith((".", " "))
                or any(ord(c) < 32 or c in '<>:"|?*' for c in part)
                or re.fullmatch(r"(?i)(con|prn|aux|nul|clock\$|conin\$|conout\$|com[1-9]|lpt[1-9])(?:\..*)?", part)):
            raise ValueError("Unsafe authoring script name: " + raw)
    return raw


def script_path(name, *, root=ROOT):
    """Return the checked logical Python script path; missing sources fail closed."""
    logical = Path(root).absolute() / "scripts" / _name(name)
    return Path(load_layout(root=root).script_spec("__main__", logical).origin)


def script_command(name, *args, root=ROOT):
    """Build a checked child command for one workspace script-relative name."""
    logical = Path(root).absolute() / "scripts" / _name(name)
    return load_layout(root=root).script_command(logical, *args)


def run_script(name, args=(), *, root=ROOT):
    """Execute one checked workspace script with its original logical __file__."""
    logical = Path(root).absolute() / "scripts" / _name(name)
    return load_layout(root=root).run_script(logical, args)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("script", help="logical script-relative Python name, e.g. runeterra.py")
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    try:
        run_script(args.script, args.arguments)
    except (FileNotFoundError, ValueError) as error:
        parser.exit(2, str(error) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
