"""Bounded, single-thread name-search bursts on FM entry; cheap watching between."""
from dataclasses import dataclass
import queue
import threading
import time
import cv2
import numpy as np
from name_finder import NameFinder
from fm_entry_gate import SnapshotGate
from fast_shop_worker import signature,name_region_changed

ROOM_BURST_SECONDS=3.0
IDLE_CAPTURE_MS=80
ACTIVE_CAPTURE_MS=16


@dataclass
class Search:
    name: str
    attempts: int = 0
    hit: object = None
    patch: object = None


class MultiShopWorker(threading.Thread):
    def __init__(self,frames,get_names,post,stop,get_versions=lambda:{},get_room_names=None):
        super().__init__(daemon=True)
        self.frames,self.get_names,self.post,self.stop=frames,get_names,post,stop
        self.get_room_names=get_room_names
        self.entry_check=threading.Event()
        self.retry=threading.Event();self.priority=queue.SimpleQueue();self.preferred=None

    def prioritize(self,name):
        self.preferred=name.casefold();self.priority.put(self.preferred)

    def run(self):
        cv2.setNumThreads(1)
        def rate(ms):
            if hasattr(self.frames,'set_interval'):self.frames.set_interval(ms)
        rate(IDLE_CAPTURE_MS)
        self.post(('shop_note','Preparing room-entry finder…'))
        try:engine=NameFinder()
        except Exception as exc:
            self.post(('shop_note','NAME FINDER ERROR: '+str(exc)[:150]));return
        gate=SnapshotGate(settle_seconds=0.0);gate.loading=True
        jobs={};version=-1;reference=None;shape=None;room=None
        active=False;deadline=0.;source_size=(1,1)
        epoch=getattr(self.frames,'loading_epoch',0)

        def names():
            values=self.get_room_names(room) if room is not None and self.get_room_names else self.get_names()
            return {name.casefold():name for name in values if name}

        def publish(note=''):
            hits={job.name:{'box':job.hit.box,'text':job.hit.text,'mode':job.hit.mode}
                  for job in jobs.values() if job.hit is not None}
            self.post(('shops_frame',source_size,hits,note))

        def idle(note):
            nonlocal active
            active=False;rate(IDLE_CAPTURE_MS);publish(note)

        def begin(bgr,manual=False):
            nonlocal room,active,deadline,jobs,reference
            deadline=time.monotonic()+ROOM_BURST_SECONDS
            if not self.get_names():idle('Waiting for FM entry · no pending sellers');return
            try:room=engine.room_number(bgr)
            except Exception as exc:
                idle('Could not read FM room header · FIND AGAIN retries');return
            if room is None and not manual:
                jobs={};idle('Waiting for FM room entry · header not identified');return
            jobs={key:Search(name) for key,name in names().items()}
            key=self.preferred
            if key in jobs:jobs={key:jobs[key],**{k:v for k,v in jobs.items() if k!=key}}
            reference=signature(bgr);active=True;rate(ACTIVE_CAPTURE_MS)
            publish(f'FM {room or "?"} · entry burst · {len(jobs)} sellers')

        while not self.stop.is_set():
            frame=self.frames.latest(version)
            if frame is None:
                self.stop.wait(.008);continue
            version,stamp,bgr=frame
            h,w=bgr.shape[:2];source_size=(w,h)
            current_epoch=getattr(self.frames,'loading_epoch',epoch)
            if current_epoch!=epoch:
                epoch=current_epoch;gate.reset();gate.loading=True
                jobs={};active=False;reference=None;rate(ACTIVE_CAPTURE_MS)
                publish('Loading · waiting for a stable FM room')
            if self.entry_check.is_set():
                self.entry_check.clear();gate.reset();gate.loading=True
                jobs={};active=False;reference=None
            trigger=gate.observe(bgr,now=stamp)
            if gate.invalidated:
                jobs={};active=False;reference=None;rate(ACTIVE_CAPTURE_MS)
                publish('Loading · waiting for a stable FM room')
            manual=self.retry.is_set()
            if manual and not gate.loading:self.retry.clear()
            if gate.loading:
                self.stop.wait(.008);continue
            sig=signature(bgr)
            if trigger or manual:begin(bgr,manual=manual)
            allowed=names()
            removed=set(jobs)-set(allowed)
            for key in removed:del jobs[key]
            if active:
                for key,name in allowed.items():
                    if key not in jobs:jobs[key]=Search(name)
            if removed:publish()
            changed=shape is not None and shape!=bgr.shape
            moved=reference is not None and np.mean(np.abs(sig-reference))>28
            shape=bgr.shape
            if changed or moved:
                for job in jobs.values():job.hit=None;job.patch=None
                reference=sig
                if active:
                    for job in jobs.values():job.attempts=0
                    publish('Camera moved during entry burst')
                else:publish('Moved · waiting for next entry or FIND AGAIN')
            invalid=False
            for job in jobs.values():
                if job.hit is None:continue
                x,y,r,b=job.hit.box;patch=bgr[y:b,x:r]
                if patch.shape!=job.patch.shape or not patch.size or np.mean(np.abs(patch.astype(np.int16)-job.patch.astype(np.int16)))>24:
                    job.hit=None;job.patch=None;invalid=True
            if invalid:publish('Name moved · waiting for next entry or FIND AGAIN')
            while not self.priority.empty():
                key=self.priority.get()
                if key in jobs:jobs={key:jobs[key],**{k:v for k,v in jobs.items() if k!=key}}
            if not active:
                self.stop.wait(.008);continue
            ready=[(job.attempts,key) for key,job in jobs.items() if job.hit is None and job.attempts<2]
            if time.monotonic()>=deadline or not ready:
                unchecked=sum(job.attempts==0 for job in jobs.values())
                idle(f'FM {room or "?"} scanned · idle until next entry'+(f' · {unchecked} unchecked; FIND AGAIN retries' if unchecked else ''))
                continue
            _,key=min(ready,key=lambda value:value[0]);job=jobs[key]
            start_epoch=epoch;attempt=job.attempts
            job.attempts+=1
            self.post(('shop_note',f'FM {room or "?"} · finding {job.name}'))
            try:
                engine.prepare(job.name,w)
                hit=engine.scan(bgr,job.name,quick_only=attempt==0,cancelled=lambda:
                    self.stop.is_set() or time.monotonic()>=deadline or
                    getattr(self.frames,'loading_epoch',start_epoch)!=start_epoch or key not in names())
            except Exception as exc:
                hit=None;self.post(('shop_note','NAME FINDER ERROR: '+str(exc)[:150]))
            if self.stop.is_set():break
            if key not in names() or getattr(self.frames,'loading_epoch',epoch)!=epoch:continue
            fresh=self.frames.peek(version) if hasattr(self.frames,'peek') else None
            if fresh is not None:
                _,fresh_stamp,new=fresh
                if new.shape!=bgr.shape or np.mean(np.abs(signature(new)-sig))>28:
                    for state in jobs.values():state.hit=None;state.patch=None
                    reference=None;publish();continue
                if hit is not None and name_region_changed(bgr,new,hit.box):continue
            if hit is not None:
                job.hit=hit;x,y,r,b=hit.box;job.patch=bgr[y:b,x:r].copy()
            publish(f'{sum(state.hit is not None for state in jobs.values())} matched · FM {room or "?"} entry burst')
