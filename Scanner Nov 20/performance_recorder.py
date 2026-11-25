"""Passive local timing telemetry. No raw images, keyboard hooks or uploads."""
from __future__ import annotations
import collections
import datetime
import json
from pathlib import Path
import queue
import statistics
import threading
import time
import uuid

SCHEMA=1
VERSION='24.66.1'
SAMPLE_INTERVAL=.05
DARK_THRESHOLD=.96
PATCH=16

def dark_fraction(frame):
    if frame is None:return None
    buf,w,h,stride=frame
    if w<=0 or h<=0 or stride<w*3 or len(buf)<stride*h:return None
    dark=sum(max(buf[i:i+3])<=16 for y in range(h)
             for i in range(y*stride,y*stride+w*3,3))
    return dark/(w*h)

class Transition:
    """Two consecutive observations; never bridge a missing/focus-lost sample."""
    def __init__(self):
        self.baseline=False
        self.dark_at=None
        self.pending=None
        self.count=0
        self.last=None

    def reset(self):
        self.__init__()

    def observe(self, at, dark):
        if dark is None or (self.last is not None and at-self.last>.25):
            self.reset()
        if dark is None:return []
        self.last=at
        if dark!=self.pending:
            self.pending=dark;self.count=1;self.first=at
        else:self.count+=1
        if self.count!=2:return []
        if dark:
            if not self.baseline or self.dark_at is not None:return []
            self.dark_at=self.first
            return [('black_start',self.first,{})]
        if self.dark_at is not None:
            start=self.dark_at;self.dark_at=None
            self.baseline=True
            return [('black_end',self.first,{'duration_ms':round((self.first-start)*1000,1)})]
        self.baseline=True
        return []

