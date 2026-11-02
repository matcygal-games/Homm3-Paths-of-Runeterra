"""Actual consumer, all35states retained, one first-state diagnostic per case.

Unlike the historical V1 draft, reorder actual site/state traversal, not the
irrelevant frames dictionary. No absence, terrain or physical waiver is added.
"""
from pathlib import Path
from copy import deepcopy
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[5]
WORKSPACE = PROJECT.parent
REPORT = PROJECT / 'build/reports/complete-town-20261028-v1/approved-implementation-v1/physical-refinement-v1'
FIXTURE = REPORT / 'fixture-v3/runeterra-bilgewater'
sys.path.insert(0, str(WORKSPACE / 'scripts'))
import faction_town_layout as actual

def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

design_path = FIXTURE / 'design/town-visuals.json'
design_bytes = design_path.read_bytes()
design = json.loads(design_bytes)
contract_path = FIXTURE / design['layout_contract']['path']
contract_bytes = contract_path.read_bytes()
contract = json.loads(contract_bytes)
content = {'factions': json.loads((FIXTURE / 'content/factions.json').read_bytes())}
results = []
try:
    for key in contract['frames']:
        current = deepcopy(contract)
        site = next(site for site in current['sites'] if key in site['states'])
        current['sites'].remove(site)
        current['sites'].insert(0, site)
        site['states'] = [key] + [state for state in site['states'] if state != key]
        assert sum(map(lambda site: len(site['states']), current['sites'])) == 35
        assert len(current['sites']) == 18
        contract_path.write_bytes(encoded(current))
        current_design = deepcopy(design)
        current_design['layout_contract']['sha256'] = sha(contract_path)
        design_path.write_bytes(encoded(current_design))
        errors, dependencies = actual.inspect(FIXTURE, content, 'bilgewater')
        result = {'errors': errors, 'dependency_count': len(dependencies)}
        row = {'first_site': site['id'], 'first_state': key, 'result': result}
        results.append(row)
        (REPORT / 'semantic-candidate-v3-triage.json').write_bytes(encoded({
            'status': 'authored configuration', 'actual_consumer': str(actual.__file__),
            'consumer_sha256': sha(Path(actual.__file__)), 'case_count': len(results),
            'all35states_and18sites_retained_each_case': True,
            'whole_baseline_pass_claimed': False, 'results': results,
        }))
        print(key + ': ' + str(result), flush=True)
finally:
    contract_path.write_bytes(contract_bytes)
    design_path.write_bytes(design_bytes)
    assert contract_path.read_bytes() == contract_bytes
    assert design_path.read_bytes() == design_bytes
(REPORT / 'v1-triage-method-correction.json').write_bytes(encoded({
    'status': 'authored configuration',
    'historical_file': 'semantic-candidate-v1-triage.json',
    'historical_error': 'Reordering frames did not reorder physical traversal; all cases were effectively the same blacksmith-first evaluation.',
    'historical_first_state_coverage_valid': False,
    'corrected_method': 'Reorder actual sites and site.states while preserving all35states/18sites and rebinding exact fixture contract pins.',
    'corrected_result': 'semantic-candidate-v3-triage.json',
}))
