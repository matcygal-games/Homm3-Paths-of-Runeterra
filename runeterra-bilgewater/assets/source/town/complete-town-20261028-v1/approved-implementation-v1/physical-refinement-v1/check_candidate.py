"""Run the unchanged public geometry consumer in an owned isolated fixture.

This is technical source verification, never a native launch or release gate.
The art owner supplies real compiler outputs before a complete baseline runs.
"""
from pathlib import Path
from copy import deepcopy
import argparse
import datetime
import hashlib
import io
import json
import sys

from PIL import Image, ImageChops, ImageDraw

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[5]
WORKSPACE = PROJECT.parent
REPORTS = PROJECT / 'build/reports/complete-town-20261028-v1/approved-implementation-v1/physical-refinement-v1'
sys.path.insert(0, str(WORKSPACE / 'scripts'))
import faction_town_layout as layout
import faction_pipeline as fp
import faction_production as production
import faction_art_compile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def png(image):
    stream = io.BytesIO()
    image.save(stream, format='PNG', compress_level=9)
    return stream.getvalue()


def image(path):
    with Image.open(path) as value:
        value.load()
        return value.convert('RGBA')


def binary(path):
    return image(path).convert('L')


def points(mask):
    bounds = mask.getbbox()
    if not bounds:
        return set()
    pixels = mask.load()
    return {(x, y) for y in range(bounds[1], bounds[3])
            for x in range(bounds[0], bounds[2]) if pixels[x, y]}


