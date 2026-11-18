"""Quick queue sweep keeps identity checks and retains weak-name recovery."""
from pathlib import Path
import unittest
from unittest.mock import patch
import cv2
from name_finder import NameFinder
from test_new_screenshot_names import CASES
ROOT=Path(__file__).parent

class QuickSweepTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cv2.setNumThreads(1);cls.finder=NameFinder()

    def test_clear_sellers_found_in_quick_pass(self):
        image=cv2.imread(str(ROOT/'regression_samples/cernia.png'))
        for name,point in [('Cernia',(1270,585)),('Melonade',(1085,585))]:
            hit=self.finder.scan(image,name,quick_only=True)
            self.assertIsNotNone(hit)
            x,y,r,b=hit.box;self.assertTrue(x<=point[0]<=r and y<=point[1]<=b)

    def test_quick_or_recovery_finds_all_uploaded_readable_names(self):
        for stamp,crop,name,(x,y) in CASES:
            with self.subTest(name=name):
                l,t,r,b=crop
                image=cv2.imread(str(ROOT/f'Screenshot 2026-11-16 {stamp}.png'))[t:b,l:r]
                hit=self.finder.scan(image,name,quick_only=True)
                if hit is None:hit=self.finder.scan(image,name)
                self.assertIsNotNone(hit)
                a,c,d,e=hit.box;self.assertTrue(a<=x-l<=d and c<=y-t<=e)

    def test_weak_names_still_recover_after_quick_miss(self):
        image=cv2.imread(str(ROOT/'Screenshot 2026-11-16 141643.png'))[210:978,1:1360]
        for name in ['MilkToast','FightClub']:
            self.assertIsNone(self.finder.scan(image,name,quick_only=True))
            self.assertIsNotNone(self.finder.scan(image,name))

    def test_substrings_and_wrong_names_are_not_fast_marked(self):
        image=cv2.imread(str(ROOT/'regression_samples/cernia.png'))
        for name in ['Melon','Melonades','Cern','NotHere','NobodyHere','NobodyElse']:
            self.assertIsNone(self.finder.scan(image,name,quick_only=True),name)

    def test_duplicate_visible_names_remain_ambiguous(self):
        image=cv2.imread(str(ROOT/'regression_samples/cernia.png'))
        image[400:425,700:775]=image[572:597,1045:1120].copy()
        self.assertIsNone(self.finder.scan(image,'Melonade',quick_only=True))

    def test_cancelled_sweep_does_not_build_candidates(self):
        with patch.object(self.finder,'_candidates',side_effect=AssertionError('stale')):
            self.assertIsNone(self.finder.scan(None,'Melonade',quick_only=True,cancelled=lambda:True))
