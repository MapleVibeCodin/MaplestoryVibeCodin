"""Low-latency candidate location for an item icon already pictured on HeneFM.

No item-name OCR, remote API, game memory access, mouse movement or input.
A positive image match identifies the icon art ONLY. Multiple identical items,
stat rolls and asking prices must be checked in the actual shop.
"""
from __future__ import annotations
import base64
import os
import ctypes
from functools import lru_cache
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import URLError, HTTPError
import re
from dataclasses import dataclass
import threading
import time
import cv2
import numpy as np

MAX_ICON_BYTES = 45_000
MAX_ICON_SIDE = 96


@dataclass(frozen=True)
class IconReference:
    listing_id: str
    item: str
    gray: np.ndarray
    pixels_bgr: np.ndarray
    opaque: np.ndarray
    offset: tuple[int, int]


def decode_reference(listing_id: str, item: str, data_url: str) -> IconReference | None:
    if not isinstance(data_url, str) or not data_url.startswith('data:image/png;base64,'):
        return None
    encoded = data_url.split(',', 1)[1]
    if not 40 <= len(encoded) <= MAX_ICON_BYTES * 4 // 3 + 8:
        return None
    try:
        blob = base64.b64decode(encoded, validate=True)
        if len(blob) > MAX_ICON_BYTES or not blob.startswith(b'\x89PNG\r\n\x1a\n'):
            return None
        png = cv2.imdecode(np.frombuffer(blob, np.uint8), cv2.IMREAD_UNCHANGED)
        if png is None or png.ndim != 3 or png.shape[2] not in (3, 4):
            return None
        h, w = png.shape[:2]
        if not (12 <= h <= MAX_ICON_SIDE and 12 <= w <= MAX_ICON_SIDE):
            return None
        if png.shape[2] == 3:
            alpha = np.full((h, w), 255, dtype=np.uint8)
        else:
            alpha = png[:, :, 3]
        opaque = alpha >= 225
        yy, xx = np.where(opaque)
        if len(xx) < 30 or len(xx) < 0.14 * (h * w):
            return None
        # Trim empty border. This also prevents transparent page backgrounds from
        # dominating the fast correlation pass.
        l, t, r, b = int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1
        trimmed = png[t:b, l:r, :3]
        mask = opaque[t:b, l:r]
        if min(trimmed.shape[:2]) < 9:
            return None
        # Background can vary by slot. A neutral gray is used only to propose
        # likely positions, then opaque BGR pixels are verified at those spots.
        composited = trimmed.copy()
        composited[~mask] = 76
        gray = cv2.cvtColor(composited, cv2.COLOR_BGR2GRAY)
        if float(gray.std()) < 12.0:
            return None
        return IconReference(str(listing_id)[:120], str(item)[:100], gray,
                             trimmed.copy(), mask.copy(), (l, t))
    except (ValueError, TypeError, cv2.error, base64.binascii.Error):
        return None


def find_icon(frame: np.ndarray, icon: IconReference, *, max_matches: int = 4):
    """Match an icon in the central game/shop region, returning candidate boxes.

    Intentionally single-scale and grayscale for low latency. The source HeneFM
    PNG must correspond to the in-game art at the current display scaling.
    """
    if icon is None or frame is None or frame.ndim != 3 or frame.shape[2] < 3:
        return [], 0.0
    started = time.perf_counter()
    h, w = frame.shape[:2]
    th, tw = icon.gray.shape
    # Avoid expensive entire-screen OCR; shops normally occupy the center.
    # Keep margin for shops opened at screen edges and high DPI.
    left, top, right, bottom = int(w * .04), int(h * .055), int(w * .96), int(h * .95)
    if right - left < tw or bottom - top < th:
        return [], round((time.perf_counter() - started) * 1000, 2)
    region = frame[top:bottom, left:right, :3]
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    # Raw zero-mean correlation is faster than normalized correlation on
    # full-HD frames; exact foreground-pixel checks below reject lookalikes.
    scores=cv2.matchTemplate(gray,icon.gray,cv2.TM_CCOEFF)
    energy=float(np.sum((icon.gray.astype(np.float32)-icon.gray.mean())**2))
    threshold=max(1.,energy*.50)
    results = []
    # Each candidate is validated against original pixels, not only grayscale.
    sample_y, sample_x = np.where(icon.opaque)
    stride = max(1, int(len(sample_x) / 175))
    sample_y, sample_x = sample_y[::stride], sample_x[::stride]
    for _ in range(min(12, max_matches * 4)):
        _, score, _, (dx, dy) = cv2.minMaxLoc(scores)
        if score < threshold:
            break
        foreground = region[dy + sample_y, dx + sample_x, :3].astype(np.int16)
        source = icon.pixels_bgr[sample_y, sample_x, :3].astype(np.int16)
        diffs = np.abs(foreground - source)
        exactish = float(np.mean(np.max(diffs, axis=1) <= 32))
        if exactish >= .74:
            x = left + dx
            y = top + dy
            # Source PNG bounding box can be asymmetric. The box still contains
            # the visible icon art and is tightened to the grid icon portion.
            results.append({'box': (x, y, x + tw, y + th),
                            'confidence': round(exactish, 3),
                            'mode': 'ICON · VERIFY STATS'})
            if len(results) >= max_matches:
                break
        scores[max(0, dy-th):min(scores.shape[0],dy+th+1),
               max(0,dx-tw):min(scores.shape[1],dx+tw+1)] = 0.0
    return results, round((time.perf_counter() - started) * 1000, 2)


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('unexpected image redirect')


