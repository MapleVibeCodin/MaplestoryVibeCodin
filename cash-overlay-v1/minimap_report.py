"""Conservative spatial EXP attribution from timestamped minimap observations."""
import json
import hashlib
import math
import bisect
from collections import defaultdict
from pathlib import Path
from quick_report import absolute_exp,rate

def scope(r):
    if not r.get('map') or r.get('status')!='candidate' or not r.get('box') or r.get('normalized_xy') is None:return None
    return (r['map'],r.get('epoch'),r.get('segment'),r.get('level'),tuple(r['box']),tuple(r.get('rect',[])))

def labels(r):
    x,y=r['normalized_xy']
    zone=('left','middle','right')[min(2,max(0,int(x*3)))]
    band=('upper','middle','lower')[min(2,max(0,int(y*3)))]
    red=r.get('red_xy')
    distance=r.get('nearest_red_px')
    prox='unknown' if red is None else 'no_red_visible' if not red else 'near' if distance is not None and distance<=18 else 'far' if distance is not None else 'unknown'
    return zone,band,prox

def summarize(rows):
    rows=sorted(rows,key=lambda r:r['monotonic'])
    times=[r['monotonic'] for r in rows]; maps=defaultdict(lambda:dict(samples=0,valid_seconds=0.,movement_px=0.,stationary_seconds=0.,red_visible_seconds=0.,zones={},bands={},proximity={},matched_exp=0,unassigned_exp=0))
    def add(g,key,label,seconds,xp):
        b=g[key].setdefault(label,dict(seconds=0.,exp=0,intervals=0))
        b['seconds']+=seconds;b['exp']+=xp;b['intervals']+=1
    for r in rows:
        if scope(r):maps[r['map']]['samples']+=1
    for a,b in zip(rows,rows[1:]):
        s=scope(a);dt=b['monotonic']-a['monotonic']
        if s is None or s!=scope(b) or not 0<dt<=.35:continue
        g=maps[a['map']];d=math.dist(a['self_xy'],b['self_xy'])
        g['valid_seconds']+=dt;g['movement_px']+=d
        if d<=1:g['stationary_seconds']+=dt
        if a.get('red_xy'):g['red_visible_seconds']+=dt
    # One event per OCR observation; only homogeneous categories across the interval qualify.
    previous=None
    for r in rows:
        s=scope(r);at=r.get('context_at');xp=absolute_exp(r.get('level'),r.get('exp'))
        if not s or not isinstance(at,(int,float)) or xp is None:
            previous=None;continue
        if previous and previous[0]==at:continue
        if previous:
            old,oldxp,olds=previous;dt=at-old
            if s==olds and 0<dt<=3 and xp>=oldxp:
                delta=xp-oldxp;g=maps[r['map']]
                i=bisect.bisect_left(times,old);j=bisect.bisect_right(times,at)
                sample=rows[i:j]
                if sample and sample[0]['monotonic']-old<=.35 and at-sample[-1]['monotonic']<=.35 and all(scope(v)==s for v in sample) and all(0<v['monotonic']-u['monotonic']<=.35 for u,v in zip(sample,sample[1:])):
                    ls=[labels(v) for v in sample]
                    g['matched_exp']+=delta
                    for k,key in enumerate(('zones','bands','proximity')):
                        values={v[k] for v in ls}
                        if len(values)==1 and 'unknown' not in values:add(g,key,next(iter(values)),dt,delta)
                        else:add(g,key,'mixed_or_unknown',dt,delta)
                else:g['unassigned_exp']+=delta
        previous=(at,xp,s)
    for g in maps.values():
        for k in ('zones','bands','proximity'):
            for b in g[k].values():b['exp_hr']=rate(b['exp'],b['seconds'])
    return dict(schema=1,observations=len(rows),maps=dict(maps),
                limits=['Marker candidates, not independently verified player identities or platforms.',
                        'No red visible is not proof of empty map. Near uses 18 minimap pixels, not game distance.',
                        'EXP attribution uses OCR timestamps, not exact kill location. Same-category intervals only; mixed/unknown separate.',
                        'Rates require 60s per category; association is not a causal player competition penalty.'])

def report_minimap(folder):
    from evidence_journal import read_journal
    folder=Path(folder);p=folder/'minimap_observations.jsonl'
    records,errors=read_journal(folder/'evidence_journal.jsonl')
    hashes=[r for r in records if r.get('kind')=='minimap_file' and r.get('file')==p.name]
    if errors or not hashes or not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=hashes[-1].get('file_sha256'):
        result=dict(error='Minimap evidence missing or unverified; rates withheld.')
    else:
        result=summarize([json.loads(line) for line in p.read_text(encoding='utf-8').splitlines() if line.strip()])
    (folder/'minimap_report.json').write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
    return result
