"""Independent, passive notification replay. One event per delivered stack-arrival row.
Never add these totals to the upstream pickup ledger; do not infer kills from drops."""
import argparse
import csv
import hashlib
import io
import json
import os
import re
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
import cv2
import numpy as np

BATCH=48
AMOUNT=re.compile(r"^(you received exp|bonus exp for party|you have gained mesos)\s*\(\+\s*([0-9][0-9 ]*)\s*\)$",re.I)
ITEM=re.compile(r"^(.+?)\s*x\s*([0-9]+)\s+ear(?:n|r|m)?ed[.,]?\s*\((etc|use|equip|setup|cash)\)$",re.I)

def norm(s):
    return " ".join(re.sub(r"[^a-z0-9' ]"," ",s.casefold()).split())

def catalog(path):
    out={}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        tab,_,name=line.partition("\t")
        if name:out.setdefault(tab.casefold(),{}).setdefault(norm(name),[]).append(name)
    return out

def parse(text,colour,items):
    s=" ".join(str(text).strip().split()).strip(" _-")
    s=re.sub(r"^You\.have ","You have ",s,flags=re.I)
    m=AMOUNT.fullmatch(s)
    if m:
        phrase=m[1].casefold(); v=int(m[2].replace(" ",""))
        if not 0<v<=10000000:return None
        if phrase=="you have gained mesos":return ("mesos",v)
        if phrase=="bonus exp for party":return ("party_bonus_exp",v)
        if colour not in ("yellow","white"):return None
        return ("shared_exp" if colour=="yellow" else "own_exp",v)
    m=ITEM.fullmatch(s)
    if not m or colour!="white":return None
    raw,qty,tab=m[1].strip(),int(m[2]),m[3].casefold()
    if not 0<qty<=10000:return None
    names=items.get(tab,{})
    matches=names.get(norm(raw),[])
    if raw.endswith("...") and len(norm(raw))>=8:
        matches=[n for k,ns in names.items() if k.startswith(norm(raw)) for n in ns]
    if len(matches)!=1:return None
    return ("item",matches[0],qty,tab)

