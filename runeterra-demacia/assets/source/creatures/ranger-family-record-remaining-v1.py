"""Persist exact builtin outputs using family provenance API; no promotion."""
from pathlib import Path
import json
import sys

PROJECT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT / 'scripts'))
from creature_family_motion_art import record_generation

jobs = json.loads((PROJECT / 'assets/source/creatures/ranger-family-remaining-generation-inputs-v1.json').read_text())
for job in jobs:
    folder = PROJECT / job['folder'];group = job['group']
    tool_record = folder / f'paint-action-g{group:02}-tool-result-v1.json'
    if not tool_record.exists():
        continue
    tool = json.loads(tool_record.read_text())
    result = record_generation(PROJECT, job['unit'], folder, folder / 'ranger-production-v4.json', group,
        Path(tool['generated']), PROJECT / job['promptPath'], [PROJECT / ref for ref in job['refs']],
        folder / f'raw-action-g{group:02}-padding-transform-v1.json')
    print(job['unit'], group, result['returned_dimensions'], result['validation_errors'])