class PerformanceRecorder:
    def __init__(self, folder, *, capture=None, focused=None, geometry=None, point_window=None,
                 init_capture=None, release_capture=None):
        self.folder=Path(folder)
        self.session=uuid.uuid4().hex
        self.file=self.folder/(self.session+'.jsonl')
        self.capture=capture;self.focused=focused;self.geometry=geometry;self.point_window=point_window
        self.init_capture=init_capture;self.release_capture=release_capture
        self.events=queue.Queue(maxsize=2048)
        self.stop=threading.Event()
        self.enabled=True
        self.error=None;self.dropped=0
        self.active=None;self.key=None;self.scene=None;self.inventory=None;self.sold=None
        self.context=None;self.last_scan_id=None
        self.worker=threading.Thread(target=self._run,name='FM-performance',daemon=True)
        self.worker.start()

    def _emit(self, event, at=None, attempt=None, **data):
        attempt=self.active if attempt is None else attempt
        if not self.enabled or attempt is None:return
        row={'schema':SCHEMA,'version':VERSION,'session':self.session,'attempt':attempt,
             'event':event,'t':time.perf_counter() if at is None else at,**data}
        try:self.events.put_nowait(row)
        except queue.Full:self.dropped+=1

    def observe(self, key, deal, hwnd, client, supported, entrance, inventory):
        if not self.enabled:return
        if key!=self.key:
            self.end('lock_changed_or_released')
            if key is not None:
                self.active=uuid.uuid4().hex
                self.key=key
                self._emit('lock_observed',cc=deal.cc,fm=deal.fm,
                           utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                           confidence='scanner_state')
        if self.active is None:return
        # Context is one immutable reference, atomically replaced by GUI thread.
        self.context=(self.active,hwnd,tuple(client)) if supported else None
        if self.sold!=deal.sold:
            self.sold=deal.sold
            if self.sold:self._emit('listing_unavailable',confidence='feed_observed')
        if not supported:return
        scene='shop' if inventory is not None else 'entrance' if entrance else 'unclassified'
        if scene!=self.scene:
            self.scene=scene
            self._emit('scene_observed',scene=scene,confidence='detector' if scene!='unclassified' else 'unknown')
        if inventory is not None:
            # Do not retain seller, item names, raw OCR or pixels.
            status=str(inventory.get('status',''))
            modes={mode for mode,_ in inventory.get('hits',())}
            low=status.casefold()
            if 'MATCH' in modes or 'name + price match' in low:state='unique_match'
            elif 'AMBIGUOUS' in modes or 'multiple exact matches' in low or 'multiple name/price matches' in low:state='multiple_matches'
            elif modes & {'SOLD','SOLD_CHECK'} or 'sold / unavailable' in low:state='target_unavailable'
            elif modes & {'FAST_NAME','FAST_PRICE','FAST_SOLD','PRICE_CHECK','ROW_CHECK'}:state='candidate'
            elif 'seller not verified' in low:state='seller_unverified'
            elif 'price differs' in low or 'price not verified' in low:state='price_differs'
            elif 'not visible' in low:state='not_visible'
            elif 'verifying visible rows' in low or 'reading inventory' in low:state='reading'
            elif 'rows changed' in low:state='rows_changed'
            elif 'ocr unavailable' in low:state='ocr_error'
            elif 'tooltip' in low:state='tooltip'
            else:state='other'
            timing=inventory.get('timing')
            if timing and timing.get('scan_id')!=self.last_scan_id:
                self.last_scan_id=timing['scan_id']
                self._emit('inventory_timing',total_ms=timing['total_ms'],
                           row_recognition_ms=timing['row_recognition_ms'],
                           used_ocr=timing['used_ocr'],visible_rows=timing['visible_rows'],
                           geometry_fallback=bool(timing.get('geometry_fallback',False)),
                           sold_retry=bool(timing.get('sold_retry',False)),
                           paired_roi_captures=timing.get('paired_roi_captures'),native_fast=bool(timing.get('native_fast',False)))
            if state!=self.inventory:
                self.inventory=state
                self._emit('inventory_observed',state=state,confidence='detector')
        else:self.inventory=None

    def marker(self,event,at=None,**data):
        self._emit(event,at=at,**data)

    def end(self,reason):
        if self.active is not None:self._emit('attempt_end',reason=reason,outcome='unknown')
        self.active=None;self.key=None;self.scene=None;self.inventory=None;self.sold=None;self.context=None;self.last_scan_id=None

    def set_enabled(self,enabled):
        if not enabled:self.end('recording_paused')
        self.enabled=bool(enabled)

    def _sample(self,context):
        if not context or self.capture is None:return None
        _,hwnd,client=context
        if not self.focused(hwnd) or self.geometry(hwnd)!=client:return None
        x,y,w,h=client
        vals=[]
        for fx,fy in ((.25,.30),(.50,.50),(.75,.65)):
            px=x+int(w*fx);py=y+int(h*fy)
            if self.point_window is not None and self.point_window(px,py)!=hwnd:return None
            value=dark_fraction(self.capture((px-PATCH//2,py-PATCH//2,PATCH,PATCH),allow_crop=True))
            if value is None:return None
            vals.append(value)
        if not self.focused(hwnd) or self.geometry(hwnd)!=client:return None
        return min(vals)>=DARK_THRESHOLD

    def _run(self):
        detector=Transition()
        previous=None;last_focus=None;next_sample=0
        last_channel={}
        interval=SAMPLE_INTERVAL
        try:
            self.folder.mkdir(parents=True,exist_ok=True)
            if self.init_capture:self.init_capture()
            with self.file.open('a',encoding='utf-8',buffering=1) as out:
                while not self.stop.is_set() or not self.events.empty():
                    for _ in range(128):
                        try:row=self.events.get_nowait()
                        except queue.Empty:break
                        if row['event']=='pointer_requested' and row.get('kind')=='channel':
                            last_channel[row['attempt']]=row['t']
                            if len(last_channel)>32:last_channel.pop(next(iter(last_channel)))
                        out.write(json.dumps(row,separators=(',',':'))+'\n')
                    if self.stop.is_set():continue
                    now=time.perf_counter();ctx=self.context
                    if ctx!=previous:
                        if previous and detector.dark_at is not None:
                            self._emit('black_interrupted',attempt=previous[0],confidence='unknown')
                        detector.reset();previous=ctx;last_focus=None
                    if ctx is not None and now>=next_sample:
                        at=time.perf_counter()
                        try:dark=self._sample(ctx)
                        except Exception:dark=None
                        elapsed=time.perf_counter()-at
                        # Slow screen capture backs off rather than competing with scanner.
                        interval=.10 if elapsed>.008 else SAMPLE_INTERVAL
                        next_sample=at+interval
                        if self.context==ctx:
                            valid=dark is not None
                            if valid!=last_focus:
                                if not valid and detector.dark_at is not None:
                                    self._emit('black_interrupted',attempt=ctx[0],confidence='unknown')
                                self._emit('sampling_available' if valid else 'sampling_gap',
                                           attempt=ctx[0],at=at,confidence='observed')
                                last_focus=valid
                            for event,stamp,data in detector.observe(at,dark):
                                if event=='black_end':
                                    started=stamp-data['duration_ms']/1000
                                    recent=last_channel.get(ctx[0])
                                    data['association']='channel_shortcut_recent' if recent is not None and 0<=started-recent<=3 else 'unclassified'
                                    data['confidence']='visual_estimate'
                                self._emit(event,attempt=ctx[0],at=stamp,**data)
                    self.stop.wait(.01 if ctx is not None else .10)
        except Exception as exc:self.error=type(exc).__name__
        finally:
            if self.release_capture:
                try:self.release_capture()
                except Exception:pass

    def close(self):
        self.end('scanner_closed')
        self.stop.set()
        self.worker.join(timeout=.5)

    def export(self,path):
        # No raw frames or identifying seller/listing fields. Read completed lines
        # across sessions; an interrupted last line is excluded, not fabricated.
        rows=[];bad=0
        for file in sorted(self.folder.glob('*.jsonl')):
            with file.open(encoding='utf-8') as source:
                for line in source:
                    try:rows.append(json.loads(line))
                    except ValueError:bad+=1
        report=summarize(rows)
        report.update({'schema':SCHEMA,'version':VERSION,'invalid_lines':bad,
                       'current_session_dropped_events':self.dropped,'recorder_error':self.error,
                       'notes':['Times are scanner observations, not server confirmations.',
                                'No purchase success or movement key recording; outcome unknown.',
                                'Black intervals use sampled pixels and may be interrupted by focus loss.',
                                'Recent channel shortcut is an association, not proof of channel loading.',
                                'Current session may have queued events not yet flushed.']})
        Path(path).write_text(json.dumps(report,indent=2),encoding='utf-8')

def summarize(rows):
    attempts=collections.defaultdict(list)
    for row in rows:attempts[row['attempt']].append(row)
    metrics=collections.defaultdict(list);result=[]
    pointer_counts=collections.Counter()
    for aid,events in attempts.items():
        events.sort(key=lambda e:e['t'])
        start=next((e['t'] for e in events if e['event']=='lock_observed'),None)
        first=set();timeline=[];shop_pointer=None
        for e in events:
            event=e['event'];elapsed=None if start is None else round((e['t']-start)*1000,1)
            data={k:v for k,v in e.items() if k not in ('t','attempt','session','schema','version')}
            data['elapsed_ms']=elapsed;timeline.append(data)
            if event in ('pointer_requested','pointer_duplicate','pointer_expired','pointer_failure','pointer_result','pointer_game_focus','pointer_displaced','pointer_watch_complete'):
                pointer_counts[event]+=1
            if event=='pointer_game_focus':
                metrics['pointer_to_game_focus_ms:'+e['kind']].append(e['elapsed_ms'])
            elif event=='pointer_displaced':
                metrics['pointer_to_displacement_ms:'+e['kind']].append(e['elapsed_ms'])
            elif event=='pointer_watch_complete':
                metrics['pointer_max_outside_px:'+e['kind']].append(e['max_outside_px'])
            if event=='inventory_timing':
                metrics['inventory_scan_ms'].append(e['total_ms'])
                metrics['inventory_scan_ms:'+('geometry' if e.get('geometry_fallback') else 'exact')].append(e['total_ms'])
                metrics['inventory_row_recognition_ms:'+('native' if e.get('native_fast') else 'ocr' if e.get('used_ocr') else 'cache')].append(e['row_recognition_ms'])
            if event=='black_end':
                metrics['black_ms:'+e.get('association','unclassified')].append(e['duration_ms'])
            elif event=='pointer_result' and e.get('ok'):
                metrics['pointer_ms:'+e['kind']].append(e['total_ms'])
                if e['kind']=='shop':shop_pointer=e['t']
            elif event=='scene_observed' and e.get('scene')=='shop' and shop_pointer is not None:
                metrics['shop_pointer_to_observed_shop_ms'].append(round((e['t']-shop_pointer)*1000,1));shop_pointer=None
            if event=='scene_observed' and e.get('scene') in ('entrance','shop'):
                label='lock_to_first_'+e['scene']+'_ms'
            elif event=='inventory_observed' and e.get('state') in ('unique_match','multiple_matches'):
                label='lock_to_first_item_match_ms'
            else:continue
            if label not in first and elapsed is not None:
                first.add(label);metrics[label].append(elapsed)
        result.append({'attempt':aid,'session':events[0]['session'],'version':events[0]['version'],
                       'outcome':'unknown','timeline':timeline})
    def distribution(values):
        v=sorted(values);idx=lambda p:v[min(len(v)-1,max(0,int((len(v)-1)*p+.5)))]
        return {'n':len(v),'min':v[0],'median':statistics.median(v),'p90':idx(.9),'max':v[-1]}
    return {'attempt_count':len(result),'metrics':{k:distribution(v) for k,v in metrics.items()},
            'pointer_event_counts':dict(pointer_counts),'attempts':result}
