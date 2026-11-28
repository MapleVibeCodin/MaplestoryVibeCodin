"""Observed farming coverage and comparable cohorts, local-only."""
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

def finite(x):
    return type(x) in (float,int) and math.isfinite(x)

def context(row):
    m=row.get("metadata") or {}
    c=m.get("context")
    t=m.get("monotonic")
    if not isinstance(c,dict) or not finite(t): return None
    at=c.get("monotonic")
    if not finite(at) or not 0<=t-at<=3 or c.get("map_uncertain") or not c.get("map"): return None
    return c

def identity(c):
    return tuple(c.get(k) for k in ("map","segment","level","job","party"))

def active_intervals(rows):
    previous=None
    last_frame=None
    session=None
    for row in rows:
        m=row.get("metadata") or {}
        t=m.get("monotonic")
        folder=str(Path(row["image"]).parent)
        c=context(row)
        if folder!=session or not finite(t) or (last_frame is not None and not 0<t-last_frame<=1.5):
            previous=None
        session=folder
        last_frame=t if finite(t) else None
        if c is None or c.get("active") is not True:
            previous=None
            continue
        if previous is not None:
            old=previous
            dt=c["monotonic"]-old["monotonic"]
            if dt==0 and identity(c)==identity(old): continue
            if identity(c)==identity(old) and 0<dt<=1.5:
                out=dict(zip(("map","segment","level","job","party"),identity(c)),
                         session=folder,start=old["monotonic"],end=c["monotonic"],seconds=dt)
                for field,key in (("exp","exp_delta"),("raw_mesos","pickup_delta")):
                    a,b=old.get(field),c.get(field)
                    good=type(a) is int and type(b) is int and b>=a
                    if field=="exp":
                        good=good and all(x.get("exp_confident") and not x.get("exp_estimated") for x in (old,c))
                    out[key]=b-a if good else None
                yield out
        previous=c

def summarize(intervals):
    groups={}
    keys=("session","map","segment","level","job","party")
    for r in intervals:
        key=tuple(r[k] for k in keys)
        g=groups.setdefault(key,{"active_seconds":0.,"exp_delta":0,"exp_seconds":0.,"pickup_delta":0,"pickup_seconds":0.})
        g["active_seconds"]+=r["seconds"]
        for field in ("exp","pickup"):
            if r[field+"_delta"] is not None:
                g[field+"_delta"]+=r[field+"_delta"]
                g[field+"_seconds"]+=r["seconds"]
    out=[]
    for key,g in groups.items():
        x=dict(zip(keys,key),**g)
        for field in ("exp","pickup"):
            s=g[field+"_seconds"]
            x[field+"_hr"]=round(3600*g[field+"_delta"]/s,2) if s>=60 else None
            if not s: x[field+"_delta"]=None
            x[field+"_coverage"]=round(s/g["active_seconds"],4)
        out.append(x)
    return out

def compare(row,archive):
    if type(row.get("level")) is not int or type(row.get("party")) is not int or row["party"]<1: return None
    if str(row.get("job","")).casefold()!="assassin" or not 30<=row["level"]<=50: return None
    mode="solo" if row["party"]==1 else "party"
    matches=[v for q in archive.get("results",[]) if q["level"]==row["level"] and q["party"]==mode
             for v in q["rows"] if v[0].casefold()==row["map"].casefold()]
    if len(matches)!=1: return None
    v=matches[0]
    return dict(source=archive.get("source"),retrieved=archive.get("retrieved"),mode=mode,
                levels=v[7],wallet_hr=v[1],exp_hr=v[2],players=v[3],runs=v[4],hours=v[5],
                local_exp_pct=None if row["exp_hr"] is None or not v[2] else round(100*row["exp_hr"]/v[2],2),
                note="Public wallet rate is not raw pickups; sample counts are EXP contributors.")

def build_report(frames,dest,public_path=None):
    dest=Path(dest)
    intervals=[]
    inventory=[]
    gaps=[]
    coverage=Counter()
    populations=defaultdict(Counter)
    last=None; prior_folder=None; prior_sequence=None
    def rows():
        nonlocal last,prior_folder,prior_sequence
        with Path(frames).open(encoding="utf-8") as f:
            for line in f:
                row=json.loads(line); m=row.get("metadata") or {}; t=m.get("monotonic"); c=context(row)
                folder=str(Path(row["image"]).parent)
                if folder!=prior_folder: last=None; prior_sequence=None
                if finite(t) and finite(last) and t-last>1.5:
                    gaps.append(dict(session=folder,start=last,end=t,seconds=round(t-last,3)))
                seq=m.get("sequence")
                if type(seq) is int and type(prior_sequence) is int and seq>prior_sequence+1:
                    coverage["missing_sequence_ids"]+=seq-prior_sequence-1
                prior_sequence=seq; prior_folder=folder; last=t
                coverage["frames"]+=1
                coverage["image_bytes"]+=m.get("image_bytes") or 0
                coverage["map_trusted_frames"]+=int(c is not None)
                coverage["active_frames"]+=int(c is not None and c.get("active") is True)
                if c:
                    for key in ("exp","wallet_read","party_observed"):
                        coverage[key+"_present_frames"]+=int(c.get(key) is not None)
                    n=row.get("observed_other_players")
                    if type(n) is int: populations[(c["map"],c.get("party"))][n]+=1
                for crop in m.get("ui",[]):
                    if crop.get("kind","").startswith("inventory_"):
                        inventory.append(dict(session=folder,map=c.get("map") if c else None,monotonic=t,
                            utc=m.get("utc"),page=crop["kind"],frame=row["image"],crop=crop.get("file"),
                            box=crop.get("box"),complete_inventory_verified=False))
                yield row
    with (dest/"active_intervals.jsonl").open("x",encoding="utf-8") as f:
        for r in active_intervals(rows()):
            intervals.append(r);f.write(json.dumps(r)+"\n")
    cohorts=summarize(intervals)
    archive=json.loads(Path(public_path).read_text(encoding="utf-8")) if public_path and Path(public_path).is_file() else {}
    for r in cohorts: r["public_comparison"]=compare(r,archive)
    with (dest/"inventory_evidence_index.jsonl").open("x",encoding="utf-8") as f:
        for r in inventory: f.write(json.dumps(r)+"\n")
    with (dest/"inventory_review_template.csv").open("x",encoding="utf-8",newline="") as f:
        csv.writer(f).writerow(["session","map","monotonic","item","category","quantity","complete_stack_coverage","evidence"])
    result=dict(schema=1,coverage=dict(coverage),capture_gaps=gaps,active_cohorts=cohorts,
        inventory_snapshots=len(inventory),inventory_pages=dict(Counter(r["page"] for r in inventory)),
        visible_player_frame_counts=[dict(map=k[0],party_size=k[1],counts=dict(v)) for k,v in populations.items()],
        policy="Consumable usage counts only, no meso equivalents.",
        limitations=["Tracker-active is not attack-active. Rates require 60 seconds of valid field coverage.",
        "Pickup OCR can miss events. Party count may be cached. Visible players are template candidates.",
        "Inventory index is raw panel evidence, not automatic item counts.",
        "Exact kills, spawn pressure and offscreen actors require further calibration and review."])
    (dest/"evidence_report.json").write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    return result