def click_exposure(fixture, content, contract):
    """Source exposure through real area PNGs and inherited native families.

    Native receiveEvent rejects transparent area pixels, while hover prefers
    the greatest z. This reports that limited source property, not UI input.
    """
    town = content['factions']['bilgewater']['town']
    effective = fp.utility('validation').effective_faction(content['factions']['bilgewater'])['town']['buildings']
    groups = {}
    for state in contract['frames']:
        base, distance, seen = state, 0, set()
        while effective[base].get('upgrades'):
            if base in seen:
                raise ValueError('Cyclic actual native building ancestry')
            seen.add(base)
            base = effective[base]['upgrades']
            distance += 1
        groups[state] = (base, distance)
    masks, resources = {}, {}
    for state, reference in contract['frames'].items():
        source = fixture / 'assets/generated/Content/Sprites' / town['structures'][state]['area']
        area = image(source).getchannel('A').point(lambda alpha: 255 if alpha else 0)
        full = image(fixture / reference['path']).getchannel('A').point(lambda alpha: 255 if alpha >= 8 else 0)
        if not area.getbbox() or ImageChops.subtract(area, full).getbbox():
            raise ValueError('Actual click area is empty or leaves its real visible silhouette: ' + state)
        masks[state] = area
        resources[state] = {'path': source.relative_to(fixture).as_posix(), 'sha256': sha(source)}
    full = [state for state in contract['silhouette_plan']['complete_scene_states']
            if next(site['id'] for site in contract['sites'] if state in site['states']) not in ('coast', 'grail')]
    scenarios = {}
    for state in contract['frames']:
        selection = [other for other in full if groups[other][0] != groups[state][0]] + [state]
        selected_by_base = {}
        for member in selection:
            base, distance = groups[member]
            if base not in selected_by_base or distance > groups[selected_by_base[base]][1]:
                selected_by_base[base] = member
        scenarios['full-others-with-' + state] = sorted(selected_by_base.values(), key=lambda member: town['structures'][member]['z'])
    scenarios['ordinary-full'] = sorted(full, key=lambda member: town['structures'][member]['z'])
    results = []
    for name, selected in scenarios.items():
        rows = []
        for state in selected:
            exposed = masks[state].copy()
            for front in selected:
                if town['structures'][front]['z'] > town['structures'][state]['z']:
                    exposed = ImageChops.subtract(exposed, masks[front])
            count = exposed.histogram()[255]
            if not count:
                raise ValueError('No exposed actual native click pixels in ' + name + ': ' + state)
            rows.append({'state': state, 'exposed_pixels': count,
                         'exposed_bounds': list(exposed.getbbox()),
                         'total_click_pixels': masks[state].histogram()[255]})
        results.append({'scene': name, 'native_visible_states': selected, 'source_exposure': rows})
    return {'scope': 'Actual generated area-alpha masks, inherited building-family selection and z exposure; no native UI interaction or readability acceptance.',
            'native_consumer_references': ['lib/entities/faction/CTownHandler.cpp:loadStructure',
                                           'client/windows/CCastleInterface.cpp:CCastleBuildings::recreate',
                                           'client/windows/CCastleInterface.cpp:CBuildingRect::receiveEvent'],
            'native_library_sha256': sha(WORKSPACE / 'vcmi-develop/vcmi-develop/config/buildingsLibrary.json'),
            'actual_area_resources': resources, 'scenes': results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture', type=Path, required=True)
    parser.add_argument('--attempt', required=True)
    parser.add_argument('--negative', action='store_true')
    parser.add_argument('--retaining-target', type=Path)
    args = parser.parse_args()
    if not args.attempt.replace('-', '').isalnum():
        raise ValueError('Use a unique simple attempt name')
    fixture = args.fixture.resolve()
    if not fixture.is_relative_to(REPORTS.resolve()) or not fixture.is_dir():
        raise ValueError('Fixture must be an existing owned physical-report directory')
    for path in (fixture, *fixture.parents):
        if path.is_symlink() or getattr(path.lstat(), 'st_file_attributes', 0) & 0x400:
            raise ValueError('Redirected fixture ancestor')
    report = REPORTS / ('consumer-' + args.attempt)
    report.mkdir(parents=True, exist_ok=False)
    helper = WORKSPACE / 'scripts/faction_town_layout.py'
    helper_pin = sha(helper)
    consumers = {name: sha(WORKSPACE / name) for name in (
        'scripts/faction_town_layout.py', 'scripts/faction_pipeline.py',
        'scripts/faction_production.py', 'scripts/faction_art_compile.py',
        'scripts/faction_sdk_profile.py', 'runeterra-demacia/scripts/common.py',
        'runeterra-demacia/scripts/identity.py', 'runeterra-demacia/scripts/validation.py')}
    design_path = fixture / 'design/town-visuals.json'
    design = load(design_path)
    contract_name = design['layout_contract']['path']
    contract_path = fixture / contract_name
    contract = load(contract_path)
    if sha(contract_path) != design['layout_contract']['sha256']:
        raise ValueError('Fixture selected contract changed')
    content = {'factions': load(fixture / 'content/factions.json')}
    compiler = faction_art_compile.create_compiler('bilgewater')
    before = {path.relative_to(fixture).as_posix(): sha(path)
              for path in fixture.rglob('*') if path.is_file()}
    errors, dependencies = layout.inspect(fixture, content, 'bilgewater')
    declared = layout.dependency_paths(fixture)
    exported = production._current_town_layout_source_entries(
        fp.Pipeline(fixture, 'runeterra-bilgewater', 'bilgewater'), {})
    closure = {}
    for path in declared:
        relative = path.relative_to(fixture).as_posix()
        pin = sha(path)
        if hashlib.sha256(exported['runeterra-bilgewater/' + relative]).hexdigest() != pin:
            raise ValueError('Actual source collector differs: ' + relative)
        closure[relative] = pin
    outcomes = []
    plan = contract['silhouette_plan']
    fixed = {key: sha(fixture / plan[key]['path']) for key in
             ('support_mask', 'stairs_mask', 'water_mask', 'paths_mask')}
    fixed['background'] = sha(fixture / contract['background']['path'])
    click_result = click_exposure(fixture, content, contract) if not errors else None

    def execute(label, mutate, diagnostic, *, changed_environment=()):
        saved = {}
        candidate = deepcopy(contract)

        def put(path, data):
            if not path.is_relative_to(fixture):
                raise ValueError('Mutation leaves owned fixture')
            if path not in saved:
                saved[path] = path.read_bytes()
            path.write_bytes(data)

        def save(reference, value):
            path = fixture / reference['path']
            put(path, png(value))
            reference['sha256'] = sha(path)

        try:
            facts = mutate(candidate, put, save)
            put(contract_path, encoded(candidate))
            candidate_design = deepcopy(design)
            candidate_design['layout_contract']['sha256'] = sha(contract_path)
            put(design_path, encoded(candidate_design))
            observed, _ = layout.inspect(fixture, content, 'bilgewater')
            current = {key: sha(fixture / candidate['silhouette_plan'][key]['path'])
                       for key in ('support_mask', 'stairs_mask', 'water_mask', 'paths_mask')}
            current['background'] = sha(fixture / candidate['background']['path'])
            environment_ok = all(current[key] == pin for key, pin in fixed.items()
                                 if key not in changed_environment)
            passed = bool(observed) and any(diagnostic in error for error in observed) and environment_ok
            folder = report / 'negative-cases' / label
            for path in saved:
                destination = folder / 'changed-inputs' / path.relative_to(fixture)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(path.read_bytes())
            result = {'control': label, 'passed': passed, 'errors': observed,
                      'actual_consumer': 'scripts/faction_town_layout.py:inspect',
                      'helper_sha256': helper_pin, 'control_facts': facts,
                      'consumer_source_pins': consumers,
                      'fixed_environment_sha256': fixed, 'current_environment_sha256': current,
                      'unchanged_environment_ok': environment_ok,
                      'baseline_contract_sha256': design['layout_contract']['sha256'],
                      'mutated_contract_sha256': sha(contract_path),
                      'changed_inputs': {path.relative_to(fixture).as_posix(): sha(path) for path in saved}}
            (folder / 'raw-result.json').write_bytes(encoded(result))
            outcomes.append(result)
            if not passed:
                raise ValueError('Consumer did not reject at the intended boundary: ' + label)
        finally:
            for path, data in saved.items():
                path.write_bytes(data)
        restored, _ = layout.inspect(fixture, content, 'bilgewater')
        if restored != errors:
            raise ValueError('Exact valid baseline was not restored')

    def move_onto(target, label):
        target_points = points(target)
        samples = sorted(target_points, key=lambda point: (point[1], point[0]))[::8]
        choices = []
        for site in contract['sites']:
            if site['id'] in ('coast', 'grail') or len(site['states']) != 1:
                continue
            state = site['states'][0]
            record = plan['states'][state]
            native = image(fixture / contract['frames'][state]['path'])
            if native.getchannel('A').point(lambda alpha: 255 if alpha >= 128 else 0).histogram()[255] < 600:
                continue
            root = binary(fixture / record['foundation_mask']['path'])
            root_points = points(root)
            rb = root.getbbox()
            cx, cy = (rb[0] + rb[2]) // 2, (rb[1] + rb[3]) // 2
            masks = [native.getchannel('A').point(lambda alpha: 255 if alpha >= 8 else 0)]
            masks.extend(binary(fixture / record[key]['path'])
                         for key in ('foundation_mask', 'door_mask', 'approach_mask'))
            union = masks[0]
            for mask in masks[1:]:
                union = ImageChops.lighter(union, mask)
            bounds = union.getbbox()
            seen = set()
            for x, y in samples:
                dx, dy = x - cx, y - cy
                if (dx, dy) in seen or (dx == 0 and dy == 0):
                    continue
                seen.add((dx, dy))
                if not (0 <= bounds[0] + dx < bounds[2] + dx <= 800
                        and 0 <= bounds[1] + dy < bounds[3] + dy <= 374):
                    continue
                hit = sum((px + dx, py + dy) in target_points for px, py in root_points)
                if hit >= min(20, len(root_points)):
                    choices.append((dx * dx + dy * dy, -hit, state, dx, dy))
        if not choices:
            raise ValueError('No unclipped actual building displacement reaches ' + label)
        _, _, state, dx, dy = min(choices)

        def mutate(candidate, put, save):
            record = candidate['silhouette_plan']['states'][state]
            frame_ref = candidate['frames'][state]

            def shift(reference):
                original = image(fixture / reference['path'])
                moved = Image.new('RGBA', original.size)
                moved.paste(original, (dx, dy))
                save(reference, moved)

            shift(frame_ref)
            for key in ('foundation_mask', 'body_mask', 'door_mask', 'approach_mask'):
                if key in record:
                    source = binary(fixture / record[key]['path'])
                    moved = Image.new('L', source.size)
                    moved.paste(source, (dx, dy))
                    save(record[key], moved)
            entrance = record.get('entrance', next(site['entrance'] for site in candidate['sites'] if state in site['states']))
            record['entrance'] = [entrance[0] + dx, entrance[1] + dy]
            site = next(site for site in candidate['sites'] if state in site['states'])
            site['entrance'] = record['entrance']
            native = image(fixture / frame_ref['path'])
            silhouette = native.getchannel('A').point(lambda alpha: 255 if alpha >= 8 else 0)
            save(site['silhouette_mask'], silhouette)
            bounds = silhouette.getbbox()
            site['box'] = [bounds[0], bounds[1], bounds[2] - bounds[0], bounds[3] - bounds[1]]
            structure = content['factions']['bilgewater']['town']['structures'][state]
            definition = load(fixture / 'assets/generated/Content/Sprites' / structure['animation'])
            frame = fp.utility('identity').animation_groups(definition, complete=True)[0][0]
            selected = fixture / 'assets/generated/Content/Sprites' / (definition.get('basepath', '') + frame)
            output_name = 'Content/Sprites/' + structure['animation']
            producers = [(path, load(path)) for path in (fixture / 'assets/recipes/town').rglob('*.json')]
            producers = [(path, value) for path, value in producers if value.get('output_path') == output_name]
            if len(producers) != 1:
                raise ValueError('Real frame mutation requires its unique actual candidate recipe: ' + state)
            recipe_path, recipe = producers[0]
            groups = recipe.get('groups', [])
            group_zero = [group for group in groups if group.get('group') == 0]
            if len(group_zero) != 1 or len(group_zero[0].get('frames', [])) != 1:
                raise ValueError('Physical mutation needs the actual one-frame static town producer')
            descriptor = group_zero[0]['frames'][0]
            if descriptor.get('source') != frame_ref['path']:
                raise ValueError('Mutation cannot silently substitute a different producer source')
            descriptor['source_sha256'] = frame_ref['sha256']
            if 'sha256' in descriptor:
                descriptor['sha256'] = frame_ref['sha256']
            put(recipe_path, encoded(recipe))
            produced, conversion = compiler.plan(fixture, recipe_path)
            for relative, data in produced.items():
                put(fixture / 'assets/generated' / relative, data)
            root = binary(fixture / record['foundation_mask']['path'])
            return {'state': state, 'offset': [dx, dy], 'target': label,
                    'root_on_fixed_stairs': ImageChops.multiply(root, binary(fixture / plan['stairs_mask']['path'])).histogram()[255],
                    'root_on_fixed_water': ImageChops.multiply(root, binary(fixture / plan['water_mask']['path'])).histogram()[255],
                    'root_outside_fixed_level_support': ImageChops.subtract(root, binary(fixture / plan['support_mask']['path'])).histogram()[255],
                    'actual_frame_and_physical_masks_moved': True,
                    'selected_generated_matches_mutated_source': sha(selected) == sha(fixture / frame_ref['path']),
                    'actual_mutant_compiler_receipt': conversion}
        return mutate

    if args.negative and not errors:
        execute('actual-building-displaced-onto-fixed-stairs',
                move_onto(binary(fixture / plan['stairs_mask']['path']), 'actual painted public stairs'),
                'Actual foundation lacks level support or lands on stairs/water')
        execute('actual-building-displaced-onto-fixed-water',
                move_onto(binary(fixture / plan['water_mask']['path']), 'actual external water'),
                'Actual foundation lacks level support or lands on stairs/water')
        if args.retaining_target:
            target = args.retaining_target.resolve()
            if not target.is_relative_to(HERE):
                raise ValueError('Retaining target must be a direct owned source annotation')
            execute('actual-building-displaced-onto-retaining-face',
                    move_onto(binary(target), 'manually traced actual retaining face'),
                    'Actual foundation lacks level support or lands on stairs/water')

        def blocked_path(candidate, put, save):
            paths = binary(fixture / candidate['silhouette_plan']['paths_mask']['path'])
            land = binary(fixture / candidate['land_mask']['path'])
            path_points = points(paths)
            for state, record in candidate['silhouette_plan']['states'].items():
                frame = image(fixture / candidate['frames'][state]['path'])
                body = frame.getchannel('A').point(lambda alpha: 255 if alpha >= 128 else 0)
                solid = ImageChops.subtract(body, binary(fixture / record['door_mask']['path']))
                candidates = points(solid)
                if not candidates:
                    continue
                anchor = record.get('entrance', next(site['entrance'] for site in candidate['sites'] if state in site['states']))
                for point in sorted(candidates, key=lambda p: (abs(p[0] - anchor[0]) + abs(p[1] - anchor[1]), p[1], p[0]))[:32]:
                    start = min(path_points, key=lambda p: (abs(p[0] - point[0]) + abs(p[1] - point[1]), p[1], p[0]))
                    changed = paths.copy()
                    # A cardinal dogleg stays connected even when the target
                    # is diagonal to the existing public path.
                    ImageDraw.Draw(changed).line([start, (point[0], start[1]), point], fill=255, width=1)
                    if ImageChops.subtract(changed, land).getbbox():
                        continue
                    save(candidate['silhouette_plan']['paths_mask'], changed)
                    return {'state': state, 'wrong_path_enters_actual_opaque_pixel': list(point),
                            'extension_starts_on_existing_path': list(start),
                            'pixel_outside_real_doorway': True, 'source_frames_unchanged': True}
            raise ValueError('No actual opaque wall witness for blocked-path control')
        execute('declared-path-enters-actual-solid-building', blocked_path,
                'Global path passes through an actual solid building outside its door',
                changed_environment=('paths_mask',))

        def stale_pin(candidate, put, save):
            state = next(iter(candidate['frames']))
            candidate['frames'][state]['sha256'] = '0' * 64
            return {'state': state, 'source_pixels_unchanged': True,
                    'boundary': 'checksum rejection only; not a physical-footing test'}
        execute('stale-frame-pin-is-a-separate-control', stale_pin, 'missing or changed')

    after = {path.relative_to(fixture).as_posix(): sha(path)
             for path in fixture.rglob('*') if path.is_file()}
    if before != after:
        raise ValueError('Isolated fixture bytes were not restored exactly')
    if sha(helper) != helper_pin:
        raise ValueError('Public consumer changed during verification')
    if any(sha(WORKSPACE / name) != pin for name, pin in consumers.items()):
        raise ValueError('A consumed technical helper changed during verification')
    receipt = {'status': 'authored configuration', 'written_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'actual_public_consumer': 'scripts/faction_town_layout.py:inspect', 'helper_sha256': helper_pin,
               'consumer_source_pins': consumers,
               'fixture': str(fixture), 'contract_path': contract_name,
               'contract_sha256': sha(contract_path), 'baseline_errors': errors,
               'valid_complete_baseline': not errors, 'source_dependencies': len(dependencies),
               'declared_dependency_count': len(declared), 'actual_collector_member_count': len(exported),
               'actual_collector_byte_closure': closure, 'controls': outcomes,
               'actual_click_area_exposure': click_result,
               'exact_fixture_restoration': before == after, 'stage_built': False,
               'native_executed': False, 'release_accepted': False}
    (report / 'receipt.json').write_bytes(encoded(receipt))
    print(json.dumps({key: receipt[key] for key in ('valid_complete_baseline', 'baseline_errors',
                                                   'source_dependencies', 'actual_collector_member_count',
                                                   'exact_fixture_restoration')}))
    if errors:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
