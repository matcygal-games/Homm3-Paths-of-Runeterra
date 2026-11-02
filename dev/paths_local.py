"""Portable paths for read-only game inputs and separate development outputs."""
from pathlib import Path


def resolve_game_root(game_root, output):
    """Resolve a read-only game input and reject overlapping output directories."""
    if not game_root:
        raise ValueError("Specify the Heroes III installation using --game-root or HOMM3_PATH")
    root = Path(game_root).expanduser().resolve()
    destination = Path(output).expanduser().resolve()
    if not (root / "Data").is_dir():
        raise ValueError("Heroes III installation must contain a Data directory")
    if destination == root or destination.is_relative_to(root) or root.is_relative_to(destination):
        raise ValueError("The output and original Heroes III installation must be separate")
    return root
