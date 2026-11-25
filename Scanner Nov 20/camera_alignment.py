"""Read-only, dependency-free grass FM camera tracking from fixed scenery.

Signatures are tiny BGR pixel strips sampled from stationary map terrain.
They contain no chat, character names, or full screenshot. An estimate is
accepted only when at least two independent landmarks agree exactly.
"""
from collections import Counter, OrderedDict
from functools import lru_cache
from ctypes import wintypes as W
import queue
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


def locate_grass_portal(buffer, width, height, stride, landmarks=LANDMARKS):
    """Return (portal_x, portal_y) in client pixels, or None on ambiguity.

    Buffer is a top-down 24-bit BGR image with DWORD-padded rows.
    A doorway may be offscreen: the surrounding terrain still locates it.
    """
    if width <= 0 or height <= 0 or stride < width * 3 or len(buffer) != stride * height:
        return None
    votes = Counter()
    for dx, dy, rows in landmarks:
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


class Header(ctypes.Structure):
    _fields_ = [('size', W.DWORD), ('width', W.LONG), ('height', W.LONG),
                ('planes', W.WORD), ('bits', W.WORD), ('compression', W.DWORD),
                ('image_size', W.DWORD), ('xppm', W.LONG), ('yppm', W.LONG),
                ('used', W.DWORD), ('important', W.DWORD)]

@lru_cache(maxsize=1)
def _capture_api():
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

    return u,g

_capture_local=threading.local()

def enable_capture_cache():
    """Opt in on a persistent capture worker; handles never cross threads."""
    if not hasattr(_capture_local,'pool'):_capture_local.pool=OrderedDict()

def _free_surface(g, surface):
    mem,bitmap,old,pixels=surface
    if old:g.SelectObject(mem,old)
    if bitmap:g.DeleteObject(bitmap)
    if mem:g.DeleteDC(mem)

def release_capture_cache():
    pool=getattr(_capture_local,'pool',None)
    if pool is not None:
        if sys.platform=='win32':
            _,g=_capture_api()
            for surface in pool.values():_free_surface(g,surface)
        del _capture_local.pool

def capture_client(client, *, allow_crop=False):
    """Capture visible desktop pixels; reuse a bounded DIB/DC pool per worker."""
    if sys.platform!='win32':return None
    left,top,width,height=client
    if width<=0 or height<=0:return None
    if not allow_crop and (width,height) not in {(1280,720),(1366,768)}:return None
    u,g=_capture_api()
    screen=u.GetDC(None)
    if not screen:return None
    pool=getattr(_capture_local,'pool',None)
    key=(width,height)
    stride=(width*3+3)&~3
    surface=pool.pop(key,None) if pool is not None else None
    mem=bitmap=old=None
    pixels=ctypes.c_void_p()
    keep=False
    try:
        if surface is not None:
            mem,bitmap,old,pixels=surface
        else:
            mem=g.CreateCompatibleDC(screen)
            if not mem:return None
            header=Header(ctypes.sizeof(Header),width,-height,1,24,0,stride*height,0,0,0,0)
            bitmap=g.CreateDIBSection(screen,ctypes.byref(header),0,ctypes.byref(pixels),None,0)
            if not bitmap or not pixels.value:return None
            old=g.SelectObject(mem,bitmap)
            if not old or old==ctypes.c_void_p(-1).value:
                old=None
                return None
        if not g.BitBlt(mem,0,0,width,height,screen,left,top,0x00CC0020):return None
        g.GdiFlush()
        data=ctypes.string_at(pixels,stride*height)
        if pool is not None:
            pool[key]=(mem,bitmap,old,pixels)
            keep=True
            while len(pool)>8:_free_surface(g,pool.popitem(last=False)[1])
        return data,width,height,stride
    finally:
        if not keep:_free_surface(g,(mem,bitmap,old,pixels))
        u.ReleaseDC(None,screen)


class GrassCameraTracker:
    """One bounded background capture at a time; never block Tk's UI thread."""
    def __init__(self, interval=0.10, max_age=0.30, matcher=locate_grass_portal):
        self.matcher = matcher
        self.interval = interval
        self.max_age = max_age
        self._lock = threading.Lock()
        self._busy = False
        self._next = 0.0
        self._latest = None
        self._requested = None
        self._closed=False
        self._jobs=queue.Queue()
        self._worker=threading.Thread(target=self._work,daemon=True,name='FM entrance capture')
        self._worker.start()

    def _work(self):
        enable_capture_cache()
        try:
            while True:
                key=self._jobs.get()
                if key is None or self._closed:return
                self._scan(key)
        finally:release_capture_cache()

    def close(self):
        self._closed=True;self.reset();self._jobs.put_nowait(None)

    def get(self, hwnd, client):
        key = (hwnd, tuple(client))
        now = time.monotonic()
        with self._lock:
            if key != self._requested:
                self._requested = key
                self._latest = None
                self._next = 0.0
            if not self._closed and not self._busy and now >= self._next:
                self._busy = True
                self._next = now + self.interval
                self._jobs.put_nowait(key)
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
                point = self.matcher(*frame)
        except (OSError, ValueError, ctypes.ArgumentError):
            pass
        finally:
            with self._lock:
                if self._requested == key:
                    self._latest = (key, captured_at, point)
                self._busy = False


