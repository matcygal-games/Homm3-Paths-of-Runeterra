"""Snapshot a tested local engine, its source correction and dependency notices."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import zipfile

from build_isolated import PROJECT, TOOLS, SOURCE, BUILD, VS, COMMIT, environment
from patch_series import validate_patch_series


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def tree(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(root.rglob("*")) if p.is_file()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-receipt", type=Path, required=True)
    args = parser.parse_args()
    receipt = args.test_receipt.resolve()
    assert receipt.is_relative_to(PROJECT / "build/reports/engine-shutdown")
    tested = json.loads(receipt.read_text())
    assert tested["phase"] == "test" and tested["exit_code"] == 0 and tested["source_commit"] == COMMIT
    gtest_path = receipt.parent / "gtest.json"
    gtest = json.loads(gtest_path.read_text())
    assert gtest["tests"] > 0 and gtest["failures"] == 0 and gtest["disabled"] == 0 and gtest["errors"] == 0
    stamp = str(time.time_ns())
    report = PROJECT / "build/reports/engine-shutdown" / ("handoff-" + stamp)
    report.mkdir(parents=True)
    series, patch_hash = validate_patch_series(report)
    assert tested["source_diff_sha256"] == patch_hash, "Source differs from native-tested source"
    for name, expected in tested["tested_binaries_sha256"].items():
        assert sha(BUILD / "bin" / name) == expected, "Binary differs from native-tested binary: " + name
    target = TOOLS / ("custom-runtime-" + patch_hash[:12] + "-" + stamp)
    app = target / "app"
    app.mkdir(parents=True)
    env = environment()
    excluded_top = {"data", "test", "logs", "cache", "saves"}
    copied_inputs = {}
    for path in sorted((BUILD / "bin").rglob("*")):
        relative = path.relative_to(BUILD / "bin")
        if not path.is_file() or relative.parts[0].lower() in excluded_top:
            continue
        if relative.as_posix() == "config/dirs.json" or path.suffix.lower() in (".pdb", ".lib", ".exp", ".ilk", ".log"):
            continue
        if path.suffix.lower() == ".exe" and path.name.lower() not in ("vcmi_client.exe", "vcmi_server.exe"):
            continue
        destination = app / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        assert sha(path) == sha(destination)
        copied_inputs[relative.as_posix()] = {"source": str(path), "sha256": sha(path)}
    for name in ("VCMI_client.exe", "VCMI_server.exe", "VCMI_lib.dll"):
        assert (app / name).is_file(), name
    for name in ("config", "scripts", "Mods/vcmi"):
        assert any(p.is_file() for p in (app / name).rglob("*")), name

    for name in (TOOLS / "conan-generated/_runtime_libs.txt").read_text().splitlines():
        dependency = Path(name)
        if not name:
            continue
        assert dependency.is_relative_to(TOOLS / "conan-home") and dependency.is_file()
        destination = app / dependency.name
        if destination.is_file():
            assert sha(destination) == sha(dependency), "Conflicting DLL producers: " + dependency.name
        else:
            shutil.copy2(dependency, destination)
        copied_inputs[dependency.name] = {"source": str(dependency), "sha256": sha(dependency)}

    # The standard CMake installation lists these redistributable CRT DLLs.
    redist = VS / "VC/Redist/MSVC/14.51.36231/x64/Microsoft.VC145.CRT"
    for path in sorted(redist.glob("*.dll")):
        shutil.copy2(path, app / path.name)
        copied_inputs[path.name] = {"source": str(path), "sha256": sha(path)}

    licenses = app / "licenses"
    licenses.mkdir()
    shutil.copy2(SOURCE / "license.txt", licenses / "VCMI-GPL-2.0.txt")
    shutil.copy2(SOURCE / "AUTHORS.h", licenses / "VCMI-AUTHORS.h")
    for name in ("Redist.txt", "ThirdPartyNotices.txt"):
        shutil.copy2(VS / "Licenses/1033" / name, licenses / ("Microsoft-" + name))

    graph_path = PROJECT / "build/reports/engine-shutdown/conan-graph.json"
    graph = json.loads(graph_path.read_text())
    nodes = [v for v in graph["graph"]["nodes"].values() if v.get("ref") and v.get("context") == "host"]

    def collect(node):
        row = {key: node.get(key) for key in ("ref", "package_id", "prev", "license", "homepage", "url", "settings", "options", "binary")}
        row["source"] = node.get("conandata", {}).get("sources", {}).get(node.get("version"))
        row["source_patches"] = node.get("conandata", {}).get("patches", {}).get(node.get("version"))
        row["license_files"] = {}
        if node.get("prev") and node.get("binary") == "Cache":
            reference = node["ref"] + ":" + node["package_id"] + "#" + node["prev"]
            command = [str(TOOLS / "venv/Scripts/conan.exe"), "cache", "path", reference]
            package_folder = Path(subprocess.check_output(command, text=True, env=env).strip())
            assert package_folder.is_relative_to(TOOLS / "conan-home")
            row["package_folder"] = str(package_folder)
            label = re.sub(r"[^A-Za-z0-9_.-]", "_", node["ref"].split("#")[0])
            source_licenses = package_folder / "licenses"
            if source_licenses.is_dir():
                for path in sorted(source_licenses.rglob("*")):
                    if not path.is_file():
                        continue
                    relative = path.relative_to(source_licenses)
                    destination = licenses / label / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, destination)
                    row["license_files"][relative.as_posix()] = sha(path)
        return row

    with ThreadPoolExecutor(max_workers=2) as executor:
        dependencies = list(executor.map(collect, nodes))
    missing_notices = [row["ref"] for row in dependencies if row.get("binary") == "Cache" and not row["license_files"]]
    write_json(report / "dependency-provenance.json", {"conan_graph_sha256": sha(graph_path), "nodes": dependencies,
        "scope": "resolved upstream host dependency graph; includes packages not linked by the disabled launcher/editor",
        "missing_package_license_files": missing_notices})

    source_zip = target / ("vcmi-725ae80-patched-source-" + patch_hash[:12] + ".zip")
    exported = {}
    for prefix, repository in (("", SOURCE), ("dependencies/", SOURCE / "dependencies"), ("test/googletest/", SOURCE / "test/googletest")):
        names = subprocess.check_output(["git", "ls-files", "-z"], cwd=repository).decode().split("\0")
        for name in names:
            if not name or not (repository / name).is_file():
                continue
            exported["vcmi/" + prefix + name] = repository / name
    for path in sorted((PROJECT / "engine-patches").rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            exported["local-correction/" + path.relative_to(PROJECT / "engine-patches").as_posix()] = path
    exported["local-correction/requirements-tools.lock.txt"] = TOOLS / "requirements-tools.lock.txt"
    exported["local-correction/conan-graph.json"] = graph_path
    exported["local-correction/dependency-provenance.json"] = report / "dependency-provenance.json"
    source_manifest = {name: sha(path) for name, path in sorted(exported.items())}
    with zipfile.ZipFile(source_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, path in sorted(exported.items()):
            archive.write(path, name)
        archive.writestr("SOURCE-FILES-SHA256.json", json.dumps(source_manifest, indent=2, sort_keys=True) + "\n")
    with zipfile.ZipFile(source_zip) as archive:
        assert archive.testzip() is None
        for name, expected in source_manifest.items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == expected

    obligations = (
        "LOCAL MODIFIED ENGINE CANDIDATE. No installation or release acceptance.\n"
        "VCMI is GPL-2.0-or-later; its upstream license and authors are included.\n"
        "The separate adjacent source ZIP contains the exact patched VCMI source, enabled source submodules, correction, build helper and dependency graph.\n"
        "Disabled Discord/innoextract submodules are not compiled or included; their pinned git links remain in the upstream source.\n"
        "Dependency binaries came from the checksummed official VCMI Conan archive. Their package notices are included where provided.\n"
        "Source URLs/checksums/recipe revisions and package license identifiers are recorded in dependency-provenance.json.\n"
        "This local handoff is not a completed redistribution/source-offer review for every third-party or Microsoft component.\n"
        "Before external distribution, review each included license, supply required corresponding dependency sources/notices and satisfy applicable Microsoft redistributable terms.\n"
        "Original Heroes III data and Riot illustrations are excluded.\n"
        "The version string retains upstream commit identity; only binary hashes plus the patch checksum identify this modified candidate.\n"
    )
    (app / "LOCAL-BUILD-NOTICE.txt").write_text(obligations, encoding="utf-8")
    shutil.copy2(report / "dependency-provenance.json", app / "dependency-provenance.json")
    provenance = {"scope": "locally patched engine candidate; no mod stage, install or release acceptance",
                  "official_build": False, "source_commit": COMMIT, "patch_sha256": patch_hash,
                  "patch_sha256_scope": "canonical combined git diff of the ordered patch series",
                  "patch_series": series["patches"],
                  "source_zip": source_zip.name, "source_zip_sha256": sha(source_zip),
                  "dependency_archive": json.loads((TOOLS / "dependency-download.json").read_text()),
                  "native_tests_receipt": str(receipt), "native_tests_receipt_sha256": sha(receipt),
                  "gtest_tests": gtest["tests"], "gtest_failures": gtest["failures"],
                  "dependency_provenance_sha256": sha(report / "dependency-provenance.json"),
                  "third_party_redistribution_review_complete": False}
    write_json(app / "local-build-provenance.json", provenance)
    inventory = tree(app)
    write_json(report / "runtime-files-sha256.json", inventory)
    write_json(report / "copied-inputs.json", copied_inputs)
    binaries = {name: value for name, value in inventory.items() if Path(name).suffix.lower() in (".exe", ".dll")}
    write_json(report / "binaries-sha256.json", binaries)
    write_json(report / "source-files-sha256.json", source_manifest)
    compiler = VS / "VC/Tools/MSVC/14.51.36231/bin/Hostx64/x64/cl.exe"
    compiler_result = subprocess.run([str(compiler), "/Bv", "/?"], env=env, capture_output=True)
    (report / "compiler-version.log").write_bytes(compiler_result.stdout + compiler_result.stderr)
    result = {**provenance, "app": str(app), "source_zip_path": str(source_zip),
              "runtime_file_count": len(inventory), "binary_count": len(binaries),
              "runtime_inventory_sha256": sha(report / "runtime-files-sha256.json"),
              "compiler_path": str(compiler), "compiler_sha256": sha(compiler),
              "compiler_version_exit_code": compiler_result.returncode,
              "compiler_version_log_sha256": sha(report / "compiler-version.log"),
              "missing_dependency_notice_files": missing_notices,
              "runtime_selected": False, "originals_bundled": False}
    write_json(report / "result.json", result)
    print(json.dumps(result, indent=2))
    print(report)


if __name__ == "__main__":
    main()
