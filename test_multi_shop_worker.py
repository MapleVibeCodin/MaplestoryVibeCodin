import threading
import unittest
from unittest.mock import patch
import numpy as np
from fast_shop_match import Hit
from multi_shop_worker import MultiShopWorker


class MultiWorkerTests(unittest.TestCase):
    def run_worker(self,names,scan,max_frames=160,frames=None,cpu_cost=0.,versions=lambda:{}):
        stop=threading.Event();events=[];calls=[];clock=[0.];cpu=[0.]
        image=np.full((600,1000,3),140,np.uint8)
        class Frames:
            index=0
            def latest(self,after):
                self.index+=1;clock[0]+=.05
                if self.index>max_frames:stop.set();return None
                frame=frames(self.index,image) if frames else image
                return self.index,clock[0],frame
        class Finder:
            def prepare(self,*args):pass
            def scan(self,frame,name,**kwargs):
                calls.append((name,clock[0]));cpu[0]+=cpu_cost
                return scan(name,names,kwargs['cancelled'])
        with patch('multi_shop_worker.NameFinder',Finder), \
             patch('multi_shop_worker.time.monotonic',side_effect=lambda:clock[0]), \
             patch('multi_shop_worker.time.thread_time',side_effect=lambda:cpu[0]):
            worker=MultiShopWorker(Frames(),lambda:tuple(names),events.append,stop,versions)
            worker.start();worker.join(4)
        self.assertFalse(worker.is_alive())
        return events,calls

    def test_arrival_during_scan_does_not_cancel_previous_seller(self):
        names=['Mora']
        def scan(name,names,cancelled):
            if name=='Mora':names.append('Oral');self.assertFalse(cancelled())
            return Hit(name,(200 if name=='Mora' else 400,200,240 if name=='Mora' else 440,215),.9,'EXACT')
        events,calls=self.run_worker(names,scan)
        self.assertEqual([c[0] for c in calls],['Mora','Oral'])
        snapshots=[event[2] for event in events if event[0]=='shops_frame']
        self.assertTrue(any(set(hits)=={'Mora','Oral'} for hits in snapshots))

    def test_missing_names_get_bounded_retries_without_continuous_ocr(self):
        events,calls=self.run_worker(['Mora','Oral'],lambda *args:None)
        self.assertEqual([c[0] for c in calls].count('Mora'),5)
        self.assertEqual([c[0] for c in calls].count('Oral'),5)

    def test_one_shared_cpu_budget_for_different_sellers(self):
        def scan(name,*args):return Hit(name,(200,200,240,215),.9,'EXACT')
        events,calls=self.run_worker(['Mora','Oral'],scan,cpu_cost=.2)
        self.assertEqual(len(calls),2)
        self.assertGreaterEqual(calls[1][1]-calls[0][1],.2*(1/.35-1))

    def test_loading_clears_all_markers_and_rechecks_saved_names(self):
        def frame(index,image):return np.zeros_like(image) if 15<=index<=18 else image
        def scan(name,*args):return Hit(name,(200,200,240,215),.9,'EXACT')
        events,calls=self.run_worker(['Mora','Oral'],scan,frames=frame,max_frames=50)
        self.assertEqual([c[0] for c in calls].count('Mora'),2)
        self.assertEqual([c[0] for c in calls].count('Oral'),2)
        snapshots=[event[2] for event in events if event[0]=='shops_frame']
        self.assertIn({},snapshots)
        self.assertEqual(set(snapshots[-1]),{'Mora','Oral'})

    def test_removed_seller_result_is_not_published(self):
        def scan(name,names,cancelled):
            names.clear();self.assertTrue(cancelled())
            return Hit(name,(200,200,240,215),.9,'EXACT')
        events,calls=self.run_worker(['Mora'],scan,max_frames=10)
        self.assertFalse(any(event[0]=='shops_frame' and event[2] for event in events))

    def test_new_listing_for_an_exhausted_seller_rearms_only_that_name(self):
        revisions={'mora':1};count=[0]
        def frame(index,image):
            if index==90:revisions['mora']=2
            return image
        def scan(*args):count[0]+=1;return None
        events,calls=self.run_worker(['Mora'],scan,frames=frame,versions=lambda:revisions)
        self.assertEqual(count[0],10)


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
