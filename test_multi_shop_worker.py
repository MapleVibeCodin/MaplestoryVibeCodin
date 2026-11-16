import threading
import unittest
from unittest.mock import patch
import numpy as np
from fast_shop_match import Hit
from multi_shop_worker import MultiShopWorker


class MultiWorkerTests(unittest.TestCase):
    def run_worker(self,names,scan,max_frames=160,frames=None,cpu_cost=0.,versions=lambda:{},room=3,room_names=None,on_frame=None,clock_step=.05,hint=None,numbered=False):
        stop=threading.Event();events=[];calls=[];clock=[0.];cpu=[0.]
        image=np.full((600,1000,3),140,np.uint8)
        class Frames:
            index=0
            def latest(self,after):
                self.index+=1;clock[0]+=clock_step
                if self.index>max_frames:stop.set();return None
                if on_frame:on_frame(self.index,worker)
                frame=frames(self.index,image) if frames else image
                return self.index,clock[0],frame
        class Finder:
            def room_number(self,frame):return room() if callable(room) else room
            def numbered_header_visible(self,frame):return numbered
            def prepare(self,*args):pass
            def scan(self,frame,name,**kwargs):
                calls.append((name,clock[0],kwargs.get('quick_only',False)));cpu[0]+=cpu_cost
                return scan(name,names,kwargs['cancelled'])
        with patch('multi_shop_worker.NameFinder',Finder), \
             patch('multi_shop_worker.time.monotonic',side_effect=lambda:clock[0]), \
             patch('multi_shop_worker.time.thread_time',side_effect=lambda:cpu[0]):
            self.event_times=[]
            def post(event):events.append(event);self.event_times.append((clock[0],event))
            worker=MultiShopWorker(Frames(),lambda:tuple(names),post,stop,versions,room_names,(lambda:hint) if hint else None)
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
        self.assertEqual([c[0] for c in calls].count('Mora'),3)
        self.assertEqual([c[0] for c in calls].count('Oral'),3)

    def test_every_seller_gets_quick_sweep_before_any_recovery(self):
        _,calls=self.run_worker(['Mora','Oral','Melonade'],lambda *args:None)
        self.assertEqual([(name,quick) for name,_,quick in calls],
            [('Mora',True),('Oral',True),('Melonade',True),
             ('Mora',True),('Oral',True),('Melonade',True),
             ('Mora',False),('Oral',False),('Melonade',False)])

    def test_no_per_seller_cooldown_inside_burst(self):
        def scan(name,*args):return Hit(name,(200,200,240,215),.9,'EXACT')
        events,calls=self.run_worker(['Mora','Oral'],scan,cpu_cost=.2)
        self.assertEqual(len(calls),2)
        self.assertLess(calls[1][1]-calls[0][1],.1)

    def test_loading_clears_all_markers_and_rechecks_saved_names(self):
        def frame(index,image):return np.zeros_like(image) if 15<=index<=18 else image
        def scan(name,*args):return Hit(name,(200,200,240,215),.9,'EXACT')
        events,calls=self.run_worker(['Mora','Oral'],scan,frames=frame,max_frames=50)
        self.assertEqual([c[0] for c in calls].count('Mora'),2)
        self.assertEqual([c[0] for c in calls].count('Oral'),2)
        snapshots=[event[2] for event in events if event[0]=='shops_frame']
        self.assertIn({},snapshots)
        self.assertEqual(set(snapshots[-1]),{'Mora','Oral'})

    def test_latched_loading_transition_rearms_even_if_black_frame_was_missed(self):
        def tick(index,worker):
            if index==30:worker.frames.loading_epoch=1
        def scan(name,*args):return Hit(name,(200,200,240,215),.9,'EXACT')
        _,calls=self.run_worker(['Mora'],scan,on_frame=tick)
        self.assertEqual(len(calls),2)

    def test_loading_during_inference_cancels_and_discards_old_result(self):
        current=[];changed=[False]
        def tick(index,worker):current[:]=[worker]
        def scan(name,names,cancelled):
            if not changed[0]:
                current[0].frames.loading_epoch=1;changed[0]=True
                self.assertTrue(cancelled())
                names.clear() # no pending seller after transition
            return Hit(name,(200,200,240,215),.9,'EXACT')
        events,calls=self.run_worker(['Mora'],scan,on_frame=tick)
        self.assertEqual(len(calls),1)
        self.assertFalse(any(e[0]=='shops_frame' and e[2] for e in events))

    def test_removed_seller_result_is_not_published(self):
        def scan(name,names,cancelled):
            names.clear();self.assertTrue(cancelled())
            return Hit(name,(200,200,240,215),.9,'EXACT')
        events,calls=self.run_worker(['Mora'],scan,max_frames=10)
        self.assertFalse(any(event[0]=='shops_frame' and event[2] for event in events))

    def test_new_listing_for_an_exhausted_seller_does_not_rearm(self):
        revisions={'mora':1};count=[0]
        def frame(index,image):
            if index==90:revisions['mora']=2
            return image
        def scan(*args):count[0]+=1;return None
        events,calls=self.run_worker(['Mora'],scan,frames=frame,versions=lambda:revisions)
        self.assertEqual(count[0],3)

    def test_new_seller_while_idle_waits_for_next_entry(self):
        names=['Mora']
        def frame(index,image):
            if index==30:names.append('Oral')
            return image
        _,calls=self.run_worker(names,lambda *args:None,frames=frame)
        self.assertEqual([x[0] for x in calls],['Mora','Mora','Mora'])

    def test_movement_alone_does_not_rearm_but_selection_does(self):
        def frame(index,image):return image if index<30 else np.full_like(image,220)
        def tick(index,worker):
            if index==50:worker.prioritize('Mora')
        _,calls=self.run_worker(['Mora'],lambda *args:None,frames=frame,on_frame=tick)
        self.assertEqual(len(calls),6)
        self.assertGreater(calls[3][1],2.4)

    def test_find_again_explicitly_starts_another_burst(self):
        def tick(index,worker):
            if index==30:worker.retry.set()
        _,calls=self.run_worker(['Mora'],lambda *args:None,on_frame=tick)
        self.assertEqual(len(calls),6)

    def test_idle_selection_is_prioritized_on_explicit_find_again(self):
        def tick(index,worker):
            if index==30:worker.prioritize('Oral')
            if index==40:worker.retry.set()
        def scan(name,*args):return Hit(name,(200,200,240,215),.9,'EXACT')
        _,calls=self.run_worker(['Mora','Oral'],scan,on_frame=tick)
        self.assertEqual([x[0] for x in calls],['Mora','Oral','Oral','Mora'])

    def test_new_selection_in_an_idle_room_starts_without_find_again(self):
        names=['Mora']
        def tick(index,worker):
            if index==30:
                names.append('Oral');worker.prioritize('Oral')
        _,calls=self.run_worker(names,lambda *args:None,on_frame=tick)
        self.assertIn('Oral',[name for name,_,_ in calls])
        self.assertEqual(calls[3][0],'Oral')

    def test_selection_after_page_expiry_does_not_scan_archived_name(self):
        names=['Mora']
        def tick(index,worker):
            if index==30:names.clear();worker.prioritize('OldSeller')
        _,calls=self.run_worker(names,lambda *args:None,on_frame=tick)
        self.assertNotIn('OldSeller',[name for name,_,_ in calls])

    def test_selecting_another_target_keeps_a_found_marker_without_researching_it(self):
        names=['Mora']
        def tick(index,worker):
            if index==30:names.append('Oral');worker.prioritize('Oral')
        def scan(name,*args):return Hit(name,(200 if name=='Mora' else 400,200,240 if name=='Mora' else 440,215),.9,'EXACT')
        events,calls=self.run_worker(names,scan,on_frame=tick)
        self.assertEqual([name for name,_,_ in calls],['Mora','Oral'])
        self.assertTrue(any(e[0]=='shops_frame' and set(e[2])=={'Mora','Oral'} for e in events))

    def test_header_retry_after_selection_keeps_already_verified_markers(self):
        names=['Mora'];headers=iter([3,None,3])
        def room():return next(headers,3)
        def tick(index,worker):
            if index==30:names.append('Oral');worker.prioritize('Oral')
        def scan(name,*args):return Hit(name,(200 if name=='Mora' else 400,200,240 if name=='Mora' else 440,215),.9,'EXACT')
        events,calls=self.run_worker(names,scan,on_frame=tick,room=room)
        self.assertEqual([name for name,_,_ in calls],['Mora','Oral'])
        self.assertTrue(any(e[0]=='shops_frame' and set(e[2])=={'Mora','Oral'} for e in events))

    def test_initial_live_page_can_recheck_room_after_empty_start(self):
        names=[]
        def tick(index,worker):
            if index==30:names.append('Mora');worker.entry_check.set()
        _,calls=self.run_worker(names,lambda *args:None,on_frame=tick)
        self.assertEqual(len(calls),3)
        self.assertGreater(calls[0][1],1.5)

    def test_initial_live_page_recheck_does_not_scan_outside_fm(self):
        def tick(index,worker):
            if index==30:worker.entry_check.set()
        _,calls=self.run_worker(['Mora'],lambda *args:None,on_frame=tick,room=None)
        self.assertEqual(calls,[])

    def test_non_fm_window_does_not_scan(self):
        _,calls=self.run_worker(['Mora'],lambda *args:None,room=None)
        self.assertEqual(calls,[])

    def test_only_sellers_for_identified_room_are_searched(self):
        rooms=[]
        def room_names(room):rooms.append(room);return ('Oral',)
        _,calls=self.run_worker(['Mora','Oral'],lambda *args:None,room_names=room_names)
        self.assertTrue(rooms and set(rooms)=={3})
        self.assertEqual([x[0] for x in calls],['Oral','Oral','Oral'])

    def test_large_queue_is_cut_off_at_burst_deadline(self):
        names=['Seller'+str(i) for i in range(100)]
        _,calls=self.run_worker(names,lambda *args:None,max_frames=160)
        self.assertLess(len(calls),100)
        self.assertLessEqual(calls[-1][1]-calls[0][1],3.)


    def test_selected_route_can_search_first_only_with_a_numbered_header(self):
        def tick(index,worker):
            if index==1:worker.prioritize('Oral')
        def scan(name,*args):return Hit(name,(200,200,240,215),.9,'EXACT')
        _,calls=self.run_worker(['Mora','Oral'],scan,room=None,hint=('Oral',3),numbered=True,on_frame=tick)
        self.assertEqual([name for name,_,_ in calls],['Oral','Mora'])
        _,calls=self.run_worker(['Mora','Oral'],scan,room=None,hint=('Oral',3),numbered=False)
        self.assertEqual(calls,[])

    def test_an_off_page_selected_route_cannot_unlock_a_scan(self):
        _,calls=self.run_worker(['Oral'],lambda *args:None,room=None,hint=('Mora',3),numbered=True)
        self.assertEqual(calls,[])

    def test_found_name_survives_page_removal_for_two_minutes_without_more_ocr(self):
        names=['Mora']
        def tick(index,worker):
            if index==20:names.clear()
        def scan(name,*args):return Hit(name,(200,200,240,215),.9,'EXACT')
        events,calls=self.run_worker(names,scan,max_frames=145,on_frame=tick,clock_step=1.)
        self.assertEqual(len(calls),1)
        matched=[t for t,e in self.event_times if e[0]=='shops_frame' and e[2]]
        cleared=[t for t,e in self.event_times if e[0]=='shops_frame' and not e[2] and t>20]
        self.assertTrue(matched)
        self.assertTrue(cleared)
        self.assertGreaterEqual(cleared[0]-matched[0],120.)

    def test_unfound_name_is_removed_as_soon_as_page_drops_it(self):
        names=['Mora']
        def scan(name,names,cancelled):
            names.clear()
            self.assertTrue(cancelled())
            return None
        _,calls=self.run_worker(names,scan)
        self.assertEqual(len(calls),1)

