"""Replacement-reader regressions using actual uploaded pixels and wrong targets."""
from pathlib import Path
import time
import unittest
import cv2
import numpy as np
from room_text_reader import RoomTextReader,SceneRegions
from test_new_screenshot_names import CASES as EARLIER
from test_uploaded_reader_names import CASES as RECENT
from test_failed_shop_labels import CASES as REPORTED

ROOT=Path(__file__).parent

class RoomReaderReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cv2.setNumThreads(1)
        cls.reader=RoomTextReader()

    def read(self,frame,name):
        self.reader.reset();start=time.monotonic()
        while time.monotonic()-start<3.:
            hit=self.reader.read(frame,[name],preferred=name,budget_ms=100).get(name)
            if hit:return hit
        return None

    def frame(self,file):
        crop=cv2.imread(str(ROOT/file));self.assertIsNotNone(crop)
        frame=np.full((768,1366,3),64,np.uint8)
        frame[100:100+crop.shape[0],100:100+crop.shape[1]]=crop
        return frame

    def test_crop_reading_does_not_depend_on_neighboring_batch_width(self):
        crop=cv2.imread(str(ROOT/'HiJeezLouise.png'))[150:175,30:120]
        wider=cv2.resize(crop,(420,20))
        alone=self.reader.recognizer([crop])[0][0]
        first=self.reader.recognizer([crop,wider])[0][0]
        second=self.reader.recognizer([wider,crop])[1][0]
        self.assertEqual(alone,first)
        self.assertEqual(alone,second)

    def test_full_game_screenshots_find_the_actual_name_position(self):
        for stamp,crop,name,point in EARLIER+RECENT:
            with self.subTest(name=name):
                image=cv2.imread(str(ROOT/f'Screenshot 2026-11-16 {stamp}.png'))
                self.assertIsNotNone(image)
                x,y,r,b=crop;hit=self.read(image[y:b,x:r],name)
                self.assertIsNotNone(hit,self.reader.last_diagnostic)
                l,t,q,d=hit.box
                self.assertTrue(l-8<=point[0]-x<=q+8 and t-5<=point[1]-y<=d+5,hit)

    def test_reported_label_crops_preserve_identity_and_position(self):
        for name,file,point,expected in REPORTED:
            with self.subTest(name=name):
                hit=self.read(self.frame(file),name)
                self.assertIsNotNone(hit,self.reader.last_diagnostic)
                l,t,r,b=hit.box
                self.assertTrue(l-8<=point[0]<=r+8 and t-5<=point[1]<=b+5,hit)
                if expected=='CHECK':self.assertNotEqual(hit.mode,'EXACT')

    def test_three_visible_letters_can_mark_a_partial_name_without_full_confirmation(self):
        # These were deliberately rejected by full-name mode. The user now
        # explicitly accepts a three-letter CHECK marker instead.
        for file,name in [('Kethan.png','Kethan'),
                          ('DeathVeil.png','DeathVei'),('sykes.png','Syk'),
                          ('JwenZzzzz.png','JwenZzzz')]:
            with self.subTest(name=name):
                self.assertIsNotNone(self.read(self.frame(file),name),self.reader.last_diagnostic)

    def test_unrelated_crop_targets_are_not_marked(self):
        for file,name in [('DeathVeil.png','Quartz'),('MrKimchi.png','Zyphora'),
                          ('Mechanicus.png','LemonTea')]:
            with self.subTest(name=name):
                self.assertIsNone(self.read(self.frame(file),name),self.reader.last_diagnostic)

    def test_three_letters_require_confidence_and_distinguish_live_sellers(self):
        def reading(text,confidence=.99):
            return text,confidence,[(c,confidence,i/max(1,len(text))) for i,c in enumerate(text)]
        match=lambda value,name,names:self.reader.three_letter_match(value,name,names,(0,0,80,15),100)
        self.assertIsNotNone(match(reading('Gim'),'Gimchigirl',['Gimchigirl','MrKimchi']))
        self.assertIsNone(match(reading('Gim'),'Gimchigirl',['Gimchigirl','Gimli']))
        self.assertIsNone(match(reading('Gi'),'Gimchigirl',['Gimchigirl']))
        self.assertIsNone(match(reading('Gim',.60),'Gimchigirl',['Gimchigirl']))
        self.assertIsNone(match(reading('Gi m'),'Gimchigirl',['Gimchigirl']))
        self.assertIsNone(match(reading('zzz'),'JwenZzzzz',['JwenZzzzz']))

    def test_new_november_17_names_and_ladder_occlusion(self):
        cases=[('NightxMare.png','NightxMare',(170,273),True),
               ('MrKimchi.png','MrKimchi',(175,286),True),
               ('MrKimchi (second).png','MrKimchi',(172,293),True),
               ('HiJeezLouise.png','HiJeezLouise',(174,263),False),
               ('Screenshot 2026-11-17 070705.png','iNOZUONODIEi',(190,268),True),
               ('Screenshot 2026-11-17 072936.png','ShirDeRanger',(173,284),False),
               ('Screenshot 2026-11-17 082311.png','Seiyoku',(169,251),False)]
        for file,name,point,uncertain in cases:
            with self.subTest(name=name,file=file):
                hit=self.read(self.frame(file),name)
                self.assertIsNotNone(hit,self.reader.last_diagnostic)
                l,t,r,b=hit.box
                self.assertTrue(l-8<=point[0]<=r+8 and t-5<=point[1]<=b+5,hit)
                if uncertain:self.assertNotEqual(hit.mode,'EXACT')

    def test_browser_only_sellers_do_not_become_game_markers(self):
        stamp,crop,_,_=RECENT[13]
        image=cv2.imread(str(ROOT/f'Screenshot 2026-11-16 {stamp}.png'))
        x,y,r,b=crop
        for name in ['Dolve','Waku']:
            with self.subTest(name=name):
                self.assertIsNone(self.read(image[y:b,x:r],name),self.reader.last_diagnostic)


