"""Replay the supplied desktop clips through the real room-entry worker.

Run from a full Git checkout: python benchmark_video_entries.py --repeats 3
The game-only rectangles remove browser/mirrored previews. Compressed 720p
clips are restored to the approximate native game capture size, not sharpened.
No target position is passed to the finder. Ground-truth regions only validate
its returned boxes. Times stop at the marker callback, not Windows rendering.
"""
from cpu_guard import initialize
initialize()
import argparse
import json
from pathlib import Path
import threading
import time
import cv2
import numpy as np
from multi_shop_worker import MultiShopWorker

ROOT=Path(__file__).parent
CASES=[
    dict(file='FM SHOP.mp4',name='Ceci',crop=(143,145,1611,964),size=None,
         start=6.5,goal=9.,room=9,truth=(870,495,925,625)),
    dict(file='FM%20SCAN%202%20-%20under%2025MB (1).mp4',name='Tounge',
         crop=(0,0,911,513),size=(1366,768),start=9.5,goal=12.,room=9,truth=(380,0,455,130)),
    dict(file='FM%20SCAN%203%20-%20under%2025MB (1).mp4',name='Gimchigirl',
         crop=(0,0,911,513),size=(1366,768),start=13.,goal=15.,room=13,truth=(1270,390,1355,425)),
    # Additional November 17 recordings: one second from the new room becoming
    # visible, rather than a user-specified clip timestamp deadline.
    dict(file='NightxMare.mp4',name='NightxMare',crop=(0,0,1366,768),size=None,
         start=1.75,goal=3.8,room=7,truth=(370,500,480,655)),
    dict(file='MrKimchi.mp4',name='MrKimchi',crop=(0,0,1366,768),size=None,
         start=22.,goal=24.5,room=16,truth=(810,480,920,555)),
]
# Current-page workload from HENEFM SCANS.png; unrelated archive sellers never
# enter this callback. The selected target is added when from a different clip.
PAGE=[('ponn2',13),('Hanatori',17),('Dontbefool',1),('Kirbu',11),
      ('Muppet232',9),('Gimchigirl',13),('CheeZZang',7)]


def clip_frame(case,seconds):
    cap=cv2.VideoCapture(str(ROOT/case['file']))
    try:
        cap.set(cv2.CAP_PROP_POS_MSEC,seconds*1000)
        ok,frame=cap.read()
        if not ok:raise RuntimeError('Could not decode '+case['file'])
        return game_frame(frame,case)
    finally:cap.release()


def game_frame(frame,case):
    x,y,r,b=case['crop'];frame=frame[y:b,x:r]
    return cv2.resize(frame,case['size'],interpolation=cv2.INTER_CUBIC) if case['size'] else frame


def replay(case):
    cv2.setNumThreads(1)
    cap=cv2.VideoCapture(str(ROOT/case['file']))
    cap.set(cv2.CAP_PROP_POS_MSEC,case['start']*1000)
    samples=[]
    try:
        while True:
            ok,frame=cap.read()
            if not ok:break
            timestamp=cap.get(cv2.CAP_PROP_POS_MSEC)/1000
            if timestamp>case['goal']+1.2:break
            samples.append((timestamp,game_frame(frame,case)))
    finally:cap.release()
    if not samples:raise RuntimeError('Missing video fixture: '+case['file'])
    stop=threading.Event();events=[];result={};clock=[0.]
    class Frames:
        value=None;loading_epoch=0;loading_started=None;dark=False
        def set_interval(self,ms):pass
        def latest(self,after=-1):
            return None if self.value is None or self.value[0]==after else self.value
        peek=latest
    frames=Frames()
    names=tuple(dict.fromkeys([name for name,_ in PAGE]+[case['name']]))
    def room_names(room):
        return tuple(dict.fromkeys([name for name,n in PAGE if n==room]+
                                   ([case['name']] if room==case['room'] else [])))
    def post(event):
        timestamp=case['start']+time.monotonic()-clock[0] if clock[0] else None
        events.append((timestamp,event))
        # Engine construction completes before it requests a frame.
        if event[0]=='shops_frame' and case['name'] in event[2] and not result:
            hit=event[2][case['name']];l,t,r,b=hit['box'];x,y,q,d=case['truth']
            location_ok=x<=(l+r)/2<=q and y<=(t+b)/2<=d
            result.update(marker_at=round(timestamp,4),mode=hit['mode'],box=hit['box'],
                          location_ok=location_ok,deadline_met=location_ok and timestamp<=case['goal'])
            stop.set()
    worker=MultiShopWorker(frames,lambda:names,post,stop,get_room_names=room_names,
                           get_room_hint=lambda:(case['name'],case['room']))
    worker.prioritize(case['name']);worker.start()
    # Prewarm completes while the player is still travelling. No measured entry
    # time is hidden here; this is the already-armed application workflow.
    if not worker.ready.wait(10):
        stop.set();worker.join(2)
        raise RuntimeError('Name finder did not become ready: '+str(events))
    clock[0]=time.monotonic()
    try:
        for version,(timestamp,frame) in enumerate(samples):
            delay=clock[0]+timestamp-case['start']-time.monotonic()
            if delay>0:time.sleep(delay)
            h,w=frame.shape[:2]
            dark=sum(float(frame[int((y-.06)*h):int((y+.06)*h):16,
                                 int((x-.06)*w):int((x+.06)*w):16].mean())<24
                     for x,y in ((.25,.25),(.75,.25),(.5,.5),(.25,.7),(.75,.7)))>=4
            if dark and not frames.dark:frames.loading_epoch+=1;frames.loading_started=time.monotonic()
            frames.dark=dark;frames.value=(version,time.monotonic(),frame)
            if stop.is_set():break
    finally:
        stop.set();worker.join(5)
    return dict(name=case['name'],goal=case['goal'],found=bool(result),**result,
                errors=[event[1] for _,event in events if event[0]=='shop_note' and 'ERROR' in str(event[1])],
                timing=next((event[1] for _,event in reversed(events) if event[0]=='shop_timing'),None))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--repeats',type=int,default=3)
    parser.add_argument('--output',default='benchmark_video_entries_results.json');args=parser.parse_args()
    rows=[]
    for repeat in range(args.repeats):
        for case in CASES:
            row={'repeat':repeat+1,**replay(case)};rows.append(row);print(json.dumps(row),flush=True)
    Path(args.output).write_text(json.dumps({'scope':'Real-time 30/60fps desktop-video replay; software marker callback; selected target plus the seven sellers from the supplied HeneFM page fixture; excludes native capture, GUI/compositor and network latency.',
        'results':rows},indent=2)+'\n')

if __name__=='__main__':main()
