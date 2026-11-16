"""Bounded, single-thread name-search bursts on FM entry; cheap watching between."""
from dataclasses import dataclass, replace
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
FOUND_HOLD_SECONDS=120.0
MAX_ENTRY_ATTEMPTS=3


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
    def __init__(self,frames,get_names,post,stop,get_versions=lambda:{},get_room_names=None,get_room_hint=None):
        super().__init__(daemon=True)
        self.frames,self.get_names,self.post,self.stop=frames,get_names,post,stop
        self.get_room_names=get_room_names
        self.get_room_hint=get_room_hint
        self.ready=threading.Event()
        self.entry_check=threading.Event()
        self.selection_check=threading.Event()
        self.retry=threading.Event();self.priority=queue.SimpleQueue();self.preferred=None

    def prioritize(self,name):
        key=name.casefold()
        changed=key!=self.preferred
        self.preferred=key;self.priority.put(key)
        if changed:self.selection_check.set()

    def run(self):
        cv2.setNumThreads(1)
        def rate(ms):
            if hasattr(self.frames,'set_interval'):self.frames.set_interval(ms)
        rate(IDLE_CAPTURE_MS)
        self.post(('shop_note','Preparing room-entry finder…'))
        try:engine=NameFinder()
        except Exception as exc:
            self.post(('shop_note','NAME FINDER ERROR: '+str(exc)[:150]));return
        self.ready.set()
        gate=SnapshotGate(settle_seconds=0.0,first_visible=True);gate.loading=True
        jobs={};version=-1;reference=None;shape=None;room=None
        active=False;deadline=0.;source_size=(1,1)
        epoch=getattr(self.frames,'loading_epoch',0)
        burst_started=0.;header_ms=0.;header_retry_at=0.;provisional=False

        def names():
            values=self.get_room_names(room) if room is not None and self.get_room_names else self.get_names()
            return {name.casefold():name for name in values if name}

        def publish(note=''):
            hits={job.name:{'box':job.hit.box,'text':job.hit.text,'mode':job.hit.mode,
                            'hold_until':job.found_at+FOUND_HOLD_SECONDS if job.found_at is not None else 0}
                  for job in jobs.values() if job.hit is not None}
            self.post(('shops_frame',source_size,hits,note))

        def idle(note):
            nonlocal active
            active=False;rate(IDLE_CAPTURE_MS);publish(note)

        def begin(bgr,manual=False,preserve=False):
            nonlocal room,active,deadline,jobs,reference,burst_started,header_ms,header_retry_at,provisional
            retained={}
            if preserve:
                for key,job in jobs.items():
                    if job.hit is None or job.patch is None or job.found_at is None:continue
                    if time.monotonic()>=job.found_at+FOUND_HOLD_SECONDS:continue
                    x,y,r,b=job.hit.box;patch=bgr[y:b,x:r]
                    if patch.shape==job.patch.shape and patch.size and np.mean(np.abs(
                            patch.astype(np.int16)-job.patch.astype(np.int16)))<=24:retained[key]=job
            burst_started=time.monotonic();deadline=burst_started+ROOM_BURST_SECONDS
            if not self.get_names():idle('Waiting for FM entry · no pending sellers');return
            provisional=False
            hint=self.get_room_hint() if self.get_room_hint else None
            if (hint and hint[0] and hint[0].casefold() in {n.casefold() for n in self.get_names()}
                    and hint[1] in range(1,21) and hasattr(engine,'numbered_header_visible')
                    and engine.numbered_header_visible(bgr)):
                room=hint[1];provisional=True
            else:
                try:room=(engine.entry_room_number(bgr) if hasattr(engine,'entry_room_number') else engine.room_number(bgr))
                except Exception:
                    idle('Could not read FM room header · FIND AGAIN retries');return
            header_ms=(time.monotonic()-burst_started)*1000
            if room is None and not manual:
                jobs=retained;active=True;rate(ACTIVE_CAPTURE_MS)
                header_retry_at=time.monotonic()+.016
                publish('Reading room header · retrying fresh entry frames');return
            jobs={key:retained.get(key,Search(name)) for key,name in names().items()}
            jobs.update(retained)
            key=self.preferred
            if key in jobs:jobs={key:jobs[key],**{k:v for k,v in jobs.items() if k!=key}}
            reference=signature(bgr);active=True;rate(ACTIVE_CAPTURE_MS)
            publish(f'FM {room or "?"} · entry burst · {len(jobs)} sellers')

        while not self.stop.is_set():
            frame=self.frames.latest(-1 if self.selection_check.is_set() else version)
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
            selected=self.selection_check.is_set()
            if trigger or manual:
                self.selection_check.clear()
                begin(bgr,manual=manual)
            elif selected:
                self.selection_check.clear()
                live={name.casefold() for name in self.get_names()}
                job=jobs.get(self.preferred)
                if self.preferred in live and (job is None or job.hit is None):
                    if not active:begin(bgr,preserve=True)
                    elif job is not None:
                        job.attempts=0;job.wait_box=None;job.candidate_hint=None
                        deadline=time.monotonic()+ROOM_BURST_SECONDS
            # A failed header on the first fade-in frame must not consume entry.
            if active and room is None and not manual:
                if time.monotonic()>=deadline:
                    idle('Room header not identified · FIND AGAIN retries')
                elif time.monotonic()>=header_retry_at:
                    header_started=time.monotonic()
                    try:room=(engine.entry_room_number(bgr,full=time.monotonic()-burst_started>.35)
                              if hasattr(engine,'entry_room_number') else engine.room_number(bgr))
                    except Exception:room=None
                    header_ms+=(time.monotonic()-header_started)*1000
                    header_retry_at=time.monotonic()+.016
                    if room is not None:
                        saved={key:job for key,job in jobs.items() if job.hit is not None and
                               job.found_at is not None and time.monotonic()<job.found_at+FOUND_HOLD_SECONDS}
                        jobs={key:saved.get(key,Search(name)) for key,name in names().items()}
                        jobs.update(saved)
                        reference=sig
                if room is None:
                    self.stop.wait(.008);continue
            allowed=names()
            held={key for key,job in jobs.items() if job.found_at is not None and
                  time.monotonic()<job.found_at+FOUND_HOLD_SECONDS}
            removed=set(jobs)-set(allowed)-held
            for key in removed:del jobs[key]
            if active:
                for key,name in allowed.items():
                    if key not in jobs:jobs[key]=Search(name)
            if removed:publish()
            changed=shape is not None and shape!=bgr.shape
            moved=reference is not None and np.mean(np.abs(sig-reference))>28
            shape=bgr.shape
            if changed or moved:
                if changed:
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
                    box=track_label(job.patch,bgr,job.hit.box)
                    if box is None:job.hit=None;job.patch=None
                    else:
                        job.hit=replace(job.hit,box=box)
                        l,t,r,b=box;job.patch=bgr[t:b,l:r].copy()
                    invalid=True
            if invalid:publish('Tracking verified shop labels')
            while not self.priority.empty():
                key=self.priority.get()
                if key in jobs:jobs={key:jobs[key],**{k:v for k,v in jobs.items() if k!=key}}
            if not active:
                self.stop.wait(.008);continue
            waiting=False;ready=[]
            for key,job in jobs.items():
                if key not in allowed or job.hit is not None or job.attempts>=MAX_ENTRY_ATTEMPTS:continue
                if job.wait_box is not None:
                    x,y,r,b=job.wait_box;patch=bgr[y:b,x:r]
                    if patch.size and np.percentile(patch,98)<140:
                        waiting=True;continue
                    job.wait_box=None
                ready.append((job.attempts,key))
            if not ready and waiting and time.monotonic()<deadline:
                self.stop.wait(.008);continue
            if time.monotonic()>=deadline or not ready:
                unchecked=sum(job.attempts==0 for job in jobs.values())
                idle(f'FM {room or "?"} scanned · idle until next entry'+(f' · {unchecked} unchecked; FIND AGAIN retries' if unchecked else ''))
                continue
            _,key=min(ready,key=lambda value:value[0]);job=jobs[key]
            if provisional and job.attempts>=2:
                try:confirmed=engine.room_number(bgr)
                except Exception:confirmed=None
                if confirmed is not None and confirmed!=room:
                    room=confirmed;jobs={k:Search(n) for k,n in names().items()};reference=sig
                    provisional=False;continue
                if confirmed is not None:provisional=False
            start_epoch=epoch;attempt=job.attempts
            job.attempts+=1
            self.post(('shop_note',f'FM {room or "?"} · finding {job.name}'))
            search_started=time.monotonic()
            try:
                engine.prepare(job.name,w)
                hit=engine.scan(bgr,job.name,quick_only=attempt<2,entry_only=attempt<2,
                    candidate_hint=job.candidate_hint,cancelled=lambda:
                    self.stop.is_set() or time.monotonic()>=deadline or
                    getattr(self.frames,'loading_epoch',start_epoch)!=start_epoch or key not in names())
            except Exception as exc:
                hit=None;self.post(('shop_note','NAME FINDER ERROR: '+str(exc)[:150]))
            if hit is None:
                job.wait_box=getattr(engine,'last_diagnostic',{}).get('wait_for_contrast')
                job.candidate_hint=getattr(engine,'last_diagnostic',{}).get('candidate_hint')
            if self.stop.is_set():break
            if key not in names() or getattr(self.frames,'loading_epoch',epoch)!=epoch:continue
            result_frame=bgr
            fresh=self.frames.peek(version) if hasattr(self.frames,'peek') else None
            if fresh is not None:
                _,fresh_stamp,new=fresh
                if new.shape!=bgr.shape:
                    reference=None;publish();continue
                if hit is not None and name_region_changed(bgr,new,hit.box):
                    x,y,r,b=hit.box;box=track_label(bgr[y:b,x:r],new,hit.box)
                    if box is None:continue
                    hit=replace(hit,box=box)
                result_frame=new
            if hit is not None:
                job.hit=hit;job.found_at=time.monotonic();x,y,r,b=hit.box;job.patch=result_frame[y:b,x:r].copy()
            posted=time.monotonic();loading_at=getattr(self.frames,'loading_started',None)
            self.post(('shop_timing',{'name':job.name,'found':hit is not None,'room':room,
                'room_source':'selected route + numbered header' if provisional else 'header OCR',
                'quick_pass':attempt<2,
                'verification':getattr(engine,'last_diagnostic',None) if hit is None and attempt>=2 else None,
                'header_ms':round(header_ms,1),
                'recognition_ms':round((posted-search_started)*1000,1),
                'queue_ms':round(max(0,(search_started-burst_started)*1000-header_ms),1),
                'frame_age_ms':round(max(0,(search_started-stamp)*1000),1),
                'burst_to_result_ms':round((posted-burst_started)*1000,1),
                'loading_to_result_ms':round((posted-loading_at)*1000,1) if loading_at is not None else None,
                'posted_at':posted}))
            publish(f'{sum(state.hit is not None for state in jobs.values())} matched · FM {room or "?"} entry burst')
