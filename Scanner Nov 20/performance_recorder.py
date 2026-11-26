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
VERSION='24.63.4-lab4'
SAMPLE_INTERVAL=.05
DARK_THRESHOLD=.96
PATCH=16
PURCHASE_TIMEOUT=10.0 # Proposed evidence-correlation window; not a live benchmark.
GATE_HEARTBEAT=1.0
GATE_SOURCE_MAX_AGE=1.25
GATE_READY_TIMEOUT=3.0

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
                 init_capture=None, release_capture=None, purchase_source_verified=False):
        self.folder=Path(folder)
        self.session=uuid.uuid4().hex
        self.file=self.folder/(self.session+'.jsonl')
        self.capture=capture;self.focused=focused;self.geometry=geometry;self.point_window=point_window
        self.init_capture=init_capture;self.release_capture=release_capture
        self.events=queue.Queue(maxsize=2048)
        self.stop=threading.Event()
        self.enabled=True
        self.error=None;self.dropped=0
        self.active=None;self.key=None;self.scope=None;self.scene=None;self.inventory=None;self.sold=None
        self.context=None;self.last_scan_id=None
        self.last_gate_sample=None;self.last_gate_at=None
        # Fail closed until a passive, independently validated receipt source exists.
        self.purchase_source_verified=bool(purchase_source_verified)
        self.purchase_pending=None
        self.purchase_seen=set()
        self.worker=threading.Thread(target=self._run,name='FM-performance',daemon=True)
        self.worker.start()

    def _emit(self, event, at=None, attempt=None, **data):
        attempt=self.active if attempt is None else attempt
        if not self.enabled or attempt is None:return
        row={'schema':SCHEMA,'version':VERSION,'session':self.session,'attempt':attempt,
             'event':event,'t':time.perf_counter() if at is None else at,**data}
        try:self.events.put_nowait(row)
        except queue.Full:self.dropped+=1

    def observe(self, key, deal, hwnd, client, supported, entrance, inventory, *, unlocked=False):
        """Observe existing state only; unlocked segments are not chase/purchase attempts."""
        if not self.enabled:return
        scope='unlocked' if unlocked else 'locked' if key is not None and deal is not None else None
        if scope!=self.scope or key!=self.key:
            self.end('observation_scope_or_target_changed')
        if self.active is None:
            # Do not start an unlocked segment while the game is unfocused/unavailable.
            # Preserve legacy locked-start behavior.
            if scope is None or (scope=='unlocked' and not supported):return
            self.active=uuid.uuid4().hex
            self.key=key
            self.scope=scope
            fields={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    'confidence':'scanner_state'}
            if scope=='locked':
                self._emit('lock_observed',cc=deal.cc,fm=deal.fm,**fields)
            else:
                self._emit('unlocked_observed',target_present=deal is not None,**fields)
        # Context is one immutable reference, atomically replaced by GUI thread.
        self.context=(self.active,hwnd,tuple(client)) if supported and hwnd is not None and client is not None else None
        self._expire_purchase('focus_gap' if self.context is None else None)
        # No feed outcome is inferred when the user has not selected a listing.
        if deal is not None and self.sold!=deal.sold:
            self.sold=deal.sold
            if self.sold:self._emit('listing_unavailable',confidence='feed_observed')
        if self.context is None:return
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
            elif modes & {'PRICE_CHECK','ROW_CHECK'}:state='candidate'
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
                           sold_retry=bool(timing.get('sold_retry',False)))
            if state!=self.inventory:
                self.inventory=state
                self._emit('inventory_observed',state=state,confidence='detector')
        else:self.inventory=None

    def _finish_purchase(self, outcome, reason, at=None):
        pending=self.purchase_pending
        if pending is None:return
        pid,segment,started=pending
        stamp=time.perf_counter() if at is None else at
        self.purchase_pending=None
        self._emit('purchase_outcome',attempt=segment,at=stamp,purchase_id=pid,
                   outcome=outcome,reason=reason,duration_ms=round(max(0,stamp-started)*1000,1),
                   confidence='verified_ui' if outcome in ('confirmed','failed','canceled') else 'unknown')

    def _expire_purchase(self, reason=None):
        if self.purchase_pending is None:return
        if reason is None and time.perf_counter()-self.purchase_pending[2]>=PURCHASE_TIMEOUT:
            reason='receipt_timeout'
        if reason is not None:self._finish_purchase('unknown',reason)

    def observe_purchase(self, kind, token, *, segment):
        """Internal passive receipt-source contract; no clicks, key hooks, or raw text.
        Only a qualified visible-UI detector may call this method. A submitted
        purchase must precede its explicit result; listing/sold status is not evidence.
        Token is an opaque UUID4 per observed submission, never an item/account ID.
        """
        if not self.purchase_source_verified or not self.enabled or self.context is None:return False
        if segment!=self.active or self.context[0]!=segment:return False
        if kind not in ('submitted','confirmed','failed','canceled'):return False
        try:
            parsed=uuid.UUID(token)
            if parsed.version!=4 or parsed.hex!=token:return False
        except (ValueError,TypeError,AttributeError):return False
        self._expire_purchase()
        if kind=='submitted':
            if token in self.purchase_seen or len(self.purchase_seen)>=4096:return False
            self._finish_purchase('unknown','superseded')
            self.purchase_seen.add(token)
            stamp=time.perf_counter()
            self.purchase_pending=(token,segment,stamp)
            self._emit('purchase_attempt',at=stamp,purchase_id=token,confidence='verified_ui')
            return True
        if self.purchase_pending is None or self.purchase_pending[:2]!=(token,segment):return False
        self._finish_purchase(kind,'explicit_ui_result')
        return True

    def observe_gate(self, state, client_size=None):
        """Reuse existing GUI gate state only; no capture or new recognition."""
        if not self.enabled or self.active is None:return
        # Every state change is retained; stable observed state gets a bounded
        # heartbeat so the offline reducer never assumes an arbitrarily old scene.
        if self.context is None:state='unavailable'
        elif state not in ('entrance','room_confirmed'):state='unclassified'
        now=time.perf_counter()
        if state==self.last_gate_sample and self.last_gate_at is not None and now-self.last_gate_at<GATE_HEARTBEAT:return
        self.last_gate_sample=state;self.last_gate_at=now
        self._emit('transition_gate_sample',at=now,state=state,
                   client_size=list(client_size) if client_size is not None else None,
                   confidence='existing_detector' if state in ('entrance','room_confirmed') else 'unknown')

    def marker(self,event,at=None,**data):
        # Late pointer/watch callbacks belong to the locked workflow, not an
        # unlocked observation segment. Only the existing scanner gate is shared.
        if event.startswith('purchase_'):return # use the evidence contract only
        if self.scope=='unlocked' and event!='scanner_gate':return
        self._emit(event,at=at,**data)

    def end(self,reason):
        self._expire_purchase('segment_ended')
        self.purchase_seen.clear()
        if self.active is not None:self._emit('attempt_end',reason=reason,outcome='unknown')
        self.active=None;self.key=None;self.scope=None;self.scene=None;self.inventory=None;self.sold=None;self.context=None;self.last_scan_id=None
        self.last_gate_sample=None;self.last_gate_at=None

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
                            if valid and detector.dark_at is not None and detector.last is not None and at-detector.last>.25:
                                self._emit('black_interrupted',attempt=ctx[0],at=at,confidence='unknown',reason='sample_gap')
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
                       'purchase_source_verified_current_session':self.purchase_source_verified,
                       'notes':['Times are scanner observations, not server confirmations.',
                                'Purchase outcomes require a validated visible-UI submission and receipt; current app has no qualified source. No movement keys recorded.',
                                'Unlocked observation segments are not lock attempts; no target means no inventory recognition.',
                                'Black intervals use sampled pixels and may be interrupted by focus loss.',
                                'Recent channel shortcut is an association, not proof of channel loading.',
                                'Transition observations pair black intervals with existing scene gates; entrance/room changes are visual estimates, not proof of portal movement or actual channel identity.',
                                'Current session may have queued events not yet flushed.']})
        Path(path).write_text(json.dumps(report,indent=2),encoding='utf-8')

