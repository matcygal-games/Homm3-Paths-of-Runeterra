"""Candidate only: actual selected icon roots, with pinned physical crest exceptions."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from PIL import Image

def project_root():
    for ancestor in Path(__file__).resolve().parents:
        if (ancestor / 'content/creatures.json').is_file():
            return ancestor
        if (ancestor / 'runeterra-freljord/content/creatures.json').is_file():
            return ancestor / 'runeterra-freljord'
    raise RuntimeError('No local project; no checkout/cache fallback')

PROJECT = project_root()
SOURCE = PROJECT / 'tests/crest-registration'
CONTRACT_SHA256 = 'b3fd446c6479c4e4cc943b58ec27a4d107c7530b8fb7b266dca17b5d141d4247'
HELPER_SHA256 = '087a69e58610fefbc3c9f92e95896de8033f36d884a7b904ef25a4658d14f747'
for path, expected in [(SOURCE/'attack-role-mask-contract-v1.json', CONTRACT_SHA256), (SOURCE/'validate_registration.py', HELPER_SHA256)]:
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError('Missing/stale registration contract/helper before import')
spec = importlib.util.spec_from_file_location('physical_crest_registration_v1', SOURCE/'validate_registration.py')
physical = importlib.util.module_from_spec(spec)
spec.loader.exec_module(physical)
sys.path.insert(0, str(PROJECT.parent/'scripts'))
from faction_art_compile import create_compiler

class SelectedReplacementRegistration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads((SOURCE/'attack-role-mask-contract-v1.json').read_text())
        cls.roles = physical.load_roles(PROJECT, cls.contract)
        compiler = create_compiler('freljord')
        cls.images = {}
        for unit, entries in cls.roles.items():
            cls.images[unit] = {}
            for role, context in entries.items():
                recipe = PROJECT/context['entry']['active_recipe']['path']
                files, _ = compiler.plan(PROJECT, recipe)
                name = f'Content/Sprites/runeterra/freljord/creatures/{unit}/{role}.png'
                cls.images[unit][role] = Image.open(io.BytesIO(files[name])).convert('RGBA')

    def test_attack_icons_reflect_about_native_root_without_one_pixel_drift(self):
        for unit in self.roles:
            with self.subTest(unit=unit):
                self.assertTrue(physical.validate_pair(self.images[unit], self.roles[unit]))

    def test_actual_selected_icon_one_pixel_translation_is_rejected(self):
        for unit in self.roles:
            for role in ('attackLeft', 'attackRight'):
                with self.subTest(unit=unit, role=role):
                    changed = dict(self.images[unit])
                    moved = Image.new('RGBA', (64, 64))
                    moved.paste(changed[role], (1, 0))
                    changed[role] = moved
                    with self.assertRaisesRegex(ValueError, 'alpha/root'):
                        physical.validate_pair(changed, self.roles[unit])

    def test_actual_selected_body_rgb_mutation_outside_physical_mask_is_rejected(self):
        for unit in self.roles:
            for role in ('attackLeft', 'attackRight'):
                with self.subTest(unit=unit, role=role):
                    context = self.roles[unit][role]
                    point = max(((x, y) for y in range(64) for x in range(64) if not context['mask'].getpixel((x, y))), key=lambda p: context['parent'].getpixel(p)[3])
                    self.assertGreater(context['parent'].getpixel(point)[3], 0)
                    changed = dict(self.images[unit])
                    changed[role] = changed[role].copy()
                    pixel = changed[role].getpixel(point)
                    changed[role].putpixel(point, (pixel[0] ^ 1, pixel[1], pixel[2], pixel[3]))
                    with self.assertRaisesRegex(ValueError, 'Body RGBA outside'):
                        physical.validate_pair(changed, self.roles[unit])

    def test_all_role_masks_reject_missing_and_stale_bytes(self):
        with tempfile.TemporaryDirectory(prefix='freljord-role-mask-check-') as temp:
            isolated = Path(temp)
            for unit in self.roles:
                for role in ('attackLeft', 'attackRight'):
                    entry = self.roles[unit][role]['entry']['mask']
                    target = isolated/entry['path']
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with self.subTest(unit=unit, role=role, mutation='missing'):
                        with self.assertRaisesRegex(ValueError, 'Missing/stale'):
                            physical.checked(isolated, entry)
                    target.write_bytes((PROJECT/entry['path']).read_bytes())
                    self.assertEqual(physical.checked(isolated, entry), target.resolve())
                    target.write_bytes(target.read_bytes()+b'changed-mask')
                    with self.subTest(unit=unit, role=role, mutation='stale'):
                        with self.assertRaisesRegex(ValueError, 'Missing/stale'):
                            physical.checked(isolated, entry)
                    target.unlink()

if __name__ == '__main__':
    unittest.main(verbosity=2)
