"""Compiled synchronization negatives; test fixtures only, no native engine."""
from pathlib import Path
import json, os, subprocess
import run_regression as runner

HERE = Path(__file__).resolve().parent


def main():
    output = HERE / 'mutation-results.json'
    if output.exists(): raise ValueError('Preserve prior mutation receipt')
    source = (HERE / 'tests-v3/patched/consumer_regression.cpp').read_text()
    guard = 'std::lock_guard<std::mutex> lock(requestedConnectionClosuresMutex);'
    assert source.count(guard) == 2
    first, last = source.index(guard), source.rindex(guard)
    long_lock = source.replace('''{
	{
		std::lock_guard<std::mutex> lock(requestedConnectionClosuresMutex);
		for(auto it = requestedConnectionClosures.begin();''', '''{
	std::lock_guard<std::mutex> lock(requestedConnectionClosuresMutex);
	{
		for(auto it = requestedConnectionClosures.begin();''', 1)
    assert long_lock != source
    variants = {
        'missing-writer-lock': (source[:first] + source[first:].replace(guard, '', 1), 'registry-lock-blocks-writer-and-reader'),
        'missing-reader-lock': (source[:last] + source[last:].replace(guard, '', 1), 'registry-lock-blocks-writer-and-reader'),
        'lock-across-reentrant-close': (long_lock, 'synchronous-close-before-removal')}
    setup = subprocess.run(f'cmd /d /s /c ""{runner.VCVARS}" >nul && set"', capture_output=True, text=True, check=True)
    env = dict(os.environ)
    for line in setup.stdout.splitlines():
        if '=' in line and not line.startswith('='):
            k, v = line.split('=', 1); env[k] = v
    results = {}
    for name, (text, case) in variants.items():
        cwd = HERE / 'mutation-tests' / name
        cwd.mkdir(parents=True, exist_ok=True)
        cpp = cwd / 'consumer_regression.cpp'; cpp.write_text(text)
        binary = cwd / 'consumer_regression.exe'
        command = [str(runner.CL), '/nologo', '/std:c++17', '/EHsc', '/W4', '/Od', str(cpp), '/Fe:' + str(binary), '/Fo:' + str(cwd / 'consumer_regression.obj')]
        build = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True)
        (cwd / 'compile.log').write_text(build.stdout + build.stderr)
        row = {'compile_exit_code': build.returncode, 'case': case, 'rejected': False}
        if build.returncode == 0:
            try:
                run = subprocess.run([str(binary), case], cwd=cwd, env=env, capture_output=True, text=True, timeout=3)
                text = run.stdout + run.stderr
                row.update(run_exit_code=run.returncode, output=text, rejected=run.returncode != 0)
            except subprocess.TimeoutExpired:
                text = 'Bounded isolated regression timed out at 3 seconds: lock held across synchronous callback. Process was killed and waited by subprocess.run.'
                row.update(timeout_seconds=3, rejected=True, output=text)
            (cwd / 'run.log').write_text(text)
        results[name] = row
    output.write_text(json.dumps(results, indent=2) + '\n')
    print(json.dumps(results, indent=2))
    raise SystemExit(0 if all(v['rejected'] for v in results.values()) else 2)


if __name__ == '__main__': main()