class RegionProducerTests(unittest.TestCase):
    def test_selected_three_letter_hit_publishes_before_other_name_confirmation(self):
        from room_text_reader import Label
        reader=RoomTextReader.__new__(RoomTextReader)
        frame=np.zeros((80,200,3),np.uint8)
        def reading(text):return text,.99,[(c,.99,i/len(text)) for i,c in enumerate(text)]
        reader.labels=[Label((10,10,50,23),False,1.,None,reading=reading('Ket'),source=frame),
                       Label((80,10,150,23),False,1.,None,reading=reading('MrKimchs'),source=frame)]
        reader.recognizer=lambda crops:self.fail('Other seller delayed the selected marker')
        hits=reader.lookup(frame,['Kethan','MrKimchi'],preferred='Kethan',confirm=True)
        self.assertEqual(set(hits),{'Kethan'})
        self.assertEqual(hits['Kethan'].mode,'CONFUSABLE')

    def test_index_uses_newest_queued_frame_instead_of_processing_a_backlog(self):
        import queue
        from types import SimpleNamespace
        reader=RoomTextReader.__new__(RoomTextReader)
        reader.producer=SimpleNamespace(output=queue.Queue(),generation=2)
        seen=[];reader.ingest=lambda frame,regions:seen.append((frame,regions))
        for generation,frame in [(1,'expired'),(2,'old'),(2,'latest')]:
            reader.producer.output.put((generation,frame,[frame]))
        reader.update('current')
        self.assertEqual(seen,[('latest',['latest'])])

    def test_idle_producer_does_not_request_or_process_images(self):
        import threading
        stop=threading.Event();requested=threading.Event()
        class Frames:
            def latest(self,after=-1):
                requested.set()
                return None
        producer=SceneRegions(Frames(),stop);producer.start()
        try:
            self.assertFalse(requested.wait(.05))
            producer.active=True
            self.assertTrue(requested.wait(.5))
            producer.active=False
        finally:
            stop.set();producer.join(1)
        self.assertFalse(producer.is_alive())
