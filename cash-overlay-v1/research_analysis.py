"""Offline movement and farming evidence analysis; never treats track loss as a kill."""
import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path

def camera_shift(previous, current, previous_boxes=(), current_boxes=()):
    """Robust translation from masked static features. Refuse ambiguous registration."""
    import cv2
    import numpy as np
    if previous.shape != current.shape: return None
    H,W=current.shape[:2]
    def features(im,boxes):
        gray=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
        mask=np.full((H,W),255,np.uint8)
        mask[:int(H*.12),:]=0; mask[int(H*.82):,:]=0
        for x,y,w,h in boxes:
            x,y,w,h=map(int,(x,y,w,h))
            mask[max(0,y):min(H,y+h),max(0,x):min(W,x+w)]=0
        orb=cv2.ORB_create(nfeatures=1000)
        return orb.detectAndCompute(gray,mask)
    ka,da=features(previous,previous_boxes)
    kb,db=features(current,current_boxes)
    if da is None or db is None or len(da)<8 or len(db)<8: return None
    pairs=cv2.BFMatcher(cv2.NORM_HAMMING).knnMatch(da,db,k=2)
    delta=np.array([np.array(kb[m.trainIdx].pt)-ka[m.queryIdx].pt
                    for pair in pairs if len(pair)==2 for m,n in [pair] if m.distance<.72*n.distance])
    if len(delta)<8: return None
    med=np.median(delta,axis=0)
    good=np.linalg.norm(delta-med,axis=1)<=3
    if good.sum()<8 or good.mean()<.65 or abs(med[0])>W*.45 or abs(med[1])>H*.45: return None
    return tuple(float(v) for v in np.median(delta[good],axis=0))

def masks(row):
    m=row.get("metadata") or {}
    boxes=[x["box"] for x in m.get("ui",[]) if "box" in x]
    boxes += [x["box"] for x in m.get("inventory_windows",[]) if "box" in x]
    boxes += [x["box"] for x in m.get("inventory_last_known",[]) if "box" in x]
    # Protect minimap pixels even on non-rich frames. Geometry is client-relative.
    rect=m.get("rect")
    if isinstance(rect,list) and len(rect)==4:
        boxes.append([0,0,int(rect[2]*.38),int(rect[3]*.30)])
    for x in row.get("detections",[]):
        boxes.append([x["x"]-x["w"]/2-8,x["y"]-x["h"]/2-8,x["w"]+16,x["h"]+16])
    return boxes

def trusted_context(m):
    c=m.get("context")
    age=m.get("context_age_seconds")
    if not isinstance(c,dict) or not isinstance(age,(int,float)) or not 0<=age<=3 or c.get("map_uncertain"): return {}
    return c

def rate(delta,seconds):
    return round(delta*3600/seconds,2) if seconds>0 else None

def reference_for(name, refs):
    if not name: return None
    matches=[dict(v,map_id=k) for k,v in refs.get("maps",{}).items() if v["name"].casefold()==name.casefold()]
    return matches[0] if len(matches)==1 else None

def compare(ref, xp_hr=None, kills_hr=None, players=None):
    if not ref: return None
    m=ref["model"]
    # Model capacity is not observed population. Only use explicit combat population, not visible count.
    cap=None if players is None else min(m["spawn_points"],m["solo_cap"]+math.floor(max(0,players-5)*m["extra_capacity_per_combat_player_after_five"]))
    return dict(map_id=ref["map_id"],source=ref["source"],retrieved=ref["retrieved"],reference=m,
                exp_pct_realistic=None if xp_hr is None else round(100*xp_hr/m["realistic_exp_hr"],2),
                exp_pct_ceiling=None if xp_hr is None else round(100*xp_hr/m["ceiling_exp_hr"],2),
                kills_pct_realistic=None if kills_hr is None else round(100*kills_hr/m["realistic_mobs_hr"],2),
                modeled_capacity_at_known_combat_population=cap)

