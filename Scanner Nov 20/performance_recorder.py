"""Passive local timing telemetry. No raw images, keyboard hooks or uploads."""
from __future__ import annotations
import collections
import datetime
import json
import os
import tempfile
from pathlib import Path
import queue
import statistics
import threading
import time
import uuid

SCHEMA=1
VERSION='24.63.4-lab6'
SAMPLE_INTERVAL=.05
DARK_THRESHOLD=.96
PATCH=16
PURCHASE_TIMEOUT=10.0 # Proposed evidence-correlation window; not a live benchmark.
GATE_HEARTBEAT=1.0
GATE_SOURCE_MAX_AGE=1.25
GATE_READY_TIMEOUT=3.0
HEALTH_INTERVAL=5.0
MAX_LINE_BYTES=65536
MAX_LOG_PART_BYTES=10*1024*1024
MAX_EXPORT_BYTES=64*1024*1024
MAX_EXPORT_ROWS=200000
WRITE_BATCH=64

class RotatingLog:
    """Single-writer append-only parts; never delete or overwrite history."""
    def __init__(self,path,limit=MAX_LOG_PART_BYTES):
        self.path=Path(path);self.limit=limit;self.part=0
        self.out=None;self.size=0
    def _open(self):
        path=self.path if self.part==0 else self.path.with_name(f'{self.path.stem}.part{self.part:04d}.jsonl')
        self.out=path.open('xb')
        self.size=0
    def __enter__(self):
        self._open();return self
    def write(self,text):
        data=text.encode('utf-8')
        if self.size and self.size+len(data)>self.limit:
            self.out.flush();os.fsync(self.out.fileno())
            self.out.close();self.part+=1;self._open()
        self.out.write(data);self.size+=len(data)
        # One flush per batch, not one per telemetry event.
        self.out.flush()
    def flush(self):
        self.out.flush()
    def fileno(self):
        return self.out.fileno()
    def __exit__(self,*exc):
        if self.out is not None:self.out.close()

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
        self._emit_lock=threading.Lock()
        self._seq=0;self._written=0
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
        # Assign sequence numbers in enqueue order, including rejected events.
        # Never perform disk I/O or wait for queue space on the producer.
        with self._emit_lock:
            if self.stop.is_set() or not self.enabled:return
            self._seq+=1;row['seq']=self._seq
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
                extra={k:timing[k] for k in (
                    'fast_path','name_cache_hits','name_cache_misses','shop_gate_ms','name_ocr_ms','queue_to_target_ms',
                    'shop_open_to_target_ms','overlay_ms','shop_open_to_overlay_ms',
                    'queue_to_overlay_ms') if k in timing}
                self._emit('inventory_timing',total_ms=timing['total_ms'],
                           row_recognition_ms=timing['row_recognition_ms'],
                           used_ocr=timing['used_ocr'],visible_rows=timing['visible_rows'],
                           geometry_fallback=bool(timing.get('geometry_fallback',False)),
                           sold_retry=bool(timing.get('sold_retry',False)),**extra)
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
        self.enabled=bool(enabled) and not self.stop.is_set()

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

    def _health(self, out, final=False):
        with self._emit_lock:
            row={'schema':SCHEMA,'version':VERSION,'session':self.session,
                 'event':'recorder_health','t':time.perf_counter(),
                 'last_seq':self._seq,'written':self._written,'dropped':self.dropped,
                 'final':final}
        out.write(json.dumps(row,separators=(',',':'),allow_nan=False)+'\n')

    def _run(self):
        detector=Transition()
        previous=None;last_focus=None;next_sample=0
        last_channel={}
        interval=SAMPLE_INTERVAL
        try:
            self.folder.mkdir(parents=True,exist_ok=True)
            if self.init_capture:self.init_capture()
            with RotatingLog(self.file) as out:
                self._health(out)
                next_health=time.perf_counter()+HEALTH_INTERVAL
                while not self.stop.is_set() or not self.events.empty():
                    batch=[]
                    for _ in range(WRITE_BATCH):
                        try:row=self.events.get_nowait()
                        except queue.Empty:break
                        if row['event']=='pointer_requested' and row.get('kind')=='channel':
                            last_channel[row['attempt']]=row['t']
                            if len(last_channel)>32:last_channel.pop(next(iter(last_channel)))
                        batch.append(json.dumps(row,separators=(',',':'),allow_nan=False)+'\n')
                    if batch:
                        out.write(''.join(batch))
                        self._written+=len(batch)
                    if time.perf_counter()>=next_health:
                        self._health(out)
                        next_health=time.perf_counter()+HEALTH_INTERVAL
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
                self._health(out,final=True)
                out.flush()
                os.fsync(out.fileno())
        except Exception as exc:
            self.error=type(exc).__name__
            with self._emit_lock:
                self.enabled=False;self.stop.set()
        finally:
            if self.release_capture:
                try:self.release_capture()
                except Exception:pass

    def close(self):
        self.end('scanner_closed')
        with self._emit_lock:self.stop.set()
        self.worker.join(timeout=.5)

    def export(self,path):
        # No raw frames or identifying seller/listing fields. Read completed lines
        # across sessions; an interrupted last line is excluded, not fabricated.
        rows,integrity=read_integrity(self.folder,failed_session=self.session if self.error else None)
        report=summarize(rows)
        cohorts=collections.defaultdict(list)
        for row in rows:cohorts[row['version']].append(row)
        report['metrics_by_recorder_version']={v:summarize(events)['metrics'] for v,events in sorted(cohorts.items())}
        if len(cohorts)>1:report['metrics']={}
        report.update({'schema':SCHEMA,'version':VERSION,'invalid_lines':integrity['invalid_lines'],
                       'integrity':integrity,'writer_alive':self.worker.is_alive(),
                       'current_session_pending_events':self.events.qsize(),
                       'current_session_dropped_events':self.dropped,'recorder_error':self.error,
                       'purchase_source_verified_current_session':self.purchase_source_verified,
                       'notes':['Times are scanner observations, not server confirmations.',
                                'Purchase outcomes require a validated visible-UI submission and receipt; current app has no qualified source. No movement keys recorded.',
                                'Unlocked observation segments are not lock attempts; no target means no inventory recognition.',
                                'Black intervals use sampled pixels and may be interrupted by focus loss.',
                                'Recent channel shortcut is an association, not proof of channel loading.',
                                'Transition observations pair black intervals with existing scene gates; entrance/room changes are visual estimates, not proof of portal movement or actual channel identity.',
                                'Current session may have queued events not yet flushed.',
                                'Only complete structurally valid segments from non-quarantined sessions enter metrics; legacy coverage remains unverified.',
                                'Log parts rotate near 10 MiB; all parts must be kept together. Export refuses histories above 64 MiB or 200000 input lines.']})
        atomic_report(path,report)

