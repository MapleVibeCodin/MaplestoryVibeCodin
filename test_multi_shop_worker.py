"""Behavior checks for the shared room-index controller, with no header reader."""
import threading
import unittest
from unittest.mock import patch
import numpy as np
from fast_shop_match import Hit
from multi_shop_worker import MultiShopWorker

class MultiWorkerTests(unittest.TestCase):
    def run_worker(self,names,read,max_frames=95,on_frame=None,frames=None,step=.05):
        stop=threading.Event();events=[];calls=[];clock=[0.];active=[]
        image=np.full((600,1000,3),140,np.uint8)
        class Frames:
            index=0;loading_epoch=0
            def latest(self,after=-1):
                self.index+=1;clock[0]+=step
                if self.index>max_frames:stop.set();return None
                if on_frame:on_frame(self.index,worker)
                return self.index,clock[0],frames(self.index,image) if frames else image
        class Reader:
            source_frame=None;hit_sources={};last_diagnostic={}
            def start_detector(self,*args):pass
            def set_active(self,value):active.append(value)
            def reset(self):pass
            def read(self,frame,wanted,**kwargs):
                self.source_frame=frame
                calls.append((tuple(wanted),kwargs.get('preferred'),clock[0]))
                return read(tuple(wanted),worker)
        with patch('multi_shop_worker.RoomTextReader',Reader),patch('multi_shop_worker.time.monotonic',side_effect=lambda:clock[0]):
            worker=MultiShopWorker(Frames(),lambda:tuple(names),lambda e:events.append((clock[0],e)),stop,
                get_room_names=lambda room:(_ for _ in ()).throw(AssertionError('Header gate used')))
            worker.start();worker.join(3);stop.set();worker.join(1)
        self.assertFalse(worker.is_alive())
        self.assertFalse(active[-1])
        return events,calls

    @staticmethod
    def hits(names):
        return {name:Hit(name,(200+i*100,200,240+i*100,215),.99,'EXACT') for i,name in enumerate(names)}

    def test_all_live_names_share_one_read_without_header_gate(self):
        events,calls=self.run_worker(['Mora','Oral'],lambda names,w:self.hits(names))
        self.assertEqual(len(calls),1)
        self.assertEqual(calls[0][0],('Mora','Oral'))
        self.assertTrue(any(e[0]=='shops_frame' and set(e[2])=={'Mora','Oral'} for _,e in events))

    def test_selected_name_is_first_and_idle_has_no_ocr(self):
        def tick(i,w):
            if i==1:w.prioritize('Oral')
        _,calls=self.run_worker(['Mora','Oral'],lambda names,w:self.hits(names),on_frame=tick)
        self.assertEqual(len(calls),1)
        self.assertEqual(calls[0][:2],(('Oral','Mora'),'Oral'))

    def test_missing_names_stop_at_three_second_burst(self):
        _,calls=self.run_worker(['Mora'],lambda *args:{})
        self.assertGreater(len(calls),1)
        self.assertLessEqual(calls[-1][2]-calls[0][2],3.)

    def test_no_page_names_means_no_ocr(self):
        _,calls=self.run_worker([],lambda *args:self.fail('OCR with empty page'))
        self.assertEqual(calls,[])

    def test_loading_clears_positions_and_rearms(self):
        def frame(i,a):return np.zeros_like(a) if 15<=i<=18 else a
        events,calls=self.run_worker(['Mora'],lambda names,w:self.hits(names),frames=frame)
        self.assertEqual(len(calls),2)
        self.assertTrue(any(t>.5 and e[0]=='shops_frame' and not e[2] for t,e in events))

    def test_latched_loading_does_not_require_observing_black(self):
        def tick(i,w):
            if i==20:w.frames.loading_epoch+=1
        _,calls=self.run_worker(['Mora'],lambda names,w:self.hits(names),on_frame=tick)
        self.assertEqual(len(calls),2)

    def test_new_seller_during_burst_does_not_discard_found_seller(self):
        names=['Mora'];first=[True]
        def read(wanted,w):
            if first[0]:first[0]=False;names.append('Oral')
            return self.hits(wanted)
        events,calls=self.run_worker(names,read)
        self.assertEqual(len(calls),2)
        self.assertTrue(any(e[0]=='shops_frame' and set(e[2])=={'Mora','Oral'} for _,e in events))

    def test_off_page_inflight_result_is_not_published(self):
        names=['Mora']
        def read(wanted,w):names.clear();return self.hits(wanted)
        events,calls=self.run_worker(names,read)
        self.assertEqual(len(calls),1)
        self.assertFalse(any(e[0]=='shops_frame' and e[2] for _,e in events))

    def test_found_marker_is_retained_for_two_minutes_after_page_removal(self):
        names=['Mora']
        def tick(i,w):
            if i==15:names.clear()
        events,calls=self.run_worker(names,lambda wanted,w:self.hits(wanted),max_frames=145,on_frame=tick,step=1.)
        self.assertEqual(len(calls),1)
        found=next(t for t,e in events if e[0]=='shops_frame' and e[2])
        cleared=next(t for t,e in events if t>15 and e[0]=='shops_frame' and not e[2])
        self.assertGreaterEqual(cleared-found,120.)

    def test_retry_and_selection_restart_a_bounded_idle_scan(self):
        names=['Mora']
        def tick(i,w):
            if i==20:names.append('Oral');w.prioritize('Oral')
            if i==40:w.retry.set()
        _,calls=self.run_worker(names,lambda wanted,w:self.hits(wanted),on_frame=tick)
        self.assertEqual([c[0] for c in calls],[('Mora',),('Oral',),('Oral','Mora')])

    def test_changed_pixels_remove_a_marker_instead_of_leaving_a_stale_square(self):
        def frame(i,a):return np.full_like(a,200) if i>15 else a
        events,_=self.run_worker(['Mora'],lambda wanted,w:self.hits(wanted),frames=frame)
        self.assertTrue(any(t>.7 and e[0]=='shops_frame' and not e[2] for t,e in events))
class MultiReplayTests(unittest.TestCase):
    def test_two_real_sellers_are_retained_in_one_marker_snapshot(self):
        from pathlib import Path
        import time
        import cv2
        image=cv2.imread(str(Path(__file__).parent/'regression_samples/cernia.png'))
        stop=threading.Event();results=[]
        class Frames:
            def latest(self,after=-1):
                now=time.monotonic();version=int(now*60)
                return None if version==after else (version,now,image)
            peek=latest
        def post(event):
            if event[0]=='shops_frame' and set(event[2])=={'Cernia','Melonade'}:
                results.append(event);stop.set()
        worker=MultiShopWorker(Frames(),lambda:('Cernia','Melonade'),post,stop)
        worker.start();worker.join(10);stop.set();worker.join(2)
        self.assertFalse(worker.is_alive())
        self.assertTrue(results)
        self.assertEqual(results[-1][2]['Cernia']['mode'],'CONFUSABLE')
        for name,(x,y) in [('Cernia',(1270,585)),('Melonade',(1085,585))]:
            l,t,r,b=results[-1][2][name]['box']
            self.assertTrue(l<=x<=r and t<=y<=b)
