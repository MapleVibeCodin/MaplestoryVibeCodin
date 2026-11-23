"""Read-only, dependency-free grass FM camera tracking from fixed scenery.

Signatures are tiny BGR pixel strips sampled from stationary map terrain.
They contain no chat, character names, or full screenshot. An estimate is
accepted only when at least two independent landmarks agree exactly.
"""
from collections import Counter
import ctypes
import sys
import threading
import time

# Relative to the reference grass doorway's bottom center (1135, 773)
# in a native-pixel FM 4 screenshot. All grass rooms share this terrain.
_SIGNATURES = (
    (-315, -423, ('eeddcceeddcceeddcceeddcceeddcceeddcceeddcc778888556677556677556677667777', 'eeddccddddcceecccceeddcceeddccddccccbbbbaabbaaaa445555556677777777aaaa99', 'eeccccddddcceeccccddddccbbaa99aa9999555555666655443333226644226655227755')),
    (-195, -273, ('112233112222112233224455114455224455224466224455114455224455224466224455', '113344223344113355224444113344113344223344113344223344113344113344113333', '112233112233112233002222111122112222001122114488114488004488114499004499')),
    (-420, -223, ('11775511664433443333554433333355444422886611774411774422443333554444bb88', '225588114477114488114477114488224477115588114488114488115588114488114488', 'ddccccddddccddcccceeddddeeddddeeddccddddccddccccbbaaaa999988555566667788')),
    (-635, -452, ('22665522775522aa7744cc99339977115533002211002211002211002211339977449977', '00225588eecc77ddcc77ccbb66ddbb55ccaa77ddcc77ddcc44bb9966bbaa66bb99225544', '11665522775511664422996633bb8833aa7722886611554422774422bb88226644226655')),
    (-400, -403, ('226644227755226644226644225533113333113322114433333333444444444444444444', '449977338866338866338855337755227755226644226644226644224433113322113322', '338866227755225533114433226644226655226644226644226644225533225544225533')),
    (-315, -373, ('112233111122112222112222111122002222112222111122112222111122001111112222', '001111001111111111001111001111111122001111111111001122112222112222111122', '001111111122002222111122112222112233112233112233112233113333112233112233')),
    (-475, -418, ('bbaaaabbaa99bbaaaabbaaaaccbbaaccbbbbddccbbddccccddccbbddccbbccccbbddbbbb', '88777777667733443333223333996633997733996633997733996633aa66339977338855', '339977339966338877339966338866227755226644227755337755337766338866338866')),
)
LANDMARKS = tuple((x, y, tuple(bytes.fromhex(s) for s in rows)) for x,y,rows in _SIGNATURES)


