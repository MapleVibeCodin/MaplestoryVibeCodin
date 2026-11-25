"""Local lossless player-shop screenshots, independent of the selected deal."""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
import os
import queue
import struct
import threading
import time
import uuid
import zlib

from camera_alignment import capture_client, enable_capture_cache, release_capture_cache
from game_window import window_has_focus, window_client_rect
from shop_inventory import locate_shop
from vision_geometry import geometry_present, WIDTH as GW, HEIGHT as GH


def crop(frame, x, y, w, h):
    if not frame:
        return None
    buf, fw, fh, stride = frame
    if (w <= 0 or h <= 0 or x < 0 or y < 0 or x+w > fw or y+h > fh
            or stride < fw*3 or len(buf) != stride*fh):
        return None
    return (b''.join(buf[i*stride+x*3:i*stride+(x+w)*3]
                     for i in range(y, y+h)), w, h, w*3)


def gate_quality(frame, anchor):
    ax, ay = anchor
    tiny = crop(frame, ax-5, ay, 85, 53)
    if tiny and locate_shop(*tiny) == (5, 0):
        return 'exact'
    geom = crop(frame, ax-140, ay-1, GW, GH)
    return 'geometry' if geom and geometry_present(geom) else None


class ShopOpenState:
    """Require two observed absent gates to rearm; capture failure is not absence."""
    def __init__(self):
        self.saved = False
        self.misses = 0

    def observe(self, present):
        if present is None:
            return False
        if present:
            self.misses = 0
            return not self.saved
        self.misses += 1
        if self.misses >= 2:
            self.saved = False
        return False

    def mark_saved(self):
        self.saved = True


def encode_png(frame):
    """Preserve native BGR pixels as RGB PNG, ignoring DWORD padding."""
    buf, w, h, stride = frame
    if w <= 0 or h <= 0 or stride < w*3 or len(buf) != stride*h:
        raise ValueError('Invalid screenshot frame')
    rows = []
    for y in range(h):
        src = buf[y*stride:y*stride+w*3]
        rgb = bytearray(w*3)
        rgb[0::3] = src[2::3]
        rgb[1::3] = src[1::3]
        rgb[2::3] = src[0::3]
        rows.append(b'\x00'+rgb)
    def chunk(kind, data):
        return (struct.pack('>I', len(data))+kind+data
                +struct.pack('>I', zlib.crc32(kind+data)&0xffffffff))
    return (b'\x89PNG\r\n\x1a\n'
            +chunk(b'IHDR', struct.pack('>IIBBBBB', w,h,8,2,0,0,0))
            +chunk(b'IDAT', zlib.compress(b''.join(rows), 3))
            +chunk(b'IEND', b''))


def save_png(folder, frame, stamp, quality):
    folder = Path(folder)/stamp.strftime('%Y-%m-%d')
    folder.mkdir(parents=True, exist_ok=True)
    name = stamp.strftime('%H-%M-%S-%f')+'_'+quality+'_'+uuid.uuid4().hex[:8]+'.png'
    path = folder/name
    temp = path.with_suffix('.part')
    try:
        temp.write_bytes(encode_png(frame))
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()
    return path


class ShopScreenshotRecorder:
    """Small gate polls; one full native client capture per observed opening."""
    def __init__(self, folder, *, capture=capture_client, focused=window_has_focus,
                 geometry=window_client_rect):
        self.folder = Path(folder)
        self.capture, self.focused, self.geometry = capture, focused, geometry
        self.enabled = True
        self.saved = 0
        self.error = None
        self._request = None
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._capture_done = threading.Event()
        self._pending = queue.Queue(maxsize=16)
        self._anchors = {(1366,768):(568,214)}
        self._search_at = {}
        self._states = {}
        self._worker = threading.Thread(target=self._work, daemon=True, name='FM shop screenshot gate')
        self._writer = threading.Thread(target=self._write, daemon=True, name='FM shop PNG writer')
        self._writer.start()
        self._worker.start()

    def observe(self, hwnd, client):
        with self._lock:
            self._request = (hwnd, tuple(client)) if hwnd and client else None

    def set_enabled(self, enabled):
        with self._lock:
            self.enabled = bool(enabled)

    def _valid(self, hwnd, client):
        with self._lock:
            active = self.enabled and self._request == (hwnd, client)
        return active and self.focused(hwnd) and self.geometry(hwnd) == client

    def _gate(self, client):
        x,y,w,h = client
        size = (w,h)
        anchor = self._anchors.get(size)
        if anchor is not None:
            ax,ay = anchor
            tiny = self.capture((x+ax-5,y+ay,85,53),allow_crop=True)
            if tiny is None:
                return None, None, None
            if locate_shop(*tiny) == (5,0):
                return anchor, 'exact', True
            if ax >= 140 and ay >= 1 and ax-140+GW <= w and ay-1+GH <= h:
                geom = self.capture((x+ax-140,y+ay-1,GW,GH),allow_crop=True)
                if geom is None:
                    return None,None,None
                if geometry_present(geom):
                    return anchor,'geometry',True
        # Search a larger centered region occasionally, never the entire desktop.
        now = time.monotonic()
        if now >= self._search_at.get(size,0):
            self._search_at[size] = now+.25
            gx,gy = max(0,w//2-260),max(0,h//2-280)
            gw,gh = min(w-gx,520),min(h-gy,360)
            frame = self.capture((x+gx,y+gy,gw,gh),allow_crop=True)
            if frame is None:
                return None,None,None
            found = locate_shop(*frame)
            if found is not None:
                anchor = gx+found[0],gy+found[1]
                self._anchors[size] = anchor
                return anchor,'exact',True
        return None,None,False if anchor is not None else None

    def _work(self):
        enable_capture_cache()
        try:
            while not self._stop.wait(.05):
                with self._lock:
                    request = self._request if self.enabled else None
                if not request:
                    continue
                hwnd,client = request
                if client[2:] not in {(1280,720),(1366,768)}:
                    continue
                try:
                    if not self._valid(hwnd,client):
                        continue
                    state = self._states.setdefault((hwnd,client[2:]),ShopOpenState())
                    if len(self._states)>16:
                        self._states.pop(next(iter(self._states)))
                    anchor,quality,present = self._gate(client)
                    if not self._valid(hwnd,client) or not state.observe(present):
                        continue
                    if self._pending.full():
                        self.error = 'Screenshot queue full; retrying'
                        continue
                    frame = self.capture(client)
                    if not frame or not self._valid(hwnd,client):
                        continue
                    # Confirm that this exact captured frame still shows the shop.
                    quality = gate_quality(frame,anchor)
                    if not quality:
                        continue
                    state.mark_saved()
                    self._pending.put_nowait((frame,datetime.now(),quality))
                except Exception as exc:
                    self.error = type(exc).__name__
        finally:
            release_capture_cache()
            self._capture_done.set()

    def _write(self):
        while not self._capture_done.is_set() or not self._pending.empty():
            try:
                frame,stamp,quality = self._pending.get(timeout=.1)
            except queue.Empty:
                continue
            try:
                save_png(self.folder,frame,stamp,quality)
                self.saved += 1
                self.error = None
            except Exception as exc:
                self.error = type(exc).__name__
                # Do not clear a newer shop session from the writer thread.
            finally:
                self._pending.task_done()

    def close(self):
        self._stop.set()
        self._worker.join(timeout=.5)
        self._writer.join(timeout=2)
