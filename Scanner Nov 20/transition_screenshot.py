"""Save one native client PNG after a visual blackout. No OCR or input."""
from datetime import datetime
from pathlib import Path
import queue
import threading
import time

from camera_alignment import capture_client, enable_capture_cache, release_capture_cache
from game_window import window_has_focus, window_client_rect
from shop_screenshot import crop, save_png
from performance_recorder import dark_fraction

IDLE_INTERVAL=.020
ARMED_INTERVAL=.005
PATCH=16
POINTS=((.20,.28),(.75,.30),(.22,.70))
SUPPORTED={(1280,720),(1366,768)}

def classify(samples):
    if len(samples)!=3 or any(v is None for v in samples):return None
    if sum(v>=.96 for v in samples)>=2:return True
    if sum(v<=.75 for v in samples)>=2:return False
    return None

class Blackout:
    def __init__(self):
        self.reset()
    def reset(self):
        self.baseline=False
        self.dark_count=0
        self.armed=False
    def observe(self,dark):
        if dark is None:
            if not self.armed:self.dark_count=0
            return False
        if dark:
            if self.baseline:
                self.dark_count+=1
                if self.dark_count>=2:self.armed=True
            return False
        self.baseline=True
        self.dark_count=0
        return self.armed
    def consumed(self):
        self.armed=False
        self.dark_count=0

def patches(client):
    x,y,w,h=client
    return [(x+int(w*fx)-PATCH//2,y+int(h*fy)-PATCH//2,PATCH,PATCH) for fx,fy in POINTS]

def full_classification(frame,client):
    x,y,w,h=client
    if frame is None or frame[1:3]!=(w,h):return None
    return classify([dark_fraction(crop(frame,px-x,py-y,pw,ph))
                     for px,py,pw,ph in patches(client)])

class TransitionScreenshotRecorder:
    def __init__(self,folder,*,capture=capture_client,focused=window_has_focus,geometry=window_client_rect):
        self.folder=Path(folder)
        self.capture=capture;self.focused=focused;self.geometry=geometry
        self.request=None
        self.saved=0;self.error=None
        self.stop=threading.Event();self.done=threading.Event()
        self.pending=queue.Queue(maxsize=16)
        self.worker=threading.Thread(target=self._work,daemon=True,name='Transition screenshot capture')
        self.writer=threading.Thread(target=self._write,daemon=True,name='Transition screenshot writer')
        self.writer.start();self.worker.start()

    def observe(self,hwnd,client):
        self.request=(hwnd,tuple(client)) if hwnd and client else None

    def _valid(self,request):
        hwnd,client=request
        return (self.request==request and client[2:] in SUPPORTED and self.focused(hwnd)
                and self.geometry(hwnd)==client)

    def _step(self,request,state):
        if not self._valid(request):
            state.reset();return
        _,client=request
        regions=patches(client)
        samples=[dark_fraction(self.capture(p,allow_crop=True)) for p in regions[:2]]
        if any(v is None for v in samples):
            state.reset();return
        if all(v>=.96 for v in samples):dark=True
        elif all(v<=.75 for v in samples):dark=False
        else:
            third=dark_fraction(self.capture(regions[2],allow_crop=True))
            if third is None:
                state.reset();return
            dark=classify(samples+[third])
        if not self._valid(request):
            state.reset();return
        if not state.observe(dark):return
        # First bright observation: capture immediately, no second bright poll.
        frame=self.capture(client)
        stamp=datetime.now()
        if not self._valid(request):
            state.reset();return
        if full_classification(frame,client) is not False:return
        state.consumed()
        try:self.pending.put_nowait((frame,stamp))
        except queue.Full:self.error='Transition screenshot queue full'

    def _work(self):
        state=Blackout();previous=None;last=0
        enable_capture_cache()
        try:
            while not self.stop.is_set():
                request=self.request
                now=time.monotonic()
                if request!=previous or now-last>.25:state.reset()
                previous=request;last=now
                if request:
                    try:self._step(request,state)
                    except Exception as exc:
                        state.reset();self.error=type(exc).__name__
                interval=ARMED_INTERVAL if state.dark_count or state.armed else IDLE_INTERVAL
                self.stop.wait(max(0,interval-(time.monotonic()-now)) if request else .05)
        finally:
            release_capture_cache();self.done.set()

    def _write(self):
        while not self.done.is_set() or not self.pending.empty():
            try:frame,stamp=self.pending.get(timeout=.1)
            except queue.Empty:continue
            try:
                save_png(self.folder,frame,stamp,'after_black')
                self.saved+=1
            except Exception as exc:self.error=type(exc).__name__
            finally:self.pending.task_done()

    def close(self):
        self.stop.set()
        self.worker.join(timeout=.5)
        self.writer.join(timeout=2)
