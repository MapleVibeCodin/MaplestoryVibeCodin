"""Replay locator accuracy, latency and CPU work; never captures the desktop.

python benchmark_name_finder.py --baseline-ref 0c77d82 --runs 5
Without --baseline-ref, works from an extracted ZIP without Git installed.
"""
from cpu_guard import initialize
initialize()
import argparse
import json
from pathlib import Path
import platform
import statistics
import subprocess
import time
import types
import threading
import cv2
import numpy as np
import onnxruntime
from name_finder import NameFinder

ROOT=Path(__file__).resolve().parent
CASES=[
    ('regression_samples/cernia.png','Cernia',(1270,585),None),
    ('regression_samples/rollermo.png','Rollermo',(524,352),None),
    ('regression_samples/jtedoigte_141333.png','jtedoigte',(704,87),None),
    ('regression_samples/isadlyfe_143200.png','iSadlyfe',(623,289),None),
    ('regression_samples/oral_222618.png','Oral',(241,617),None),
    ('regression_samples/foxgod_060516.png','FoxGod',(1152,179),None),
    ('regression_samples/kilerious_085956.png','Kilerious',(621,296),None),
    ('Screenshot 2026-11-16 141643.png','MilkToast',(888,108),(1,210,1360,978)),
    ('Screenshot 2026-11-16 141643.png','FightClub',(766,325),(1,210,1360,978)),
    ('regression_samples/snapkin_072432.png','Snapkin',None,None),
    ('Screenshot 2026-11-16 141643.png','Ballor',None,(1,210,1360,978)),
]


class CountRecognition:
    def __init__(self,recognizer):
        object.__setattr__(self,'inner',recognizer)
        self.reset()

    def reset(self):
        object.__setattr__(self,'calls',0)
        object.__setattr__(self,'images',0)

    def __getattr__(self,name):
        return getattr(self.inner,name)

    def __setattr__(self,name,value):
        setattr(self.inner,name,value)

    def __call__(self,images):
        object.__setattr__(self,'calls',self.calls+1)
        object.__setattr__(self,'images',self.images+len(images))
        return self.inner(images)


def measure(finder,image,target,point,runs):
    finder.scan(image,target)
    wall=[];cpu=[];images=[];calls=[];correct=[]
    last=None
    for _ in range(runs):
        finder.recognizer.reset()
        t=time.perf_counter();c=time.process_time()
        last=finder.scan(image,target)
        cpu.append(round((time.process_time()-c)*1000,2))
        wall.append(round((time.perf_counter()-t)*1000,2))
        images.append(finder.recognizer.images);calls.append(finder.recognizer.calls)
        correct.append(last is None if point is None else last is not None and
                       last.box[0]<=point[0]<=last.box[2] and last.box[1]<=point[1]<=last.box[3])
    return {'median_ms':round(statistics.median(wall),2),
            'median_cpu_ms':round(statistics.median(cpu),2),
            'median_ocr_images':statistics.median(images),
            'median_ocr_calls':statistics.median(calls),
            'correct_runs':sum(correct),'wall_ms':wall,'cpu_ms':cpu,
            'last_hit':last.__dict__ if last else None}


