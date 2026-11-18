"""Game-only replay crops from the user's November 16 screenshot upload.

Coordinates are checked against in-game name labels, never browser seller text.
"""
from pathlib import Path
import unittest
import cv2
from name_finder import NameFinder

ROOT=Path(__file__).parent
CASES=[
    ('150317',(0,0,1360,770),'suc2er',(1230,590)),
    ('152324',(0,12,1360,780),'IamNotty',(588,234)),
    ('152648',(0,44,1360,812),'Meryelse',(548,392)),
    ('153119',(0,43,1360,811),'RavenNoir',(710,371)),
    ('153839',(106,40,1474,808),'Hyouden',(1274,299)),
    ('162229',(109,40,1477,808),'BigChui',(1054,178)),
]

class NewScreenshotNames(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cv2.setNumThreads(1);cls.finder=NameFinder()

    def read(self,stamp,crop,name):
        image=cv2.imread(str(ROOT/f'Screenshot 2026-11-16 {stamp}.png'))
        self.assertIsNotNone(image)
        x,y,r,b=crop
        return self.finder.scan(image[y:b,x:r],name)

    def test_new_readable_sellers_have_correct_marker_coordinates(self):
        for stamp,crop,name,(x,y) in CASES:
            with self.subTest(name=name):
                hit=self.read(stamp,crop,name)
                self.assertIsNotNone(hit,self.finder.last_diagnostic)
                l,t,r,b=hit.box
                self.assertTrue(l<=x-crop[0]<=r and t<=y-crop[1]<=b,hit)
                if name=='IamNotty':self.assertEqual(hit.mode,'CONFUSABLE')

    def test_other_rooms_browser_text_and_incorrect_spellings_are_rejected(self):
        for stamp,crop,name in [
            ('150317',(0,0,1360,770),'Lithomanium'),
            ('153839',(106,40,1474,808),'Rustle'),
            ('152648',(0,44,1360,812),'Menyelse')]:
            with self.subTest(name=name):self.assertIsNone(self.read(stamp,crop,name))
