"""Actual OCR checks on supplied examples, including forced primary misses."""
from cpu_guard import initialize
initialize()
import json,time
from pathlib import Path
import cv2
import numpy as np
from snapshot_ocr import SnapshotOCR
ROOT=Path(__file__).parent


def main():
    cv2.setNumThreads(1)
    engine=SnapshotOCR()
    print('Preparing local recovery engine...',flush=True)
    engine.prepare_recovery()
    mora=np.full((650,1050,3),170,np.uint8)
    mora[370:420,180:280]=cv2.imread(str(ROOT/'assets/mora_badge_test.png'))
    fixtures=[('Rollermo',cv2.imread(str(ROOT/'regression_samples/rollermo.png')),(505,342,548,363)),
              ('Cernia',cv2.imread(str(ROOT/'regression_samples/cernia.png')),(1248,572,1300,599)),
              ('Mora',mora,(205,380,262,415))]
    results=[]
    actual_native=engine.native
    class Miss:
        def recognize_cv2_sync(self,image,language):return {'lines':[]}
    for route in ('normal','forced primary miss'):
        engine.native=actual_native if route=='normal' else Miss()
        for target,image,bounds in fixtures:
            if image is None:raise RuntimeError('Missing regression sample '+target)
            start=time.perf_counter();hit=engine.scan(image,target)
            center=((hit.box[0]+hit.box[2])/2,(hit.box[1]+hit.box[3])/2) if hit else (-1,-1)
            passed=bounds[0]<=center[0]<=bounds[2] and bounds[1]<=center[1]<=bounds[3]
            row={'route':route,'target':target,'passed':passed,'read':hit.text if hit else None,
                 'mode':hit.mode if hit else None,'milliseconds':round((time.perf_counter()-start)*1000)}
            results.append(row);print(row,flush=True)
    (ROOT/'self_test_results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    if not all(row['passed'] for row in results):
        print('FAILED: keep self_test_results.json and last_scan_debug.json for diagnosis.')
        return 1
    print('PASS: all six sample checks located the correct label. Live game capture is a separate check.')
    return 0

if __name__=='__main__':raise SystemExit(main())
