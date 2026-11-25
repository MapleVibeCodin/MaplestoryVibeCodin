"""Read-only shop inventory OCR. No input injection, network, or game memory access."""
from __future__ import annotations
from collections import OrderedDict
import hashlib
import json
import os
from pathlib import Path
import queue
import re
import struct
import subprocess
import tempfile
import threading
import time
import unicodedata
import zlib
from camera_alignment import capture_client, enable_capture_cache, release_capture_cache
from vision_guard import parse_price_line, highlight_expired, revalidate_changed_hits
from vision_geometry import geometry_present, conservative_hits, WIDTH as GEOMETRY_WIDTH, HEIGHT as GEOMETRY_HEIGHT

# Native shop UI: stable colored button borders, not seller or item pixels.
GREEN = bytes((67,223,208))*24
ORANGE = bytes((92,159,255))*24
ROWS = 6
STEP = 40
SCALE = 3
CACHE_LIMIT = 64
GATE_INTERVAL = .75

def locate_shop(buffer,w,h,stride):
    """Return SELLER INFO button left highlight anchor, or None."""
    if len(buffer)!=stride*h or stride<w*3:return None
    hits=[]
    for y in range(max(0,h-52)):
        line=buffer[y*stride:y*stride+w*3]
        at=line.find(GREEN)
        while at>=0:
            # Require the beginning of a long green strip plus both orange buttons.
            if at%3==0 and at>=3 and line[at-3:at]==bytes((17,179,151)):
                x=at//3
                if x+72<w and all(buffer[(y+dy)*stride+at-3:(y+dy)*stride+at]==bytes((28,117,216)) and
                                  buffer[(y+dy)*stride+at:(y+dy)*stride+at+len(ORANGE)]==ORANGE
                                  for dy in (31,51)):
                    hits.append((x,y))
            at=line.find(GREEN,at+3)
    return hits[0] if len(hits)==1 else None

def tooltip_blocked_rows(frame):
    """Identify inventory rows with broad tooltip pixels; bridge internal icon gaps."""
    buf,w,h,stride=frame
    if w<204 or h<263 or stride<w*3 or len(buf)!=stride*h:return set(range(ROWS))
    blocked=set()
    for row in range(ROWS):
        consecutive=0
        for y in range(26+row*STEP,min(h,60+row*STEP)):
            run=0
            for x in range(40,198):
                i=y*stride+x*3
                b,g,r=buf[i:i+3]
                run=run+1 if 40<b and r<145 and g<145 and b-r>28 and b-g>23 else 0
                if run>=12:break
            consecutive=consecutive+1 if run>=12 else 0
            if consecutive>=3:
                blocked.add(row);break
    return set(range(min(blocked),max(blocked)+1)) if blocked else set()

def inventory_tooltip_visible(frame):
    return bool(tooltip_blocked_rows(frame))


def section_fingerprints(frame):
    """Hash native seller and row text, not icons or overlay edges."""
    buf,w,h,stride=frame
    if w<204 or h<263 or stride<w*3 or len(buf)!=stride*h:
        raise ValueError('Invalid inventory crop')
    def region(start,end,left,right):
        digest=hashlib.blake2b(digest_size=20)
        for y in range(start,end):
            digest.update(buf[y*stride+left*3:y*stride+right*3])
        return digest.digest()
    return ((-1,region(3,16,9,89)),)+tuple(
        (row,region(25+row*STEP,60+row*STEP,40,198)) for row in range(ROWS))

def inventory_fingerprint(frame):
    return hashlib.blake2b(b''.join(digest for _,digest in section_fingerprints(frame)),digest_size=20).digest()

class InventoryCache:
    """Bounded session-local cache of OCR results by exact visible text pixels."""
    def __init__(self,limit=CACHE_LIMIT):
        self.limit=limit
        self.entries=OrderedDict()
    def get(self,digest):
        result=self.entries.get(digest)
        if result is not None:self.entries.move_to_end(digest)
        return result
    def put(self,digest,lines,unavailable):
        self.entries[digest]=(lines,unavailable)
        self.entries.move_to_end(digest)
        while len(self.entries)>self.limit:self.entries.popitem(last=False)

def normalized(s):
    return ' '.join(unicodedata.normalize('NFKC',str(s)).casefold().split())

