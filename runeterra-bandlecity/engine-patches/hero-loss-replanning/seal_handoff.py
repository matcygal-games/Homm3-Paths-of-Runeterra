"""Seal executed fifth/sixth source and runtime evidence; no engine/game launch."""
import argparse, ast, difflib, hashlib, json, time, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FOURTH = ROOT.parent / 'ai-turn-lifecycle'
SIXTH = ROOT.parent / 'creature-previews'
W = ROOT.parents[2]
REPORTS = W / 'runeterra-bandlecity/build/reports/engine-ai-lifecycle/hero-loss-combined'
sha = lambda data: hashlib.sha256(data).hexdigest()
def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()
def inventory(root):
    return {p.relative_to(root).as_posix(): digest(p) for p in sorted(root.rglob('*')) if p.is_file()}
def signature(values):
    return sha(json.dumps(values, sort_keys=True, separators=(',', ':')).encode())
def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', newline='\n')

def main():
    parser = argparse.ArgumentParser()
    for name in ('build', 'targeted', 'broader', 'red', 'control'):
        parser.add_argument('--' + name, required=True)
    args = vars(parser.parse_args())
    out = REPORTS.parent / ('hero-loss-handoff-' + str(time.time_ns()))
    out.mkdir()
    source = inventory(FOURTH / 'src')
    baseline = inventory(FOURTH / 'src-reproduced-final')
    assert signature(baseline) == '6b1aebe017d3f0f4cfa100ca4fb165682c5738cdf74aa5f990f5b945091703f0'
    names = ['AI/Nullkiller2/AIGateway.h', 'AI/Nullkiller2/AIGateway.cpp',
             'AI/Nullkiller2/Engine/Nullkiller.cpp', 'AI/Nullkiller2/Goals/AbstractGoal.h',
             'test/CMakeLists.txt', 'test/nullkiller2/HeroLossReplanningTest.cpp']
    changes, patch = {}, []
    for name in sorted(names):
        before = (FOURTH / 'src-reproduced-final' / name)
        old = before.read_bytes() if before.exists() else b''
        target = ROOT / 'overlay' / name
        # CMake was checkpointed before the sixth-only test registration.
        new = target.read_bytes() if name == 'test/CMakeLists.txt' else (FOURTH / 'src' / name).read_bytes()
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or target.read_bytes() != new:
            target.write_bytes(new)
        changes[name] = {'before_sha256': sha(old) if before.exists() else None, 'after_sha256': sha(new)}
        patch.extend(difflib.unified_diff(old.decode().splitlines(True), new.decode().splitlines(True),
                                        fromfile='a/' + name if before.exists() else '/dev/null', tofile='b/' + name))
    write(ROOT / 'changes.json', changes)
    (ROOT / '0005-hero-loss-replanning.patch').write_text(''.join(patch).replace('\r\n', '\n'), newline='\n')

    audit = json.loads((W / 'runeterra-bandlecity/build/reports/integration-review/runtime-candidate-v1.json').read_text())
    zipped = Path(audit['source_zip']['path'])
    assert digest(zipped) == audit['source_zip']['sha256']
    files = {}
    with zipfile.ZipFile(zipped) as archive:
        pins = json.loads(archive.read('SOURCE-FILES-SHA256.json'))
        for name, expected in pins.items():
            data = archive.read(name)
            assert sha(data) == expected, name
            if name.startswith('vcmi/'):
                files[name[5:]] = data
    reconstructed = []
    for family in (FOURTH, ROOT, SIXTH):
        document = json.loads((family / 'changes.json').read_text())
        if family == SIXTH:
            assert document['schema'] == 1 and len(document['files']) == 6
            entries = {entry['path']: entry for entry in document['files']}
            assert len(entries) == 6
        else:
            entries = document
        for name, pins in entries.items():
            assert (sha(files[name]) if name in files else None) == pins['before_sha256'], (family.name, name)
            data = (family / 'overlay' / name).read_bytes()
            assert sha(data) == pins['after_sha256'], (family.name, name)
            files[name] = data
        reconstructed.append({'family': family.name, 'files': len(files), 'signature': signature({n: sha(b) for n, b in files.items()})})
    assert {name: sha(data) for name, data in files.items()} == source
    write(out / 'source-inventory.json', source)
    records = {key: json.loads((REPORTS / args[key] / 'result.json').read_text()) for key in ('build', 'targeted', 'broader', 'red')}
    receipts = {}
    for key, record in records.items():
        folder = REPORTS / args[key]
        row = {'path': folder.relative_to(W).as_posix(), 'result_sha256': digest(folder / 'result.json'),
               'output_sha256': digest(folder / 'output.log'), 'exit_code': record['exit_code']}
        if key != 'red':
            assert record['exit_code'] == 0 and record['source_hashes'] == source
        if (folder / 'gtest.json').exists():
            result = json.loads((folder / 'gtest.json').read_text())
            row.update({k: result[k] for k in ('tests', 'failures', 'errors')})
            row['gtest_sha256'] = digest(folder / 'gtest.json')
            if key != 'red':
                assert result['failures'] == result['errors'] == 0
        receipts[key] = row
    red_result = json.loads((REPORTS / args['red'] / 'gtest.json').read_text())
    failed = sorted(s['name'] + '.' + t['name'] for s in red_result['testsuites'] for t in s['testsuite'] if t.get('failures'))
    assert failed == sorted('HeroLossReplanning.' + name for name in (
        'realNormalDefeatCancelsMovingHeroTaskAndReplansWithoutErrors',
        'realNormalDefeatProducesTypedCancellationAtMovementBoundary',
        'realRetreatActionProducesEscapeAndCancelsTaskWithoutErrors', 'realSurrenderActionCancelsTaskWithoutErrors'))
    control_path = REPORTS / args['control'] / 'control.json'
    control = json.loads(control_path.read_text())
    assert control['candidate_source_restored'] and control['red_build_exit'] == 0 and control['red_test_exit'] == 1
    differences = sorted(name for name in source if source[name] != records['red']['source_hashes'][name])
    assert differences == sorted(control['red'])
    assert all(records['red']['source_hashes'][name] == value for name, value in control['red'].items())
    assert all(source[name] == value for name, value in control['candidate'].items())
    assert all(records['red']['source_hashes'][name] == value for name, value in source.items() if name.startswith('test/'))

    app = FOURTH / 'b/bin'
    old_app = W / 'runeterra-bandlecity/.tools/ai-life-20261022-f807efe4f18d/app'
    old_files = inventory(old_app)
    pe = {p.relative_to(app).as_posix(): digest(p) for p in sorted(app.rglob('*')) if p.is_file() and p.suffix.lower() in ('.exe', '.dll') and p.name != 'vcmitest.exe'}
    old_pe = {n: value for n, value in old_files.items() if Path(n).suffix.lower() in ('.exe', '.dll')}
    assert set(pe) == set(old_pe)
    delta = [{'path': name, 'sha256': value, 'bytes': (app / name).stat().st_size, 'fourth_sha256': old_pe[name]} for name, value in pe.items() if value != old_pe[name]]
    assert {row['path'] for row in delta} == {'VCMI_client.exe', 'VCMI_server.exe', 'VCMI_lib.dll'}
    for key in ('build', 'targeted', 'broader'):
        assert all(records[key]['binaries_sha256'][name] == value for name, value in pe.items())
        assert records[key]['binaries_sha256']['vcmitest.exe'] == digest(app / 'vcmitest.exe')
    ninja = (FOURTH / 'b/build.ninja').read_text().replace('\\', '/')
    lines = ninja.splitlines()
    core = next(x for x in lines if x.startswith('build bin/VCMI_lib.dll '))
    client = next(x for x in lines if x.startswith('build bin/VCMI_client.exe:'))
    client_archive = next(x for x in lines if x.startswith('build bin/VCMI_vcmiclientcommon.lib:'))
    server = next(x for x in lines if x.startswith('build bin/VCMI_server.exe:'))
    server_archive = next(x for x in lines if x.startswith('build bin/VCMI_vcmiservercommon.lib:'))
    core_objects = ['AI/Nullkiller2/CMakeFiles/Nullkiller2.dir/AIGateway.cpp.obj', 'AI/Nullkiller2/CMakeFiles/Nullkiller2.dir/Engine/Nullkiller.cpp.obj', 'lib/CMakeFiles/vcmiMain.dir/CCreatureHandler.cpp.obj']
    widget = 'client/CMakeFiles/vcmiclientcommon.dir/widgets/MiscWidgets.cpp.obj'
    assert all(name in core for name in core_objects)
    assert widget in client_archive and 'bin/VCMI_vcmiclientcommon.lib' in client
    assert 'bin/VCMI_vcmiservercommon.lib' in server
    proof = {'ninja_sha256': digest(FOURTH / 'b/build.ninja'), 'core_link': core, 'client_link': client, 'client_archive': client_archive, 'server_link': server, 'server_archive': server_archive,
             'game_used_AI': 'Nullkiller2 OBJECT target is bundled in VCMI_lib.dll; no separate AI DLL.',
             'objects': {name: digest(FOURTH / 'b' / name) for name in core_objects + [widget]}}
    write(out / 'link-proof.json', proof)
    schema = 'config/schemas/creature.json'
    schema_delta = {'path': schema, 'sha256': source[schema], 'fourth_sha256': old_files[schema], 'source': (SIXTH / 'overlay' / schema).relative_to(W).as_posix()}
    runtime = {'status': 'authored configuration', 'locally_modified_engine': True, 'baseline_app': old_app.relative_to(W).as_posix(), 'baseline_file_count': len(old_files), 'baseline_inventory_sha256': signature(old_files),
               'runtime_pe_inventory': pe, 'binary_delta': delta, 'additional_dependency_delta': [], 'runtime_configuration_changes_required': [schema_delta],
               'copy_policy': 'Copy sealed fourth app into new own app; overlay ONLY3 named final binaries plus config/schemas/creature.json; update build notice/private dirs separately. Never copy b/bin wholesale, Data, user/test/config trees.',
               'link_proof_sha256': digest(out / 'link-proof.json'), 'source_inventory_sha256': signature(source), 'game_launch_or_selection_by_worker': False}
    write(out / 'runtime-overlay.json', runtime)
    previous = json.loads((FOURTH / 'provenance.json').read_text())
    provenance = {'schema': 1, 'status': 'authored configuration', 'locally_modified_engine': True, 'release_accepted': False,
                  'baseline_source_zip_sha256': audit['source_zip']['sha256'], 'fourth_patch_sha256': digest(FOURTH / '0004-ai-turn-lifecycle.patch'), 'incremental_patch_sha256': digest(ROOT / '0005-hero-loss-replanning.patch'),
                  'changes_sha256': digest(ROOT / 'changes.json'), 'ordered_reconstruction': reconstructed, 'combined_source_inventory_sha256': signature(source), 'combined_source_files': len(source),
                  'source_reconstruction_equals_final_build_and_green_receipts': True, 'receipts': receipts, 'red_failed_cases': failed,
                  'red_scope': control['scope'], 'red_source_differences': differences, 'identical_native_test_sources_red_green': True,
                  'red_control_path': control_path.relative_to(W).as_posix(), 'red_control_sha256': digest(control_path),
                  'runtime_handoff': (out / 'runtime-overlay.json').relative_to(W).as_posix(), 'runtime_handoff_sha256': digest(out / 'runtime-overlay.json'),
                  'link_proof': (out / 'link-proof.json').relative_to(W).as_posix(), 'link_proof_sha256': digest(out / 'link-proof.json'),
                  'runtime_configuration_changes_required': [schema_delta], 'runtime_binary_delta': delta, 'additional_dependency_delta': [], 'toolchain': previous['toolchain'],
                  'compatibility': {'serialized_or_network_fields_added': False, 'save_protocol_version_change': False, 'RNG_changes': False, 'bit_identical_async_gameplay_asserted': False},
                  'fixture_limits': 'In-process server-finalization/task adapter: passive battle interface/statusONGOING substitute; no HeroVisit/PlayerBlocked/battleResultsApplied routing, full CClient lifecycle, network concurrency or tactical strength claim.',
                  'diagnosis_correction': 'Preserved v1 inferred NORMAL incorrectly; actual captured native actionType2 RETREAT maps to ESCAPE. Corrected authoritative known-result+opposite-winner classification is exercised by real MakeAction retreat/surrender.',
                  'remaining': ['independent final source/runtime audit', 'coordinator runtime preparation/selection', 'fresh exact-stage native frontier and human UI', 'external human and rights approvals'],
                  'payload_excludes': ['working src/b/reconstruction', 'licensed Data/references', 'native binaries', 'private config/cache/user', 'dependency/source ZIP caches']}
    for name in ('prepare_source.py', 'build_candidate.py'):
        ast.parse((ROOT / name).read_text())
    write(ROOT / 'provenance.json', provenance)
    exported = ['README.md', '0005-hero-loss-replanning.patch', 'changes.json', 'provenance.json', 'prepare_source.py', 'build_candidate.py'] + ['overlay/' + name for name in sorted(names)]
    assert len(exported) == 12
    write(ROOT / 'source-export-files.json', {'schema': 2, 'scope': 'Compact reviewed incremental fifth source; working source/build/private data/binaries excluded.', 'files': [{'path': name, 'sha256': digest(ROOT / name)} for name in exported]})
    write(out / 'freeze.json', {'status': 'authored configuration', 'source_files': len(source), 'source_inventory_sha256': signature(source), 'manifest_sha256': digest(ROOT / 'source-export-files.json'), 'provenance_sha256': digest(ROOT / 'provenance.json'), 'patch_sha256': digest(ROOT / '0005-hero-loss-replanning.patch'), 'receipts': receipts, 'runtime_handoff_sha256': digest(out / 'runtime-overlay.json'), 'link_proof_sha256': digest(out / 'link-proof.json')})
    print(out)
    print(json.dumps({'manifest_sha256': digest(ROOT / 'source-export-files.json'), 'source_inventory_sha256': signature(source), 'binary_delta': delta, 'schema_delta': schema_delta}, indent=2))

if __name__ == '__main__':
    main()
