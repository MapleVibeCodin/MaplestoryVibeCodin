"""Hybrid frame evidence and periodic inventory reminders, local-only."""
import hashlib
import json
import time
from pathlib import Path
import cv2
from inventory_ui import clip
from screenshots import encode_lossless, lossless_webp

def png_bytes(img):
    ok,buf=cv2.imencode('.png',img,[cv2.IMWRITE_PNG_COMPRESSION,1])
    if not ok: raise OSError('PNG encode failed')
    return buf.tobytes()

def jpeg_bytes(img):
    params=[cv2.IMWRITE_JPEG_QUALITY,65]
    if not hasattr(cv2,'IMWRITE_JPEG_SAMPLING_FACTOR_444'):
        return png_bytes(img) # do not silently switch to chroma subsampling
    params += [cv2.IMWRITE_JPEG_SAMPLING_FACTOR,cv2.IMWRITE_JPEG_SAMPLING_FACTOR_444]
    ok,buf=cv2.imencode('.jpg',img,params)
    if not ok: return png_bytes(img)
    return buf.tobytes()

def atomic_write(path,data):
    if path.exists(): return
    tmp=path.with_suffix(path.suffix+'.part')
    try:
        with tmp.open('xb') as f: f.write(data)
        tmp.replace(path)
    finally:
        if tmp.exists(): tmp.unlink()

def evidence_regions(frame,rect,reader,windows,stack_area):
    H,W=frame.shape[:2]
    # Broad fallback regions retain useful evidence even when recognition fails.
    candidates=[('minimap',(0,0,int(W*.38),int(H*.30))),('status',(0,int(H*.83),W,H-int(H*.83))),('buffs',(int(W*.55),0,W-int(W*.55),int(H*.12)))]
    # Prefer the calibrated EXP rectangle; preserve broad fallback if unknown.
    if reader.box:
        x,y,w,h=reader.box
        candidates[1]=('status',(x-8,y-8,w+16,h+16))
    if reader.gh:
        x,y,w,h=stack_area(rect,reader.gh)
        candidates.append(('messages',(x-rect[0],y-rect[1],w,h)))
    else:
        candidates.append(('messages_fallback',(int(W*.60),int(H*.45),W-int(W*.60),int(H*.38))))
    if reader.party_area:
        x,y,w,h=reader.party_area
        candidates.append(('party',(x-rect[0],y-rect[1],w,h)))
    if reader.mesos_box:
        x,y,w,h=reader.mesos_box
        candidates.append(('wallet',(x-8,y-8,w+16,h+16)))
    candidates.extend(('inventory_'+(v['page'] or v['kind']),v['box']) for v in windows)
    return [(name,box) for name,r in candidates if (box:=clip(r,frame.shape))]

def save_crops(store,frame,regions):
    directory=store.folder/'ui'
    directory.mkdir(exist_ok=True)
    rows=[]
    for name,(x,y,w,h) in regions:
        img=frame[y:y+h,x:x+w]
        # Hash raw pixels and shape; unchanged crops are reused without re-encoding.
        key=hashlib.sha256(str(img.shape).encode()+img.tobytes()).hexdigest()
        p=directory/(key+'.webp')
        fallback=directory/(key+'.png')
        if not p.exists() and fallback.exists(): p=fallback
        if not p.exists():
            if not store.has_space(): break
            data=encode_lossless(img)
            if not lossless_webp(data):p=fallback
            atomic_write(p,data)
        rows.append(dict(kind=name,box=[x,y,w,h],file='ui/'+p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    return rows

class Reminders:
    intervals={'map':180,'use':600,'etc':600,'pet':1800}
    delays={'map':20,'use':40,'etc':60,'pet':80}
    labels={'map':'Show minimap / map title','use':'Open Use tab — show potion stacks',
            'etc':'Open Etc tab — scroll through all pages','pet':'Open Equipment > Deco — show pet HP/MP pots'}
    def __init__(self,now=None):
        self.start=time.monotonic() if now is None else now
        self.seen={}
        self.last_map=None
    def observe(self,now,pages,map_name=None):
        if map_name:
            self.last_map=map_name
            self.seen['map']=now
        for page in pages:
            if page in ('use','etc','pet'): self.seen[page]=now
    def due(self,now):
        return [k for k in self.intervals if now-self.start>=self.delays[k] and
                (k not in self.seen or now-self.seen[k]>=self.intervals[k])]
    def text(self,now):
        due=self.due(now)
        if due: return self.labels[due[0]]
        return 'Evidence: '+ ' · '.join(k+(' OK' if k in self.seen else ' pending') for k in self.intervals)

def context_at(ctx, captured):
    if ctx is None or ctx['monotonic']>captured: return None,None
    return ctx, round(captured-ctx['monotonic'],3)
