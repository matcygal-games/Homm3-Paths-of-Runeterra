"""Require copied-consumer tests to reject broad suppression and late marking."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

HERE = Path(__file__).resolve().parent
CL = Path('C:/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/VC/Tools/MSVC/14.51.36231/bin/Hostx64/x64/cl.exe')
VCVARS = Path('C:/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/VC/Auxiliary/Build/vcvars64.bat')


def main():
    result_path = HERE / 'mutation-results.json'
    if result_path.exists():
        raise ValueError('Preserve mutation results')
    original = (HERE / 'tests-v2/patched/consumer_regression.cpp').read_text()
    mutations = {
        'global-shutdown-suppression': ('if(requestedConnectionClosures.find(connection) != requestedConnectionClosures.end())',
            'if(state == EServerState::SHUTDOWN)', 'unknown-loss-after-shutdown-remains-error'),
        'mark-after-close': ('requestedConnectionClosures.insert(connection);\n\tconnection->close();',
            'connection->close();\n\trequestedConnectionClosures.insert(connection);', 'synchronous-close-before-removal')}
    setup = subprocess.run(f'cmd /d /s /c ""{VCVARS}" >nul && set"', capture_output=True, text=True, check=True)
    env = dict(os.environ)
    for line in setup.stdout.splitlines():
        if '=' in line and not line.startswith('='):
            key, value = line.split('=', 1); env[key] = value
    results = {}
    for name, (before, after, case) in mutations.items():
        assert original.count(before) == 1
        cwd = HERE / 'mutation-tests' / name
        cwd.mkdir(parents=True, exist_ok=True)
        source = cwd / 'consumer_regression.cpp'
        source.write_text(original.replace(before, after))
        binary = cwd / 'consumer_regression.exe'
        command = [str(CL), '/nologo', '/std:c++17', '/EHsc', '/W4', '/Od', str(source), '/Fe:' + str(binary), '/Fo:' + str(cwd / 'consumer_regression.obj')]
        build = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True)
        (cwd / 'compile.log').write_text(build.stdout + build.stderr)
        entry = {'compile_command': command, 'compile_exit_code': build.returncode,
            'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'case': case}
        if build.returncode == 0:
            run = subprocess.run([str(binary), case], cwd=cwd, env=env, capture_output=True, text=True, timeout=10)
            (cwd / 'run.log').write_text(run.stdout + run.stderr)
            entry.update(run_exit_code=run.returncode, output=run.stdout + run.stderr, rejected=run.returncode != 0)
        results[name] = entry
    result_path.write_text(json.dumps(results, indent=2) + '\n')
    print(json.dumps(results, indent=2))
    raise SystemExit(0 if all(v.get('rejected') for v in results.values()) else 2)


if __name__ == '__main__':
    main()
