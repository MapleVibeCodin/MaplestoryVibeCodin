"""Capture-free performance recording; disk writes only on the worker."""
import json
import queue
import time
import statistics
from pathlib import Path
from collections import Counter, defaultdict


def writer_loop(recorder, rotating_log, batch_size=64):
    """Use the pinned recorder's queue/health protocol, without sampling pixels."""
    try:
        recorder.folder.mkdir(parents=True, exist_ok=True)
        with rotating_log(recorder.file) as out:
            recorder._health(out)
            next_health = time.perf_counter() + 5
            while not recorder.stop.is_set() or not recorder.events.empty():
                batch = []
                try:
                    batch.append(recorder.events.get(timeout=.2 if not recorder.stop.is_set() else 0))
                except queue.Empty:
                    pass
                for _ in range(batch_size - len(batch)):
                    try:
                        batch.append(recorder.events.get_nowait())
                    except queue.Empty:
                        break
                if batch:
                    out.write(''.join(json.dumps(row, separators=(',', ':'), allow_nan=False) + '\n' for row in batch))
                    recorder._written += len(batch)
                if time.perf_counter() >= next_health:
                    recorder._health(out)
                    next_health = time.perf_counter() + 5
            recorder._health(out, final=True)
    except Exception as exc:
        recorder.error = type(exc).__name__
        recorder.enabled = False
        recorder.stop.set()


class NoScreenshots:
    """Keep the base UI contract; never start a capture or writer thread."""
    def __init__(self, folder, **kwargs):
        self.folder = Path(folder)
        self.enabled = False
        self.saved = 0
        self.error = 'Disabled for low-overhead test'
    def observe(self, *args):
        pass
    def set_enabled(self, enabled):
        self.enabled = False
    def close(self):
        pass


def stats(values):
    values = sorted(v for v in values if type(v) in (float, int) and 0 <= v < 1e10)
    if not values:
        return {'n': 0}
    import math
    return {'n': len(values), 'p50': round(statistics.median(values), 2),
            'p95': round(values[math.ceil(.95*len(values))-1], 2), 'max': round(values[-1], 2)}


