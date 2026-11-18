"""Accuracy and entry-state regressions from the supplied movement recordings."""
from pathlib import Path
import unittest
from unittest.mock import patch
import cv2
import numpy as np
from name_finder import NameFinder
from multi_shop_worker import track_label
from benchmark_video_entries import CASES,clip_frame

ROOT=Path(__file__).parent

@unittest.skipUnless(all((ROOT/c['file']).exists() for c in CASES),'Video fixtures are available in the full Git checkout')
class VideoEntries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cv2.setNumThreads(1);cls.finder=NameFinder()
        cls.frames=[clip_frame(case,t) for case,t in zip(CASES,[8.6,12.,14.9])]

    def test_selected_sellers_have_correct_game_coordinates(self):
        for case,frame in zip(CASES,self.frames):
            with self.subTest(name=case['name']):
                hit=self.finder.scan(frame,case['name'],entry_only=True)
                self.assertIsNotNone(hit,self.finder.last_diagnostic)
                l,t,r,b=hit.box;x,y,q,d=case['truth']
                self.assertTrue(x<=(l+r)/2<=q and y<=(t+b)/2<=d,hit)
                if case['name']=='Gimchigirl':self.assertEqual(hit.mode,'CHECK')

    def test_wrong_names_and_truncated_names_are_not_marked(self):
        for index,name in [(0,'Cec'),(0,'CeciShop'),(0,'Cecii'),
                           (1,'Toung'),(1,'Toungee'),(2,'GimchigirlX'),(2,'NotHere')]:
            with self.subTest(name=name):
                self.assertIsNone(self.finder.scan(self.frames[index],name,entry_only=True))

    def test_entrance_does_not_unlock_a_selected_room_hint(self):
        self.assertFalse(self.finder.numbered_header_visible(clip_frame(CASES[2],12.)))
        self.assertTrue(self.finder.numbered_header_visible(self.frames[2]))

    def test_dim_proposal_waits_for_contrast_then_verifies_without_another_scene_search(self):
        dim=clip_frame(CASES[2],14.8)
        self.assertIsNone(self.finder.scan(dim,'Gimchigirl',entry_only=True))
        self.assertIn('wait_for_contrast',self.finder.last_diagnostic)
        hint=self.finder.last_diagnostic['candidate_hint']
        with patch.object(self.finder,'_candidates',side_effect=AssertionError('repeated scene search')):
            hit=self.finder.scan(self.frames[2],'Gimchigirl',entry_only=True,candidate_hint=hint)
        self.assertIsNotNone(hit);self.assertEqual(hit.mode,'CHECK')

    def test_verified_label_tracks_camera_scroll_and_disappears_on_loss(self):
        first=self.frames[0];second=clip_frame(CASES[0],8.8)
        patch=first[581:598,878:912]
        box=track_label(patch,second,(878,581,912,598))
        self.assertIsNotNone(box)
        l,t,r,b=box;self.assertTrue(l<=895<=r and t<=568<=b,box)
        self.assertIsNone(track_label(patch,np.zeros_like(second),(878,581,912,598)))

    def test_visual_room_cache_does_not_confuse_different_numbered_rooms(self):
        for stamp,room in [('212444',1),('212549',2),('191120',13)]:
            image=cv2.imread(str(ROOT/f'Screenshot 2026-11-16 {stamp}.png'))
            crop=(2,48,1368,816) if room==13 else (3,45,1370,806)
            x,y,r,b=crop
            self.assertEqual(self.finder.room_number(image[y:b,x:r]),room)
