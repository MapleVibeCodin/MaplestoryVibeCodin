"""Replay game-window pixels from reported failures, never the desktop IGN label."""
import unittest
from pathlib import Path
import cv2
from name_finder import NameFinder

ROOT=Path(__file__).parent/'regression_samples'
class ReportedMisses(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cv2.setNumThreads(1)
        cls.finder=NameFinder()

    def test_visible_names_and_marker_coordinates(self):
        cases=[('jtedoigte','141333',(704,87)),('iSadlyfe','143200',(623,289)),
               ('Oral','222618',(241,617)),('FoxGod','060516',(1152,179)),
               ('Kilerious','085956',(621,296))]
        for name,suffix,(x,y) in cases:
            with self.subTest(name=name):
                hit=self.finder.scan(cv2.imread(str(ROOT/(name.lower()+'_'+suffix+'.png'))),name)
                self.assertIsNotNone(hit)
                l,t,r,b=hit.box
                self.assertTrue(l<=x<=r and t<=y<=b,hit)
                if name=='Kilerious':self.assertEqual(hit.mode,'CONFUSABLE')

    def test_unreadable_or_wrong_room_does_not_invent_a_match(self):
        for name,suffix in [('Snapkin','072432'),('Kilerious','090017')]:
            with self.subTest(name=name):
                self.assertIsNone(self.finder.scan(cv2.imread(str(ROOT/(name.lower()+'_'+suffix+'.png'))),name))

    def test_similar_names_and_short_prefixes_rejected(self):
        cases=[('oral_222618.png',['Ora','Oran','Bral','God']),
               ('foxgod_060516.png',['FoxGo','FoxGox','NotHere']),
               ('kilerious_085956.png',['Kiler','Kilerio','Kileriaus'])]
        for file,names in cases:
            im=cv2.imread(str(ROOT/file))
            for name in names:
                with self.subTest(name=name):self.assertIsNone(self.finder.scan(im,name))
