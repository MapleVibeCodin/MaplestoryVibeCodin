"""Reported November 17 crops, placed unchanged in a native-size viewport.

These exercise recognition, not the entry/header gate: the supplied files are
small label crops, not complete game frames. Two physically truncated names
remain unverified instead of being completed from their filenames.
"""
from pathlib import Path
import unittest
import cv2
import numpy as np
from name_finder import NameFinder

ROOT=Path(__file__).parent
CASES=[('DeathVeil','DeathVeil.png',(177,264),'EXACT'),
       ('JwenZzzzz','JwenZzzzz.png',(170,264),'CHECK'),
       ('Mechanicus','Mechanicus.png',(152,254),'CHECK'),
       ('MrSogiamo','MrSogiamo.png',(170,263),'EXACT'),
       ('SillySpend','SillySpend.png',(169,302),'CHECK'),
       ('Sykes','sykes.png',(160,246),'EXACT')]

class FailedShopLabels(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cv2.setNumThreads(1);cls.finder=NameFinder()

    def frame(self,file):
        crop=cv2.imread(str(ROOT/file));self.assertIsNotNone(crop)
        frame=np.full((768,1366,3),64,np.uint8)
        frame[100:100+crop.shape[0],100:100+crop.shape[1]]=crop
        return frame

    def test_readable_or_occluded_labels_have_correct_markers(self):
        for name,file,point,mode in CASES:
            with self.subTest(name=name):
                frame=self.frame(file)
                hit=self.finder.scan(frame,name,entry_only=True) or self.finder.scan(frame,name)
                self.assertIsNotNone(hit,self.finder.last_diagnostic)
                x,y,r,b=hit.box
                self.assertTrue(x<=point[0]<=r and y<=point[1]<=b,hit)
                self.assertEqual(hit.mode,mode)

    def test_complete_new_labels_work_in_entry_pass(self):
        for name,file,_,_ in CASES:
            if name=='Mechanicus':continue # Rope occlusion uses bounded recovery.
            with self.subTest(name=name):
                self.assertIsNotNone(self.finder.scan(self.frame(file),name,entry_only=True))

    def test_cut_off_name_letters_are_not_invented(self):
        for name in ['HisCapybara','Kethan']:
            with self.subTest(name=name):
                self.assertIsNone(self.finder.scan(self.frame(name+'.png'),name))

    def test_similar_names_prefixes_and_different_repeated_counts_are_rejected(self):
        for file,name in [('DeathVeil.png','DeathVei'),('sykes.png','Syk'),
                          ('MrSogiamo.png','MrSogiam'),('SillySpend.png','SillySpends'),
                          ('JwenZzzzz.png','JwenZzzz'),('JwenZzzzz.png','JwenZzz'),
                          ('JwenZzzzz.png','JwenZzzzzz'),('Mechanicus.png','Mecbanicus')]:
            with self.subTest(name=name):
                frame=self.frame(file)
                self.assertIsNone(self.finder.scan(frame,name,entry_only=True),self.finder.last_diagnostic)
                self.assertIsNone(self.finder.scan(frame,name),self.finder.last_diagnostic)