class TrackLinker:
    """Anonymous tracks in registered coordinates, with explicit uncertain termination."""
    def __init__(self):
        self.tracks={}; self.counter=0; self.last=None
    def end(self,reason,t):
        events=[dict(track_id=i,kind=v["kind"],species=v["species"],event="visibility_end",
                     last_seen=v["t"],observed_until=t,reason=reason,confirmed_kill=False)
                for i,v in self.tracks.items()]
        self.tracks={}; self.last=None
        return events
    def step(self,t,dets):
        events=[]; points=[]
        if self.last is not None and (t<=self.last or t-self.last>1.5):
            events+=self.end("capture_gap",t)
        self.last=t
        edges=[]
        for i,v in self.tracks.items():
            dt=t-v["t"]
            if not 0<dt<=1.5: continue
            for j,d in enumerate(dets):
                if (v["kind"],v["species"])!=(d["kind"],d["species"]): continue
                dist=math.hypot(v["x"]-d["x"],v["y"]-d["y"])
                if dist<=max(18,180*dt): edges.append((dist,i,j))
        used=set(); assigned={}
        for dist,i,j in sorted(edges):
            if i in used or j in assigned: continue
            # Do not force a link in a near-tie between same-type actors.
            if any(abs(q-dist)<8 and (ii==i or jj==j) and (ii,jj)!=(i,j)
                   for q,ii,jj in edges if ii not in used and jj not in assigned): continue
            used.add(i); assigned[j]=i
        for i,v in list(self.tracks.items()):
            if i not in used:
                events.append(dict(track_id=i,kind=v["kind"],species=v["species"],event="visibility_end",
                                   last_seen=v["t"],observed_until=t,reason="unmatched_or_occluded",confirmed_kill=False))
                del self.tracks[i]
        for j,d in enumerate(dets):
            i=assigned.get(j); speed=None
            if i is None:
                self.counter+=1; i=self.counter
                events.append(dict(track_id=i,kind=d["kind"],species=d["species"],event="visibility_start",
                                   first_seen=t,confirmed_spawn=False))
            else:
                old=self.tracks[i]; speed=math.hypot(d["x"]-old["x"],d["y"]-old["y"])/(t-old["t"])
            self.tracks[i]={**d,"t":t}
            points.append({**d,"track_id":i,"t":t,"observed_speed_px_s":None if speed is None else round(speed,3)})
        return points,events

