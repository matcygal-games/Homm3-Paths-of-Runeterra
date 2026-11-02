"""Common local development commands for Paths of Runeterra."""
import argparse
from pathlib import Path
import subprocess
import sys

from .authoring import script_command

ROOT = Path(__file__).resolve().parents[1]
FACTIONS = ("demacia", "noxus", "freljord", "zaun", "bandlecity", "ionia", "piltover", "ixtal", "bilgewater", "targon", "shurima")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    play = commands.add_parser("play", help="launch an existing installed or sealed profile")
    play.add_argument("--profile", help="profile folder (or set PATHS_OF_RUNETERRA_PROFILE)")
    commands.add_parser("check", help="run quick offline developer checks")
    audit = commands.add_parser("audit", help="inspect publication risks")
    audit.add_argument("--tracked-only", action="store_true")
    audit.add_argument("--all", action="store_true", help="show every finding")
    audit.add_argument("--format", choices=("text", "json"), default="text", help="audit output format")
    source = commands.add_parser("source", help="plan or export a clean source tree without private Git history")
    source_commands = source.add_subparsers(dest="source_action", required=True)
    source_plan = source_commands.add_parser("plan", help="read-only inventory, exclusions and blockers as JSON")
    source_plan.add_argument("--root", type=Path, default=ROOT, help="source checkout")
    source_export = source_commands.add_parser("export", help="copy an admitted source tree to a new directory")
    source_export.add_argument("--root", type=Path, default=ROOT, help="source checkout")
    source_export.add_argument("--output", type=Path, required=True, help="new empty destination (never overwritten)")
    doctor = commands.add_parser("doctor", help="inventory a component's prerequisites")
    selection = doctor.add_mutually_exclusive_group()
    selection.add_argument("--faction", choices=FACTIONS, help="regional component (default: demacia)")
    selection.add_argument("--world", action="store_true", help="inspect the world component")
    args = parser.parse_args(argv)

    command = [sys.executable, "-B"]
    if args.command == "play":
        command.extend(("-m", "dev.play"))
        if args.profile:
            command.extend(("--profile", str(Path(args.profile).expanduser().absolute())))
    elif args.command == "check":
        command.extend(("-m", "dev.check"))
    elif args.command == "audit":
        command.extend(("-m", "dev.publication_audit"))
        if args.tracked_only:
            command.append("--tracked-only")
        if args.all:
            command.append("--all")
        command.extend(("--format", args.format))
    elif args.command == "source":
        command.extend(("-m", "dev.public_source", "--root", str(args.root.absolute())))
        if args.source_action == "export":
            command.extend(("--write", "--output", str(args.output.absolute())))
    else:
        selection = []
        if args.world:
            selection.extend(("--component", "world"))
        elif args.faction:
            selection.extend(("--faction", args.faction))
        try:
            command = script_command("runeterra.py", *selection, "doctor")
        except (FileNotFoundError, ValueError):
            parser.exit(2, "doctor requires the separate maintainer production tools, which are not included in a standard source checkout.\n")
    return subprocess.call(command, cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
