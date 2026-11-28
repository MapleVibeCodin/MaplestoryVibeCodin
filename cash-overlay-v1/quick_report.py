"""Map-independent quick report. Never confuse capture time with combat time."""
import json
import hashlib
import math
import statistics
from collections import Counter
from pathlib import Path

# Pinned Javipen EXP_TABLE, 1a25186943a42fccd89eec2e0777c7b41ea5a21f.
EXP_TABLE = [15,34,57,92,135,372,560,840,1242,1716,2360,3216,4200,5460,7050,8840,11040,13716,16680,20216,24402,28980,34320,40512,47216,54900,63666,73080,83720,95700,108480,122760,138666,155540,174216,194832,216600,240500,266682,294216,324240,356916,391160,428280,468450,510420,555680,604416,655200,709716,748608,789631,832902,878545,926689,977471,1031036,1087536,1147132,1209994,1276301,1346242,1420016,1497832,1579913,1666492,1757815,1854143,1955750,2062925,2175973,2295216,2420993,2553663,2693603,2841212,2996910,3161140,3334370,3517093,3709829,3913127,4127566,4353756,4592341,4844001,5109452,5389449,5684790,11938059,25069923,52646838,110558359,232172553,487562361,1023880958,2150150011,4515315023,9482161548]

def absolute_exp(level,exp):
    if type(level) is not int or type(exp) is not int or not 1<=level<=len(EXP_TABLE) or not 0<=exp<EXP_TABLE[level-1]:return None
    return sum(EXP_TABLE[:level-1])+exp

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
    minute_bins=Counter(); last_key=None; runs=[]; run=None; levelups=0; endpoints={}
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
        absolute=absolute_exp(c["level"],c["exp"])
        if absolute is None:previous=None;run=None;last_gain=None;continue
        ep=endpoints.setdefault(key[0],dict(first_t=at,first_absolute=absolute,first_level=key[1],first_exp=c["exp"]))
        ep.update(last_t=at,last_absolute=absolute,last_level=key[1],last_exp=c["exp"])
        cur=(at,absolute,key,name,c.get("party") if c.get("party_confirmed") else None)
        if previous is not None:
            a,old,k,oldmap,oldparty=previous
            if at==a:continue
            dt=at-a
            if k[0]==key[0] and key[1] in (k[1],k[1]+1) and 0<dt<=3:
                d=absolute-old
                if key[1]==k[1]+1 and d>=0:
                    levelups+=1;run=None
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
    endpoint_rows=[dict(epoch=k,**v,net_exp=v["last_absolute"]-v["first_absolute"],elapsed_s=v["last_t"]-v["first_t"],net_exp_hr=rate(v["last_absolute"]-v["first_absolute"],v["last_t"]-v["first_t"])) for k,v in endpoints.items()]
    return dict(schema=2,frame_count=len(frames),levelups_observed=levelups,endpoint_progression=endpoint_rows,capture_elapsed_s=round(span,3),observed_capture_s=round(covered,3),
        gap_count=len(gaps),largest_gap_s=max(gaps,default=0),map_frame_counts=dict(map_counts),
        exp_observed_delta=exp_delta if exp_seconds else None,exp_observed_s=round(exp_seconds,3),
        exp_observed_hr=rate(exp_delta,exp_seconds),exp_positive_changes=positive,exp_negative_changes=negative,
        exp_per_minute_observed=dict(sorted(minute_bins.items())),exp_runs=runs,
        median_exp_event_gap_s=statistics.median(gain_gaps) if gain_gaps else None,
        wallet_start=w[0][1] if w else None,wallet_end=w[-1][1] if w else None,
        wallet_observation_count=len(w),wallet_first_t=w[0][0] if w else None,wallet_last_t=w[-1][0] if w else None,wallet_endpoint_seconds=ws,wallet_change=wd,wallet_change_hr=rate(wd,ws),
        conditional_monster_counts=dict(counts),unresolved_exp=unresolved,
        limitations=["Capture time and EXP-covered time are not attack-active time.",
        "Wallet change includes any spending/transfers; endpoint rate is not raw pickups.",
        "Monster counts conditional on fresh same-map confirmed solo and unmodified EXP; not verified kills.",
        "Unknown map does not discard EXP or wallet evidence; no map-specific attribution.",
        "No consumable meso valuation. Adjacent observed level-ups included; resets and gaps excluded from interval rates. Endpoint net progression spans gaps and can include deaths."])

def report_folder(folder,output=None,refs=None):
    folder=Path(folder); rows=[]
    from evidence_journal import read_journal
    records,errors=read_journal(folder/"evidence_journal.jsonl")
    frames=[r for r in records if r["kind"]=="frame"]
    missing_pixels=0; intentionally_unsaved=0; bad_sidecars=0; bad_pixels=0; verified=0
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
                if r.get("image_retained") is False:
                    if image.exists() or m.get("image_retained") is not False or r.get("image_sha256") is not None:
                        bad_pixels+=1;continue
                    intentionally_unsaved+=1
                elif image.exists():
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
    result.update(metadata_verified=verified,missing_image_bytes=missing_pixels,intentionally_unsaved_images=intentionally_unsaved,
                  invalid_sidecars=bad_sidecars,invalid_images=bad_pixels,journal_errors=errors,
                  evidence_mode="indexed_metadata" if frames and not errors else "legacy_unverified",
                  visual_coverage_note="Missing images cannot be independently verified or used for movement; verified sidecars still support statistical analysis.")
    if frames and not errors and (bad_sidecars or bad_pixels):
        result["limitations"].append("Invalid frame evidence excluded; rates may be incomplete.")
    target=Path(output) if output else folder/"quick_report.json"
    target.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    return result
