import unittest
import numpy as np
from visual_excerpt import visual_key
from visual_bank import VerifiedVisualBank
from test_visual_bank import reviewed


def image(selected=False, variant=0, occluded=False, blank=False):
    p=np.empty((263,204,3),dtype=np.uint8);p[:]=(40,152,230) if selected else (227,217,205)
    p[29:37,10:18]=(20,30,40)
    if not blank:
        p[30:37,44:49]=(30,30,30)
        p[30:37,54+variant:59+variant]=(30,30,30)
    if occluded:p[28:40,44:49]=(124,75,70)
    return p.tobytes(),204,263,612


class SignatureTests(unittest.TestCase):
    def test_normal_selected_reuse(self):
        a=visual_key(image(),0);b=visual_key(image(selected=True),0)
        self.assertIsNotNone(a);self.assertEqual(a,b)
        bank=VerifiedVisualBank();bank.qualify(a,reviewed())
        self.assertIsNotNone(bank.lookup(b,eligible=True))

    def test_same_sprite_different_name_pixels(self):
        self.assertNotEqual(visual_key(image(),0),visual_key(image(variant=1),0))

    def test_blank_rejected_and_occlusion_abstains(self):
        self.assertIsNone(visual_key(image(blank=True),0))
        bank=VerifiedVisualBank();bank.qualify(visual_key(image(),0),reviewed())
        self.assertIsNone(bank.lookup(visual_key(image(occluded=True),0),eligible=False))


if __name__=='__main__':
    unittest.main()