def _finite_number(value):
    return type(value) in (int,float) and 0<=value<=1e15

def _counter(value):
    return type(value) is int and 0<=value<=2**53-1

def _identifier(value):
    return isinstance(value,str) and 0<len(value)<=256

def _unique_object(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('duplicate JSON key')
        result[key]=value
    return result

def _reject_constant(value):
    raise ValueError('non-finite JSON constant')

def _valid_record(row):
    if not isinstance(row,dict) or type(row.get('schema')) is not int or row['schema']!=1:return False
    if not all(_identifier(row.get(k)) for k in ('version','session','event')) or not _finite_number(row.get('t')):return False
    event=row['event']
    if event=='recorder_health':
        return (type(row.get('final')) is bool and all(_counter(row.get(k)) for k in ('last_seq','written','dropped'))
                and row['written']+row['dropped']<=row['last_seq'])
    if not _identifier(row.get('attempt')):return False
    if 'seq' in row or row['version'].endswith(('-lab5','-lab6')):
        if not _counter(row.get('seq')) or row['seq']==0:return False
    required={'pointer_game_focus':('elapsed_ms',),'pointer_displaced':('elapsed_ms',),
              'pointer_watch_complete':('max_outside_px',),'inventory_timing':('total_ms','row_recognition_ms'),
              'black_end':('duration_ms',)}
    if event=='pointer_result' and row.get('ok') is True:required[event]=('total_ms',)
    if event in required and not all(_finite_number(row.get(k)) for k in required[event]):return False
    if event in ('pointer_game_focus','pointer_displaced','pointer_watch_complete','pointer_result'):
        if not _identifier(row.get('kind')):return False
    if event=='pointer_result' and type(row.get('ok')) is not bool:return False
    if event=='inventory_timing' and type(row.get('used_ocr')) is not bool:return False
    if event=='transition_gate_sample' and row.get('state') not in ('entrance','room_confirmed','unclassified','unavailable'):return False
    if event in ('scene_observed','inventory_observed'):
        if not _identifier(row.get('scene' if event=='scene_observed' else 'state')):return False
    if event=='black_end' and 'association' in row and not _identifier(row['association']):return False
    if event in ('purchase_attempt','purchase_outcome'):
        try:
            token=row.get('purchase_id')
            if uuid.UUID(token).version!=4 or uuid.UUID(token).hex!=token:return False
        except (ValueError,TypeError,AttributeError):return False
        if event=='purchase_attempt' and row.get('confidence')!='verified_ui':return False
        if event=='purchase_outcome':
            if row.get('outcome') not in ('confirmed','failed','canceled','unknown'):return False
            if row.get('confidence')!=('unknown' if row['outcome']=='unknown' else 'verified_ui'):return False
    return True

def read_integrity(folder,failed_session=None):
    """Read-only snapshot. Quarantine suspect sessions, never repair raw history."""
    groups=collections.defaultdict(list);health=collections.defaultdict(list)
    tainted=set();files=[];invalid=0;duplicates=0
    paths=sorted(Path(folder).glob('*.jsonl'))
    # Refuse oversized exports explicitly instead of silently omitting history.
    try:total_bytes=sum(p.stat().st_size for p in paths)
    except OSError as exc:raise ValueError('Cannot inspect all log files') from exc
    if total_bytes>MAX_EXPORT_BYTES:raise ValueError('Raw history exceeds 64 MiB export limit; use a separate copied cohort folder')
    rows_read=0;bytes_read=0
    for file in paths:
        sessions=set();bad=0;tail=0;read_error=None
        try:
            with file.open('rb') as source:
                while True:
                    raw=source.readline(MAX_LINE_BYTES+1)
                    if not raw:break
                    bytes_read+=len(raw);rows_read+=1
                    if rows_read>MAX_EXPORT_ROWS or bytes_read>MAX_EXPORT_BYTES:raise ValueError('History exceeds bounded export budget; use a separate copied cohort folder')
                    if len(raw)>MAX_LINE_BYTES:
                        while raw and not raw.endswith(b'\n'):
                            raw=source.readline(MAX_LINE_BYTES+1);bytes_read+=len(raw)
                            if bytes_read>MAX_EXPORT_BYTES:raise ValueError('History exceeds bounded export budget')
                        bad+=1;continue
                    if not raw.endswith(b'\n'):
                        tail+=1;break
                    try:
                        row=json.loads(raw,object_pairs_hook=_unique_object,parse_constant=_reject_constant)
                        if not _valid_record(row):raise ValueError('invalid event')
                        # Reject nested non-finite numbers including overflowed 1e999.
                        json.dumps(row,allow_nan=False)
                    except (ValueError,TypeError,OverflowError,RecursionError):
                        bad+=1;continue
                    sid=row['session'];sessions.add(sid)
                    (health if row['event']=='recorder_health' else groups)[sid].append(row)
        except OSError as exc:read_error=type(exc).__name__
        # A partial tail may be an active writer; completed prior records remain
        # readable, but no metrics are derived from any affected session.
        if bad or tail or read_error:tainted.update(sessions)
        invalid+=bad
        files.append({'file':file.name,'invalid_lines':bad,'partial_tail':tail,'read_error':read_error})
    if failed_session:tainted.add(failed_session)
    eligible=[];summaries=[];excluded=0;incomplete=0
    for sid in sorted(set(groups)|set(health)|tainted):
        raw=groups[sid];checks=health[sid];reasons=[]
        if sid in tainted:reasons.append('file_or_writer_error')
        by_seq={};legacy=set();clean=[];versions=set();dup=0
        for row in raw:
            versions.add(row['version'])
            canonical=json.dumps(row,sort_keys=True,separators=(',',':'),allow_nan=False)
            if 'seq' in row:
                n=row['seq']
                if n in by_seq:
                    if by_seq[n]!=canonical:reasons.append('conflicting_sequence')
                    else:dup+=1
                    continue
                by_seq[n]=canonical
            else:
                if canonical in legacy:dup+=1;continue
                legacy.add(canonical)
            clean.append(row)
        duplicates+=dup
        if len(versions)>1:reasons.append('mixed_versions')
        if legacy and (by_seq or checks):reasons.append('mixed_sequence_formats')
        if checks and versions and any(h['version'] not in versions for h in checks):reasons.append('health_version_mismatch')
        max_seq=max(by_seq,default=0)
        gap=max_seq-len(by_seq) if by_seq else 0
        finals={ (h['last_seq'],h['written'],h['dropped']) for h in checks if h['final'] }
        if len(finals)>1:reasons.append('conflicting_final_health')
        if finals:
            last,written,dropped=next(iter(finals))
            gap=max(last,max_seq)-len(by_seq)
            if last<max_seq or written!=len(by_seq) or last!=written+dropped:reasons.append('final_count_mismatch')
        else:dropped=None
        if gap:reasons.append('sequence_gap')
        if any(h['dropped']>0 for h in checks):reasons.append('reported_drops')
        segments=collections.defaultdict(list)
        for row in clean:segments[row['attempt']].append(row)
        completed=[];open_count=0;invalid_segments=0
        for events in segments.values():
            anchors=[e for e in events if e['event'] in ('lock_observed','unlocked_observed')]
            ends=[e for e in events if e['event']=='attempt_end']
            if len(anchors)!=1 or len(ends)>1:
                invalid_segments+=1;continue
            if not ends:
                open_count+=1;continue
            if ends[0]['t']<anchors[0]['t']:
                invalid_segments+=1;continue
            # Late worker events outside the segment are not valid observations.
            if any(e['t']<anchors[0]['t'] or e['t']>ends[0]['t'] for e in events):
                invalid_segments+=1;continue
            purchases={};valid=True
            for event in sorted(events,key=lambda e:(e['t'],e.get('seq',0))):
                k=event['event']
                if k not in ('purchase_attempt','purchase_outcome'):continue
                token=event['purchase_id']
                if k=='purchase_attempt':
                    if token in purchases:valid=False;break
                    purchases[token]=False
                else:
                    if token not in purchases or purchases[token]:valid=False;break
                    purchases[token]=True
            if not valid:invalid_segments+=1;continue
            completed.append(events)
        incomplete+=open_count
        if reasons:
            excluded+=len(segments);included=0
        else:
            included=len(completed)
            excluded+=open_count+invalid_segments
            for events in completed:eligible.extend(events)
        summaries.append({'session':sid,'coverage':'quarantined' if reasons else
                          'finalized' if finals else 'open_or_interrupted' if by_seq or checks else 'legacy_unverified',
                          'reasons':sorted(set(reasons)),'events_read':len(raw),'unique_events':len(clean),
                          'duplicates':dup,'sequence_gaps_lower_bound':gap if by_seq or finals else None,
                          'final_reported_drops':dropped,'segments':len(segments),'included_segments':included,
                          'open_segments':open_count,'invalid_segments':invalid_segments})
    return eligible,{'files':files,'sessions':summaries,'invalid_lines':invalid,
                     'duplicates_removed':duplicates,'excluded_segments':excluded,
                     'incomplete_segments':incomplete,'included_events':len(eligible)}

def atomic_report(path,report):
    """Same-directory temporary file; failed writes preserve the previous export."""
    path=Path(path)
    if path.suffix.lower()=='.jsonl':raise ValueError('report must not overwrite a raw log')
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=None
    try:
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=path.parent,
                                         prefix='.fm-report-',suffix='.tmp',delete=False) as out:
            temp=Path(out.name)
            json.dump(report,out,indent=2,allow_nan=False)
            out.flush();os.fsync(out.fileno())
        os.replace(temp,path)
    finally:
        if temp is not None:
            try:temp.unlink(missing_ok=True)
            except OSError:pass

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
                for field,label in (
                    ('shop_gate_ms','shop_gate_ms'),
                    ('name_ocr_ms','name_ocr_ms'),
                    ('queue_to_target_ms','queue_to_target_ms'),
                    ('shop_open_to_target_ms','shop_open_to_target_ms'),
                    ('overlay_ms','target_to_overlay_ms'),
                    ('shop_open_to_overlay_ms','shop_open_to_overlay_ms'),
                    ('queue_to_overlay_ms','queue_to_overlay_ms')):
                    if _finite_number(e.get(field)):metrics[label].append(e[field])
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
