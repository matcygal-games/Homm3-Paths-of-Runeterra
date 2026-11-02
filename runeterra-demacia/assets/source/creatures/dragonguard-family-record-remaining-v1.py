"""Persist all actual built-in outputs and their exact executed provenance."""
from pathlib import Path
import json
import sys

PROJECT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT / 'scripts'))
from creature_family_motion_art import record_generation

jobs = json.loads((PROJECT / 'assets/source/creatures/dragonguard-family-remaining-generation-inputs-v1.json').read_text(encoding='utf-8'))
for job in jobs:
    folder = PROJECT / job['folder']
    metadata = json.loads((folder / f'paint-action-g{job["group"]:02}-tool-result-v1.json').read_text())
    record_generation(PROJECT, job['unit'], folder, folder / 'dragonguard-production-v3.json', job['group'],
        Path(metadata['generated']), PROJECT / job['promptPath'], [PROJECT / path for path in job['refs']],
        PROJECT / job['atlas_metadata'])
    print(job['unit'], job['group'], 'saved actual built-in creative source and exact provenance')