def row_hash(row):
    return hashlib.sha256(json.dumps(row,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def source_rows(folder):
    path=Path(folder)/"message_evidence"/"lines.jsonl"
    if not path.is_file():return []
    # The capture writer may be appending; only completed newline records are visible.
    rows=[]
    with path.open("rb") as f:
        for line in f:
            if not line.endswith(b"\n"):break
            try:rows.append(json.loads(line))
            except (ValueError,UnicodeError):rows.append({"invalid_source":True})
    return rows

def read_image(folder,row):
    n=row.get("image")
    if not isinstance(n,str) or not re.fullmatch(r"[0-9a-f]{64}\.png",n):return None
    try:
        raw=(Path(folder)/"message_evidence"/n).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=n[:-4]:return None
        im=cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_COLOR)
        if im is None or not (4<=im.shape[0]<=128 and 16<=im.shape[1]<=2048):return None
        a,b=row.get("span",(0,im.shape[1]))
        if not (0<=a<b<=im.shape[1]):return None
        return im[:,max(0,a-4):min(im.shape[1],b+4)]
    except (OSError,ValueError,TypeError):return None

def prepare(im,colour,variant):
    b,g,r=cv2.split(im)
    # Yellow letters are bright in red/green, not necessarily blue.
    v=np.minimum(g,r) if colour=="yellow" else im.min(2)
    v=cv2.resize(v,None,fx=4,fy=4,interpolation=cv2.INTER_CUBIC)
    v=(v>max(45 if variant else 50,np.percentile(v,92)*(.50 if variant else .60))).astype(np.uint8)*255
    return 255-v

def ocr_batch(entries,tess,variant):
    if not entries:return {}
    pics=[prepare(im,row.get("colour"),variant) for _,row,im in entries]
    pitch=max(x.shape[0] for x in pics)+24
    width=max(x.shape[1] for x in pics)+40
    page=np.full((pitch*len(pics),width),255,np.uint8)
    for i,p in enumerate(pics):page[i*pitch+8:i*pitch+8+p.shape[0],20:20+p.shape[1]]=p
    with tempfile.TemporaryDirectory(prefix="maple-notify-") as d:
        p=Path(d)/"batch.png"
        if not cv2.imwrite(str(p),page):raise OSError("batch image write")
        env=dict(os.environ,OMP_THREAD_LIMIT="1")
        proc=subprocess.run([str(tess),str(p),"stdout","--psm","6","tsv"],capture_output=True,text=True,
                            encoding="utf-8",errors="replace",timeout=10,env=env,
                            creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        if proc.returncode:raise RuntimeError("Tesseract batch failed")
    words={}
    for q in csv.DictReader(io.StringIO(proc.stdout),delimiter="\t"):
        if q.get("level")!="5" or not q.get("text","").strip():continue
        try:
            y=int(q["top"]);h=int(q["height"]);idx=int((y+h/2)//pitch)
            if not 0<=idx<len(entries) or y<idx*pitch or y+h>(idx+1)*pitch:continue
            words.setdefault(idx,[]).append((int(q["left"]),q["text"]))
        except (ValueError,KeyError):continue
    return {entries[i][0]:" ".join(t for _,t in sorted(v)) for i,v in words.items()}

def replay_batch(folder,rows,start,tess,items):
    batch=[(i,rows[i]) for i in range(start,min(len(rows),start+BATCH))]
    entries=[]
    for i,row in batch:
        im=read_image(folder,row)
        if im is not None:entries.append((i,row,im))
    valid={i for i,_,_ in entries}
    a=ocr_batch(entries,tess,0);b=ocr_batch(entries,tess,1)
    out=[]
    for i,row in batch:
        p=parse(a.get(i,""),row.get("colour"),items)
        q=parse(b.get(i,""),row.get("colour"),items)
        event=list(p) if p is not None and p==q else None
        out.append(dict(index=i,source_sha256=row_hash(row),born=row.get("born"),epoch=row.get("epoch"),
                        map=row.get("map"),tracking_enabled=row.get("tracking_enabled"),
                        colour=row.get("colour"),event=event,
                        status="accepted" if event else "unreadable" if i in valid else "missing_or_bad_image",
                        reads=[a.get(i,""),b.get(i,"")]))
    return out

def results(folder,rows):
    p=Path(folder)/"notification_events.jsonl"; out=[]
    if p.is_file():
        with p.open(encoding="utf-8") as f:
            for line in f:
                r=json.loads(line)
                i=len(out)
                if i>=len(rows) or r.get("index")!=i or r.get("source_sha256")!=row_hash(rows[i]):
                    raise ValueError("notification result/source mismatch")
                out.append(r)
    return out

def process(folder,tess,items,max_batches=None):
    folder=Path(folder); rows=source_rows(folder); done=results(folder,rows)
    if not tess:return len(done),len(rows)
    n=0
    while len(done)<len(rows) and (max_batches is None or n<max_batches):
        batch=replay_batch(folder,rows,len(done),tess,items)
        with (folder/"notification_events.jsonl").open("a",encoding="utf-8") as f:
            for r in batch:f.write(json.dumps(r,ensure_ascii=False,allow_nan=False)+"\n")
        done.extend(batch);n+=1
    return len(done),len(rows)

def summarize(folder):
    from cash_core import NPC
    folder=Path(folder);rows=source_rows(folder);done=results(folder,rows)
    groups={}; counts=Counter(r["status"] for r in done)
    prices={k.casefold():v for k,v in NPC.items()}
    for r in done:
        e=r.get("event")
        if not e:continue
        key=(r.get("epoch"),r.get("map"),r.get("tracking_enabled"))
        g=groups.setdefault(key,{"mesos":0,"own_exp":0,"shared_exp":0,"party_bonus_exp":0,"events":Counter(),"items":Counter()})
        g["events"][e[0]]+=1
        if e[0]=="item":g["items"][(e[1],e[3])]+=e[2]
        else:g[e[0]]+=e[1]
    output=[]
    for (epoch,map_name,active),g in groups.items():
        its=[dict(name=n,tab=t,quantity=q,npc_value=q*prices[n.casefold()] if t!="use" and n.casefold() in prices else None)
             for (n,t),q in sorted(g["items"].items())]
        output.append(dict(epoch=epoch,map=map_name,tracking_enabled=active,**{k:v for k,v in g.items() if k!="items"},
                           items=its,known_npc_value=sum(v["npc_value"] for v in its if v["npc_value"] is not None),
                           party_evidence=bool(g["events"]["shared_exp"] or g["events"]["party_bonus_exp"]),
                           personal_kills=None))
    report=dict(schema=1,raw_rows=len(rows),processed_rows=len(done),pending_rows=len(rows)-len(done),
                accepted_rows=counts["accepted"],unreadable_rows=counts["unreadable"],
                bad_image_rows=counts["missing_or_bad_image"],groups=output,
                limitations=["Delivered stack arrivals only; upstream can miss/duplicate arrivals. Two image preparations must agree.",
                             "Never add these pickup amounts to upstream totals; independent alternative reader.",
                             "EXP bar is authoritative for total EXP; notification split is incomplete.",
                             "Party evidence contradicts solo; drops/EXP lines are not confirmed personal kills.",
                             "No consumable valuation; unknown NPC prices are not zero-valued drops."])
    (folder/"notification_summary.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    with (folder/"notification_items.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f);w.writerow(["epoch","map","tracking_enabled","item","tab","quantity","known_npc_value"])
        for g in output:
            for v in g["items"]:w.writerow([g["epoch"],g["map"],g["tracking_enabled"],v["name"],v["tab"],v["quantity"],v["npc_value"]])
    return report

def worker(folder,tess,assets,stop,log_error):
    try:
        items=catalog(Path(assets)/"items.txt")
        while not stop.is_set():
            try:process(folder,tess,items,max_batches=1)
            except Exception as exc:log_error("notification replay",exc)
            stop.wait(2)
        # Bounded final batch. Remaining originals are included and replayable.
        process(folder,tess,items,max_batches=1)
    except Exception as exc:log_error("notification worker",exc)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("folder",type=Path);p.add_argument("--tesseract",required=True)
    p.add_argument("--assets",type=Path,default=Path(__file__).with_name("assets"))
    a=p.parse_args();process(a.folder,a.tesseract,catalog(a.assets/"items.txt"));print(json.dumps(summarize(a.folder),indent=2))
