"""Offline synthetic workload: no game, input hooks, or production installation."""
from __future__ import annotations
import argparse
import gc
import json
import math
from pathlib import Path
import platform
import statistics
import sys
import tempfile
import threading
import time
import tracemalloc
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'Scanner Nov 20'))
from performance_recorder import PerformanceRecorder, VERSION, atomic_report

CLIENT=(0,0,1366,768)
DEAL=SimpleNamespace(cc=1,fm=1,sold=False)
PIXELS=bytes([255])*(16*16*3)

def distribution(values):
    v=sorted(values);n=len(v)
    def q(p):return round(v[math.ceil(n*p)-1],5) if n else None
    return {'n':n,'p50_ms':q(.5),'p95_ms':q(.95),'p99_ms':q(.99),'max_ms':round(v[-1],5) if n else None}

class MeasuredRecorder(PerformanceRecorder):
    def __init__(self,*args,**kwargs):
        self.capture_ms=[];self.emit_ms=[]
        super().__init__(*args,**kwargs)
    def _sample(self,context):
        start=time.perf_counter_ns()
        try:return super()._sample(context)
        finally:self.capture_ms.append((time.perf_counter_ns()-start)/1e6)
    def _emit(self,*args,**kwargs):
        start=time.perf_counter_ns()
        try:return super()._emit(*args,**kwargs)
        finally:self.emit_ms.append((time.perf_counter_ns()-start)/1e6)

def run(mode,seconds,hz,trace=False):
    with tempfile.TemporaryDirectory(prefix='fm-lab6-') as folder:
        r=MeasuredRecorder(folder,capture=lambda *a,**k:(PIXELS,16,16,48),
                           focused=lambda _:True,geometry=lambda _:CLIENT,
                           point_window=lambda *a:1)
        r.set_enabled(mode=='on')
        time.sleep(.2) # startup excluded
        if trace:tracemalloc.start()
        samples=[];lateness=[];start=time.perf_counter();cpu=time.process_time()
        ticks=round(seconds*hz)
        for i in range(ticks):
            due=start+i/hz
            delay=due-time.perf_counter()
            if delay>0:time.sleep(delay)
            at=time.perf_counter_ns()
            lateness.append(max(0,(at/1e9-due)*1000))
            r.observe('synthetic',DEAL,1,CLIENT,True,False,None)
            r.observe_gate('room_confirmed',CLIENT[2:])
            r.marker('scanner_gate',state='room_confirmed')
            samples.append((time.perf_counter_ns()-at)/1e6)
        elapsed=time.perf_counter()-start
        cpu_s=time.process_time()-cpu
        if trace:
            _,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
        else:peak=None
        close_at=time.perf_counter();r.close()
        shutdown_ms=(time.perf_counter()-close_at)*1000
        files=list(Path(folder).glob('*.jsonl'))
        return {'mode':mode,'wall_seconds':elapsed,'cpu_seconds':cpu_s,
                'cpu_percent_one_core':100*cpu_s/elapsed,
                'observe_path':distribution(samples),'schedule_lateness':distribution(lateness),
                'emit_path':distribution(r.emit_ms),'synthetic_capture_path':distribution(r.capture_ms),
                'python_peak_traced_bytes':peak,'trace_enabled':trace,
                'disk_bytes':sum(p.stat().st_size for p in files),'files':len(files),
                'enqueued':r._seq-r.dropped,'written':r._written,'dropped':r.dropped,
                'pending':r.events.qsize(),'writer_error':r.error,'worker_still_alive':r.worker.is_alive(),
                'shutdown_ms':shutdown_ms}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seconds',type=int,default=10)
    p.add_argument('--hz',type=int,default=100)
    p.add_argument('--rounds',type=int,default=3)
    p.add_argument('--output',type=Path,default=Path('FM_Rush_Lab6_Benchmark.json'))
    a=p.parse_args()
    if not 2<=a.seconds<=60 or not 10<=a.hz<=200 or not 2<=a.rounds<=5:p.error('seconds 2–60, hz 10–200, rounds 2–5')
    pairs=[]
    for i in range(a.rounds):
        order=('off','on') if i%2==0 else ('on','off')
        runs={}
        for mode in order:
            gc.collect();runs[mode]=run(mode,a.seconds,a.hz)
        off,on=runs['off'],runs['on']
        pairs.append({'order':order,'off':off,'on':on,
                      'cpu_delta_pp_one_core':on['cpu_percent_one_core']-off['cpu_percent_one_core'],
                      'observe_p95_delta_ms':on['observe_path']['p95_ms']-off['observe_path']['p95_ms']})
    # Memory tracing is separate: tracemalloc changes timing and CPU.
    memory={mode:run(mode,a.seconds,a.hz,trace=True)['python_peak_traced_bytes'] for mode in ('off','on')}
    report={'schema':1,'recorder':VERSION,'kind':'synthetic_offline','host':platform.platform(),
            'python':platform.python_version(),'seconds':a.seconds,'hz':a.hz,'pairs':pairs,
            'memory_traced_separate_bytes':memory,
            'median_cpu_delta_pp_one_core':statistics.median(x['cpu_delta_pp_one_core'] for x in pairs),
            'median_observe_p95_delta_ms':statistics.median(x['observe_p95_delta_ms'] for x in pairs),
            'note':'CPU is one logical core equivalent, not total system CPU; synthetic capture is memory-only, not GDI. Timing includes profiler wrappers. Off mode is paused recorder, not absent worker. No live-game performance claims.'}
    atomic_report(a.output,report)
    print(json.dumps(report,indent=2))
    if any(x['on']['dropped'] or x['on']['writer_error'] or x['on']['worker_still_alive'] or x['on']['pending'] or x['on']['enqueued']!=x['on']['written'] for x in pairs):
        raise SystemExit(1)

if __name__=='__main__':main()