def summarize_transitions(events):
    """Conservative offline correlation of existing visual observations.
    A transition is never proof of an actual channel change or portal use.
    Incomplete/interrupted loading and missing destination are explicit.
    """
    result=[];source=None;pending=None;ready=None
    known={'entrance','room_confirmed'}
    def number(x):
        return isinstance(x,(int,float)) and not isinstance(x,bool) and 0<=x<float('inf')
    def finish_pending(reason):
        nonlocal pending
        if pending is None:return
        result.append({'status':'incomplete','reason':reason,'source':pending[1],
                       'destination':None,'loading_ms':None,'readiness_ms':None,
                       'association':'unclassified','scene_change':'unknown'})
        pending=None
    def finish_ready(reason):
        nonlocal ready
        if ready is None:return
        ready['reason']=reason
        result.append(ready);ready=None
    for e in sorted(events,key=lambda row:row['t']):
        t=e['t'];kind=e['event']
        if ready is not None and t-ready['end_t']>GATE_READY_TIMEOUT:finish_ready('destination_timeout')
        if kind=='transition_gate_sample':
            state=e.get('state')
            if state=='unavailable':
                finish_pending('observation_gap');finish_ready('observation_gap')
                source=None;continue
            if state not in known:
                source=None;continue
            if ready is not None and t>=ready['end_t']:
                ready['destination']=state
                ready['readiness_ms']=round((t-ready['end_t'])*1000,1)
                old=ready['source']
                ready['scene_change']=('same_scene' if old==state else
                    'entrance_to_room' if old=='entrance' and state=='room_confirmed' else
                    'room_to_entrance' if old=='room_confirmed' and state=='entrance' else 'unknown')
                finish_ready('destination_observed')
            source=(state,t)
        elif kind in ('sampling_gap','black_interrupted','attempt_end'):
            finish_pending('segment_ended' if kind=='attempt_end' else 'observation_gap')
            finish_ready('segment_ended' if kind=='attempt_end' else 'observation_gap')
            source=None
        elif kind=='black_start':
            finish_pending('superseded');finish_ready('next_loading')
            scene=source[0] if source and 0<=t-source[1]<=GATE_SOURCE_MAX_AGE else None
            pending=(t,scene);source=None
        elif kind=='black_end':
            if pending is None:
                finish_ready('unpaired_black_end')
                result.append({'status':'incomplete','reason':'unpaired_black_end','source':None,
                               'destination':None,'loading_ms':None,'readiness_ms':None,
                               'association':'unclassified','scene_change':'unknown'})
                source=None;continue
            start,scene=pending
            d=e.get('duration_ms')
            if not number(d) or t<start or abs(d-(t-start)*1000)>1:
                finish_pending('duration_mismatch');source=None;continue
            pending=None;source=None
            ready={'status':'loading_observed','reason':None,'source':scene,'destination':None,
                   'loading_ms':d,'readiness_ms':None,'end_t':t,
                   'association':'channel_shortcut_recent' if e.get('association')=='channel_shortcut_recent' else 'unclassified',
                   'scene_change':'unknown'}
    finish_pending('missing_black_end');finish_ready('destination_unobserved')
    for row in result:row.pop('end_t',None)
    return result

