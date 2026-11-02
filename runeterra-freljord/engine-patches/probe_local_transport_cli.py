"""Probe only the built server's early CLI paths, without starting networking."""
from __future__ import annotations

import hashlib
import json
import subprocess
import time

from build_isolated import PROJECT, BUILD, environment


def main():
    binary = BUILD / "bin/VCMI_server.exe"
    before = hashlib.sha256(binary.read_bytes()).hexdigest()
    report = PROJECT / "build/reports/engine-shutdown" / ("local-transport-cli-" + str(time.time_ns()))
    report.mkdir(parents=True)
    probes = []
    for label, arguments, expected in (("help", ["--help"], 0),
                                       ("local-lobby-conflict", ["--local-only", "--lobby"], 1),
                                       ("version", ["--version"], 0)):
        result = subprocess.run([str(binary), *arguments], cwd=BUILD / "bin", env=environment(),
                                capture_output=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                                timeout=15)
        output = result.stdout + result.stderr
        (report / (label + ".log")).write_bytes(output)
        assert result.returncode == expected, label
        if label == "help":
            assert b"--local-only" in output and b"loopback" in output
        if label == "local-lobby-conflict":
            assert b"--local-only cannot be combined with --lobby" in output
        probes.append({"command": [str(binary), *arguments], "exit_code": result.returncode,
                       "output_sha256": hashlib.sha256(output).hexdigest()})
    assert hashlib.sha256(binary.read_bytes()).hexdigest() == before
    (report / "result.json").write_text(json.dumps({"server_sha256": before, "probes": probes,
        "scope": "early CLI only; no networking, game, GUI, OS policy or runtime selection"}, indent=2) + "\n")
    print(report)


if __name__ == "__main__":
    main()