def displayed_buy_step(raw_text, price):
    """Only infer display precision from an explicit Buy token, never a resale value."""
    m=re.search(r'\bBuy(?:\s+at)?\s*[:=]?\s*([\d,]+(?:\.\d+)?)\s*([KMB])\b',raw_text or '',re.I)
    if not m or price is None:return 0
    number=m[1].replace(',','')
    unit={'K':1000,'M':1000000,'B':1000000000}[m[2].upper()]
    if abs(float(number)*unit-price)>0.01:return 0
    digits=len(number.partition('.')[2])
    return max(1,unit//10**digits)

def price_in_display_bucket(actual, expected, step):
    return (step>1 and actual is not None and expected is not None
            and -step<=2*(actual-expected)<step)

def pick_rows(lines, unavailable, seller, item, price, *, buy_step=0):
    """Exact normalized names and numeric displayed prices; no fuzzy guesses."""
    groups=[[] for _ in range(ROWS)]
    seller_text=[]
    for line in lines:
        text=str(line.get('text','')).strip()
        y=float(line.get('y',-100))/SCALE
        if 0<=y<22:seller_text.append(text)
        elif 28<=y<28+ROWS*STEP:
            groups[int((y-28)//STEP)].append((y,text))
    if normalized(' '.join(seller_text))!=normalized(seller):
        return [], 'Shop open · seller not verified'
    active=[];sold=[];wrong_price=[];price_unknown=[];candidates=[];truncated=[]
    target=normalized(item)
    strict='scroll' in target
    for i, group in enumerate(groups):
        base=28+i*STEP
        name=normalized(' '.join(t for y,t in group if y-base<19))
        prefix=name.rstrip('.…').strip()
        is_truncated=(name.endswith(('...','…')) and len(prefix)>=12 and target.startswith(prefix) and name!=target)
        if name!=target and not is_truncated:continue
        price_text=' '.join(t for y,t in group if y-base>=19)
        found=parse_price_line(price_text)
        compatible=found is not None and price is not None and (found==price or price_in_display_bucket(found,price,buy_step))
        if is_truncated:
            if compatible:truncated.append(i)
            continue
        if price is None or found is None:
            price_unknown.append(i)
            if unavailable[i] and not strict:candidates.append((i,'SOLD_CHECK'))
            continue
        if found!=price:
            wrong_price.append(i)
            if not strict and compatible:candidates.append((i,'SOLD_CHECK' if unavailable[i] else 'PRICE_CHECK'))
            continue
        (sold if unavailable[i] else active).append(i)
    if len(active)>1:return [], 'Multiple exact matches · no highlight'
    if active:return [(active[0],'MATCH')], 'Exact name + price · verify stats'
    if len(sold)>1:return [], 'Multiple sold matches · no highlight'
    if sold:return [(sold[0],'SOLD')], 'Target sold / unavailable'
    if len(candidates)==1 and not truncated:
        row,mode=candidates[0]
        return [(row,mode)], ('Sold candidate · price not verified' if mode=='SOLD_CHECK' else 'Rounded price candidate · verify exact price')
    if truncated:return [], 'Name truncated · verify full tooltip manually'
    if len(candidates)>1:return [], 'Multiple uncertain candidates · no highlight'
    if wrong_price:return [],'Item found · displayed price differs'
    if price_unknown:return [],'Item found · price not verified'
    return [],'Target not visible · scroll manually'


def sold_row_mask(frame, row):
    """Require pale neutral background and faded text across the native row."""
    buf,w,h,stride=frame
    y=23+row*STEP
    samples=[buf[yy*stride+194*3:yy*stride+194*3+3] for yy in range(y+4,y+36)]
    pale=sum(min(v)>=230 and max(v)-min(v)<=22 for v in samples)
    dark=sum(max(buf[j:j+3])<110 for yy in range(y+2,y+16)
             for j in range(yy*stride+41*3,yy*stride+198*3,3))
    return pale>=24 and dark<12

def selected_row_mask(frame, row):
    """Recognize the native orange selection background at the row's right edge."""
    buf,w,h,stride=frame
    y=23+row*STEP
    samples=[buf[yy*stride+194*3:yy*stride+194*3+3] for yy in range(y+4,y+36)]
    return sum(20<=b<=100 and 100<=g<=205 and r>=195 and r-g>=45 and g-b>=45
               for b,g,r in samples)>=24

def row_ink(b,g,r,cutoff,selected=False,delta=0):
    # Selected background is orange, with red ~230; its average can be <145.
    # Dark glyphs have low red. Never mistake the orange fill for glyphs.
    return r<145+delta if selected else (r+g+b)//3<cutoff

def stable_item_hits(hits,before,after):
    """Read-only, amber candidates when other rows are no longer verified."""
    if -1 not in before or before[-1]!=after.get(-1):return []
    return [(i,'ROW_CHECK' if mode=='MATCH' else mode) for i,mode in hits
            if mode in ('MATCH','PRICE_CHECK','ROW_CHECK') and i in before and before[i]==after.get(i)]

def sold_line_cutoff(frame, y, delta=0):
    """Normalize pale glyphs to black against the local light row background."""
    buf,w,h,stride=frame
    values=sorted(sum(buf[y*stride+x*3:y*stride+x*3+3])//3 for x in range(40,198))
    # Upper quartile is background even when most of the line contains glyphs.
    background=values[(len(values)*3)//4]
    return max(0,min(250,background-max(5,12-delta//3)))

def stable_sold_hits(hits, before, after):
    """Orange-only fallback when unrelated rows change during OCR."""
    if -1 not in before or before[-1]!=after.get(-1):return []
    return [(i,'SOLD_CHECK') for i,mode in hits if mode in ('SOLD','SOLD_CHECK')
            and i in before and before[i]==after.get(i)]

def prepare_ocr(frame, sections=None, *, threshold_delta=0):
    """Create contrast-normalized 3x monochrome strip, including seller and six rows."""
    buf,w,h,stride=frame
    # Capture starts at button anchor (-140,+70). Seller is on dark blue.
    out_w,out_h=162,28+ROWS*STEP
    rows=[];unavailable=[]
    selected=set(range(-1,ROWS)) if sections is None else set(sections)
    for row in range(ROWS):
        if row not in selected:
            unavailable.append(False);continue
        unavailable.append(sold_row_mask(frame,row))
    selected_rows={row for row in selected & set(range(ROWS)) if selected_row_mask(frame,row)}
    # Precompute expansion for each of the only two output pixel values.
    black=b'\x00'*SCALE;white=b'\xff'*SCALE
    for oy in range(out_h):
        line=bytearray([255])*out_w
        if -1 in selected and 3<=oy<16:
            sy=oy
            for x in range(9,89):
                i=sy*stride+x*3
                b,g,r=buf[i:i+3]
                if min(b,g,r)>175-threshold_delta:line[x-8]=0
        elif oy>=28:
            row=(oy-28)//STEP;dy=(oy-28)%STEP
            # Original list row starts 23 pixels below capture origin.
            sy=23+row*STEP+dy
            cutoff=sold_line_cutoff(frame,sy,threshold_delta) if unavailable[row] and 3<=dy<=36 else 145+threshold_delta
            if row in selected and 3<=dy<=36:
                for x in range(40,198):
                    i=sy*stride+x*3
                    b,g,r=buf[i:i+3]
                    if row_ink(b,g,r,cutoff,row in selected_rows,threshold_delta):line[x-40]=0
                # Pale sold rows may include a dark horizontal divider.
                # Remove only near-full-width rules, never ordinary glyphs.
                if line.count(0)>=120:line[:]=b'\xff'*out_w
        scaled=b''.join(white if v else black for v in line)
        rows.extend([scaled]*SCALE)
    ww,hh=out_w*SCALE,out_h*SCALE
    # Standard top-down 8-bit grayscale PNG, no BMP decoder conversion.
    return encode_gray_png(ww,hh,rows),unavailable

def encode_gray_png(width,height,rows):
    if len(rows)!=height or any(len(row)!=width for row in rows):
        raise ValueError('Invalid PNG row dimensions')
    def chunk(kind,data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    header=struct.pack('>IIBBBBB',width,height,8,0,0,0,0)
    data=zlib.compress(b''.join(b'\x00'+row for row in rows),1)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',header)+chunk(b'IDAT',data)+chunk(b'IEND',b'')

class RowOCRCache:
    """Cache OCR by exact native seller or row pixels, independent of row index."""
    def __init__(self,limit=512):
        self.limit=limit;self.entries=OrderedDict()

    @staticmethod
    def _base(section):return 0 if section==-1 else 28+section*STEP

    def recognize(self,frame,ocr,sections=None):
        sections=section_fingerprints(frame) if sections is None else sections
        keys={section:(section==-1,digest) for section,digest in sections}
        results={};missing=set()
        for section,key in keys.items():
            if key in self.entries:
                results[section]=self.entries[key];self.entries.move_to_end(key)
            else:missing.add(section)
        if missing:
            png,sold=prepare_ocr(frame,missing)
            raw=ocr.recognize(png)
            grouped={section:[] for section in missing}
            for line in raw:
                y=float(line.get('y',-100))/SCALE
                section=-1 if 0<=y<22 else int((y-28)//STEP) if 28<=y<28+ROWS*STEP else None
                if section in grouped:
                    grouped[section].append({'text':line.get('text',''),'y':float(line['y'])-self._base(section)*SCALE})
            for section in missing:
                value=(grouped[section],False if section==-1 else sold[section])
                results[section]=value
                # Do not permanently cache failed/empty text recognition.
                if value[0]:
                    self.entries[keys[section]]=value;self.entries.move_to_end(keys[section])
            while len(self.entries)>self.limit:self.entries.popitem(last=False)
        lines=[];unavailable=[]
        for section in range(-1,ROWS):
            relative,sold=results.get(section,([],False))
            lines.extend({'text':line['text'],'y':line['y']+self._base(section)*SCALE} for line in relative)
            if section>=0:unavailable.append(sold)
        return lines,unavailable,bool(missing)


class WindowsOCR:
    """Persistent Windows PowerShell / WinRT OCR worker, warmed once."""
    def __init__(self):
        self.proc=None
        self.responses=queue.Queue()
        self._process_lock=threading.Lock()
    def start(self):
        with self._process_lock:self._start()
    def _start(self):
        if self.proc and self.proc.poll() is None:return
        self.responses=queue.Queue()
        self.proc=subprocess.Popen(['powershell.exe','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass',
            '-File',str(Path(__file__).with_name('SHOP_OCR.ps1'))],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
            text=True,encoding='utf-8',errors='replace',bufsize=1,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        proc=self.proc;responses=self.responses
        def read():
            diagnostic=''
            for line in proc.stdout:
                try:responses.put(json.loads(line))
                except ValueError:
                    if line.strip():diagnostic=line.strip()[:160]
            responses.put({'ok':False,'error':diagnostic or 'Windows OCR worker exited'})
        threading.Thread(target=read,daemon=True).start()
    def recognize(self,png):
        self.start()
        with tempfile.TemporaryDirectory(prefix='fm_rush_ocr_') as tmp:
            path=Path(tmp)/'inventory.png';path.write_bytes(png)
            proc=self.proc
            if proc is None or proc.poll() is not None:raise RuntimeError('Windows OCR worker exited')
            proc.stdin.write(json.dumps(str(path))+'\n');proc.stdin.flush()
            try:res=self.responses.get(timeout=8)
            except queue.Empty:
                self.close();raise RuntimeError('Windows OCR timed out')
            if not res.get('ok'):
                # A handled recognition error does not require a worker restart.
                if proc.poll() is not None:self.close()
                raise RuntimeError(res.get('error','Windows OCR unavailable'))
            return res.get('lines',[])
    def close(self):
        with self._process_lock:
            if self.proc:
                try:self.proc.terminate()
                except OSError:pass
                self.proc=None

class ShopInventoryTracker:
    def __init__(self):
        self._lock=threading.Lock()
        self._key=None;self._latest=None;self._next=0;self._busy=False;self._generation=0
        self._digest=None;self._observed_at=None;self._ocr=WindowsOCR();self._closed=False
        # Two native 1366x768 screenshots share the same shop anchor.
        # Still verify pixels and fall back if the window/layout differs.
        self._anchors={(1366,768):(568,214)};self._gate_next={};self._cache=InventoryCache()
        self._row_cache=RowOCRCache();self._scroll_checks=OrderedDict();self._ocr_failures=0
        self._jobs=queue.Queue()
        self._worker=threading.Thread(target=self._work,daemon=True,name='FM inventory capture')
        self._worker.start()
    def _work(self):
        enable_capture_cache()
        try:
            if os.name=='nt' and not self._closed:
                try:self._ocr.start()
                except OSError:pass
            while True:
                key=self._jobs.get()
                if key is None or self._closed:return
                self._scan(key)
        finally:
            self._ocr.close();release_capture_cache()
    def reset(self):
        with self._lock:
            if self._key is not None:self._generation+=1
            self._key=None;self._latest=None;self._next=0;self._digest=None;self._observed_at=None
    def close(self):
        self._closed=True;self.reset();self._jobs.put_nowait(None);self._ocr.close()
    def get(self,hwnd,client,deal):
        identity=(hwnd,tuple(client),deal.listing_id,deal.ign,deal.item,deal.buy_mesos,displayed_buy_step(getattr(deal,'raw_text',''),deal.buy_mesos))
        now=time.monotonic()
        with self._lock:
            if self._key is None or self._key[:7]!=identity:
                self._generation+=1
                self._key=identity+(self._generation,)
                self._latest=None;self._digest=None;self._next=0;self._observed_at=None
            if highlight_expired(self._latest,self._observed_at,now):
                self._latest={'status':'Shop open · waiting for fresh verification','hits':[]}
                self._digest=None;self._observed_at=None
            if not self._closed and not self._busy and now>=self._next:
                self._busy=True;self._next=now+.05
                self._jobs.put_nowait(self._key)
            return self._latest
    def _publish(self,key,result,digest=None):
        with self._lock:
            if self._key==key:
                self._latest=result;self._digest=digest;self._observed_at=time.monotonic()
    def _find_anchor(self,client):
        """Learn one anchor per client resolution; use a tiny fixed pixel gate."""
        x,y,w,h=client
        size=(w,h)
        cached=self._anchors.get(size)
        if cached is not None:
            ax,ay=cached
            gx,gy=ax-5,ay
            if gx>=0 and gy>=0 and gx+85<=w and gy+53<=h:
                gate=capture_client((x+gx,y+gy,85,53),allow_crop=True)
                if gate and locate_shop(*gate)==(5,0):
                    return cached
            return None
        # Only search the larger centered area for initial calibration or
        # a moved shop; rate-limit when the shop is closed.
        now=time.monotonic()
        if now<self._gate_next.get(size,0):return None
        self._gate_next[size]=now+GATE_INTERVAL
        gx=max(0,w//2-260);gy=max(0,h//2-280)
        gw=min(w-gx,520);gh=min(h-gy,360)
        gate=capture_client((x+gx,y+gy,gw,gh),allow_crop=True)
        anchor=locate_shop(*gate) if gate else None
        if anchor is None:return None
        result=(gx+anchor[0],gy+anchor[1])
        self._anchors[size]=result
        return result

    def _find_geometry_anchor(self,client):
        """Use only an existing calibrated anchor; never learn from tolerance."""
        x,y,w,h=client
        anchor=getattr(self,'_anchors',{}).get((w,h))
        if anchor is None:return None
        ax,ay=anchor
        left,top=ax-140,ay-1
        if left<0 or top<0 or left+GEOMETRY_WIDTH>w or top+GEOMETRY_HEIGHT>h:return None
        frame=capture_client((x+left,y+top,GEOMETRY_WIDTH,GEOMETRY_HEIGHT),allow_crop=True)
        return anchor if geometry_present(frame) else None

    def _scan(self,key):
        started=time.perf_counter()
        try:
            with self._lock:
                if self._key!=key:return
            _,client,_,seller,item,price,buy_step,_=key
            x,y,w,h=client
            anchor=self._find_anchor(client)
            geometry=anchor is None
            if geometry:anchor=self._find_geometry_anchor(client)
            if anchor is None:
                self._publish(key,None);return
            strict='scroll' in normalized(item)
            if geometry and strict:
                self._publish(key,{'status':'Shop geometry detected · waiting for exact scroll gate','hits':[]});return
            ax,ay=anchor
            left,top=ax-140,ay+70
            if left<0 or top<0 or left+204>w or top+263>h:
                self._publish(key,{'status':'Shop open · inventory clipped','hits':[]});return
            with self._lock:
                existing=self._latest if self._key==key else None
                prev_digest=self._digest if self._key==key else None
            if existing is None:self._publish(key,{'status':'Shop open · verifying visible rows','hits':[]})
            frame=capture_client((x+left,y+top,204,263),allow_crop=True)
            if not frame:
                self._publish(key,{'status':'Shop open · capture retry','hits':[]});return
            blocked=tooltip_blocked_rows(frame)
            sections=tuple((section,fp) for section,fp in section_fingerprints(frame) if section not in blocked)
            digest=(left,top,sections,geometry)
            if digest==prev_digest:
                self._publish(key,existing,digest);return
            # Hide stale hits immediately unless seller and matched row pixels
            # are identical and the match is still unobstructed.
            verified=dict(sections)
            prior=dict(prev_digest[2]) if prev_digest else {}
            held=[]
            if existing and prev_digest and prev_digest[:2]==digest[:2]:
                prior_hits=[((box[1]-top-23)//STEP,mode) for mode,box in existing['hits']]
                for row,mode in revalidate_changed_hits(prior_hits,prior,verified,strict):
                    held.append((mode,(left+1,top+23+row*STEP,left+200,top+23+(row+1)*STEP-2)))
            self._publish(key,{'status':'Shop open · verifying visible rows','hits':held},None)
            with self._lock:
                if self._key!=key:return
            ocr_started=time.perf_counter()
            lines,unavailable,used_ocr=self._row_cache.recognize(frame,self._ocr,sections)
            ocr_ms=(time.perf_counter()-ocr_started)*1000
            with self._lock:
                if self._key!=key:return
            self._ocr_failures=0
            hits,status=pick_rows(lines,unavailable,seller,item,price,buy_step=buy_step)
            if hits and 'scroll' in normalized(item):
                # Independently render the seller and candidate row(s) using
                # a second contrast cutoff. Never use a prefix or fuzzy name.
                selected={-1}|{row for row,_ in hits}
                check_key=(seller,item,price,tuple((i,v) for i,v in sections if i in selected),tuple(hits))
                checked=self._scroll_checks.get(check_key)
                if checked is None:
                    with self._lock:
                        if self._key!=key:return
                    alt,alt_sold=prepare_ocr(frame,selected,threshold_delta=15)
                    alt_hits,_=pick_rows(self._ocr.recognize(alt),alt_sold,seller,item,price)
                    checked=alt_hits==hits
                    if checked:
                        self._scroll_checks[check_key]=True
                        while len(self._scroll_checks)>512:self._scroll_checks.popitem(last=False)
                if not checked:hits=[];status='Scroll text not independently confirmed'
            confirmed=self._find_anchor(client)
            if confirmed!=anchor:
                if not geometry or confirmed is not None or self._find_geometry_anchor(client)!=anchor:
                    self._publish(key,None);return
            frame_after=capture_client((x+left,y+top,204,263),allow_crop=True)
            if not frame_after:
                self._publish(key,{'status':'Shop open · capture retry','hits':[]});return
            after_blocked=tooltip_blocked_rows(frame_after)
            after=tuple((section,fp) for section,fp in section_fingerprints(frame_after) if section not in after_blocked)
            before_map=dict(sections);after_map=dict(after)
            # Even a newly hidden unrelated row changes the evidence set.
            # A single unchanged non-scroll candidate may survive in amber/orange;
            # never carry a green match or a strict scroll across changed evidence.
            if after!=sections:
                hits=revalidate_changed_hits(hits,before_map,after_map,'scroll' in normalized(item))
                if not hits:
                    self._publish(key,{'status':'Shop open · visible rows changed, retrying','hits':[]});return
                status=('Sold candidate · other rows changed' if hits[0][1]=='SOLD_CHECK'
                        else 'Row verified · other rows changing; check price/stats')
                # Force a new recognition; do not cache partial evidence as complete.
                digest=None
            if blocked and not hits and status=='Target not visible · scroll manually':
                status='Tooltip covers rows · no unverified highlight'
            if geometry:
                hits=conservative_hits(hits,strict)
                status=('Geometry candidate · verify seller, item and price' if hits
                        else 'Shop geometry detected · '+status)
            hits=[(mode,(left+1,top+23+i*STEP,left+200,top+23+(i+1)*STEP-2)) for i,mode in hits]
            self._publish(key,{'status':status,'hits':hits,
                              'timing':{'scan_id':started,'total_ms':round((time.perf_counter()-started)*1000,2),
                                        'row_recognition_ms':round(ocr_ms,2),'used_ocr':bool(used_ocr),
                                        'visible_rows':sum(i>=0 for i,_ in sections),'geometry_fallback':geometry}},digest)
        except Exception as exc:
            # A malformed capture/worker response must not kill the capture thread.
            # Report the error class without copying raw OCR or private text.
            self._publish(key,{'status':'Shop OCR unavailable · '+type(exc).__name__,'hits':[]})
            self._ocr_failures+=1
            with self._lock:
                if self._key==key:self._next=time.monotonic()+min(15.0,2.0**min(4,self._ocr_failures-1))
        finally:
            with self._lock:self._busy=False
