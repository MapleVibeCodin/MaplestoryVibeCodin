import unittest
from pathlib import Path
import shutil
import cv2
import numpy as np
from fm_entry_gate import current_room, EntryGate, references
from nameplate_scan import find_wooden_labels, read_small_nameplate

ASSETS=Path(__file__).parent/'assets'

class TestMoraAndAlreadyInFM(unittest.TestCase):
    def test_already_inside_numbered_room(self):
        room, entrance=references()
        self.assertTrue(room)
        for signature in room.values():
            self.assertTrue(current_room(signature))
        for signature in entrance.values():
            self.assertFalse(current_room(signature))

    def test_mora_nameplate_from_user_screenshot(self):
        patch=cv2.imread(str(ASSETS/'mora_badge_test.png'))
        self.assertIsNotNone(patch)
        frame=np.full((650,1050,3),170,np.uint8)
        frame[370:420,180:280]=patch
        labels=find_wooden_labels(frame)
        self.assertTrue(any(l<=230<=r for l,_,r,_ in labels))
        if not shutil.which('tesseract'):
            self.skipTest('Tesseract executable not installed in test environment')
        result=read_small_nameplate(frame,'Mora')
        self.assertIsNotNone(result)
        self.assertEqual(result.mode,'EXACT')
        self.assertEqual(result.text.casefold(),'mora')
        x0,y0,x1,y1=result.box
        self.assertLess(x0,242)
        self.assertGreater(x1,215)
        self.assertLess(y0,400)
        self.assertGreater(y1,390)

if __name__=='__main__':unittest.main()