# Native screenshot client origin (3,40). Numbered-door artwork, not player data.
_ENTRANCE_SIGNATURES = (
    (462,103, ('00bbdd00ccdd00ccdd00bbcc0066aa00336611668833779922779911557714303d028394', 'cc66331b0e1600bbcc00ccdd0077cc0044990044663377992277991155770e20290e7a92', '4a4a5812171b00ccdd00ccdd0099cc004488004477337799226688226688337799337799')),
    (612,105, ('00bbdd0077bb00337711668833779922779911557733779911668822668844669933eeee', '00ccdd0088cc00449900446633779922668811667733779933779944669900ccdd22eeff', '00ccdd0088cc003377004477337799226688226688337799337799337799002d3e005566')),
    (774,102, ('00559922668855668800ccdd00bbdd00559900336622779933779922779911667714303d', 'ca6734cb69351b0e2500bbbb00ccdd0077cc004499004477337799206f8f01062800dddd', '8899aa4a585811142200ccdd00ccdd0088cc00449900336633779917445b09283d00ccdd')),
    (929,104, ('33779933779933779933779944669900ccdd00dddd00ccdd00dddd00dddd00dddd1199bb', '00ccdd0077bb0033881b0e07cc6633cc6633c061329a542e814b2c5c3d29363025102020', '3355664477aa4488cc2266883377aa5599dd3388bb4488cc4f9fde11223a00889900ccdd')),
    (463,341, ('2266880066990077aa227799337799225577115566337799115577337799366d8802203f', '00ccdd0077cc00448800447733779922779911557733779922668833668800ccee22ffff', '00ccdd0088cc00449900336633779922668822668833779933779944779900bbcc00eeee')),
    (611,342, ('2266880066990077aa2277993377992255771155663377991155773377993f7f9f093f3f', '00ccdd0077cc00448800447733779922779911557733779922668833668800a3be05314e', '00ccdd0088cc004499003366337799226688226688337799337799447799003e4400b1b8')),
    (777,341, ('1166881166883377993377993377990011330022443377991155773377994499aa0b9faa', '00ccdd0077cc004488005577337799227799115577337799226688226688446699114f4f', '00ccdd0099cc00449900446633779922668811668833779933779944779900a2c0000f0f')),
    (932,341, ('1166883377993377993377990011330022443377991155773377994499aa0fcedd001122', '0077cc004488005577337799227799115577337799226688226688446699114f4f0096aa', '0099cc00449900446633779922668811668833779933779944779900bbdd000f1f00cccc')),
    (279,582, ('00eeff0088cc0055aa004477004477001133001133115577337799337799115577337799', '00eeff0088bb0055aa00337700557733779922779911557733779922779922668800ddee', '6d7a8b333d442d3636222929171c1c0b1117090e120e17200e1b24112833203f5f203f5f')),
    (431,582, ('74a7a647666400556600ffff00ccee0055aa0055aa004488002244227799337799226688', '77c0c067acac081d3d00ccdd0088bb0055aa003366337799115577227799337799337799', '4455660a1b2c00778800ccdd00ccdd0088bb0055aa004488003355115577337799337799')),
    (585,582, ('00eeff44eeee0055aa004499003366004477115577005566115577115577116688226688', '0066bb00337700447733779933779933779933779944779900eeff22eeff00aacc0055aa', '0088cc00336600447700446600446600446600446600557700447700337700aadd00ccdd')),
    (788,581, ('0066990077aa2277993377992255771155663377991155773377994488aa22eeee0088bb', '0077cc00448800447733779922779911557733779922668833668800ccee22ffff00ccee', '0088cc00449900336633779922668822668833779933779944779900bbcc00eeee00aacc')),
    (944,580, ('004499004488004477003377003366002266003366003366003366003366004466004477', '00ccdd00ccdd00ccdd00ccdd00bbdd0077bb003377116688337799227799115577337799', '28443e28443e0b0b1c00ccdd00ccdd0088cc004499004466337799226688116677337799')),
    (1098,582, ('003366115577115577337799116688116688337799337799337799001133002244337799', '78aabb7eaabb090b1c00bbcc00ccdd0077cc004488005577337799227799115577337799', '99aaaa8899aa0b0e0e00ccdd00ccdd0099cc004499004466337799226688116688337799')),
)
ENTRANCE_LANDMARKS = tuple((x,y,tuple(bytes.fromhex(v) for v in rows)) for x,y,rows in _ENTRANCE_SIGNATURES)
_ENTRANCE_TITLE = (
    bytes.fromhex('dbd0b8ccbb99ccbb99ccbb99dbd0b8ffffffffffffdbd0b8ccbb99ccbb99ccbb99ccbb99ccbb99ffffffffffffd7c7b8ba9f86c5b18ee0d6c1e6ddcfffffffffffff9c7552d0c1a2e3dac7ffffffffffffeae3d5d4c5a8ccbb99ffffffffffff'),
    bytes.fromhex('ffffffffffff9c7552c9b797ffffffc9b3a0c6b391dbd0b8ffffffb29378d0c1a2ffffffe3dac7ccbb99ccbb99ffffffffffff9c7552ccbb99ccbb99ccbb99ccbb99ffffffffffff9c7552ccbb99ccbb99ccbb99ccbb99ffffffffffff9c7552'),
)

