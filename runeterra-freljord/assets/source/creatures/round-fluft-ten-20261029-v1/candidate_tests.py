"""Execute bounded compiler/source regressions before candidate selection."""
from pathlib import Path
from copy import deepcopy
import io
import json
import unittest

from PIL import Image
from validate_packet import validate_packet,validate_recipe,validate_payloads,read,COHORT

P=Path(__file__).resolve().parents[4]


class SphericalFluftCandidate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payloads=validate_packet(P)
        cls.packet=read(P/(COHORT+'source-selection.json'))
        cls.battle=read(P/(COHORT+'recipes/battle.json'))

    def test_actual_all_six_roles_compile_to_exact_71_output_closure(self):
        self.assertEqual(len(self.payloads),71)
        self.assertTrue(validate_payloads(self.payloads,self.packet['outputs']))

    def test_old_actual_portrait_source_cannot_replace_new_body_even_with_valid_hash(self):
        recipe=deepcopy(self.battle)
        old=read(P/(COHORT+'before-selection/recipes/battle.json'))
        recipe['groups'][0]['frames'][0]=deepcopy(old['groups'][0]['frames'][0])
        with self.assertRaisesRegex(ValueError,'Retired or foreign'):validate_recipe(P,recipe)

    def test_loss_of_native_launch_or_landing_is_rejected(self):
        for group in (20,21):
            recipe=deepcopy(self.battle)
            recipe['groups']=[g for g in recipe['groups'] if g['group']!=group]
            with self.assertRaisesRegex(ValueError,'native action groups'):validate_recipe(P,recipe)

    def test_one_repeated_still_cannot_supply_roll_cycle(self):
        recipe=deepcopy(self.battle)
        recipe['groups'][0]['frames']=[deepcopy(recipe['groups'][0]['frames'][0]) for _ in range(6)]
        with self.assertRaisesRegex(ValueError,'Still/repeated motion'):validate_recipe(P,recipe)

    def test_actual_native_body_translation_or_rgb_mutation_is_rejected(self):
        name=next(n for n in self.payloads if n.endswith('g0-f0.png') or n.endswith('g00-f000.png'))
        original=Image.open(io.BytesIO(self.payloads[name])).convert('RGBA')
        for mutation in ('root','body'):
            im=original.copy()
            if mutation=='root':
                im=Image.new('RGBA',original.size);im.paste(original,(1,0))
            else:
                point=max(((x,y) for y in range(im.height) for x in range(im.width)),key=lambda p:im.getpixel(p)[3])
                pixel=im.getpixel(point);im.putpixel(point,(pixel[0]^1,*pixel[1:]))
            buffer=io.BytesIO();im.save(buffer,format='PNG')
            payloads=dict(self.payloads);payloads[name]=buffer.getvalue()
            with self.assertRaisesRegex(ValueError,'payload/root/body'):validate_payloads(payloads,self.packet['outputs'])

    def test_generated_leftovers_are_rejected(self):
        payloads=dict(self.payloads);payloads['retired-running-frame.png']=b'old'
        with self.assertRaisesRegex(ValueError,'closure'):validate_payloads(payloads,self.packet['outputs'])


if __name__=='__main__':unittest.main(verbosity=2)
