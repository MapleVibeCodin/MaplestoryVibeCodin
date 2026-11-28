"""Offline template-based monster/player observations from local screenshot folders.
No game input. Matching is conditional on user-supplied, labeled sprite crops.
Positions relative to an optional static map landmark, otherwise screen coordinates only.
"""
import argparse
import csv
import json
import math
from pathlib import Path

def distance(a,b):
    return math.hypot(a[0]-b[0],a[1]-b[1])

def suppress(matches):
    out=[]
    for a in sorted(matches,key=lambda x:-x["score"]):
        if not any(a["kind"]==b["kind"] and distance((a["x"],a["y"]),(b["x"],b["y"])) < max(a["w"],b["w"],a["h"],b["h"])*0.55 for b in out):
            out.append(a)
    return out

def template_hits(img, tpl, kind, name, threshold, limit=200):
    import cv2
    import numpy as np
    h,w=tpl.shape[:2]
    if h<4 or w<4 or h>img.shape[0] or w>img.shape[1] or float(np.std(tpl))<3:
        return []
    scores=cv2.matchTemplate(img,tpl,cv2.TM_CCOEFF_NORMED)
    out=[]
    for _ in range(limit):
        _,score,_,(x,y)=cv2.minMaxLoc(scores)
        if not math.isfinite(score) or score<threshold: break
        out.append(dict(kind=kind,name=name,x=x+w/2,y=y+h/2,w=w,h=h,score=round(score,4)))
        scores[max(0,y-h//2):y+h//2+1,max(0,x-w//2):x+w//2+1]=-1
    return out

def nearest(a, others):
    return min((distance((a["x"],a["y"]),(b["x"],b["y"])) for b in others), default=None)

def gap_bounds(previous, first_absent, last_absent, reappearance):
    # Disappearance and reappearance happened somewhere between samples.
    if not previous<=first_absent<=last_absent<=reappearance: raise ValueError("invalid ordering")
    return [round(last_absent-first_absent,3),round(reappearance-previous,3)]

def main():
    import cv2
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("screenshots",type=Path);p.add_argument("templates",type=Path)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--threshold",type=float,default=.90)
    args=p.parse_args()
    if not .75<=args.threshold<=1: p.error("threshold must be .75–1")
    # Folder names: monster, self, player, anchor. Template basename identifies species/landmark.
    templates=[]
    for kind in ("monster","self","player","anchor"):
        for f in sorted((args.templates/kind).glob("*.png")):
            im=cv2.imread(str(f),cv2.IMREAD_COLOR)
            if im is not None: templates.append((kind,f.stem,im))
    if not any(k=="monster" for k,_,_ in templates):
        raise SystemExit("No monster templates. Supply labeled crops from the captured game images.")
    args.output.mkdir(parents=True,exist_ok=True)
    # Never overwrite a previous analysis.
    import uuid
    dest=args.output/("analysis_"+uuid.uuid4().hex[:8]);dest.mkdir()
    with (dest/"frames.jsonl").open("x",encoding="utf-8") as out:
        for f in sorted(args.screenshots.rglob("*.png")):
            im=cv2.imread(str(f),cv2.IMREAD_COLOR)
            if im is None: continue
            try: meta=json.loads(f.with_suffix(".json").read_text(encoding="utf-8"))
            except (OSError,ValueError): meta={}
            hits=suppress([hit for k,n,t in templates for hit in template_hits(im,t,k,n,args.threshold)])
            anchors=[a for a in hits if a["kind"]=="anchor"]
            anchor=anchors[0] if len(anchors)==1 else None
            players=[a for a in hits if a["kind"]=="player"]
            own=[a for a in hits if a["kind"]=="self"]
            monsters=[a for a in hits if a["kind"]=="monster"]
            for m in monsters:
                m["nearest_player_px"]=nearest(m,players)
                m["nearest_self_px"]=nearest(m,own) if len(own)==1 else None
            for a in hits:
                if anchor:
                    a["landmark_x"]=round(a["x"]-anchor["x"],2)
                    a["landmark_y"]=round(a["y"]-anchor["y"],2)
            row={"image":str(f),"metadata":meta,"anchor":anchor,"observed_monsters":len(monsters),
                 "observed_other_players":len(players) if any(k=="player" for k,_,_ in templates) else None,
                 "detections":hits}
            out.write(json.dumps(row,ensure_ascii=False)+"\n")
    print(dest/"frames.jsonl")
    print("Template observations only; missed detections, camera changes and offscreen actors prevent exact spawn claims.")

if __name__=="__main__": main()