def locate_entrance(buffer, width, height, stride):
    """Return (entrance_confirmed, camera_translation_or_None)."""
    if width <= 0 or height <= 0 or stride < width * 3 or len(buffer) != stride * height:
        return None
    def has_title(strip):
        return any(buffer[y*stride:y*stride+min(width,200)*3].find(strip) >= 0
                   for y in range(min(height,120)))
    if not all(has_title(strip) for strip in _ENTRANCE_TITLE):
        return False, None
    return True, locate_grass_portal(buffer,width,height,stride,ENTRANCE_LANDMARKS)


def entrance_title_present(buffer, width, height, stride):
    return all(any(buffer[y*stride:y*stride+min(width,200)*3].find(strip)>=0
                   for y in range(min(height,120))) for strip in _ENTRANCE_TITLE)


def verify_translation(client,translation,landmarks=ENTRANCE_LANDMARKS):
    """Revalidate two independent stationary strips at the last unique offset."""
    x,y,w,h=client;dx,dy=translation
    matches=attempts=0
    for lx,ly,rows in landmarks:
        sx,sy=lx+dx,ly+dy;sw=len(rows[0])//3
        if sx<0 or sy<0 or sx+sw>w or sy+15>h:continue
        frame=capture_client((x+sx,y+sy,sw,15),allow_crop=True)
        attempts+=1
        if frame:
            buf,_,_,stride=frame
            if all(buf[i*stride:i*stride+len(row)]==row for i,row in zip((0,7,14),rows)):
                matches+=1
                if matches>=2:return True
        if attempts>=4:break
    return False


class EntranceCameraTracker(GrassCameraTracker):
    """Cheap title crop outside entrance; full matching only in confirmed entrance."""
    def __init__(self):
        super().__init__(interval=0.20,max_age=0.60,matcher=locate_entrance)
        self._verified_key=None;self._translation=None;self._full_at=0.0

    def _scan(self, key):
        scene=None
        at=time.monotonic()
        try:
            x,y,w,h=key[1]
            crop=capture_client((x,y,min(w,200),min(h,120)),allow_crop=True)
            if crop is not None:
                if entrance_title_present(*crop):
                    # Periodically repeat unique full matching; never keep an
                    # offset when its stationary signatures no longer agree.
                    if (self._verified_key==key and self._translation is not None
                            and at-self._full_at<2.0
                            and verify_translation(key[1],self._translation)):
                        scene=(True,self._translation)
                    else:
                        frame=capture_client(key[1])
                        scene=locate_entrance(*frame) if frame is not None else (True,None)
                        self._verified_key=key;self._full_at=at
                        self._translation=scene[1] if scene and scene[0] else None
                else:
                    scene=(False,None);self._translation=None;self._verified_key=None
        except (OSError,ValueError,ctypes.ArgumentError):
            pass
        finally:
            with self._lock:
                if self._requested==key:
                    self._latest=(key,at,scene)
                self._busy=False


# Two native strips of the end of "Free Market <"; three rows apart.
# Valid for both cave and grass room titles, not "Free Market Entrance".
_ROOM_TITLE = (bytes.fromhex('ffffffe3dac7e6decdccbb99ffffffffffff9c7552d0c1a2f0eae0f0eae0d0c1a2ccbb99dbd0b8ffffffffffffdbd0b8ccbb99ccbb99ffffffffffffffffffffffffccbb99ccbb99ccbb99ccbb99ccbb99d5c8aceae3d5ffffffffffffb69b79'),
               bytes.fromhex('ffffff9c7552ccbb99ccbb99ffffffffffffe1d5cbe5dcd1c9b3a0c3ae8cccbb99ffffffffffffffffffffffffffffffffffffb0926fccbb99ffffffffffff9c7552ccbb99ccbb99ccbb99ccbb99d9cdb3e1d5cbffffffe3dacad7caafccbb99ccbb99'))

def room_title_present(buffer,width,height,stride):
    if width<=0 or height<4 or stride<width*3 or len(buffer)!=stride*height:return False
    limit=min(height,120)
    end=min(width,200)*3
    first,second=_ROOM_TITLE
    for y in range(limit-3):
        a=buffer[y*stride:y*stride+end]
        at=a.find(first)
        while at>=0:
            if at%3==0 and buffer[(y+3)*stride+at:(y+3)*stride+at+len(second)]==second:
                return True
            at=a.find(first,at+1)
    return False
