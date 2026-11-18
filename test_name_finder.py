import unittest
from pathlib import Path
import cv2
import numpy as np
from name_finder import NameFinder

ROOT=Path(__file__).parent
class NameFinderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cv2.setNumThreads(1)
        cls.finder=NameFinder()
        cls.room=cv2.imread(str(ROOT/'regression_samples/cernia.png'))
        cls.small=cv2.imread(str(ROOT/'regression_samples/rollermo.png'))

    def test_real_screenshots_and_coordinate_accuracy(self):
        for image,name,point,mode in [(self.room,'Cernia',(1270,585),'CONFUSABLE'),
             (self.small,'Rollermo',(524,352),'CONFUSABLE'),
             (self.room,'SpringBuck',(925,322),'EXACT'),
             (self.room,'Melonade',(1085,585),'EXACT')]:
            with self.subTest(name=name):
                hit=self.finder.scan(image,name)
                self.assertIsNotNone(hit)
                x,y,r,b=hit.box
                self.assertTrue(x<=point[0]<=r and y<=point[1]<=b)
                self.assertEqual(hit.mode,mode)

    def test_absent_names_substrings_and_nearby_spelling_rejected(self):
        for name in ['Melo','Melon','Melonadf','Spring','Cerni','NotHere','Oakhaven']:
            with self.subTest(name=name):self.assertIsNone(self.finder.scan(self.room,name))

    def test_real_wooden_nameplate(self):
        patch=cv2.imread(str(ROOT/'assets/mora_badge_test.png'))
        scene=np.full((650,1050,3),170,np.uint8);scene[370:420,180:280]=patch
        hit=self.finder.scan(scene,'Mora')
        self.assertIsNotNone(hit);self.assertEqual(hit.text,'Mora')
        self.assertTrue(hit.box[0]<230<hit.box[2])

    def test_duplicate_visible_names_not_arbitrarily_selected(self):
        scene=self.room.copy()
        scene[400:425,700:775]=scene[572:597,1045:1120].copy()
        self.assertIsNone(self.finder.scan(scene,'Melonade'))

    def test_no_detector_classifier_or_native_ocr_instances(self):
        self.assertFalse(hasattr(self.finder,'text_det'))
        self.assertFalse(hasattr(self.finder,'text_cls'))
        self.assertFalse(hasattr(self.finder,'native'))

    def test_dark_letters_on_light_tag(self):
        from PIL import Image,ImageDraw,ImageFont
        image=Image.new('RGB',(1280,720),'#4488bb')
        draw=ImageDraw.Draw(image)
        draw.rectangle((395,295,490,322),fill='#efecd8')
        draw.text((400,300),'NekoMaple',font=ImageFont.truetype(str(ROOT/'assets/name_font.ttf'),12),fill='#222222')
        hit=self.finder.scan(np.array(image)[:,:,::-1].copy(),'NekoMaple')
        self.assertIsNotNone(hit)
        self.assertEqual(hit.mode,'EXACT')
        self.assertTrue(hit.box[0]<430<hit.box[2])

    def test_new_readable_names_below_old_visual_cutoff(self):
        # Only the game client; the browser's seller text must never count as a hit.
        image=cv2.imread(str(ROOT/'Screenshot 2026-11-16 141643.png'))[210:978,1:1360]
        for name,point in [('MilkToast',(888,108)),('FightClub',(766,325))]:
            with self.subTest(name=name):
                hit=self.finder.scan(image,name)
                self.assertIsNotNone(hit,self.finder.last_diagnostic)
                self.assertEqual(hit.mode,'EXACT')
                l,t,r,b=hit.box
                self.assertTrue(l<=point[0]<=r and t<=point[1]<=b,hit)
                self.assertEqual(self.finder.last_diagnostic['proposal_threshold'],.48)

    def test_recovery_does_not_accept_prefixes_or_similar_sellers(self):
        image=cv2.imread(str(ROOT/'Screenshot 2026-11-16 141643.png'))[210:978,1:1360]
        for name in ('MilkToas','MilkT','MilkToost','FightClu','FightClubs','Ballor'):
            with self.subTest(name=name):
                self.assertIsNone(self.finder.scan(image,name),self.finder.last_diagnostic)

    def test_superseded_target_cancels_before_expensive_search(self):
        from unittest.mock import patch
        with patch.object(self.finder,'_candidates',side_effect=AssertionError('stale search')):
            self.assertIsNone(self.finder.scan(self.room,'Melonade',cancelled=lambda:True))
        self.assertTrue(self.finder.last_diagnostic['cancelled'])
