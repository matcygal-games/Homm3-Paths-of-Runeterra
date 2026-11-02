"""Seal already executed source/binary evidence; no engine/game commands."""
from pathlib import Path
import ast
import hashlib
import importlib.util
import json
import sys
import time

W = Path(__file__).resolve().parents[3]
R = Path(__file__).resolve().parent
REPORTS = W / "runeterra-bandlecity/build/reports/engine-ai-lifecycle"

def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

def inventory(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(root.rglob("*")) if p.is_file()}

def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")

def main():
    output = REPORTS / f"handoff-{time.time_ns()}"
    output.mkdir()
    ids = {
        "original_consumer_red": "test-1792679808463508700",
        "targeted_green": "test-1792680406116474000",
        "broader_green": "test-1792680334133395100",
        "full_build": "build-1792679951324726500",
    }
    records = {k: json.loads((REPORTS / v / "result.json").read_text()) for k, v in ids.items()}
    source = inventory(R / "src")
    assert source == inventory(R / "src-reproduced-final")
    assert all(source == records[k]["source_hashes"] for k in ("targeted_green", "broader_green", "full_build"))
    assert len(source) == 4074
    changes = json.loads((R / "changes.json").read_text())
    differences = sorted(k for k in source if source[k] != records["original_consumer_red"]["source_hashes"][k])
    assert differences == sorted(k for k in changes if not k.startswith("test/"))
    for relative, pins in changes.items():
        assert sha(R / "overlay" / relative) == pins["after_sha256"] == source[relative]
    source_signature = hashlib.sha256(json.dumps(source, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    audit = json.loads((W / "runeterra-bandlecity/build/reports/integration-review/runtime-candidate-v1.json").read_text())
    baseline = Path(audit["app"])
    assert inventory(baseline) == audit["production_inventory"]["files"]
    assert len(audit["production_inventory"]["files"]) == 928
    app = R / "b/bin"
    binaries = {p.relative_to(app).as_posix(): sha(p) for p in sorted(app.rglob("*"))
                if p.is_file() and p.suffix.lower() in (".dll", ".exe") and p.name.lower() != "vcmitest.exe"}
    baseline_binaries = {k: v for k, v in audit["production_inventory"]["files"].items()
                         if Path(k).suffix.lower() in (".dll", ".exe")}
    assert set(binaries) == set(baseline_binaries)
    delta = [{"path": k, "sha256": v, "bytes": (app / k).stat().st_size, "baseline_sha256": baseline_binaries[k]}
             for k, v in binaries.items() if v != baseline_binaries[k]]
    assert {x["path"] for x in delta} == {"VCMI_client.exe", "VCMI_server.exe", "VCMI_lib.dll"}
    assert all(records[k]["binaries_sha256"][p] == h for k in ("targeted_green", "broader_green", "full_build")
               for p, h in binaries.items())

    ninja = (R / "b/build.ninja").read_text().replace("\\", "/")
    lines = ninja.splitlines()
    core = next(x for x in lines if x.startswith("build bin/VCMI_lib.dll "))
    server = next(x for x in lines if x.startswith("build bin/VCMI_server.exe:"))
    archive = next(x for x in lines if x.startswith("build bin/VCMI_vcmiservercommon.lib:"))
    ai_objects = ["AI/Nullkiller2/CMakeFiles/Nullkiller2.dir/AIGateway.cpp.obj",
                  "AI/Nullkiller2/CMakeFiles/Nullkiller2.dir/Engine/Nullkiller.cpp.obj",
                  "AI/Nullkiller2/CMakeFiles/Nullkiller2.dir/Goals/ExecuteHeroChain.cpp.obj"]
    server_objects = ["server/CMakeFiles/vcmiservercommon.dir/CGameHandler.cpp.obj",
                      "server/CMakeFiles/vcmiservercommon.dir/NetPacksServer.cpp.obj"]
    assert all(p in core for p in ai_objects)
    assert all(p in archive for p in server_objects)
    assert "bin/VCMI_vcmiservercommon.lib" in server
    proof = {"ninja_sha256": sha(R / "b/build.ninja"),
             "game_used_ai": "Nullkiller2 OBJECT library is bundled into VCMI_lib.dll; no separate AI DLL",
             "core_link_rule": core, "server_archive_rule": archive, "server_link_rule": server,
             "objects": {p: sha(R / "b" / p) for p in ai_objects + server_objects},
             "server_archive_sha256": sha(app / "VCMI_vcmiservercommon.lib"),
             "facade_cmake_sha256": sha(R / "src/libFacade/CMakeLists.txt"),
             "nullkiller_cmake_sha256": sha(R / "src/AI/Nullkiller2/CMakeLists.txt")}
    write(output / "link-proof.json", proof)
    runtime = {"schema": 1, "status": "authored configuration", "baseline_app": baseline.relative_to(W).as_posix(),
               "baseline_file_count": 928, "baseline_production_signature": audit["runtime_signature"],
               "baseline_all_files_reverified": True, "own_build_bin": app.relative_to(W).as_posix(),
               "runtime_pe_inventory": binaries, "binary_delta": delta, "additional_dependency_delta": [],
               "runtime_configuration_changes_required": [],
               "metadata_requirement": "Coordinator updates LOCAL-BUILD-NOTICE for fourth patch and owns any private probe dirs.json separately from required three binary delta.",
               "copy_policy": "Copy audited928-file baseline to new owned app, overlay only three named binaries, update build notice/private probe metadata, seal complete inventory. Never copy entire own b/bin, Data, user/cache/test/config resources.",
               "link_proof_sha256": sha(output / "link-proof.json"),
               "native_gameplay_executed": False, "runtime_selection_changed": False}
    write(output / "runtime-overlay.json", runtime)
    receipts = {}
    failed_cases = []
    for key, folder in ids.items():
        directory = REPORTS / folder
        row = {"directory": directory.relative_to(W).as_posix(), "result_sha256": sha(directory / "result.json"),
               "output_sha256": sha(directory / "output.log"), "exit_code": records[key]["exit_code"]}
        if (directory / "gtest.json").exists():
            result = json.loads((directory / "gtest.json").read_text())
            row.update({k: result[k] for k in ("tests", "failures", "errors")})
            row["gtest_sha256"] = sha(directory / "gtest.json")
            if key == "original_consumer_red":
                failed_cases = [suite["name"] + "." + case["name"] for suite in result["testsuites"]
                                for case in suite["testsuite"] if case.get("failures")]
        receipts[key] = row
    spec = importlib.util.spec_from_file_location("own_builder", R / "build_candidate.py")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    environment = builder.environment()
    for script in ("build_candidate.py", "prepare_source.py"):
        ast.parse((R / script).read_text())
    series = json.loads((W / "runeterra-freljord/engine-patches/patch-series.json").read_text())
    provenance = {"schema": 1, "status": "authored configuration", "locally_modified_engine": True,
                  "release_accepted": False, "native_gameplay_executed": False,
                  "baseline_source_zip": "vcmi-725ae80-patched-source-a168a7b34aef.zip",
                  "baseline_source_zip_sha256": "ecf04d296dcd02fc26219eae26749165fb2890022e4ae7454beb032945751346",
                  "baseline_commit": audit["source_commit"],
                  "baseline_existing_combined_diff_sha256": audit["canonical_combined_diff_sha256"],
                  "baseline_ordered_patches": series["patches"],
                  "incremental_patch_sha256": sha(R / "0004-ai-turn-lifecycle.patch"),
                  "changes_sha256": sha(R / "changes.json"), "source_file_count": 4074,
                  "source_inventory_sha256": source_signature,
                  "exact_reproduction_matches_build_and_both_green_receipts": True,
                  "original_consumer_red_diff_exactly_these8_production_files": differences,
                  "identical_native_fixtures_between_red_and_green": True, "red_failed_cases": failed_cases,
                  "receipts": receipts, "runtime_pe_inventory": binaries, "runtime_binary_delta": delta,
                  "additional_dependency_delta": [], "runtime_configuration_changes_required": [],
                  "runtime_baseline_signature": audit["runtime_signature"],
                  "runtime_handoff_report": (output / "runtime-overlay.json").relative_to(W).as_posix(),
                  "runtime_handoff_sha256": sha(output / "runtime-overlay.json"),
                  "link_proof_report": (output / "link-proof.json").relative_to(W).as_posix(),
                  "link_proof_sha256": sha(output / "link-proof.json"),
                  "toolchain": {"python": sys.version, "msvc": environment.get("VCToolsVersion"),
                                "windows_sdk": environment.get("WindowsSDKVersion"),
                                "msvc_cl_sha256": sha(builder.VS / "VC/Tools/MSVC/14.51.36231/bin/Hostx64/x64/cl.exe"),
                                "cmake_sha256": sha(builder.CMAKE), "ninja_sha256": sha(builder.NINJA),
                                "external_conan_tree": "runeterra-freljord/.tools/engine-shutdown-fix/conan-home",
                                "conan_toolchain_sha256": sha(builder.DEPS / "conan-generated/conan_toolchain.cmake"),
                                "conan_runtime_list_sha256": sha(builder.DEPS / "conan-generated/_runtime_libs.txt"),
                                "requirements_tools_lock_sha256": sha(W / "runeterra-freljord/engine-patches/requirements-tools.lock.txt"),
                                "build_flags": "Release;2/4jobs;SDL3 ON;launcher/editor/MMAI/LTO/ccache/GITVERSION/COPY_CONFIG_ON_BUILD OFF"},
                  "determinism_and_compatibility": {"new_serialized_or_network_fields": False,
                                                   "save_or_protocol_version_change": False, "rng_api_changes": False,
                                                   "bit_identical_asynchronous_outcomes_asserted": False,
                                                   "save_load_execution_performed": False,
                                                   "day_guard_proof": "acting->acted, authoritative NewTurn(day+1), then acted->awaiting; one normal turn/player/day. Load-resume uses new interface/session. GSshared blocks day mutation between guard/send; carried day catches delayed callback."},
                  "source_payload_excludes": ["src/", "src-reproduced*/", "b/", "licensed Data", "private user/config/cache", "executables/DLL/PDB", "dependency caches", "source ZIP"],
                  "remaining": ["independent final complete candidate metadata audit", "coordinator runtime selection", "fresh exact-stage gameplay by sole operator", "ordinary lost-hero/unrelated AI diagnostics", "external human and rights acceptance"]}
    write(R / "provenance.json", provenance)
    files = ["README.md", "0004-ai-turn-lifecycle.patch", "changes.json", "prepare_source.py", "build_candidate.py",
             "capture_msvc_environment.cmd", "provenance.json"] + ["overlay/" + p for p in sorted(changes)]
    assert len(files) == 21
    write(R / "source-export-files.json", {"schema": 2, "scope": "Compact reviewed source only; full source copies/builds/private data/binaries excluded.",
                                           "files": [{"path": p, "sha256": sha(R / p)} for p in files]})
    freeze = {"schema": 1, "status": "authored configuration", "source_inventory_sha256": source_signature,
              "source_file_count": 4074, "source_export_manifest_sha256": sha(R / "source-export-files.json"),
              "provenance_sha256": sha(R / "provenance.json"), "patch_sha256": sha(R / "0004-ai-turn-lifecycle.patch"),
              "receipts": receipts, "binary_delta": delta, "runtime_pe_file_count": len(binaries),
              "baseline_file_count": 928, "all_original_baseline_files_reverified": True,
              "game_used_AI": proof["game_used_ai"], "runtime_report_sha256": sha(output / "runtime-overlay.json"),
              "link_proof_sha256": sha(output / "link-proof.json"),
              "ownership": "Only own new engine-patch/report paths written; no protected input, production/stage/shared edits, game launch or runtime selection by this worker."}
    write(output / "freeze.json", freeze)
    print(output)
    print(json.dumps({k: freeze[k] for k in ("source_inventory_sha256", "source_export_manifest_sha256", "provenance_sha256", "patch_sha256", "binary_delta")}, indent=2))

if __name__ == "__main__":
    main()
