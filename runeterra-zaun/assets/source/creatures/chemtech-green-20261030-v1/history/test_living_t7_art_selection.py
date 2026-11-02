"""Exercise selected T7 art and exported native resources, not only a planner.

These checks establish selection/serialization closure. They cannot approve the
painted anatomy, native motion/contact, balance or release rights.
"""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
WORKSPACE = PROJECT.parent
sys.path.insert(0, str(WORKSPACE / 'scripts'))
import faction_artifacts as converter

UNITS = ('chemGolem', 'pressureColossus')
ROLES = ('battle', 'map', 'large', 'small', 'attackLeft', 'attackRight')
COHORT = 'assets/source/creatures/living-chemtech-tubes-20261028-v1/'
PREFIX = 'Content/Sprites/runeterra/zaun/'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def descriptors(recipe):
    if 'groups' in recipe:
        return [frame for group in recipe['groups'] for frame in group['frames']]
    return [{'source': recipe['source'], 'source_sha256': recipe['source_sha256']}]


class LivingT7SelectedArt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location(
            '_living_selected_action_planner', PROJECT / 'scripts/art_recipes.py')
        cls.planner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.planner)
        cls.creatures = read(PROJECT / 'content/creatures.json')
        backend_spec = importlib.util.spec_from_file_location(
            '_living_selected_native_backend', PROJECT / 'scripts/native_backend.py')
        cls.backend = importlib.util.module_from_spec(backend_spec)
        backend_spec.loader.exec_module(cls.backend)

    def recipe(self, unit, role):
        return read(PROJECT / f'assets/recipes/creatures/{unit}-{role}.json')

    def expected_groups(self, unit):
        return {group: count for group, _, count in
                self.planner.creature_actions(self.creatures[unit])}

    def require_motion(self, unit, groups):
        self.assertEqual(len(groups), len({group for group, _ in groups}),
                         'Native movement resource contains duplicate groups')
        self.assertEqual(self.expected_groups(unit), dict(groups),
                         f'{unit}: selected/exported actions differ from current abilities')

    def require_living_sources(self, unit, recipe):
        root = COHORT + unit + '/'
        for descriptor in descriptors(recipe):
            self.assertTrue(descriptor['source'].startswith(root),
                            f'{unit}: retired or foreign body source {descriptor["source"]}')
        generation = recipe['generation']
        self.assertTrue(generation['painted_master'].startswith(root),
                        f'{unit}: retired mechanical painted master')
        for master in generation.get('supplemental_masters', []):
            self.assertTrue(master['path'].startswith(root),
                            f'{unit}: retired mechanical supplemental master')

    def test_native_consumer_uses_twenty_and_twenty_one_and_skips_absent_phases(self):
        native = WORKSPACE / 'vcmi-develop/vcmi-develop/client/battle'
        constants = (native / 'BattleConstants.h').read_text(encoding='utf-8')
        self.assertRegex(constants, r'MOVE_START\s*=\s*20')
        self.assertRegex(constants, r'MOVE_END\s*=\s*21')
        classes = (native / 'BattleAnimationClasses.cpp').read_text(encoding='utf-8')
        for class_name, group in [('MovementStartAnimation', 'MOVE_START'),
                                  ('MovementEndAnimation', 'MOVE_END')]:
            method = classes.split('bool ' + class_name + '::init()', 1)[1].split('\n}', 1)[0]
            compact = re.sub(r'\s+', '', method)
            self.assertIn('autogroupID=ECreatureAnimType::' + group + ';', compact)
            self.assertIn('if(!myAnim->framesInGroup(groupID)){deletethis;returnfalse;}', compact)
            self.assertIn('myAnim->setType(groupID);', compact)

    def test_all_selected_body_roles_use_fresh_living_cohort_and_real_hashes(self):
        for unit in UNITS:
            for role in ROLES:
                with self.subTest(unit=unit, role=role):
                    recipe = self.recipe(unit, role)
                    self.require_living_sources(unit, recipe)
                    for descriptor in descriptors(recipe):
                        self.assertEqual(descriptor.get('source_sha256', descriptor.get('sha256')),
                                         sha(PROJECT / descriptor['source']))
                    generation = recipe['generation']
                    self.assertEqual(generation['painted_master_sha256'],
                                     sha(PROJECT / generation['painted_master']))
                    for master in generation.get('supplemental_masters', []):
                        self.assertEqual(master['sha256'], sha(PROJECT / master['path']))

    def test_selected_actions_survive_actual_converter_as_complete_native_resources(self):
        for unit in UNITS:
            with self.subTest(unit=unit):
                recipe = self.recipe(unit, 'battle')
                self.require_motion(unit, [(g['group'], len(g['frames'])) for g in recipe['groups']])
                self.assertEqual(self.expected_groups(unit),
                                 {int(k): v for k, v in recipe['required_groups'].items()})
                captured = {}
                def collect(path, payload, resume, check):
                    self.assertNotIn(path, captured)
                    captured[path] = payload
                with patch.object(converter, 'store_output', side_effect=collect):
                    result = converter.convert_animation(PROJECT, recipe, PREFIX, False, {})
                definition_path = PROJECT / 'assets/generated' / recipe['output_path']
                definition = json.loads(captured[definition_path])
                self.require_motion(unit, [(g['group'], len(g['frames'])) for g in definition['sequences']])
                self.assertEqual({str(k): v for k, v in self.expected_groups(unit).items()},
                                 result['required_groups'])
                sources = {g['group']: g['frames'] for g in recipe['groups']}
                for sequence in definition['sequences']:
                    for index, filename in enumerate(sequence['frames']):
                        exported = PROJECT / 'assets/generated/Content/Sprites' / definition['basepath'] / filename
                        self.assertEqual((PROJECT / sources[sequence['group']][index]['source']).read_bytes(),
                                         captured[exported])

    def test_generated_native_resources_and_frames_match_the_selected_actions(self):
        for unit in UNITS:
            with self.subTest(unit=unit):
                recipe = self.recipe(unit, 'battle')
                definition = read(PROJECT / 'assets/generated' / recipe['output_path'])
                self.require_motion(unit, [(g['group'], len(g['frames'])) for g in definition['sequences']])
                sources = {g['group']: g['frames'] for g in recipe['groups']}
                for sequence in definition['sequences']:
                    for index, filename in enumerate(sequence['frames']):
                        exported = PROJECT / 'assets/generated/Content/Sprites' / definition['basepath'] / filename
                        self.assertEqual(sha(PROJECT / sources[sequence['group']][index]['source']),
                                         sha(exported), f'{unit}: stale generated frame {filename}')

    def test_regression_controls_reject_missing_leap_and_retired_metal_body(self):
        complete = list(self.expected_groups('pressureColossus').items())
        self.require_motion('pressureColossus', complete)
        for missing in (20, 21):
            with self.subTest(missing=missing), self.assertRaises(AssertionError):
                self.require_motion('pressureColossus', [(g, count) for g, count in complete if g != missing])
        # Both the metal chassis and the superseded pre-violet-tube organic
        # cohort are historical. A live-frame reference cannot revive either.
        for retired in ('humanoid-20261025-v1', 'living-chemtech-20261028-v1'):
            wrong = deepcopy(self.recipe('chemGolem', 'battle'))
            wrong['groups'][0]['frames'][0]['source'] = (
                f'assets/source/creatures/{retired}/chemGolem/native-v1/old.png')
            with self.subTest(retired=retired), self.assertRaisesRegex(AssertionError, 'retired or foreign body source'):
                self.require_living_sources('chemGolem', wrong)

    def test_real_production_gate_requires_selected_and_compiled_leap_phases(self):
        pipeline = SimpleNamespace(root=PROJECT, content=lambda: {
            'creatures': {unit: self.creatures[unit] for unit in UNITS}})
        recipes = {f'assets/recipes/creatures/{unit}-battle.json': self.recipe(unit, 'battle')
                   for unit in UNITS}
        self.assertEqual([], self.backend._movement_phase_errors(pipeline, recipes))

    def test_real_production_gate_negative_controls_cover_each_native_phase(self):
        recipe = {'output_path': 'Content/Sprites/' + self.creatures['pressureColossus']['graphics']['animation'],
                  'groups': [{'group': group, 'frames': ['authored.png'] * count}
                             for group, count in self.expected_groups('pressureColossus').items()]}
        name = 'assets/recipes/creatures/pressureColossus-battle.json'
        native = {'basepath': '', 'sequences': deepcopy(recipe['groups'])}
        with tempfile.TemporaryDirectory(prefix='zaun-flight-gate-') as folder:
            project = Path(folder)
            target = project / 'assets/generated' / recipe['output_path']
            target.parent.mkdir(parents=True)
            pipeline = SimpleNamespace(root=project, content=lambda: {
                'creatures': {unit: self.creatures[unit] for unit in UNITS}})
            def validate(selected, definition):
                target.write_text(json.dumps(definition), encoding='utf-8')
                return self.backend._movement_phase_errors(pipeline, {name: selected})
            self.assertEqual([], validate(recipe, native))
            for label, field in [('selected recipe', 'groups'), ('generated native animation', 'sequences')]:
                for group in (20, 21):
                    for defect in ('missing', 'short', 'duplicate'):
                        with self.subTest(label=label, group=group, defect=defect):
                            selected, definition = deepcopy(recipe), deepcopy(native)
                            changed = selected if field == 'groups' else definition
                            if defect == 'missing':
                                changed[field] = [entry for entry in changed[field] if entry['group'] != group]
                            elif defect == 'short':
                                next(entry for entry in changed[field] if entry['group'] == group)['frames'].pop()
                            else:
                                changed[field].append(deepcopy(next(entry for entry in changed[field] if entry['group'] == group)))
                            errors = validate(selected, definition)
                            self.assertTrue(any(label + ' requires native flight group ' + str(group) in error
                                                for error in errors), errors)
            # This addition does not impose a new exact frame count on walking
            # variants or forbid longer genuine launch/landing cohorts.
            extended = deepcopy(recipe)
            for entry in extended['groups']:
                if entry['group'] in (20, 21):
                    entry['frames'].append('additional-authored.png')
            self.assertEqual([], validate(extended, {'sequences': deepcopy(extended['groups'])}))
            for field in ('groups', 'sequences'):
                for malformed in (None, {}, [{'group': [], 'frames': []}]):
                    with self.subTest(field=field, malformed=malformed):
                        selected, definition = deepcopy(recipe), deepcopy(native)
                        (selected if field == 'groups' else definition)[field] = malformed
                        self.assertTrue(validate(selected, definition))
            self.assertTrue(validate(recipe, []))


if __name__ == '__main__':
    unittest.main(verbosity=2)
