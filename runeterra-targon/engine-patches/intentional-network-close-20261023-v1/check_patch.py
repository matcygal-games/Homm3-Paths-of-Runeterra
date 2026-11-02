"""Apply the patch only to a NEW disposable three-file source copy below this folder."""
from pathlib import Path
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent


def main():
    target = HERE / 'apply-check-v2'
    if target.exists():
        raise ValueError('Preserve previous apply-check fixture')
    patch = HERE / '0001-track-explicit-server-connection-close-ownership.patch'
    inputs = json.loads((HERE / 'patch-inputs.json').read_text())['files']
    for name, hashes in inputs.items():
        raw = (HERE / 'upstream' / name).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == hashes['upstream_sha256']
        out = target / name
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(raw)
    commands = [['git', '-c', 'core.autocrlf=false', '-C', str(target), 'init', '--quiet'],
                ['git', '-c', 'core.autocrlf=false', '-C', str(target), 'apply', '--check', str(patch)],
                ['git', '-c', 'core.autocrlf=false', '-C', str(target), 'apply', str(patch)]]
    receipt = {'scope': 'Only own three-file disposable fixture modified, no source checkout/private build/stage edits', 'commands': []}
    for cmd in commands:
        run = subprocess.run(cmd, capture_output=True, text=True)
        receipt['commands'].append({'command': cmd, 'exit_code': run.returncode, 'output': run.stdout + run.stderr})
        if run.returncode:
            break
    receipt['patched_files_match'] = all((target / name).read_bytes() == (HERE / 'patched' / name).read_bytes() for name in inputs)
    (HERE / 'patch-apply-check-v2.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))
    raise SystemExit(0 if receipt['patched_files_match'] and all(v['exit_code'] == 0 for v in receipt['commands']) else 2)


if __name__ == '__main__':
    main()
