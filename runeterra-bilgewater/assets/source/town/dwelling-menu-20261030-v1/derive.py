"""Replay only the own-source Bilgewater scenic dwelling cards into a new directory."""
from pathlib import Path
import argparse
import hashlib
import io
import json
from PIL import Image


def checked(project, record):
    path = (project / record['path']).resolve()
    if not path.is_relative_to(project.resolve()):
        raise ValueError('Source escapes own project')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != record['sha256']:
        raise ValueError('Pinned source changed: ' + record['path'])
    return raw


def replay(project, ledger_path, output):
    ledger = json.loads(ledger_path.read_bytes())
    background = Image.open(io.BytesIO(checked(project, ledger['background']))).convert('RGBA')
    if background.size != (800, 374):
        raise ValueError('Native backdrop required')
    background = background.resize((150, 70), Image.Resampling.LANCZOS)
    background.putalpha(255)
    if output.exists():
        raise ValueError('A new output directory is required')
    output.mkdir(parents=True)
    for row in ledger['cards']:
        figure = Image.open(io.BytesIO(checked(project, {'path': row['figure'], 'sha256': row['original_source_sha256']}))).convert('RGBA')
        if figure.size != (150, 70):
            raise ValueError('Native card foreground required')
        result = Image.alpha_composite(background, figure)
        path = output / (row['building'] + '.png')
        result.save(path, format='PNG', compress_level=9)
        if hashlib.sha256(path.read_bytes()).hexdigest() != row['source_sha256']:
            raise ValueError('Derived card bytes differ')
    return len(ledger['cards'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    project = next(p for p in here.parents if (p / 'content/factions.json').is_file())
    print(replay(project, here / 'derivation.json', args.output))
