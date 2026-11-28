"""Independent local evidence journal; no game input, network or remote upload."""
import hashlib
import bisect
import csv
import json
import math
import statistics
import time
import threading
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

def canonical(record):
    return json.dumps(record,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode("utf-8")

class Journal:
    def __init__(self,path):
        self.path=Path(path)
        self.previous=None
        self.sequence=0
        self.lock=threading.Lock()
    def append(self,kind,at,**fields):
        with self.lock:
            return self._append(kind,at,**fields)
    def _append(self,kind,at,**fields):
        if {"kind","monotonic","utc","sequence","previous_sha256","sha256"} & fields.keys():
            raise ValueError("reserved journal field")
        record=dict(kind=kind,monotonic=at,utc=datetime.now(timezone.utc).isoformat(),
                    sequence=self.sequence+1,previous_sha256=self.previous,**fields)
        digest=hashlib.sha256(canonical(record)).hexdigest()
        with self.path.open("a",encoding="utf-8") as f:
            f.write(json.dumps(dict(record,sha256=digest),ensure_ascii=False,allow_nan=False)+"\n")
            f.flush()
        self.sequence+=1
        self.previous=digest
        return digest

def read_journal(path):
    records=[]; errors=[]; previous=None
    if not Path(path).is_file(): return records,["journal_missing"]
    with Path(path).open(encoding="utf-8") as f:
        for i,line in enumerate(f,1):
            try:
                record=json.loads(line); digest=record.pop("sha256")
                legacy=False
                if digest!=hashlib.sha256(canonical(record)).hexdigest():
                    # Only the demonstrated v2.1 collision is recoverable. Original bytes stay unchanged.
                    if record.get("kind")!="minimap_file" or record.get("file")!="minimap_observations.jsonl" or "file_sha256" in record:
                        raise ValueError("digest mismatch")
                    mini=Path(path).parent/"minimap_observations.jsonl"
                    try:payload=hashlib.sha256(mini.read_bytes()).hexdigest()
                    except OSError:raise ValueError("legacy minimap bytes unavailable")
                    if digest!=hashlib.sha256(canonical(dict(record,sha256=payload))).hexdigest():
                        raise ValueError("legacy digest mismatch")
                    record["file_sha256"]=payload;legacy=True
                if record["sequence"]!=i or record["previous_sha256"]!=previous: raise ValueError("chain mismatch")
                if type(record["monotonic"]) not in (int,float) or not math.isfinite(record["monotonic"]): raise ValueError("invalid clock")
                previous=digest; records.append(dict(record,sha256=digest,**({"legacy_minimap_recovered":True} if legacy else {})))
            except (ValueError,KeyError,TypeError) as e:
                errors.append(f"line {i}: {e}")
                break
    return records,errors

def scope(c):
    c=c or {}
    if not c.get("active") or c.get("map_uncertain") or not c.get("map") or not c.get("segment"): return None
    return dict(map=c["map"],segment=c["segment"],level=c.get("level"),job=c.get("job"),
                party=c.get("party") if c.get("party_confirmed") is True else None)

def trusted_scope(c,at,max_age=2):
    if not c or type(c.get("monotonic")) not in (float,int) or not 0<=at-c["monotonic"]<=max_age: return None
    return scope(c)

def classify_messages(lines):
    """Each visual line is an observation, not an independent confirmed kill."""
    out=[]
    for line in lines:
        kind=getattr(line,"kind",None); amount=getattr(line,"amount",None)
        if kind in ("exp","bonus","mesos") and type(amount) is int and amount>0:
            out.append(dict(kind=kind,amount=amount,born=getattr(line,"born",None)))
    return out

def potion_delta(before,after):
    # A decrease is net inventory change, not necessarily gross consumption.
    return [dict(item_id=k,before=before[k],after=after[k],net_decrease=before[k]-after[k])
            for k in sorted(before.keys() & after.keys()) if before[k]!=after[k]]

def verified_frame(session,record):
    # Hashes establish matching bytes, not authenticity before local capture.
    name=record.get("file")
    if not isinstance(name,str) or Path(name).name!=name: return False
    p=Path(session)/name
    try:
        if hashlib.sha256(p.read_bytes()).hexdigest()!=record.get("image_sha256"): return False
        expected=record.get("sidecar_sha256")
        return expected is None or hashlib.sha256(p.with_suffix('.json').read_bytes()).hexdigest()==expected
    except OSError: return False

def summarize(records):
    groups={}
    for r in records:
        c=r.get("scope")
        if not isinstance(c,dict) or not c.get("map"): continue
        key=tuple(c.get(k) for k in ("map","segment","level","job","party"))
        g=groups.setdefault(key,dict(normal_exp_lines=0,normal_exp_total=0,party_bonus_lines=0,
                party_bonus_total=0,observed_pickup_mesos=0,meso_lines=0,items=Counter(),
                potion_net_decrease=Counter(),potion_observations=0))
        if r["kind"]=="visual_messages":
            for line in r.get("lines",[]):
                if line["kind"]=="exp":
                    g["normal_exp_lines"]+=1;g["normal_exp_total"]+=line["amount"]
                elif line["kind"]=="bonus":
                    g["party_bonus_lines"]+=1;g["party_bonus_total"]+=line["amount"]
        if r["kind"]=="accepted_pickups":
            for p in r.get("messages",[]):
                if len(p)==2 and p[0]=="mesos" and type(p[1]) is int and p[1]>0:
                    g["observed_pickup_mesos"]+=p[1];g["meso_lines"]+=1
                elif len(p)==4 and p[0]=="item" and type(p[2]) is int and p[2]>0:
                    g["items"][(str(p[3]),str(p[1]))]+=p[2]
        if r["kind"]=="potion_counts":
            g["potion_observations"]+=1
            for d in r.get("changes",[]):g["potion_net_decrease"][str(d["item_id"])]+=d["net_decrease"]
    result=[]
    for k,g in groups.items():
        items=[dict(tab=t,item=n,quantity=q) for (t,n),q in sorted(g.pop("items").items())]
        g["potion_net_decrease"]=dict(g["potion_net_decrease"])
        if not g["meso_lines"]:g["observed_pickup_mesos"]=None
        result.append(dict(zip(("map","segment","level","job","party"),k),**g,items=items,
            confirmed_kills=None,normal_exp_line_count_is_kill_count=False))
    return result

def interval_metrics(records,intervals,prices):
    """Align each event to one recorded active interval, never use wall time as active time."""
    keys=("map","segment","level","job","party")
    groups=defaultdict(list)
    for x in intervals:
        groups[tuple(x.get(k) for k in keys)].append((x["start"],x["end"]))
    starts={}
    for key,spans in groups.items():
        spans.sort()
        starts[key]=[a for a,b in spans]
    accepted=[]
    for r in records:
        c=r.get("scope")
        if not isinstance(c,dict): continue
        key=tuple(c.get(k) for k in keys); t=r["monotonic"]
        if key not in groups: continue
        i=bisect.bisect_left(starts[key],t)-1
        if i>=0 and groups[key][i][0]<t<=groups[key][i][1]: accepted.append(r)
    result=[]
    for row in summarize(accepted):
        key=tuple(row.get(k) for k in keys)
        seconds=sum(b-a for a,b in groups[key])
        npc=0; unknown=0; priced=0
        for item in row["items"]:
            if item["tab"].casefold() in ("use","cash"): continue
            price=prices.get(item["item"].casefold())
            if type(price) is int and price>=0: npc+=price*item["quantity"];priced+=item["quantity"]
            else: unknown+=item["quantity"]
        raw=row["observed_pickup_mesos"]
        row.update(active_observed_seconds=seconds,known_npc_value=npc if priced else None,
            unknown_nonconsumable_units=unknown,priced_nonconsumable_units=priced,
            observed_pickup_hr=round(raw*3600/seconds,2) if raw is not None and seconds>=60 else None,
            raw_plus_known_npc_hr=round((raw+npc)*3600/seconds,2) if raw is not None and seconds>=60 else None,
            normal_exp_lines_hr=round(row["normal_exp_lines"]*3600/seconds,2) if row["normal_exp_lines"] and seconds>=60 else None,
            rate_note="Observed message pickups within recorded active intervals; undercount possible. No potion valuation.")
        result.append(row)
    return result

def audit_session(session,dest):
    session=Path(session); dest=Path(dest)
    records,errors=read_journal(session/"evidence_journal.jsonl")
    frames=[r for r in records if r["kind"]=="frame"]
    missing_pixels=[]; intentionally_unsaved=[]; mismatched=[]
    for r in frames:
        name=r.get('file')
        if not isinstance(name,str) or Path(name).name!=name:
            mismatched.append(name); continue
        p=session/name
        if not p.is_file():
            try:
                if hashlib.sha256(p.with_suffix('.json').read_bytes()).hexdigest()!=r.get('sidecar_sha256'):
                    mismatched.append(name); continue
                if r.get('image_retained') is False and r.get('image_sha256') is None:
                    if json.loads(p.with_suffix('.json').read_bytes()).get('image_retained') is not False:
                        mismatched.append(name);continue
                    intentionally_unsaved.append(name)
                else:missing_pixels.append(name)
            except (OSError,ValueError,AttributeError): mismatched.append(name)
        elif not verified_frame(session,r): mismatched.append(name)
    known={r.get("file") for r in frames}
    orphan=[p.name for p in session.iterdir() if p.suffix.lower() in (".jpg",".png",".webp") and p.name not in known]
    gaps=[]; frame_intervals=[]
    for a,b in zip(frames,frames[1:]):
        dt=b["monotonic"]-a["monotonic"]
        if dt<=0 or dt>1.5:gaps.append(dict(previous=a.get("file"),next=b.get("file"),seconds=dt))
        else:frame_intervals.append(dt)
    intervals_path=dest/"active_intervals.jsonl"
    from cash_core import NPC
    with intervals_path.open(encoding="utf-8") as f:
        intervals=[r for line in f for r in [json.loads(line)] if Path(r["session"]).resolve()==session.resolve()]
    metrics=interval_metrics(records,intervals,{k.casefold():v for k,v in NPC.items()}) if not errors and not mismatched and not orphan and not missing_pixels and not intentionally_unsaved else []
    report=dict(journal_records=len(records),journal_errors=errors,frame_count=len(frames),
        clean_close=bool(records and records[-1]["kind"]=="close"),active_message_metrics=metrics,
        frame_hash_mismatch=mismatched,unavailable_images=missing_pixels,intentionally_unsaved_images=intentionally_unsaved,unindexed_frames=orphan,capture_gaps=gaps,
        active_metrics_withheld_for_sampled_images=bool(missing_pixels or intentionally_unsaved),
        median_frame_gap_s=statistics.median(frame_intervals) if frame_intervals else None,
        cohorts=summarize(records),limitations=["Hashes detect changes to recorded bytes; not proof of original authenticity or trusted time.",
        "Missing journal records, OCR or missed pickups are unknown, not zero. Hash chains cannot detect a deleted tail without an independent checkpoint.",
        "Normal EXP lines can include party-shared EXP; no confirmed kill counts.",
        "Potion changes are net observed counts, not gross consumption; no meso equivalents."])
    (dest/"journal_audit.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    return report
