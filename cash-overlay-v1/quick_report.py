"""Map-independent quick report. Never confuse capture time with combat time."""
import json
import hashlib
import math
import statistics
from collections import Counter
from pathlib import Path

def number(x):
    return type(x) in (int,float) and math.isfinite(x)

def rate(value,seconds):
    return round(value*3600/seconds,2) if value is not None and seconds>=60 else None

def solutions(delta, monsters, cap=12):
    """Unique unmodified EXP decomposition, or None for ambiguous/impossible."""
    if type(delta) is not int or delta<=0 or not monsters or len(monsters)>8: return None
    if any(type(m.get("exp")) is not int or m["exp"]<=0 for m in monsters): return None
    found=[]
    def visit(i,left,budget,counts):
        if len(found)>1:return
        if i==len(monsters):
            if left==0:found.append(counts)
            return
        xp=monsters[i]["exp"]
        for n in range(min(budget,left//xp)+1):
            visit(i+1,left-n*xp,budget-n,counts+[n])
    visit(0,delta,cap,[])
    if len(found)!=1:return None
    return {m["name"]:n for m,n in zip(monsters,found[0]) if n}

def summarize(rows,refs=None):
    refs=refs or {}
    maps={v["name"].casefold():v for v in refs.get("maps",{}).values()}
    frames=sorted((r for r in rows if number(r.get("monotonic"))),key=lambda r:r["monotonic"])
    gaps=[]; covered=0.; prior_frame=None; previous=None; wallet={}; counts=Counter(); map_counts=Counter()
    exp_seconds=0.; exp_delta=0; positive=0; negative=0; unresolved=0; last_gain=None; gain_gaps=[]
    minute_bins=Counter(); last_key=None; runs=[]; run=None
    for m in frames:
        t=m["monotonic"]; c=m.get("context") or {}; at=c.get("monotonic")
        contiguous=prior_frame is not None and 0<t-prior_frame<=1.5
        if contiguous:covered+=t-prior_frame
        elif prior_frame is not None:gaps.append(round(t-prior_frame,3))
        prior_frame=t
        if not contiguous:previous=None;last_gain=None;run=None
        if not number(at) or not 0<=t-at<=3:previous=None;continue
        name=c.get("map") if not c.get("map_uncertain") else None
        map_counts[name or "UNKNOWN"]+=1
        if type(c.get("wallet")) is int and c["wallet"]>=0 and number(c.get("wallet_observed_at")):
            w=c["wallet_observed_at"]
            if 0<=t-w<=3:wallet[w]=c["wallet"]
        if not c.get("exp_confident") or c.get("exp_estimated") or type(c.get("exp")) is not int or type(c.get("level")) is not int:continue
        key=(c.get("recording_epoch"),c["level"])
        cur=(at,c["exp"],key,name,c.get("party") if c.get("party_confirmed") else None)
        if previous is not None:
            a,old,k,oldmap,oldparty=previous
            if at==a:continue
            dt=at-a
            if k==key and 0<dt<=3:
                d=c["exp"]-old
                if d>=0:
                    exp_delta+=d;exp_seconds+=dt
                    if run is None:
                        run=dict(start=a,end=at,level=key[1],exp_delta=0);runs.append(run)
                    run["end"]=at;run["exp_delta"]+=d
                    if d:
                        positive+=1;minute_bins[int((at-frames[0]["monotonic"])//60)]+=d
                        if last_gain is not None:gain_gaps.append(at-last_gain)
                        last_gain=at
                        ref=maps.get(str(name).casefold()) if name and name==oldmap and cur[4]==oldparty==1 else None
                        result=solutions(d,ref["monsters"]) if ref else None
                        if result:counts.update(result)
                        else:unresolved+=d
                else:negative+=1;run=None;last_gain=None
            else:run=None;last_gain=None
        previous=cur
    w=sorted(wallet.items()); span=frames[-1]["monotonic"]-frames[0]["monotonic"] if len(frames)>1 else 0
    wd=w[-1][1]-w[0][1] if len(w)>1 else None; ws=w[-1][0]-w[0][0] if len(w)>1 else 0
    return dict(schema=1,frame_count=len(frames),capture_elapsed_s=round(span,3),observed_capture_s=round(covered,3),
        gap_count=len(gaps),largest_gap_s=max(gaps,default=0),map_frame_counts=dict(map_counts),
        exp_observed_delta=exp_delta if exp_seconds else None,exp_observed_s=round(exp_seconds,3),
        exp_observed_hr=rate(exp_delta,exp_seconds),exp_positive_changes=positive,exp_negative_changes=negative,
        exp_per_minute_observed=dict(sorted(minute_bins.items())),exp_runs=runs,
        median_exp_event_gap_s=statistics.median(gain_gaps) if gain_gaps else None,
        wallet_start=w[0][1] if w else None,wallet_end=w[-1][1] if w else None,
        wallet_observation_count=len(w),wallet_endpoint_seconds=ws,wallet_change=wd,wallet_change_hr=rate(wd,ws),
        conditional_monster_counts=dict(counts),unresolved_exp=unresolved,
        limitations=["Capture time and EXP-covered time are not attack-active time.",
        "Wallet change includes any spending/transfers; endpoint rate is not raw pickups.",
        "Monster counts conditional on fresh same-map confirmed solo and unmodified EXP; not verified kills.",
        "Unknown map does not discard EXP or wallet evidence; no map-specific attribution.",
        "No consumable meso valuation. Level-up/reset gaps excluded."])

def report_folder(folder,output=None,refs=None):
    folder=Path(folder); rows=[]
    from evidence_journal import read_journal
    records,errors=read_journal(folder/"evidence_journal.jsonl")
    frames=[r for r in records if r["kind"]=="frame"]
    missing_pixels=0; bad_sidecars=0; bad_pixels=0; verified=0
    if frames and not errors:
        for r in frames:
            name=r.get("file")
            if not isinstance(name,str) or Path(name).name!=name:
                bad_sidecars+=1;continue
            image=folder/name; side=image.with_suffix(".json")
            try:
                raw=side.read_bytes()
                if hashlib.sha256(raw).hexdigest()!=r.get("sidecar_sha256"):
                    bad_sidecars+=1;continue
                m=json.loads(raw)
                if m.get("image")!=name or m.get("monotonic")!=r.get("monotonic"):
                    bad_sidecars+=1;continue
                if image.exists():
                    if hashlib.sha256(image.read_bytes()).hexdigest()!=r.get("image_sha256"):
                        bad_pixels+=1;continue
                else:missing_pixels+=1
                rows.append(m);verified+=1
            except (OSError,ValueError):bad_sidecars+=1
    else:
        for p in folder.glob("*.json"):
            if not any(p.with_suffix(ext).is_file() for ext in (".png",".jpg",".jpeg",".webp")):continue
            try:rows.append(json.loads(p.read_text(encoding="utf-8")))
            except (OSError,ValueError):continue
    result=summarize(rows,refs)
    result.update(metadata_verified=verified,missing_image_bytes=missing_pixels,
                  invalid_sidecars=bad_sidecars,invalid_images=bad_pixels,journal_errors=errors,
                  evidence_mode="indexed_metadata" if frames and not errors else "legacy_unverified",
                  visual_coverage_note="Missing images cannot be independently verified or used for movement; verified sidecars still support statistical analysis.")
    if frames and not errors and (bad_sidecars or bad_pixels):
        result["limitations"].append("Invalid frame evidence excluded; rates may be incomplete.")
    target=Path(output) if output else folder/"quick_report.json"
    target.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    return result
