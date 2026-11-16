"""Compare warm-worker room-entry latency on a saved FM5 frame; no live capture."""
from cpu_guard import initialize
initialize()
import argparse
import json
import statistics
import subprocess
import sys
import threading
import time
import types
from pathlib import Path
import cv2
from name_finder import NameFinder
import multi_shop_worker
ROOT=Path(__file__).resolve().parent

def replay(module,engine,image,names,room_names):
    stop=threading.Event();elapsed=[];calls=[];notes=[]
    class Frames:
        def latest(self,after=-1):
            now=time.monotonic();v=int(now*60)
            return None if v==after else (v,now,image)
        peek=latest
    class Finder:
        def room_number(self,*args):return engine.room_number(*args)
        def prepare(self,*args):return engine.prepare(*args)
        def scan(self,*args,**kwargs):
            calls.append(args[1]);return engine.scan(*args,**kwargs)
    old=module.NameFinder;module.NameFinder=Finder
    started=time.perf_counter()
    def post(event):
        if event[0]=='shops_frame' and {'Cernia','Melonade'}<=set(event[2]):
            elapsed.append(time.perf_counter()-started);stop.set()
    kwargs={'get_room_names':lambda room:room_names} if module is multi_shop_worker else {}
    worker=module.MultiShopWorker(Frames(),lambda:names,post,stop,**kwargs)
    try:
        worker.start();worker.join(20);stop.set();worker.join(3)
        if worker.is_alive() or not elapsed:raise RuntimeError('Both sellers were not located')
    finally:module.NameFinder=old
    return round(elapsed[0]*1000,2),calls

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--runs',type=int,default=3)
    parser.add_argument('--baseline-ref',default='30b232a');args=parser.parse_args()
    source=subprocess.check_output(['git','show',args.baseline_ref+':multi_shop_worker.py'],cwd=ROOT)
    baseline=types.ModuleType('baseline_entry_worker');sys.modules[baseline.__name__]=baseline
    exec(compile(source,'baseline_entry_worker.py','exec'),vars(baseline))
    cv2.setNumThreads(1);engine=NameFinder()
    image=cv2.imread(str(ROOT/'regression_samples/cernia.png'))
    targets=('Cernia','Melonade')
    for name in ('NotHere','NobodyHere',*targets):engine.prepare(name,image.shape[1]);engine.scan(image,name)
    results={}
    for scenario,names in [('same_room_only',targets),('other_rooms_queued_first',('NotHere','NobodyHere',*targets))]:
        results[scenario]={}
        for label,module in [('v24_11',baseline),('v24_12',multi_shop_worker)]:
            runs=[replay(module,engine,image,names,targets) for _ in range(args.runs)]
            results[scenario][label]={'median_ms':round(statistics.median(row[0] for row in runs),2),
                'runs_ms':[row[0] for row in runs],'searches':[row[1] for row in runs]}
        print(scenario,results[scenario],flush=True)
    result={'scope':'Prewarmed single-thread worker, static FM5 frame at simulated 60Hz. Includes v24.12 room header OCR and v24.11 cooldown; excludes model startup, live capture and GUI. Other-room scenario has two archived sellers from other rooms before the two visible FM5 sellers.',
            'baseline_ref':args.baseline_ref,'runs':args.runs,'results':results}
    (ROOT/'benchmark_entry_v24_12.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
