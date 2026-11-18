"""Bounded, single-thread name-search bursts on FM entry; cheap watching between."""
from dataclasses import dataclass, replace
import queue
import threading
import time
import cv2
import numpy as np
from room_text_reader import RoomTextReader
from fm_entry_gate import SnapshotGate
from frame_motion import name_region_changed,relocate_label,follow_word

ROOM_BURST_SECONDS=3.0
IDLE_CAPTURE_MS=80
ACTIVE_CAPTURE_MS=16
FOUND_HOLD_SECONDS=120.0


def track_label(patch,frame,box):
    """Relocate already verified lettering locally during camera movement.

    This does no OCR and cannot introduce a new identity. Reject weak/duplicate
    image matches instead of leaving a square at an old screen position.
    """
    if patch is None or not patch.size:return None
    x,y,r,b=box;h,w=frame.shape[:2]
    left=max(0,x-100);top=max(0,y-140)
    region=frame[top:min(h,b+140),left:min(w,r+100)]
    if region.shape[0]<patch.shape[0] or region.shape[1]<patch.shape[1]:return None
    template=cv2.cvtColor(patch,cv2.COLOR_BGR2GRAY)
    if float(template.std())<8:return None
    scores=cv2.matchTemplate(cv2.cvtColor(region,cv2.COLOR_BGR2GRAY),template,cv2.TM_CCOEFF_NORMED)
    _,score,_,(dx,dy)=cv2.minMaxLoc(scores)
    if score<.82:return None
    scores[max(0,dy-8):dy+9,max(0,dx-patch.shape[1]//2):dx+patch.shape[1]//2+1]=-1
    if float(scores.max())>score-.05:return None
    return (left+dx,top+dy,left+dx+patch.shape[1],top+dy+patch.shape[0])


@dataclass
class Search:
    name: str
    attempts: int = 0
    hit: object = None
    patch: object = None
    found_at: float = None
    wait_box: object = None
    candidate_hint: object = None


class MultiShopWorker(threading.Thread):
    def __init__(self,frames,get_names,post,stop,get_versions=lambda:{},get_room_names=None,get_room_hint=None,single_target=False):
        super().__init__(daemon=True)
        self.frames,self.get_names,self.post,self.stop=frames,get_names,post,stop
        self.get_room_names=get_room_names
        self.get_room_hint=get_room_hint
        self.single_target=single_target
        self.ready=threading.Event()
        self.entry_check=threading.Event()
        self.selection_check=threading.Event()
        self.retry=threading.Event();self.priority=queue.SimpleQueue();self.preferred=None

    def prioritize(self,name):
        key=name.casefold()
        changed=key!=self.preferred
        self.preferred=key;self.priority.put(key)
        if changed:self.selection_check.set()

    def run_index(self,engine,rate):
        """One shared room index, independent of room-header OCR and IGN fonts."""
        engine.start_detector(self.frames,self.stop)
        gate=SnapshotGate(settle_seconds=0.,first_visible=True,visible_level=26);gate.loading=True
        epoch=getattr(self.frames,'loading_epoch',0);version=-1;shape=None
        jobs={};active=False;deadline=0.;started=0.;last_read=0.;size=(1,1)
        pending_loading_at=None;burst_loading_at=None
        def live():return {name.casefold():name for name in self.get_names() if name}
        def publish(note=''):
            self.post(('shops_frame',size,{job.name:dict(box=job.hit.box,text=job.hit.text,mode=job.hit.mode,
                hold_until=job.found_at+FOUND_HOLD_SECONDS) for job in jobs.values() if job.hit is not None},note))
        def begin(reset=False,loading_at=None):
            nonlocal active,deadline,started,burst_loading_at
            burst_loading_at=loading_at
            if reset:engine.reset()
            started=time.monotonic();deadline=started+ROOM_BURST_SECONDS;active=bool(live())
            engine.set_active(active)
            rate(ACTIVE_CAPTURE_MS if active else IDLE_CAPTURE_MS)
            publish('Reading visible name labels' if active else 'No current-page sellers')
        while not self.stop.is_set():
            now=time.monotonic();allowed=live();expired=False
            for key,job in list(jobs.items()):
                if (self.single_target and key!=self.preferred) or (key not in allowed and (job.found_at is None or now>=job.found_at+FOUND_HOLD_SECONDS)):
                    del jobs[key];expired=True
            if expired:publish()
            if active and now>=deadline:
                active=False;engine.set_active(False);rate(IDLE_CAPTURE_MS)
                publish('Entry scan finished · select a deal or FIND AGAIN to retry')
            event=self.selection_check.is_set() or self.retry.is_set() or self.entry_check.is_set()
            frame=self.frames.latest(-1 if event else version)
            if frame is None and active and (now-last_read>.04 or getattr(engine,'pending_regions',False)):frame=self.frames.latest(-1)
            if frame is None:
                self.stop.wait(.008);continue
            version,stamp,image=frame;h,w=image.shape[:2];size=(w,h)
            current_epoch=getattr(self.frames,'loading_epoch',epoch)
            if current_epoch!=epoch:
                pending_loading_at=getattr(self.frames,'loading_started',None)
            if current_epoch!=epoch or (shape is not None and shape!=image.shape):
                epoch=current_epoch;engine.set_active(False);engine.reset();jobs={};active=False
                gate.reset();gate.loading=True;rate(ACTIVE_CAPTURE_MS);publish('Loading · waiting for game pixels')
            shape=image.shape
            if self.entry_check.is_set():
                self.entry_check.clear();engine.set_active(False);engine.reset();jobs={};active=False
                gate.reset();gate.loading=True
            trigger=gate.observe(image,now=stamp)
            if gate.invalidated:
                engine.set_active(False);engine.reset();jobs={};active=False;rate(ACTIVE_CAPTURE_MS);publish('Loading · waiting for game pixels')
            if gate.loading:
                self.stop.wait(.008);continue
            allowed=live()
            selected=self.selection_check.is_set();self.selection_check.clear()
            manual=self.retry.is_set();self.retry.clear()
            if trigger:
                begin(reset=True,loading_at=pending_loading_at)
                pending_loading_at=None
            elif manual:
                jobs={};begin(reset=True)
            elif selected and self.preferred in allowed:
                job=jobs.get(self.preferred)
                if job is None or job.hit is None:begin()
            changed=False
            for job in jobs.values():
                if job.hit is None:continue
                x,y,r,b=job.hit.box;patch=image[y:b,x:r]
                if patch.shape!=job.patch.shape or not patch.size or np.mean(np.abs(patch.astype(np.int16)-job.patch.astype(np.int16)))>24:
                    box=track_label(job.patch,image,job.hit.box)
                    if box is None:job.hit=None;job.patch=None
                    else:
                        job.hit=replace(job.hit,box=box);x,y,r,b=box;job.patch=image[y:b,x:r].copy()
                    changed=True
            if changed:publish('Tracking verified shop labels')
            if not active:
                self.stop.wait(.008);continue
            missing=[name for key,name in allowed.items() if key not in jobs or jobs[key].hit is None]
            if not missing:
                active=False;engine.set_active(False);rate(IDLE_CAPTURE_MS);publish('All live sellers in view located');continue
            preferred=allowed.get(self.preferred)
            if preferred in missing:missing.remove(preferred);missing.insert(0,preferred)
            before=time.monotonic()
            if before>=deadline:continue
            start_epoch=epoch;last_read=before
            try:
                hits=engine.read(image,tuple(missing),preferred=preferred,budget_ms=120,
                    cancelled=lambda:self.stop.is_set() or time.monotonic()>=deadline or
                        getattr(self.frames,'loading_epoch',start_epoch)!=start_epoch)
            except Exception as exc:
                self.post(('shop_note','ROOM READER ERROR: '+str(exc)[:160]));hits={}
            if self.stop.is_set():break
            image=engine.source_frame if getattr(engine,'source_frame',None) is not None else image
            if getattr(self.frames,'loading_epoch',epoch)!=epoch:continue
            fresh=self.frames.peek(version) if hasattr(self.frames,'peek') else None
            current=image
            if fresh is not None:
                _,_,current=fresh
                if current.shape!=image.shape:continue
            allowed=live()
            published=set();dropped=[]
            for name,hit in hits.items():
                if name.casefold() not in allowed:continue
                source=engine.hit_sources.get(name,image)
                if name_region_changed(source,current,hit.box):
                    x,y,r,b=hit.box;box=relocate_label(source,current,hit.box) or follow_word(source,current,hit.box) or track_label(source[y:b,x:r],current,hit.box)
                    if box is None:
                        dropped.append(name);continue
                    hit=replace(hit,box=box)
                published.add(name)
                key=name.casefold();job=jobs.setdefault(key,Search(name))
                job.hit=hit;job.found_at=time.monotonic();x,y,r,b=hit.box;job.patch=current[y:b,x:r].copy()
            posted=time.monotonic();focus=preferred or missing[0]
            self.post(('shop_timing',dict(name=focus,found=focus in published,tracking_dropped=dropped,room=None,room_source='visible text index',
                quick_pass=True,header_ms=0.,recognition_ms=round((posted-before)*1000,1),queue_ms=0.,
                frame_age_ms=round(max(0,(before-stamp)*1000),1),burst_to_result_ms=round((posted-started)*1000,1),
                loading_to_result_ms=round((posted-burst_loading_at)*1000,1) if burst_loading_at is not None else None,
                posted_at=posted,verification=engine.last_diagnostic)))
            publish(f'{sum(job.hit is not None for job in jobs.values())} located · reading visible labels')

    def run(self):
        cv2.setNumThreads(1)
        def rate(ms):
            if hasattr(self.frames,'set_interval'):self.frames.set_interval(ms)
        rate(IDLE_CAPTURE_MS)
        self.post(('shop_note','Preparing room-entry finder…'))
        try:engine=RoomTextReader()
        except Exception as exc:
            self.post(('shop_note','NAME FINDER ERROR: '+str(exc)[:150]));return
        self.ready.set()
        try:
            self.run_index(engine,rate)
        finally:
            engine.set_active(False)
            if hasattr(engine,'close'):engine.close()
