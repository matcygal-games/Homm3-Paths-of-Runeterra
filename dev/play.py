"""Launch an existing Paths of Runeterra profile without a machine-specific shortcut."""
import argparse
import os
from pathlib import Path
import subprocess
import sys


def resolve_launcher(profile):
    """Prefer the profile's sealed Python launcher; accept the installed Windows launcher."""
    root = Path(profile).expanduser().resolve()
    if (root / "launch.py").is_file() and (root / "manifest.json").is_file():
        return root, "sealed"
    if (root / "launch.cmd").is_file() and (root / "app" / "VCMI_client.exe").is_file():
        return root, "installed"
    raise ValueError("No supported Paths of Runeterra profile was found at " + str(root))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", help="profile folder (or set PATHS_OF_RUNETERRA_PROFILE)")
    args = parser.parse_args(argv)
    profile = args.profile or os.environ.get("PATHS_OF_RUNETERRA_PROFILE")
    if not profile and os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        profile = str(Path(os.environ["LOCALAPPDATA"]) / "Programs" / "Paths of Runeterra")
    if not profile:
        parser.error("provide --profile or set PATHS_OF_RUNETERRA_PROFILE")
    try:
        root, kind = resolve_launcher(profile)
    except (ValueError, OSError) as error:
        parser.exit(2, str(error) + "\n")
    if kind == "sealed":
        return subprocess.call([sys.executable, "-u", "-B", str(root / "launch.py"), "--root", str(root)])
    if os.name != "nt":
        parser.exit(2, "The installed profile requires Windows.\n")
    os.startfile(str(root / "launch.cmd"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