class StaticSelectionTests(unittest.TestCase):
    def test_selection_uses_latest_frame_when_capture_has_not_changed(self):
        import time
        names=['Mora'];stop=threading.Event();idle=threading.Event();found=threading.Event()
        image=np.full((600,1000,3),140,np.uint8)
        class Frames:
            version=0;value=None
            def latest(self,after=-1):
                if not idle.is_set():
                    self.version+=1;self.value=(self.version,time.monotonic(),image)
                return None if self.value is None or self.value[0]==after else self.value
        class Finder:
            def room_number(self,frame):return 3
            def prepare(self,*args):pass
            def scan(self,frame,name,**kwargs):
                return Hit(name,(200 if name=='Mora' else 400,200,240 if name=='Mora' else 440,215),.9,'EXACT')
        def post(event):
            if event[0]=='shops_frame':
                if 'scanned' in event[-1]:idle.set()
                if 'Oral' in event[2]:found.set()
        with patch('multi_shop_worker.NameFinder',Finder):
            worker=MultiShopWorker(Frames(),lambda:tuple(names),post,stop)
            worker.start()
            try:
                self.assertTrue(idle.wait(1))
                names.append('Oral');worker.prioritize('Oral')
                self.assertTrue(found.wait(1),'Selection waited indefinitely for a new capture frame')
            finally:stop.set();worker.join(2)
        self.assertFalse(worker.is_alive())


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
