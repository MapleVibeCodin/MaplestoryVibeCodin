"""Replay a same-room queue with absent sellers before visible sellers."""
from cpu_guard import initialize
initialize()
import json
from pathlib import Path
import statistics
import subprocess
import sys
import types
import cv2
from name_finder import NameFinder
import multi_shop_worker
from benchmark_entry_burst import replay
ROOT=Path(__file__).resolve().parent
baseline=types.ModuleType('baseline_queue_worker');sys.modules[baseline.__name__]=baseline
source=subprocess.check_output(['git','show','55c8af0:multi_shop_worker.py'],cwd=ROOT)
exec(compile(source,'baseline_queue_worker.py','exec'),vars(baseline))
cv2.setNumThreads(1);engine=NameFinder();image=cv2.imread(str(ROOT/'regression_samples/cernia.png'))
results={}
for label,names in [('two_visible',('Cernia','Melonade')),('six_absent_first',('NotHere','NobodyHere','NobodyElse','MissingShop','OtherSeller','GoneAway','Cernia','Melonade'))]:
    # Both versions receive the exact same same-room names. Avoid model/candidate
    # warmup skew; the benchmark compares worker policy, not cold startup.
    for name in names:engine.scan(image,name,fast_only=True)
    results[label]={}
    for version,module in [('v24_13',baseline),('v24_14',multi_shop_worker)]:
        rows=[replay(module,engine,image,names,names) for _ in range(3)]
        results[label][version]={'median_ms':round(statistics.median(row[0] for row in rows),2),
            'runs_ms':[row[0] for row in rows],'searches':[row[1] for row in rows]}
    print(label,results[label],flush=True)
(ROOT/'benchmark_queue_v24_14.json').write_text(json.dumps({'scope':'Warm static FM5 frame at simulated 60Hz; time until both visible sellers have correct name matches. Same room queue, same name verification engine. Includes room read and worker waits, excludes model startup, live capture and UI. Three runs per scenario.', 'results':results},indent=2)+'\n')
