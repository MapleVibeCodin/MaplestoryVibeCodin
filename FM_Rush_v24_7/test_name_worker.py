import unittest,threading
from unittest.mock import patch
import numpy as np
from fast_shop_worker import FastShopWorker
from fast_shop_match import Hit

class NameWorkerTests(unittest.TestCase):
    def run_worker(self,frames,change_target=False):
        stop=threading.Event();events=[];calls=[];target=['Mora',1]
        class Frames:
            index=0
            def latest(self,after):
                if not frames:stop.set();return None
                self.index+=1
                return self.index,self.index*.10,frames.pop(0)
        class Finder:
            def prepare(self,*args):pass
            def scan(self,frame,name):
                calls.append(name)
                if change_target:target[:]=['NewName',2]
                return Hit(name,(200,200,240,215),.9,'EXACT')
        with patch('fast_shop_worker.NameFinder',Finder):
            worker=FastShopWorker(Frames(),lambda:tuple(target),events.append,stop)
            worker.start();worker.join(3)
        self.assertFalse(worker.is_alive())
        return events,calls

    def test_scan_on_arm_and_again_only_after_loading(self):
        a=np.full((600,1000,3),140,np.uint8)
        events,calls=self.run_worker([a]*10+[np.zeros_like(a)]+[a]*10)
        self.assertEqual(calls,['Mora','Mora'])
        self.assertEqual(len([e for e in events if e[0]=='shop_frame']),2)
        self.assertTrue(all(e[2] is None for e in events if e[0]=='shop_frame'))

    def test_old_target_result_not_published(self):
        a=np.full((600,1000,3),140,np.uint8)
        events,calls=self.run_worker([a],change_target=True)
        self.assertFalse(any(e[0]=='shop_frame' for e in events))

    def test_black_frames_never_searched(self):
        events,calls=self.run_worker([np.zeros((600,1000,3),np.uint8)]*12)
        self.assertEqual(calls,[])

    def test_initial_miss_gets_only_one_bounded_retry(self):
        stop=threading.Event();events=[];calls=[];clock=[0.]
        frame=np.full((600,1000,3),140,np.uint8)
        class Frames:
            index=0
            def latest(self,after):
                self.index+=1;clock[0]+=.10
                if self.index>20:stop.set();return None
                return self.index,clock[0],frame
        class Finder:
            def prepare(self,*args):pass
            def scan(self,*args):calls.append(clock[0]);return None
        with patch('fast_shop_worker.NameFinder',Finder), patch('fast_shop_worker.time.monotonic',side_effect=lambda:clock[0]):
            worker=FastShopWorker(Frames(),lambda:('Oral',1),events.append,stop)
            worker.start();worker.join(3)
        self.assertFalse(worker.is_alive())
        self.assertEqual(len(calls),2)
        self.assertGreaterEqual(calls[1]-calls[0],.15)
