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

def section_fingerprints(frame):
    """Seller and six native row hashes; identical rows can be reused after scrolling."""
    """Hash only native seller/name/price pixels, not icons/chat/overlay edges.
    This inexpensive check happens before any scaling, binarization or OCR.
    """
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

def pick_rows(lines, unavailable, seller, item, price):
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
    active=[];sold=[];wrong_price=[];price_unknown=[]
    for i, group in enumerate(groups):
        base=28+i*STEP
        name=normalized(' '.join(t for y,t in group if y-base<19))
        if name!=normalized(item):continue
        price_text=' '.join(t for y,t in group if y-base>=19)
        m=re.search(r'\bfor\s+([\d,]+)\s*mesos\b',price_text,re.I)
        found=int(m.group(1).replace(',','')) if m else None
        if price is None or found is None:price_unknown.append(i);continue
        if found!=price:wrong_price.append(i);continue
        (sold if unavailable[i] else active).append(i)
    if active:
        mode='MATCH' if len(active)==1 else 'AMBIGUOUS'
        return [(i,mode) for i in active], ('Name + price match · verify stats' if len(active)==1 else 'Multiple name/price matches · verify stats')
    if sold:return [(i,'SOLD') for i in sold], 'Target sold / unavailable'
    if wrong_price:return [],'Item found · displayed price differs'
    if price_unknown:return [],'Item found · price not verified'
    return [],'Target not visible · scroll manually'

def prepare_ocr(frame, sections=None):
    """Create contrast-normalized 3x monochrome strip, including seller and six rows."""
    buf,w,h,stride=frame
    # Capture starts at button anchor (-140,+70). Seller is on dark blue.
    out_w,out_h=162,28+ROWS*STEP
    rows=[];unavailable=[]
    selected=set(range(-1,ROWS)) if sections is None else set(sections)
    for row in range(ROWS):
        if row not in selected:
            unavailable.append(False);continue
        y=23+row*STEP
        # Gray sold rows have pale background and no dark text. Require both.
        sample=buf[(y+2)*stride+194*3:(y+2)*stride+194*3+3]
        dark=sum(max(buf[j:j+3])<110 for yy in range(y+2,y+16)
                 for j in range(yy*stride+41*3,yy*stride+198*3,3))
        unavailable.append(bool(len(sample)==3 and min(sample)>=230 and dark<12))
    # Precompute expansion for each of the only two output pixel values.
    black=b'\x00'*SCALE;white=b'\xff'*SCALE
    for oy in range(out_h):
        line=bytearray([255])*out_w
        if -1 in selected and 3<=oy<16:
            sy=oy
            for x in range(9,89):
                i=sy*stride+x*3
                b,g,r=buf[i:i+3]
                if min(b,g,r)>175:line[x-8]=0
        elif oy>=28:
            row=(oy-28)//STEP;dy=(oy-28)%STEP
            # Original list row starts 23 pixels below capture origin.
            sy=23+row*STEP+dy
            cutoff=225 if unavailable[row] else 145
            if row in selected and 3<=dy<=36:
                for x in range(40,198):
                    i=sy*stride+x*3
                    b,g,r=buf[i:i+3]
                    if (r+g+b)//3<cutoff:line[x-40]=0
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

    def recognize(self,frame,ocr):
        sections=section_fingerprints(frame)
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
            relative,sold=results[section]
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
        self._key=None;self._latest=None;self._next=0;self._busy=False
        self._digest=None;self._ocr=WindowsOCR();self._closed=False
        # Two native 1366x768 screenshots share the same shop anchor.
        # Still verify pixels and fall back if the window/layout differs.
        self._anchors={(1366,768):(568,214)};self._gate_next={};self._cache=InventoryCache()
        self._row_cache=RowOCRCache();self._ocr_failures=0
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
            self._key=None;self._latest=None;self._next=0;self._digest=None
    def close(self):
        self._closed=True;self.reset();self._jobs.put_nowait(None);self._ocr.close()
    def get(self,hwnd,client,deal):
        key=(hwnd,tuple(client),deal.listing_id,deal.ign,deal.item,deal.buy_mesos)
        now=time.monotonic()
        with self._lock:
            if self._key!=key:
                self._key=key;self._latest=None;self._digest=None;self._next=0
            if not self._closed and not self._busy and now>=self._next:
                self._busy=True;self._next=now+.10
                self._jobs.put_nowait(key)
            return self._latest
    def _publish(self,key,result,digest=None):
        with self._lock:
            if self._key==key:
                self._latest=result;self._digest=digest
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

    def _scan(self,key):
        try:
            _,client,_,seller,item,price=key
            x,y,w,h=client
            anchor=self._find_anchor(client)
            if anchor is None:
                self._publish(key,None);return
            ax,ay=anchor
            left,top=ax-140,ay+70
            if left<0 or top<0 or left+204>w or top+263>h:
                self._publish(key,{'status':'Shop open · inventory clipped','hits':[]});return
            with self._lock:
                existing=self._latest if self._key==key else None
                prev_digest=self._digest if self._key==key else None
            if existing is None:
                # Let Tk hide old room/channel markers before capturing the rows.
                self._publish(key,{'status':'Shop open · reading inventory','hits':[]});return
            frame=capture_client((x+left,y+top,204,263),allow_crop=True)
            if not frame:return
            pixels=inventory_fingerprint(frame)
            digest=(pixels,left,top)
            if digest==prev_digest:return
            cached=self._cache.get(pixels)
            if cached is None:
                self._publish(key,{'status':'Shop open · reading inventory','hits':[]})
                lines,unavailable,used_ocr=self._row_cache.recognize(frame,self._ocr)
                self._ocr_failures=0
                # Cache the original recognized pixels, even if the shop
                # subsequently changes. Reuse only when those pixels recur.
                self._cache.put(pixels,lines,unavailable)
                if self._find_anchor(client)!=anchor:
                    self._publish(key,None);return
                frame_after=capture_client((x+left,y+top,204,263),allow_crop=True)
                if not frame_after:
                    self._publish(key,{'status':'Shop open · capture retry','hits':[]});return
                if inventory_fingerprint(frame_after)!=pixels:
                    self._publish(key,{'status':'Shop open · rows changed, retrying','hits':[]});return
            else:
                lines,unavailable=cached
            hits,status=pick_rows(lines,unavailable,seller,item,price)
            # Coordinates relative to game client. Outline, never click.
            hits=[(mode,(left+1,top+23+i*STEP,left+200,top+23+(i+1)*STEP-2)) for i,mode in hits]
            self._publish(key,{'status':status,'hits':hits},digest)
        except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as exc:
            self._publish(key,{'status':'Shop OCR unavailable · '+str(exc)[:100],'hits':[]})
            self._ocr_failures+=1
            with self._lock:
                if self._key==key:self._next=time.monotonic()+min(15.0,2.0**min(4,self._ocr_failures-1))
        finally:
            with self._lock:self._busy=False