def build_report(events, *, writer_error=None, dropped=0, writer_alive=False):
    groups = defaultdict(list)
    for e in events:
        if e.get('attempt'):
            groups[e['attempt']].append(e)
    timing = [e for e in events if e.get('event') == 'inventory_timing']
    metrics = {k: stats([e.get(k) for e in timing]) for k in (
        'total_ms', 'row_recognition_ms', 'name_ocr_ms', 'shop_gate_ms', 'overlay_ms',
        'shop_open_to_overlay_ms', 'queue_to_overlay_ms')}
    runs = []
    for aid, rows in groups.items():
        rows.sort(key=lambda e: e.get('t', 0))
        start = next((e for e in rows if e.get('event') == 'lock_observed'), None)
        if start is None:
            continue
        t0 = start['t']
        phases = [e for e in rows if e.get('event') == 'beast_phase']
        first_flow = next((e for e in phases if e.get('stage') == 'item_ready'), None)
        first = next((e for e in rows if e.get('event') == 'inventory_observed' and e.get('state') in ('candidate','unique_match')), None)
        end = next((e for e in reversed(rows) if e.get('event') == 'attempt_end'), None)
        spans = defaultdict(float)
        for a, b in zip(phases, phases[1:]):
            spans[a.get('stage', 'unknown')] += max(0, b['t']-a['t'])
        if end and phases:
            spans[phases[-1].get('stage', 'unknown')] += max(0, end['t']-phases[-1]['t'])
        runs.append({'attempt': aid, 'cc': start.get('cc'), 'fm': start.get('fm'),
            'first_candidate_ms': round(max(0,first['t']-t0)*1000, 2) if first else None,
            'first_flow_item_ready_ms': round(max(0,first_flow['t']-t0)*1000, 2) if first_flow else None,
            'phase_ms': {k: round(v*1000, 2) for k,v in spans.items()},
            'gate_states': dict(Counter(e.get('state','unknown') for e in rows if e.get('event')=='scanner_gate')),
            'inventory_states': dict(Counter(e.get('state','unknown') for e in rows if e.get('event')=='inventory_observed')),
            'channel_failures': sum(e.get('event')=='beast_channel_failed' for e in rows),
            'ended': end is not None, 'purchase_outcome': 'unknown'})
    handoffs = [e for e in events if e.get('event')=='beast_pointer_handoff']
    health = [e for e in events if e.get('event')=='recorder_health']
    final = bool(health and health[-1].get('final'))
    requests=[e for e in events if e.get('event')=='beast_pointer_request']
    outcomes=[e for e in events if e.get('event')=='beast_pointer_outcome']
    ids={e.get('request_id') for e in outcomes}
    return {'schema': 'ultimate-beast-trial-2', 'engine': 'runescape', 'build': 'Smooth Shortcuts Stable', 'extra_capture': True,
        'camera_capture': 'passive grass landmarks; local session title crops and shop screenshots',
        'pointer_audit': {'requests':len(requests),'outcomes':len(outcomes),
                          'unmatched':sum(e.get('request_id') not in ids for e in requests),
                          'reasons':dict(Counter(e.get('reason','unknown') for e in outcomes)),
                          'move_ms':stats([e.get('total_ms') for e in outcomes if e.get('ok') is True])},
        'writer_error': writer_error, 'dropped': dropped, 'writer_alive': writer_alive,
        'final_health': final, 'events': len(events), 'locked_attempts': len(runs),
        'session_observed_seconds': round(max(e['t'] for e in events)-min(e['t'] for e in events),2) if events else 0,
        'phase_metrics_ms': {k: stats([r['phase_ms'].get(k) for r in runs]) for k in sorted({k for r in runs for k in r['phase_ms']})},
        'gate_state_changes': dict(Counter(e.get('state','unknown') for e in events if e.get('event')=='scanner_gate')),
        'inventory_state_changes': dict(Counter(e.get('state','unknown') for e in events if e.get('event')=='inventory_observed')),
        'pointer_handoffs': {'count':len(handoffs),'succeeded':sum(e.get('ok') is True for e in handoffs),
                             'reasons':dict(Counter(e.get('reason','unknown') for e in handoffs)),
                             'total_ms':stats([e.get('total_ms') for e in handoffs])},
        'candidate_attempts': sum(r['first_candidate_ms'] is not None for r in runs),
        'first_candidate_ms': stats([r['first_candidate_ms'] for r in runs]),
        'inventory_metrics': metrics, 'ocr_scans': sum(bool(e.get('used_ocr')) for e in timing),
        'name_cache_hits': sum(e.get('name_cache_hits',0) or 0 for e in timing),
        'name_cache_misses': sum(e.get('name_cache_misses',0) or 0 for e in timing),
        'runs': runs, 'raw_events': events,
        'limitations': ['Candidate is not independently verified correctness or purchase.',
          'Times begin at observed lock, not external alert delivery; phases use existing detector observations.',
          'Phase durations include human waits and focus gaps; only transitions observed by scanner are recorded.',
          'No extra screen capture; missed visual evidence cannot be reconstructed from timing alone.',
          'Missing final health, drops or writer error indicate incomplete evidence.'],
        'user_feedback': {'wrong_highlights': '', 'missed_items': '', 'purchase_results': '', 'other': ''}}


def finish_report(recorder):
    rows = []
    invalid = 0
    for p in sorted(recorder.folder.glob(recorder.file.stem+'*.jsonl')):
        with p.open(encoding='utf-8') as f:
            for line in f:
                try:
                    rows.append(json.loads(line))
                except (ValueError, TypeError):
                    invalid += 1
    report = build_report(rows, writer_error=recorder.error, dropped=recorder.dropped,
                          writer_alive=recorder.worker.is_alive())
    report['invalid_lines'] = invalid
    dest = recorder.folder.parent/'feedback'/('Trial-'+recorder.file.stem+'.json')
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open('x',encoding='utf-8') as f:
        json.dump(report,f,indent=2,allow_nan=False)
    return dest
