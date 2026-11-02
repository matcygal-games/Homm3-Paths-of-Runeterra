"""Flag common publication risks in the current Git worktree.

This is a triage aid, not a license, secret, malware or Git history audit.
"""

import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent
GAME_ARCHIVES = {".lod", ".snd", ".vid", ".h3s"}
TEXT_EXTENSIONS = {".md", ".txt", ".json", ".jsonc", ".py", ".ps1", ".cmd", ".bat", ".toml", ".yaml", ".yml",
                   ".html", ".htm", ".css", ".js", ".ts", ".ini", ".cfg", ".csv", ".xml"}
# Keep the declarative pattern from resembling an actual user-directory value
# when this source file is audited. Adjacent literals compile to the same regex.
LOCAL_PATH = re.compile(r"(?i)(?:[a-z]:[\\/]users[\\/][^\\/\s\"']+|/" r"home/[^/\s\"']+)")


def contains_local_path(path):
    """Scan large manifests and logs without loading them entirely into memory."""
    tail = ""
    with path.open("r", encoding="utf-8", errors="replace") as source:
        while chunk := source.read(65536):
            text = tail + chunk
            # Keep raw characters between chunks, so doubled JSON separators
            # and path prefixes split at a chunk boundary are still matched.
            normalized = text.replace("\\\\", "/").replace("\\", "/")
            if LOCAL_PATH.search(normalized):
                return True
            tail = text[-1024:]
    return False


def main():
    # Windows can redirect stdout through a legacy code page. Preserve a
    # printable representation of paths that that code page cannot encode.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tracked-only", action="store_true", help="inspect tracked worktree files only")
    parser.add_argument("--all", action="store_true", help="list every finding instead of the first 20 in each category")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="output format (JSON always includes every finding)")
    args = parser.parse_args()
    # Limit this override to this invocation; many asset names exceed the
    # legacy Windows path limit and changing global Git settings is unwanted.
    command = ["git", "-c", "core.longpaths=true", "ls-files", "-z", "--cached"]
    if not args.tracked_only:
        command.extend(["--others", "--exclude-standard"])
    result = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    names = sorted({p.decode(sys.getfilesystemencoding(), errors="surrogateescape") for p in result.stdout.split(b"\0") if p})
    findings = defaultdict(list)
    inspected = 0
    for name in names:
        path = ROOT / name
        if sys.platform == "win32" and len(str(path)) >= 240:
            path = Path("\\\\?\\" + str(path))
        try:
            # Git's cached list already excludes staged deletions. An indexed
            # file absent from the worktree is an unstaged deletion or an
            # unavailable checkout; it must not count as successfully scanned.
            if not path.exists():
                findings["missing indexed or enumerated paths"].append(name)
                continue
            if path.is_symlink() or path.resolve() != path.absolute():
                findings["linked paths not inspected"].append(name)
                continue
            if not path.is_file():
                findings["non-file paths not inspected"].append(name)
                continue
            size = path.stat().st_size
            inspected += 1
            if size >= 100_000_000:
                findings["files at least 100 MB"].append(name)
            if path.suffix.lower() in GAME_ARCHIVES:
                findings["possible game archives"].append(name)
            if path.name.lower() in {".env", "local-paths.json", "dirs.json"}:
                findings["possibly local settings"].append(name)
            if path.suffix.lower() in TEXT_EXTENSIONS:
                if contains_local_path(path):
                    findings["text containing a user-directory path"].append(name)
        except OSError:
            findings["unreadable files"].append(name)
    if args.format == "json":
        print(json.dumps({"enumerated_paths": len(names), "inspected_files": inspected,
                          "findings": dict(sorted(findings.items())), "git_warnings": bool(result.stderr),
                          "scope": "Current worktree triage; Git history, secrets, rights, artwork and binary contents require separate review."},
                         ensure_ascii=True, indent=2))
        return 1 if findings or result.stderr else 0
    print(f"Enumerated {len(names)} Git-listed paths; inspected {inspected} files in the current worktree.")
    if result.stderr:
        print("Git reported warnings while enumerating files; this inventory may be incomplete.")
    for category, paths in sorted(findings.items()):
        print(f"\n{category}: {len(paths)}")
        for name in paths if args.all else paths[:20]:
            print(f"  {name}")
        if not args.all and len(paths) > 20:
            print(f"  ... and {len(paths) - 20} more")
    print("\nReview Git history, licenses, secrets, binaries and artwork separately.")
    return 1 if findings or result.stderr else 0


if __name__ == "__main__":
    raise SystemExit(main())
