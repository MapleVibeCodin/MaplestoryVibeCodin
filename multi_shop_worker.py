"""One CPU-budgeted worker for all archived seller names; arrivals never cancel peers."""
from dataclasses import dataclass
import threading
import queue
import time
import cv2
import numpy as np
from name_finder import NameFinder
from fm_entry_gate import SnapshotGate
from fast_shop_worker import signature,name_region_changed,MISS_RETRY_DELAYS
from scan_budget import ScanDutyBudget


@dataclass
class Search:
    name: str
    attempts: int = 0
    due: float = 0.
    hit: object = None
    patch: object = None
    revision: object = None


class MultiShopWorker(threading.Thread):
    def __init__(self,frames,get_names,post,stop,get_versions=lambda:{}):
        super().__init__(daemon=True)
        self.frames,self.get_names,self.post,self.stop=frames,get_names,post,stop
        self.retry=threading.Event()
        self.get_versions=get_versions
        self.priority=queue.SimpleQueue()

    def prioritize(self,name):
        self.priority.put(name.casefold())

    def run(self):
        cv2.setNumThreads(1)
        self.post(('shop_note','Preparing name finder…'))
        try:engine=NameFinder()
        except Exception as exc:
            self.post(('shop_note','NAME FINDER ERROR: '+str(exc)[:150]));return
        gate=SnapshotGate(settle_seconds=0.0);gate.loading=True
        duty=ScanDutyBudget()
        jobs={};version=-1;reference=None;shape=None;cursor=0
        source_size=(1,1)

        def publish(note=''):
            hits={job.name:{'box':job.hit.box,'text':job.hit.text,'mode':job.hit.mode}
                  for job in jobs.values() if job.hit is not None}
            self.post(('shops_frame',source_size,hits,note))

        def reset(now):
            for job in jobs.values():
                job.attempts=0;job.due=now;job.hit=None;job.patch=None

        while not self.stop.is_set():
            now=time.monotonic()
            names={name.casefold():name for name in self.get_names() if name}
            removed=set(jobs)-set(names)
            for key in removed:del jobs[key]
            versions=self.get_versions()
            for key,name in names.items():
                revision=versions.get(key)
                if key not in jobs:jobs[key]=Search(name,due=now,revision=revision)
                elif jobs[key].revision!=revision:
                    jobs[key].revision=revision
                    if jobs[key].hit is None:jobs[key].attempts=0;jobs[key].due=now
            while not self.priority.empty():
                priority=self.priority.get()
                if priority in jobs:
                    if jobs[priority].hit is None:jobs[priority].attempts=0;jobs[priority].due=now
                    cursor=list(jobs).index(priority)
            if removed:publish()
            frame=self.frames.latest(version)
            if frame is None or not jobs:
                self.stop.wait(.008);continue
            version,stamp,bgr=frame
            h,w=bgr.shape[:2];source_size=(w,h)
            trigger=gate.observe(bgr,now=stamp)
            sig=signature(bgr)
            if gate.invalidated:
                reset(now);reference=None;publish('Waiting for room to load…')
            if shape is not None and shape!=bgr.shape:
                reset(now+.10);reference=None;publish()
            shape=bgr.shape
            if trigger:
                reset(now);reference=sig
            elif not gate.loading and reference is not None and np.mean(np.abs(sig-reference))>28:
                reset(now+.10);reference=sig;publish('Scene moved; finding saved sellers…')
            if self.retry.is_set():
                self.retry.clear();reset(now);publish('Finding all saved sellers…')
            if gate.loading:
                self.stop.wait(.008);continue
            if reference is None:reference=sig
            changed=False
            for job in jobs.values():
                if job.hit is None:continue
                x,y,r,b=job.hit.box;patch=bgr[y:b,x:r]
                if (patch.shape!=job.patch.shape or not patch.size or
                    np.mean(np.abs(patch.astype(np.int16)-job.patch.astype(np.int16)))>24):
                    job.hit=None;job.patch=None;job.attempts=0;job.due=now+.10;changed=True
            if changed:publish()
            if duty.remaining(now)>0:
                self.stop.wait(min(.008,duty.remaining(now)));continue
            ordered=list(jobs)
            ready=[ordered[(cursor+i)%len(ordered)] for i in range(len(ordered))
                   if jobs[ordered[(cursor+i)%len(ordered)]].hit is None and
                   jobs[ordered[(cursor+i)%len(ordered)]].attempts<=len(MISS_RETRY_DELAYS) and
                   jobs[ordered[(cursor+i)%len(ordered)]].due<=now]
            if not ready:
                self.stop.wait(.008);continue
            key=ready[0];job=jobs[key];cursor=(ordered.index(key)+1)%len(ordered)
            self.post(('shop_note',f'Finding {job.name} · {len(jobs)} saved sellers'))
            cpu=time.thread_time()
            try:
                engine.prepare(job.name,w)
                hit=engine.scan(bgr,job.name,cancelled=lambda:self.stop.is_set() or
                    key not in {name.casefold() for name in self.get_names()})
            except Exception as exc:
                hit=None;self.post(('shop_note','NAME FINDER ERROR: '+str(exc)[:150]))
            finally:duty.charge(time.thread_time()-cpu,time.monotonic())
            if self.stop.is_set():break
            if key not in {name.casefold() for name in self.get_names()}:continue
            fresh=self.frames.peek(version) if hasattr(self.frames,'peek') else None
            if fresh is not None:
                _,fresh_stamp,new=fresh
                if new.shape!=bgr.shape or np.mean(np.abs(signature(new)-sig))>28:
                    gate.observe(new,now=fresh_stamp)
                    reset(time.monotonic()+.10);reference=None;publish();continue
                if hit is not None and name_region_changed(bgr,new,hit.box):
                    job.due=time.monotonic()+.10;continue
            job.attempts+=1
            if hit is not None:
                job.hit=hit;x,y,r,b=hit.box;job.patch=bgr[y:b,x:r].copy()
            elif job.attempts<=len(MISS_RETRY_DELAYS):
                job.due=time.monotonic()+MISS_RETRY_DELAYS[job.attempts-1]
            else:job.due=float('inf')
            found=sum(job.hit is not None for job in jobs.values())
            publish(f'{found} name matches · {len(jobs)} saved sellers · new deals stay queued')