def summarize(rows):
    attempts=collections.defaultdict(list)
    for row in rows:attempts[(row['session'],row['attempt'])].append(row)
    metrics=collections.defaultdict(list);result=[]
    pointer_counts=collections.Counter()
    for (session,aid),events in attempts.items():
        events.sort(key=lambda e:e['t'])
        anchor=next((e for e in events if e['event'] in ('lock_observed','unlocked_observed')),None)
        scope=('unlocked' if anchor['event']=='unlocked_observed' else 'locked') if anchor else 'unknown'
        start=anchor['t'] if anchor else None
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
                metrics['inventory_row_recognition_ms:'+('ocr' if e.get('used_ocr') else 'cache')].append(e['row_recognition_ms'])
            if event=='black_end':
                metrics['black_ms:'+e.get('association','unclassified')].append(e['duration_ms'])
            elif event=='pointer_result' and e.get('ok'):
                metrics['pointer_ms:'+e['kind']].append(e['total_ms'])
                if e['kind']=='shop':shop_pointer=e['t']
            elif event=='scene_observed' and e.get('scene')=='shop' and shop_pointer is not None:
                metrics['shop_pointer_to_observed_shop_ms'].append(round((e['t']-shop_pointer)*1000,1));shop_pointer=None
            if event=='scene_observed' and e.get('scene') in ('entrance','shop'):
                label=scope+'_to_first_'+e['scene']+'_ms' if scope!='locked' else 'lock_to_first_'+e['scene']+'_ms'
            elif event=='inventory_observed' and e.get('state') in ('unique_match','multiple_matches'):
                label='lock_to_first_item_match_ms' if scope=='locked' else scope+'_to_first_item_match_ms'
            else:continue
            if label not in first and elapsed is not None:
                first.add(label);metrics[label].append(elapsed)
        transitions=summarize_transitions(events)
        for transition in transitions:
            if transition['loading_ms'] is not None:metrics['visual_loading_ms'].append(transition['loading_ms'])
            if transition['readiness_ms'] is not None:metrics['black_to_observed_scene_ms'].append(transition['readiness_ms'])
        result.append({'attempt':aid,'session':session,'version':events[0]['version'],
                       'scope':scope,'outcome':'unknown','timeline':timeline,
                       'transition_observations':transitions})
    def distribution(values):
        v=sorted(values);idx=lambda p:v[min(len(v)-1,max(0,int((len(v)-1)*p+.5)))]
        return {'n':len(v),'min':v[0],'median':statistics.median(v),'p90':idx(.9),'max':v[-1]}
    return {'attempt_count':len(result),
            'locked_attempt_count':sum(a['scope']=='locked' for a in result),
            'unlocked_segment_count':sum(a['scope']=='unlocked' for a in result),
            'unknown_scope_count':sum(a['scope']=='unknown' for a in result),
            'metrics':{k:distribution(v) for k,v in metrics.items()},
            'pointer_event_counts':dict(pointer_counts),'attempts':result}
