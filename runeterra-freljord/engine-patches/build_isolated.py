"""Build only the separately provisioned, pinned VCMI shutdown candidate.

No installed runtime, game, mod stage or checked-out reference source is modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

PROJECT = Path(__file__).resolve().parents[1]
TOOLS = PROJECT / ".tools" / "engine-shutdown-fix"
SOURCE = TOOLS / "source"
BUILD = TOOLS / "build"
VS = Path(r"C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools")
CMAKE = VS / "Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe"
NINJA = VS / "Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe"
COMMIT = "725ae80c42929ebbf6ccd620b38bd45ac32644c2"


def environment():
    command = str(PROJECT / "engine-patches/capture_msvc_environment.cmd")
    result = subprocess.run(["cmd.exe", "/d", "/c", command], check=True,
                            capture_output=True, text=True)
    env = dict(os.environ)
    for line in result.stdout.splitlines():
        if "=" in line and not line.startswith("="):
            key, value = line.split("=", 1)
            env[key] = value
    env["CONAN_HOME"] = str(TOOLS / "conan-home")
    env["PATH"] = str(NINJA.parent) + os.pathsep + env["PATH"]
    runtime_list = TOOLS / "conan-generated/_runtime_libs.txt"
    if runtime_list.exists():
        directories = sorted({str(Path(x).parent) for x in runtime_list.read_text().splitlines() if x})
        env["PATH"] = os.pathsep.join(directories) + os.pathsep + env["PATH"]
    return env


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("configure", "build", "test"))
    parser.add_argument("--gtest-filter", default="ConnectionShutdownTest.*:ExpectedConnectionClosuresTest.*:ExecuteHeroChainMovementTest.*:FailedEscapeRouteTest.*:Nullkiller2_Engine_TaskFailure.*:Nullkiller2_Behaviors_EscapeBehavior.*:Nullkiller2_AIGateway.*:LocalServerDiscovery.*")
    args = parser.parse_args()
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=SOURCE, text=True).strip() == COMMIT
    report = PROJECT / "build/reports/engine-shutdown" / f"{args.phase}-{time.time_ns()}"
    report.mkdir(parents=True)
    env = environment()
    source_diff_hash = hashlib.sha256(subprocess.check_output(["git", "diff", "--binary"], cwd=SOURCE)).hexdigest()
    archives = {}
    if args.phase == "configure":
        command = [str(CMAKE), "-S", str(SOURCE), "-B", str(BUILD), "-G", "Ninja",
                   "--toolchain", str(TOOLS / "conan-generated/conan_toolchain.cmake"),
                   "-DCMAKE_BUILD_TYPE=Release", "-DENABLE_LAUNCHER=OFF", "-DENABLE_EDITOR=OFF",
                   "-DENABLE_DISCORD=OFF", "-DENABLE_MMAI=OFF", "-DENABLE_TEST=ON",
                   "-DENABLE_CCACHE=OFF", "-DENABLE_LTO=OFF", "-DENABLE_SDL3=ON"]
    elif args.phase == "build":
        command = [str(CMAKE), "--build", str(BUILD), "--parallel", "2", "--target",
                   "vcmiclient", "vcmiserver", "vcmitest"]
    else:
        app = BUILD / "bin"
        user = report / "user"
        redist = VS / "VC/Redist/MSVC/14.51.36231/x64/Microsoft.VC145.CRT"
        for dependency in sorted(redist.glob("*.dll")):
            shutil.copy2(dependency, app / dependency.name)
        (app / "config").mkdir(parents=True, exist_ok=True)
        (app / "config/dirs.json").write_text(json.dumps({
            "userDataPath": str(user), "userConfigPath": str(user / "config"),
            "userLogsPath": str(user / "logs"), "userCachePath": str(user / "cache")}, indent=2))
        original_data = Path(r"D:\e2e\Heroes of Might & Magic III\Data")
        for original in sorted(original_data.iterdir()):
            if original.suffix.lower() not in (".lod", ".snd", ".vid"):
                continue
            before = hashlib.file_digest(original.open("rb"), "sha256").hexdigest()
            copied = app / "Data" / original.name
            copied.parent.mkdir(parents=True, exist_ok=True)
            if not copied.is_file() or hashlib.file_digest(copied.open("rb"), "sha256").hexdigest() != before:
                shutil.copy2(original, copied)
            after = hashlib.file_digest(original.open("rb"), "sha256").hexdigest()
            assert before == after == hashlib.file_digest(copied.open("rb"), "sha256").hexdigest()
            archives[str(original)] = before
        command = [str(BUILD / "bin/vcmitest.exe"), "--gtest_filter=" + args.gtest_filter,
                   f"--gtest_output=json:{report / 'gtest.json'}"]
    started = time.time()
    tested_binaries = {}
    if args.phase == "test":
        tested_binaries = {p.relative_to(BUILD / "bin").as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in sorted((BUILD / "bin").rglob("*"))
                           if p.is_file() and p.suffix.lower() in (".exe", ".dll")}
    with (report / "output.log").open("wb") as output:
        result = subprocess.run(command, cwd=BUILD / "bin" if args.phase == "test" else SOURCE,
                                env=env, stdout=output, stderr=subprocess.STDOUT,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                                timeout=180 if args.phase == "test" else None)
    for original, expected in archives.items():
        assert hashlib.file_digest(Path(original).open("rb"), "sha256").hexdigest() == expected
    assert source_diff_hash == hashlib.sha256(subprocess.check_output(["git", "diff", "--binary"], cwd=SOURCE)).hexdigest(), "Source changed during command"
    record = {"phase": args.phase, "command": command, "cwd": str(BUILD / "bin" if args.phase == "test" else SOURCE),
              "source_commit": COMMIT, "exit_code": result.returncode,
              "source_diff_sha256": source_diff_hash, "tested_binaries_sha256": tested_binaries,
              "elapsed_seconds": time.time() - started,
              "original_archives_sha256_before_after": archives,
              "log_sha256": hashlib.sha256((report / "output.log").read_bytes()).hexdigest(),
              "scope": "isolated patched engine; no mod launch, installation or release acceptance"}
    (report / "result.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))
    print(report)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
