import unittest,threading
from unittest.mock import patch
import numpy as np
from fast_shop_worker import FastShopWorker, MISS_RETRY_DELAYS
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
            def scan(self,frame,name,**kwargs):
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
        events,calls=self.run_worker([a]*3,change_target=True)
        self.assertTrue(calls)
        self.assertFalse(any(e[0]=='shop_frame' for e in events))

    def test_black_frames_never_searched(self):
        events,calls=self.run_worker([np.zeros((600,1000,3),np.uint8)]*12)
        self.assertEqual(calls,[])

    def test_misses_retry_with_backoff_then_stop(self):
        stop=threading.Event();events=[];calls=[];clock=[0.]
        frame=np.full((600,1000,3),140,np.uint8)
        class Frames:
            index=0
            def latest(self,after):
                self.index+=1;clock[0]+=.10
                if self.index>100:stop.set();return None
                return self.index,clock[0],frame
        class Finder:
            def prepare(self,*args):pass
            def scan(self,*args,**kwargs):calls.append(clock[0]);return None
        with patch('fast_shop_worker.NameFinder',Finder), patch('fast_shop_worker.time.monotonic',side_effect=lambda:clock[0]):
            worker=FastShopWorker(Frames(),lambda:('Oral',1),events.append,stop)
            worker.start();worker.join(3)
        self.assertFalse(worker.is_alive())
        self.assertEqual(len(calls),1+len(MISS_RETRY_DELAYS))
        for gap,delay in zip(np.diff(calls),MISS_RETRY_DELAYS):
            self.assertGreaterEqual(gap+1e-9,delay)

    def test_starting_mid_fade_waits_for_two_stable_frames(self):
        levels=[40,80,130,180,180,180]
        stop=threading.Event();calls=[]
        class Frames:
            index=0
            def latest(self,after):
                if self.index==len(levels):stop.set();return None
                value=levels[self.index];self.index+=1
                return self.index,self.index*.016,np.full((600,1000,3),value,np.uint8)
        class Finder:
            def prepare(self,*args):pass
            def scan(self,frame,name,**kwargs):
                calls.append(int(frame[0,0,0]))
                return Hit(name,(200,200,240,215),.9,'EXACT')
        with patch('fast_shop_worker.NameFinder',Finder):
            worker=FastShopWorker(Frames(),lambda:('Mora',1),lambda e:None,stop)
            worker.start();worker.join(3)
        self.assertFalse(worker.is_alive())
        self.assertEqual(calls,[180])

    def test_delayed_name_is_found_without_manual_retry(self):
        stop=threading.Event();events=[];calls=[];clock=[0.]
        frame=np.full((600,1000,3),140,np.uint8)
        class Frames:
            index=0
            def latest(self,after):
                self.index+=1;clock[0]+=.05
                if self.index>100:stop.set();return None
                return self.index,clock[0],frame
        class Finder:
            def prepare(self,*args):pass
            def scan(self,frame,name,**kwargs):
                calls.append(clock[0])
                return Hit(name,(200,200,240,215),.9,'EXACT') if clock[0]>=.8 else None
        with patch('fast_shop_worker.NameFinder',Finder),patch('fast_shop_worker.time.monotonic',side_effect=lambda:clock[0]):
            worker=FastShopWorker(Frames(),lambda:('Mora',1),events.append,stop)
            worker.start();worker.join(3)
        self.assertFalse(worker.is_alive())
        self.assertLessEqual(len(calls),1+len(MISS_RETRY_DELAYS))
        found=[e for e in events if e[0]=='shop_frame' and e[4] is not None]
        self.assertEqual(len(found),1)
        self.assertGreaterEqual(calls[-1],.8)

    def test_local_name_change_clears_marker_even_without_camera_motion(self):
        a=np.full((600,1000,3),140,np.uint8)
        b=a.copy();b[200:215,200:240]=0
        events,calls=self.run_worker([a]*4+[b]*30)
        frames=[i for i,e in enumerate(events) if e[0]=='shop_frame']
        self.assertEqual(len(calls),2)
        self.assertTrue(any(e[0]=='shop_clear' for e in events[frames[0]+1:frames[1]]))

    def test_name_that_moves_during_recognition_is_not_published(self):
        stop=threading.Event();events=[];calls=[]
        a=np.full((600,1000,3),140,np.uint8)
        b=a.copy();b[200:215,200:240]=0
        class Frames:
            index=0
            changed=False
            def latest(self,after):
                self.index+=1
                if self.index>8:stop.set();return None
                return self.index,self.index*.1,b if self.changed else a
            def peek(self,after):
                return self.index+1,(self.index+1)*.1,b
        frames=Frames()
        class Finder:
            def prepare(self,*args):pass
            def scan(self,frame,name,**kwargs):
                calls.append(name);frames.changed=True
                return Hit(name,(200,200,240,215),.9,'EXACT') if len(calls)==1 else None
        with patch('fast_shop_worker.NameFinder',Finder):
            worker=FastShopWorker(frames,lambda:('Mora',1),events.append,stop)
            worker.start();worker.join(3)
        self.assertFalse(worker.is_alive())
        self.assertTrue(calls)
        self.assertFalse(any(e[0]=='shop_frame' and e[4] is not None for e in events))

    def test_new_target_cannot_bypass_search_cpu_cooldown(self):
        stop=threading.Event();events=[];calls=[];wall=[0.];cpu=[0.];target=['Mora',1]
        frame=np.full((600,1000,3),140,np.uint8)
        class Frames:
            index=0
            def latest(self,after):
                self.index+=1;wall[0]+=.05
                if self.index==4:target[:]=['Oral',2]
                if self.index>30:stop.set();return None
                return self.index,wall[0],frame
        class Finder:
            def prepare(self,*args):pass
            def scan(self,frame,name,**kwargs):
                calls.append((name,wall[0]));cpu[0]+=.2
                return Hit(name,(200,200,240,215),.9,'EXACT')
        with patch('fast_shop_worker.NameFinder',Finder), \
             patch('fast_shop_worker.time.monotonic',side_effect=lambda:wall[0]), \
             patch('fast_shop_worker.time.thread_time',side_effect=lambda:cpu[0]):
            worker=FastShopWorker(Frames(),lambda:tuple(target),events.append,stop)
            worker.start();worker.join(3)
        self.assertFalse(worker.is_alive())
        self.assertEqual([name for name,_ in calls],['Mora','Oral'])
        self.assertGreaterEqual(calls[1][1]-calls[0][1],.2*(1/.35-1))

    def test_manual_retry_during_cpu_cooldown_is_not_lost(self):
        stop=threading.Event();calls=[];wall=[0.];cpu=[0.]
        frame=np.full((600,1000,3),140,np.uint8)
        class Frames:
            index=0
            def latest(self,after):
                self.index+=1;wall[0]+=.05
                if self.index==4:worker.retry.set()
                if self.index>30:stop.set();return None
                return self.index,wall[0],frame
        class Finder:
            def prepare(self,*args):pass
            def scan(self,frame,name,**kwargs):
                calls.append(wall[0]);cpu[0]+=.2
                return Hit(name,(200,200,240,215),.9,'EXACT')
        with patch('fast_shop_worker.NameFinder',Finder), \
             patch('fast_shop_worker.time.monotonic',side_effect=lambda:wall[0]), \
             patch('fast_shop_worker.time.thread_time',side_effect=lambda:cpu[0]):
            worker=FastShopWorker(Frames(),lambda:('Mora',1),lambda e:None,stop)
            worker.start();worker.join(3)
        self.assertFalse(worker.is_alive())
        self.assertEqual(len(calls),2)
        self.assertGreaterEqual(calls[1]-calls[0],.2*(1/.35-1))

class SceneSignatureTests(unittest.TestCase):
    def test_local_animation_does_not_look_like_a_scene_change(self):
        from fast_shop_worker import signature
        before=np.full((768,1360,3),140,np.uint8)
        after=before.copy();after[250:310,400:460]=0
        self.assertLess(np.mean(np.abs(signature(before)-signature(after))),28)

    def test_major_scene_change_is_still_detected(self):
        from fast_shop_worker import signature
        before=np.full((768,1360,3),140,np.uint8)
        after=np.full_like(before,210)
        self.assertGreater(np.mean(np.abs(signature(before)-signature(after))),28)
