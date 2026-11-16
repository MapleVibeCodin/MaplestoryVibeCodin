"""Entry-only OCR, room-header replay and brief-loading capture regressions."""
import sys
import threading
import types
import unittest
from pathlib import Path
from unittest.mock import patch
import cv2
import numpy as np
from name_finder import NameFinder
from window_capture import WindowFrames

class RoomHeaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cv2.setNumThreads(1);cls.finder=NameFinder()

    def test_actual_room_headers_with_expanded_collapsed_and_title_bar_layouts(self):
        cases=[('regression_samples/cernia.png',None,5),
               ('Screenshot 2026-11-16 153119.png',(0,43,1360,811),9),
               ('Screenshot 2026-11-16 153839.png',(106,40,1474,808),7),
               ('Screenshot 2026-11-16 162229.png',(109,40,1477,808),6),
               ('Screenshot 2026-11-16 141643.png',(1,171,1360,978),9),
               ('Screenshot 2026-11-16 152324.png',(0,12,1360,780),20)]
        for file,crop,room in cases:
            with self.subTest(file=file):
                image=cv2.imread(str(Path(__file__).parent/file))
                self.assertIsNotNone(image)
                if crop:x,y,r,b=crop;image=image[y:b,x:r]
                self.assertEqual(self.finder.room_number(image),room)

    def test_header_requires_market_label_confidence_and_valid_room(self):
        f=NameFinder.__new__(NameFinder)
        class Recognition:
            rec_image_shape=[3,48,320]
            reads=[]
            def __call__(self,crops):return self.reads,0
        f.recognizer=Recognition();image=np.full((600,1000,3),140,np.uint8)
        for reads in [[('Free Market',.99)],[('Hidden Street 9',.99)],
                      [('Free Market<21>',.99)],[('Free Market<9>',.4)],
                      [('Market 13',.99)],[('Market<21>',.99)],[('Market<13>',.4)]]:
            f.recognizer.reads=reads
            self.assertIsNone(f.room_number(image))
        f.recognizer.rec_image_shape=[3,48,999]
        f.recognizer.reads=[('Market<13>',.9)]
        self.assertEqual(f.room_number(image),13)
        f.recognizer.reads=[('Free Market<9>',.9)]
        self.assertEqual(f.room_number(image),9)
        self.assertEqual(f.recognizer.rec_image_shape,[3,48,999])

class CaptureTransitionTests(unittest.TestCase):
    def test_brief_black_frame_is_latched_even_when_latest_is_visible(self):
        callbacks={}
        class Capture:
            def __init__(self,**kwargs):pass
            def event(self,fn):callbacks[fn.__name__]=fn;return fn
            def start_free_threaded(self):return types.SimpleNamespace(stop=lambda:None)
        fake=types.SimpleNamespace(WindowsCapture=Capture)
        frames=WindowFrames(1);frames.set_interval(80)
        def send(value):
            callbacks['on_frame_arrived'](types.SimpleNamespace(frame_buffer=np.full((600,1000,4),value,np.uint8)),None)
        with patch.dict(sys.modules,windows_capture=fake),patch('window_capture.time.perf_counter',side_effect=[1.,1.01,1.02,1.03]):
            frames.start();send(140);first=frames.latest()[0]
            send(140);self.assertEqual(frames.latest()[0],first)
            send(0);send(140)
            self.assertEqual(frames.loading_epoch,1)
            self.assertEqual(frames.latest()[0],first+2)
            self.assertEqual(int(frames.latest()[2].mean()),140)
            frames.stop()
        self.assertFalse(frames.error)