@lru_cache(maxsize=128)
def download_icon(url: str) -> str | None:
    """Fetch one official HeneFM sprite asynchronously *before* entering a shop.

    Host and path are strictly allowed; no private IPs, redirects or tokens.
    """
    if not isinstance(url, str) or not re.fullmatch(
        r'https://(?:www\.)?henefm\.com/classic/items/\d{5,9}\.png', url):
        return None
    opener = build_opener(_NoRedirect())
    try:
        with opener.open(Request(url, headers={'User-Agent':'FM-Rush-IconPreview/1.0'}), timeout=2.5) as response:
            if 'image/png' not in response.headers.get('Content-Type','').lower():
                return None
            blob = response.read(MAX_ICON_BYTES + 1)
            if len(blob) > MAX_ICON_BYTES or not blob.startswith(b'\x89PNG\r\n\x1a\n'):
                return None
            return 'data:image/png;base64,' + base64.b64encode(blob).decode('ascii')
    except (HTTPError, URLError, OSError, ValueError, TimeoutError):
        return None


class IconTarget:
    """Atomic reference shared by UI and scanning threads."""
    def __init__(self):
        self.lock = threading.Lock()
        self.target = None
        self.revision = 0
        self.listing_id = ''

    def clear(self, listing_id: str = ''):
        with self.lock:
            if self.listing_id != listing_id or self.target is not None:
                self.listing_id = listing_id
                self.target = None
                self.revision += 1

    def install(self, icon: IconReference):
        with self.lock:
            if icon.listing_id != self.listing_id:
                return False
            self.target = icon
            self.revision += 1
            return True

    def snapshot(self):
        with self.lock:
            return self.target, self.revision


def verify_at(frame, icon: IconReference, hits) -> bool:
    """Cheap sub-millisecond recheck of previously found slot positions."""
    if not hits:return False
    h,w=frame.shape[:2];th,tw=icon.gray.shape
    sy,sx=np.where(icon.opaque)
    stride=max(1,len(sx)//120)
    sy,sx=sy[::stride],sx[::stride]
    for hit in hits:
        x,y,_,_=hit['box']
        if not (0<=x<=w-tw and 0<=y<=h-th):return False
        seen=frame[y+sy,x+sx,:3].astype(np.int16)
        expected=icon.pixels_bgr[sy,sx,:3].astype(np.int16)
        if float(np.mean(np.max(np.abs(seen-expected),axis=1)<=32))<.74:return False
    return True


class ItemScanWorker(threading.Thread):
    """Scans only pre-rendered icon pixels, never loads an OCR model."""
    def __init__(self, frames, target: IconTarget, emit, stop):
        super().__init__(daemon=True, name='FM-ItemIcon-Locator')
        self.frames, self.target, self.emit, self.stop = frames, target, emit, stop

    def run(self):
        last_revision = -1
        last_version = -1
        last_signature = None
        last_hits = []
        while not self.stop.is_set():
            icon, revision = self.target.snapshot()
            if icon is None:
                last_hits=[]
                if last_signature:
                    self.emit(('item_found', revision, None, (0, 0), [], 0.0))
                    last_signature = None
                last_revision = revision
                self.stop.wait(.04)
                continue
            if os.name=='nt' and getattr(self.frames,'hwnd',None):
                try:
                    if ctypes.windll.user32.GetForegroundWindow()!=self.frames.hwnd:
                        self.stop.wait(.025);continue
                except (OSError,AttributeError):pass
            sample = self.frames.peek(last_version if revision == last_revision else -1)
            if sample is None:
                self.stop.wait(.02)
                continue
            version, stamp, frame = sample
            if revision != last_revision:
                last_signature = None
                last_hits=[]
            last_version, last_revision = version, revision
            try:
                if last_hits and verify_at(frame,icon,last_hits):
                    hits,scan_ms=last_hits,0.0
                else:
                    hits,scan_ms=find_icon(frame, icon)
                sig = tuple((tuple(hit['box']), hit['mode']) for hit in hits)
                # Always publish the first result when switching targets;
                # afterwards only update on a change (not on every frame).
                if sig != last_signature:
                    if self.target.snapshot()[1] == revision:
                        self.emit(('item_found', revision, icon.listing_id,
                                   (frame.shape[1], frame.shape[0]), hits, scan_ms))
                        last_signature = sig
                last_hits=hits
            except (cv2.error, ValueError, IndexError) as error:
                self.emit(('item_scan_error', str(error)[:100]))
            self.stop.wait(.045 if last_signature else .018)
