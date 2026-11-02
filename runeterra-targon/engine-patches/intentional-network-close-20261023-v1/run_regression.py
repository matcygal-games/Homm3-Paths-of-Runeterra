"""Build/run only the isolated copied-consumer regression executables."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import re
import subprocess

HERE = Path(__file__).resolve().parent
VCVARS = Path('C:/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/VC/Auxiliary/Build/vcvars64.bat')
CL = Path('C:/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/VC/Tools/MSVC/14.51.36231/bin/Hostx64/x64/cl.exe')


def main():
    output = HERE / 'regression-result-v2.json'
    if output.exists():
        raise ValueError('Preserve prior compiled regression results')
    setup = subprocess.run(f'cmd /d /s /c ""{VCVARS}" >nul && set"', capture_output=True, text=True, check=True)
    env = dict(os.environ)
    for line in setup.stdout.splitlines():
        if '=' in line and not line.startswith('='):
            key, value = line.split('=', 1)
            env[key] = value
    cases = re.findall(r'test\("([^\"]+)"', (HERE / 'consumer_fixture.cpp.in').read_text())
    result = {'scope': 'Compiled extracted actual official66fa consumer bodies with minimal dependency fixtures and actual InternalConnection methods; not full engine/native gameplay',
              'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'compiler': str(CL),
              'compiler_sha256': hashlib.sha256(CL.read_bytes()).hexdigest(), 'variants': {}}
    for variant in ('upstream', 'patched'):
        cwd = HERE / 'tests-v2' / variant
        cmd = [str(CL), '/nologo', '/std:c++17', '/EHsc', '/W4', '/Od', str(cwd / 'consumer_regression.cpp'),
               '/Fe:' + str(cwd / 'consumer_regression.exe'), '/Fo:' + str(cwd / 'consumer_regression.obj')]
        compile_result = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
        (cwd / 'compile.log').write_text(compile_result.stdout + compile_result.stderr)
        entry = {'compile_command': cmd, 'compile_exit_code': compile_result.returncode, 'cases': {}}
        result['variants'][variant] = entry
        if compile_result.returncode == 0:
            for name in cases:
                execution = subprocess.run([str(cwd / 'consumer_regression.exe'), name], cwd=cwd, env=env, capture_output=True, text=True, timeout=10)
                raw = execution.stdout + execution.stderr
                (cwd / (name + '.log')).write_text(raw)
                entry['cases'][name] = {'exit_code': execution.returncode, 'output': raw}
            entry['passed'] = sum(v['exit_code'] == 0 for v in entry['cases'].values())
            entry['failed'] = len(cases) - entry['passed']
            entry['binary_sha256'] = hashlib.sha256((cwd / 'consumer_regression.exe').read_bytes()).hexdigest()
        print(variant, json.dumps(entry, indent=2))
    output.write_text(json.dumps(result, indent=2) + '\n')
    patched = result['variants']['patched']
    raise SystemExit(0 if patched.get('passed') == len(cases) and patched.get('failed') == 0 else 2)


if __name__ == '__main__':
    main()
