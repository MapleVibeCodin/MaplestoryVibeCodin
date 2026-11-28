import unittest,tempfile
from pathlib import Path
from datetime import datetime,timezone
import cv2,numpy as np
from screenshots import ScreenshotStore
from hybrid_capture import Reminders, context_at, save_crops, jpeg_bytes,png_bytes
from scene_analysis import screenshot_files
from inventory_ui import clip, InventoryDetector

class HybridTests(unittest.TestCase):
    def test_context(self):
        self.assertEqual(context_at({'monotonic':2},1),(None,None))
        self.assertEqual(context_at({'monotonic':2},3)[1],1)
    def test_reminders(self):
        r=Reminders(0)
        self.assertEqual(r.due(20),['map'])
        r.observe(80,['etc','pet','use'],'Map')
        self.assertEqual(r.due(80),[])
        self.assertIn('map',r.due(260))
        self.assertIn('use',r.due(680))
    def test_crops_reuse_and_pixel_accuracy(self):
        with tempfile.TemporaryDirectory() as d:
            s=ScreenshotStore(d,min_free=0)
            im=np.random.default_rng(1).integers(0,256,(80,100,3),dtype=np.uint8)
            p=s.save_scene(jpeg_bytes(im))
            self.assertIn(p.suffix,('.jpg','.png'))
            rows=save_crops(s,im,[('ui',(2,4,20,22))])
            self.assertEqual(rows,save_crops(s,im,[('ui',(2,4,20,22))]))
            crop=cv2.imread(str(s.folder/rows[0]['file']))
            self.assertTrue(np.array_equal(crop,im[4:26,2:22]))
            self.assertEqual(screenshot_files(Path(d)),[p])
    def test_empty_frame_no_inventory(self):
        self.assertEqual(InventoryDetector().detect(np.zeros((200,400,3),dtype=np.uint8)),[])
    def test_clip(self):
        self.assertEqual(clip((-5,-5,10,10),(50,50,3)),(0,0,5,5))
    def test_jpeg_not_allowed_in_old_save(self):
        with tempfile.TemporaryDirectory() as d:
            s=ScreenshotStore(d,min_free=0)
            data=jpeg_bytes(np.zeros((20,20,3),dtype=np.uint8))
            if data[:2]==b'\xff\xd8':
                with self.assertRaises(ValueError):s.save(data)
if __name__=='__main__': unittest.main()