def reviewed_combat(path):
    """Only explicit evidence-reviewed kills enter confirmed TTK. Bounds use frame brackets."""
    if path is None: return []
    rows=[]
    with Path(path).open(encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            if r.get("confirmed","").strip().lower()!="yes": continue
            a,b,c,d=[float(r[k]) for k in ("attack_lo","attack_hi","death_lo","death_hi")]
            if not all(math.isfinite(x) for x in (a,b,c,d)) or not a<=b<=c<=d: raise ValueError("Invalid combat time brackets")
            if not r.get("evidence","").strip(): raise ValueError("Reviewed kill requires evidence reference")
            rows.append(dict(map=r["map"],species=r["species"],attack_lo=a,attack_hi=b,death_lo=c,death_hi=d,
                             ttk_lower_s=round(c-b,3),ttk_upper_s=round(d-a,3),evidence=r["evidence"]))
    return rows

def track_summaries(path):
    """Aggregate only observed points; lifetime is visible duration, not age since spawn."""
    rows={}
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            p=json.loads(line); i=p["track_id"]
            if i not in rows:
                rows[i]=dict(track_id=i,map=p["map"],registration_epoch=p["epoch"],
                             kind=p["kind"],species=p["species"],first_t=p["t"],last_t=p["t"],
                             first_x=p["x"],first_y=p["y"],last_x=p["x"],last_y=p["y"],
                             first_source=p["source"],last_source=p["source"],samples=0,
                             distance_px=0.,speeds=[],self_distances=[],player_distances=[])
            s=rows[i]
            if s["samples"] and p.get("observed_speed_px_s") is not None:
                s["distance_px"]+=math.hypot(p["x"]-s["last_x"],p["y"]-s["last_y"])
                s["speeds"].append(p["observed_speed_px_s"])
            s.update(last_t=p["t"],last_x=p["x"],last_y=p["y"],last_source=p["source"],samples=s["samples"]+1)
            for key,field in [("nearest_self_px","self_distances"),("nearest_player_px","player_distances")]:
                if p.get(key) is not None: s[field].append(p[key])
    out=[]
    for s in rows.values():
        speeds=s.pop("speeds"); self_d=s.pop("self_distances"); other=s.pop("player_distances")
        out.append(dict(**s,visible_span_s=round(s["last_t"]-s["first_t"],3),
                        median_speed_px_s=statistics.median(speeds) if speeds else None,
                        nearest_self_px=min(self_d) if self_d else None,
                        nearest_other_player_px=min(other) if other else None))
    return out

def visibility_recurrences(summaries):
    # Match only nearby appearances within one registered epoch and session.
    # This is not a respawn detector. An existing monster may re-enter view.
    history=defaultdict(list)
    out=[]
    for s in sorted(summaries,key=lambda q:(str(q["map"]),q["registration_epoch"],q["first_t"])):
        if s["kind"]!="monster" or s["map"] is None: continue
        key=(s["map"],s["registration_epoch"],s["species"])
        prev=history[key]
        prev[:]=[p for p in prev if s["first_t"]-p["last_t"]<=30]
        matches=[p for p in prev if .15<=s["first_t"]-p["last_t"]<=30 and
                 math.hypot(s["first_x"]-p["last_x"],s["first_y"]-p["last_y"])<=24 and p["samples"]>=2]
        if len(matches)==1 and s["samples"]>=2:
            p=matches[0]
            out.append(dict(map=s["map"],species=s["species"],old_track=p["track_id"],new_track=s["track_id"],
                            last_visible=p["last_t"],next_visible=s["first_t"],
                            visible_gap_s=round(s["first_t"]-p["last_t"],3),
                            old_frame=p["last_source"],new_frame=s["first_source"],confirmed_respawn=False))
        prev.append(s)
    return out

def analyze(frames_path, dest, refs, review=None):
    import cv2
    dest=Path(dest)
    linker=TrackLinker()
    prev=None; prev_row=None; offset=(0.,0.); last_t=None; last_session=None
    last_map=None; epoch=0
    sections=[]; section=None; movement=defaultdict(list); occupancy=Counter()
    event_counts=Counter(); frame_count=0; aligned=0; gaps=0
    reviewed=reviewed_combat(review)
    with (dest/"actor_tracks.jsonl").open("x",encoding="utf-8") as tracks, (dest/"visibility_events.jsonl").open("x",encoding="utf-8") as ev:
        def events(items):
            for item in items:
                event_counts[item["event"]]+=1
                ev.write(json.dumps(item)+"\n")
        for line in Path(frames_path).open(encoding="utf-8"):
            row=json.loads(line); m=row.get("metadata") or {}; t=m.get("monotonic")
            if not isinstance(t,(float,int)) or not math.isfinite(t): continue
            frame_count+=1
            c=trusted_context(m); name=c.get("map")
            # Parent directory separates monotonic time domains across launches.
            session=str(Path(row["image"]).parent)
            dt=None if last_t is None else t-last_t
            contiguous=(session==last_session and name==last_map and dt is not None and 0<dt<=1.5)
            if not contiguous:
                if prev is not None: gaps+=1
                events(linker.end("map_session_or_gap",t)); prev=None; epoch+=1; offset=(0.,0.); section=None
            if name:
                key=(session,name,c.get("segment"),c.get("level"))
                if section is None or section["key"]!=key:
                    section=dict(key=key,first_t=t,last_t=t,first_exp=None,last_exp=None,first_wallet=None,last_wallet=None,first_raw=None,last_raw=None,frames=0)
                    sections.append(section)
                section["frames"]+=1; section["last_t"]=t
                # Absolute EXP within one level; never sum cumulative values across resets.
                if c.get("exp_confident") and not c.get("exp_estimated") and isinstance(c.get("exp"),int):
                    v=[t,c["exp"]]
                    if section["first_exp"] is None: section["first_exp"]=v
                    section["last_exp"]=v
                if isinstance(c.get("wallet"),int) and isinstance(c.get("wallet_age"),(int,float)) and 0<=c["wallet_age"]+(m.get("context_age_seconds") or 0)<=3:
                    v=[t,c["wallet"]]
                    if section["first_wallet"] is None: section["first_wallet"]=v
                    section["last_wallet"]=v
                if isinstance(c.get("raw_mesos"),int):
                    v=[t,c["raw_mesos"]]
                    if section["first_raw"] is None: section["first_raw"]=v
                    section["last_raw"]=v
            im=cv2.imread(row["image"],cv2.IMREAD_COLOR)
            if im is None:
                prev=None; events(linker.end("unreadable_frame",t)); last_t=t; last_session=session; last_map=name; continue
            shift=camera_shift(prev,im,masks(prev_row),masks(row)) if prev is not None else None
            if shift is None:
                if prev is not None: events(linker.end("registration_uncertain",t)); epoch+=1
                offset=(0.,0.)
            else:
                aligned+=1; offset=(offset[0]-shift[0],offset[1]-shift[1])
            detections=[]
            for d in row.get("detections",[]):
                if d["kind"] not in ("monster","self","player"): continue
                species=d["name"] if d["kind"]=="monster" else d["kind"]
                detections.append(dict(kind=d["kind"],species=species,x=d["x"]+offset[0],y=d["y"]+offset[1],
                                       screen_x=d["x"],screen_y=d["y"],score=d["score"],nearest_self_px=d.get("nearest_self_px"),
                                       nearest_player_px=d.get("nearest_player_px")))
            points,e=linker.step(t,detections); events(e)
            for p in points:
                tracks.write(json.dumps({**p,"map":name,"epoch":epoch,"source":row["image"],"registered_from_previous":shift is not None})+"\n")
                if p["observed_speed_px_s"] is not None: movement[(name,p["kind"],p["species"])].append(p["observed_speed_px_s"])
                if shift is not None and p["kind"] in ("monster","self","player"):
                    occupancy[(name,epoch,p["kind"],int(p["x"]//64),int(p["y"]//64))]+=dt
            prev=im; prev_row=row; last_t=t; last_session=session; last_map=name
        if last_t is not None: events(linker.end("end_of_capture",last_t))
    def endpoint(s,k,nonnegative=False):
        a,b=s["first_"+k],s["last_"+k]
        if a is None or b is None or b[0]<=a[0] or (nonnegative and b[1]<a[1]): return None
        return rate(b[1]-a[1],b[0]-a[0])
    summary=[]
    for s in sections:
        session,name,segment,level=s["key"]
        xp=endpoint(s,"exp",True); wallet=endpoint(s,"wallet"); raw=endpoint(s,"raw",True)
        # Scope reviewed kills to this segment's observed time range; no inferred count if none reviewed.
        kills=[k for k in reviewed if k["map"]==name and s["first_t"]<=k["attack_lo"] and k["death_hi"]<=s["last_t"]]
        # A subset of confirmed kills is a lower bound, not a complete kill count.
        kills_hr=rate(len(kills),s["last_t"]-s["first_t"]) if kills else None
        summary.append(dict(**s,map=name,exp_hr=xp,wallet_change_hr=wallet,observed_pickup_hr=raw,
                            reviewed_kills_lower_bound=len(kills) if review is not None else None,
                            reviewed_kills_lower_bound_hr=kills_hr,comparison=compare(reference_for(name,refs),xp,kills_hr)))
    with (dest/"region_occupancy.csv").open("x",encoding="utf-8",newline="") as f:
        w=csv.writer(f);w.writerow(["map","registration_epoch","kind","cell_x_64px","cell_y_64px","observed_actor_seconds"])
        for key,val in sorted(occupancy.items(),key=lambda x:str(x[0])): w.writerow([*key,round(val,3)])
    track_rows=track_summaries(dest/"actor_tracks.jsonl")
    recurrences=visibility_recurrences(track_rows)
    with (dest/"track_summary.csv").open("x",encoding="utf-8",newline="") as f:
        if track_rows:
            w=csv.DictWriter(f,fieldnames=list(track_rows[0]));w.writeheader();w.writerows(track_rows)
    (dest/"visibility_recurrence_candidates.json").write_text(json.dumps(recurrences,indent=2),encoding="utf-8")
    result=dict(frames=frame_count,registered_pairs=aligned,discontinuities=gaps,
                tracked_objects=len(track_rows),visibility_recurrence_candidates=len(recurrences),
                visibility_events=dict(event_counts),map_segments=summary,
                movement=[dict(map=k[0],kind=k[1],species=k[2],samples=len(v),median_visible_px_s=statistics.median(v)) for k,v in movement.items()],
                reviewed_combat=reviewed,limitations=["Tracks are candidates, not authoritative identities. Visibility starts/ends are not births/deaths.",
                "Pixel speeds only within camera registration epochs. No global map coordinates without calibration.",
                "EXP and wallet rates require fresh same-level/map endpoints. NPC inventory delta requires separate reconciliation.",
                "Reviewed kill throughput is a lower bound unless the review covers the complete session.",
                "A visible player count is not total map population; no inferred server spawn cap."])
    (dest/"research_summary.json").write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    return result