def locate_grass_portal(buffer, width, height, stride):
    """Return (portal_x, portal_y) in client pixels, or None on ambiguity.

    Buffer is a top-down 24-bit BGR image with DWORD-padded rows.
    A doorway may be offscreen: the surrounding terrain still locates it.
    """
    if width <= 0 or height <= 0 or stride < width * 3 or len(buffer) != stride * height:
        return None
    votes = Counter()
    for dx, dy, rows in LANDMARKS:
        first = rows[0]
        length = len(first)
        at = buffer.find(first)
        hits = set()
        while at >= 0:
            y, offset = divmod(at, stride)
            if (offset % 3 == 0 and offset + length <= width * 3 and y + 14 < height
                    and all(buffer[at + d*stride:at + d*stride + length] == row
                            for d, row in zip((7,14), rows[1:]))):
                hits.add((offset // 3 - dx, y - dy))
            at = buffer.find(first, at + 1)
        votes.update(hits)
    ranked = votes.most_common(2)
    if not ranked or ranked[0][1] < 2 or (len(ranked) > 1 and ranked[1][1] == ranked[0][1]):
        return None
    return ranked[0][0]


def capture_client(client):
    """Capture visible desktop pixels for this client only, using Windows GDI."""
    if sys.platform != 'win32':
        return None
    from ctypes import wintypes as W
    left, top, width, height = client
    if (width, height) not in {(1280,720),(1366,768)}:
        return None

    class Header(ctypes.Structure):
        _fields_ = [('size', W.DWORD), ('width', W.LONG), ('height', W.LONG),
                    ('planes', W.WORD), ('bits', W.WORD), ('compression', W.DWORD),
                    ('image_size', W.DWORD), ('xppm', W.LONG), ('yppm', W.LONG),
                    ('used', W.DWORD), ('important', W.DWORD)]

    u, g = ctypes.windll.user32, ctypes.windll.gdi32
    u.GetDC.argtypes = [W.HWND]; u.GetDC.restype = W.HDC
    u.ReleaseDC.argtypes = [W.HWND, W.HDC]; u.ReleaseDC.restype = ctypes.c_int
    g.CreateCompatibleDC.argtypes = [W.HDC]; g.CreateCompatibleDC.restype = W.HDC
    g.CreateDIBSection.argtypes = [W.HDC, ctypes.POINTER(Header), W.UINT,
                                  ctypes.POINTER(ctypes.c_void_p), W.HANDLE, W.DWORD]
    g.CreateDIBSection.restype = W.HANDLE
    g.SelectObject.argtypes = [W.HDC, W.HANDLE]; g.SelectObject.restype = W.HANDLE
    g.BitBlt.argtypes = [W.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                         W.HDC, ctypes.c_int, ctypes.c_int, W.DWORD]
    g.BitBlt.restype = W.BOOL
    g.DeleteObject.argtypes = [W.HANDLE]; g.DeleteObject.restype = W.BOOL
    g.DeleteDC.argtypes = [W.HDC]; g.DeleteDC.restype = W.BOOL

    screen = u.GetDC(None)
    if not screen:
        return None
    mem = bitmap = old = None
    try:
        mem = g.CreateCompatibleDC(screen)
        if not mem:
            return None
        stride = (width * 3 + 3) & ~3
        header = Header(ctypes.sizeof(Header), width, -height, 1, 24, 0,
                        stride*height, 0,0,0,0)
        pixels = ctypes.c_void_p()
        bitmap = g.CreateDIBSection(screen, ctypes.byref(header), 0,
                                    ctypes.byref(pixels), None, 0)
        if not bitmap or not pixels.value:
            return None
        old = g.SelectObject(mem, bitmap)
        if not old or old == ctypes.c_void_p(-1).value:
            old = None
            return None
        if not g.BitBlt(mem,0,0,width,height,screen,left,top,0x00CC0020):
            return None
        g.GdiFlush()
        return ctypes.string_at(pixels, stride*height), width, height, stride
    finally:
        if old: g.SelectObject(mem, old)
        if bitmap: g.DeleteObject(bitmap)
        if mem: g.DeleteDC(mem)
        u.ReleaseDC(None,screen)


class GrassCameraTracker:
    """One bounded background capture at a time; never block Tk's UI thread."""
    def __init__(self, interval=0.10, max_age=0.30):
        self.interval = interval
        self.max_age = max_age
        self._lock = threading.Lock()
        self._busy = False
        self._next = 0.0
        self._latest = None
        self._requested = None

    def get(self, hwnd, client):
        key = (hwnd, tuple(client))
        now = time.monotonic()
        with self._lock:
            if key != self._requested:
                self._requested = key
                self._latest = None
                self._next = 0.0
            if not self._busy and now >= self._next:
                self._busy = True
                self._next = now + self.interval
                threading.Thread(target=self._scan, args=(key,), daemon=True).start()
            if self._latest is not None:
                saved, at, point = self._latest
                if saved == key and now - at <= self.max_age:
                    return point
        return None

    def reset(self):
        with self._lock:
            self._requested = None
            self._latest = None
            self._next = 0.0

    def _scan(self, key):
        point = None
        captured_at = time.monotonic()
        try:
            frame = capture_client(key[1])
            if frame is not None:
                point = locate_grass_portal(*frame)
        except (OSError, ValueError, ctypes.ArgumentError):
            pass
        finally:
            with self._lock:
                if self._requested == key:
                    self._latest = (key, captured_at, point)
                self._busy = False