def stress_worker(finder,seconds,baseline_ref=None):
    """Simulated 60 Hz frames and target replacement every 250 ms; no capture."""
    if baseline_ref:
        source=subprocess.check_output(['git','show',baseline_ref+':fast_shop_worker.py'],cwd=ROOT)
        worker_module=types.ModuleType('baseline_shop_worker')
        exec(compile(source,str(ROOT/'fast_shop_worker.py'),'exec'),vars(worker_module))
    else:
        import multi_shop_worker as worker_module
    import numpy as np
    image=cv2.imread(str(ROOT/'regression_samples/snapkin_072432.png'))
    stop=threading.Event();scans=[];started=time.monotonic()
    class Frames:
        def latest(self,after=-1):
            now=time.monotonic();version=int((now-started)*60)
            return None if version==after else (version,now,image)
        peek=latest
    class CountFinder:
        def prepare(self,*args):finder.prepare(*args)
        def scan(self,*args,**kwargs):
            cpu=time.thread_time()
            try:return finder.scan(*args,**kwargs)
            finally:scans.append(time.thread_time()-cpu)
    worker_module.NameFinder=lambda:CountFinder()
    names=('NotHere','NobodyHere','NotASeller')
    def target():
        generation=int((time.monotonic()-started)/.25)
        return names[generation%len(names)],generation
    if baseline_ref:
        worker=worker_module.FastShopWorker(Frames(),target,lambda event:None,stop)
    else:
        def queued_names():return names[:min(3,1+int((time.monotonic()-started)/.25))]
        def revisions():return {name.casefold():int((time.monotonic()-started)/.75) for name in queued_names()}
        worker=worker_module.MultiShopWorker(Frames(),queued_names,lambda event:None,stop,revisions)
    cpu=time.process_time();wall=time.perf_counter()
    worker.start();stop.wait(seconds);stop.set();worker.join(5)
    if worker.is_alive():raise RuntimeError('Stress worker did not stop')
    wall=time.perf_counter()-wall;cpu=time.process_time()-cpu
    return {'simulated_fps':60,'target_period_s':.25,'wall_seconds':round(wall,3),
            'searches':len(scans),'search_cpu_seconds':round(sum(scans),3),
            'search_cpu_fraction_of_one_core':round(sum(scans)/wall,3),
            'process_cpu_fraction_of_one_core':round(cpu/wall,3),
            'scope':'Static in-memory frames; legacy worker replaces targets, current worker retains incoming sellers. Excludes capture/GUI/Discord; models prewarmed.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-ref',help='Optional local Git revision to compare')
    parser.add_argument('--runs',type=int,default=5)
    parser.add_argument('--stress-seconds',type=float,default=0.,help='Optional simulated rapid-target stress duration per version')
    parser.add_argument('--output',type=Path,default=ROOT/'benchmark_v24_11.json')
    args=parser.parse_args()
    if args.runs<1:parser.error('--runs must be positive')
    cv2.setNumThreads(1)
    engines={}
    if args.baseline_ref:
        source=subprocess.check_output(['git','show',args.baseline_ref+':name_finder.py'],cwd=ROOT)
        module=types.ModuleType('baseline_name_finder')
        module.__file__=str(ROOT/'name_finder.py')
        exec(compile(source,module.__file__,'exec'),vars(module))
        engines['before']=module.NameFinder()
    engines['after']=NameFinder()
    for finder in engines.values():finder.recognizer=CountRecognition(finder.recognizer)
    rows=[]
    for path,target,point,crop in CASES:
        image=cv2.imread(str(ROOT/path))
        if image is None:raise FileNotFoundError(path)
        if crop:
            x,y,r,b=crop;image=image[y:b,x:r]
        row={'image':path,'target':target,'expected_point':point,'crop':crop}
        for label,finder in engines.items():
            row[label]=measure(finder,image,target,point,args.runs)
        rows.append(row)
        print(target, {label:row[label]['median_ms'] for label in engines},flush=True)
    report={'baseline_ref':args.baseline_ref,'runs_per_case':args.runs,
            'warmup_runs_per_case':1,'platform':platform.platform(),
            'opencv':cv2.__version__,'numpy':np.__version__,'onnxruntime':onnxruntime.__version__,
            'opencv_threads':1,'recognizer_threads':1,
            'scope':'Saved-image algorithm time/CPU only. Excludes capture, waits, worker cooldown and marker drawing; not a live accuracy or whole-app CPU estimate.',
            'cases':rows}
    if args.stress_seconds>0:
        report['scheduler_stress']={}
        for label,finder in engines.items():
            report['scheduler_stress'][label]=stress_worker(finder,args.stress_seconds,
                args.baseline_ref if label=='before' else None)
            print('CPU stress',label,report['scheduler_stress'][label],flush=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    return 0 if all(row['after']['correct_runs']==args.runs for row in rows) else 1


if __name__=='__main__':raise SystemExit(main())
