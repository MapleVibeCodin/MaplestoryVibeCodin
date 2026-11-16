"""One target-specific search on entry; no map OCR or full-screen OCR."""
from __future__ import annotations
import threading
import time
import cv2
import numpy as np
from name_finder import NameFinder
from fm_entry_gate import SnapshotGate
from fast_shop_match import candidates


def signature(bgr):
    return cv2.resize(bgr,(48,28),interpolation=cv2.INTER_AREA).astype(np.int16)


class FastShopWorker(threading.Thread):
    def __init__(self,frames,get_target,post,stop):
        super().__init__(daemon=True)
        self.frames,self.get_target,self.post,self.stop=frames,get_target,post,stop
        self.retry=threading.Event()

    def run(self):
        cv2.setNumThreads(1)
        self.post(('shop_note','Preparing name finder…'))
        try:engine=NameFinder()
        except Exception as exc:
            self.post(('shop_note','STARTUP ERROR: '+str(exc)[:150]))
            return
        gate=SnapshotGate(settle_seconds=0.0)
        last_key=None;last_version=-1;reference=None
        pending=False;retry_at=None;retry_left=0
        while not self.stop.is_set():
            raw=self.get_target()
            raw=raw if isinstance(raw,tuple) else (raw or '',0)
            key=((raw[0] or '').strip(),raw[1])
            if key!=last_key:
                last_key=key;pending=bool(key[0]);reference=None;retry_at=None;retry_left=0
                self.post(('shop_clear',key))
                self.post(('shop_note','READY · '+key[0]))
            frame=self.frames.latest(last_version)
            if frame is None or not key[0]:
                self.stop.wait(.008);continue
            ver,ts,bgr=frame;last_version=ver
            trigger=gate.observe(bgr,now=ts)
            sig=signature(bgr)
            if gate.invalidated:
                self.post(('shop_clear',key));pending=False;retry_at=None;reference=None
            manual=self.retry.is_set()
            if manual:self.retry.clear()
            # Clear stale coordinates after camera movement. Settle briefly,
            # then search once; animated characters alone do not cause a loop.
            if reference is not None and np.mean(np.abs(sig-reference))>28:
                self.post(('shop_clear',key));reference=sig
                retry_at=time.monotonic()+.10;retry_left=0
            due=retry_at is not None and time.monotonic()>=retry_at
            if not (trigger or pending or manual or due) or gate.loading:
                self.stop.wait(.008);continue
            # A stable visible frame is required even for a new deal/manual find.
            if float(np.mean(bgr[::24,::24]))<30:continue
            if trigger or manual or pending:retry_left=1
            pending=False;retry_at=None
            started=time.perf_counter()
            try:
                engine.prepare(key[0],bgr.shape[1])
                hit=engine.scan(bgr,key[0])
            except Exception as exc:
                self.post(('shop_note','NAME FINDER ERROR: '+str(exc)[:150]));continue
            if self.stop.is_set():break
            current=self.get_target();current=current if isinstance(current,tuple) else (current or '',0)
            if ((current[0] or '').strip(),current[1])!=key:continue
            latest=self.frames.peek(ver) if hasattr(self.frames,'peek') else None
            if latest is not None:
                _,fresh_ts,fresh=latest
                if np.mean(np.abs(signature(fresh)-sig))>28:
                    gate.observe(fresh,now=fresh_ts)
                    self.post(('shop_clear',key));pending=not gate.loading;reference=None
                    continue
            reference=sig
            ms=round((time.perf_counter()-started)*1000,1)
            h,w=bgr.shape[:2]
            mode=('FOUND' if hit.mode=='EXACT' else 'LIKELY · CHECK NAME') if hit else 'NOT VISIBLE'
            self.post(('shop_frame',key,None,(w,h),hit.box if hit else None,
                       mode,hit.text if hit else '',ms,'NAME MATCH'))
            if hit is None and retry_left:
                retry_left-=1;retry_at=time.monotonic()+.15

def from_tesseract(data,target,offset_y=0):
    if not data or not data.get('text'):
        return []
    words=[];boxes=[];scores=[]
    for i,t in enumerate(data['text']):
        if not str(t).strip():
            continue
        try:
            conf=float(data['conf'][i])/100
        except (ValueError,IndexError,TypeError):
            continue
        x=int(data['left'][i]);y=int(data['top'][i])+offset_y
        w=int(data['width'][i]);h=int(data['height'][i])
        words.append(t);boxes.append(((x,y),(x+w,y),(x+w,y+h),(x,y+h)));scores.append(conf)
    return candidates(words,boxes,scores,target)
