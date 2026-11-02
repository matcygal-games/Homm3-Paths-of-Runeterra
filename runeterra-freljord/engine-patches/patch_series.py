"""Verify that an ordered patch series accounts for every compiled source change."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess

from build_isolated import PROJECT, SOURCE, COMMIT


def validate_patch_series(report: Path):
    manifest = json.loads((PROJECT / "engine-patches/patch-series.json").read_text())
    assert manifest["base_commit"] == COMMIT
    env = dict(os.environ)
    env["GIT_INDEX_FILE"] = str((report / "patch-series.index").resolve())
    assert not Path(env["GIT_INDEX_FILE"]).exists()
    subprocess.run(["git", "read-tree", "HEAD"], cwd=SOURCE, env=env, check=True)
    for entry in manifest["patches"]:
        name = entry["file"]
        assert Path(name).name == name and name.endswith(".patch")
        patch = PROJECT / "engine-patches" / name
        assert hashlib.sha256(patch.read_bytes()).hexdigest() == entry["sha256"]
        subprocess.run(["git", "apply", "--cached", str(patch)], cwd=SOURCE, env=env, check=True)
    expected = subprocess.check_output(["git", "diff", "--cached", "--binary", "HEAD"], cwd=SOURCE, env=env)
    actual = subprocess.check_output(["git", "diff", "--binary", "HEAD"], cwd=SOURCE)
    assert actual == expected, "Ordered patches differ from the compiled source tree"
    subprocess.run(["git", "diff", "--check"], cwd=SOURCE, check=True)
    (report / "combined-source.patch").write_bytes(expected)
    return manifest, hashlib.sha256(expected).hexdigest()
