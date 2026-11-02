"""Reproduce the current bounded semantic/whole-layer-registration fixture."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[5]
WORKSPACE = PROJECT.parent
REPORT = PROJECT / 'build/reports/complete-town-20261028-v1/approved-implementation-v1/physical-refinement-v1/execution-v3'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(script, *args):
    cmd = [sys.executable, '-B', str(HERE / script), *map(str, args)]
    result = subprocess.run(cmd, cwd=WORKSPACE, capture_output=True, text=True)
    (REPORT / (script + '.stdout.txt')).write_text(result.stdout, encoding='utf-8')
    (REPORT / (script + '.stderr.txt')).write_text(result.stderr, encoding='utf-8')
    rows.append({'command': cmd, 'exit_code': result.returncode})
    (REPORT / 'commands.json').write_text(json.dumps(rows, indent=2) + '\n', encoding='utf-8')
    if result.returncode:
        raise RuntimeError(result.stderr or result.stdout)
    print(result.stdout)

REPORT.mkdir(parents=True, exist_ok=False)
rows = []
index = HERE / 'lower-roost-registration-v1/states.json'
run('bind_contract.py', '--index', index.relative_to(PROJECT).as_posix(),
    '--index-sha256', sha(index), '--annotations', HERE / 'semantic-candidate-v3/annotations.json',
    '--out-name', 'contract-v3')
payload = HERE / 'compiler-roost-v1/payload-and-compiler.json'
receipts = HERE / 'compiler-roost-v1/compiler-receipts.json'
contract = HERE / 'contract-v3/layout-contract.json'
compiled = PROJECT / 'build/reports/complete-town-20261028-v1/approved-implementation-v1/physical-refinement-v1/compiler-roost-v1/compiled'
run('prepare_fixture.py', '--payload', payload.relative_to(PROJECT).as_posix(),
    '--payload-sha256', sha(payload), '--compiler-receipts', receipts.relative_to(PROJECT).as_posix(),
    '--compiler-receipts-sha256', sha(receipts), '--compiled-root', compiled,
    '--contract', contract.relative_to(PROJECT).as_posix(), '--contract-sha256', sha(contract),
    '--out-name', 'fixture-v3')
