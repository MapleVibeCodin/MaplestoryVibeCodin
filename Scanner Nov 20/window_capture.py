"""Selected-window capture without recordings, file writes or process-memory reads.

Primary backend: Windows.Graphics.Capture via windows-capture 2.x, targeting an
HWND. Captures this window alone even when other windows overlap it.
Frames are ephemeral NumPy arrays kept only in RAM. The Python callback never OCRs.
"""
from __future__ import annotations
import ctypes
from ctypes import wintypes
import sys
import threading
import time

if sys.platform == 'win32':
    u32 = ctypes.windll.user32
    u32.EnumWindows.argtypes = [ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM), wintypes.LPARAM]
    u32.EnumWindows.restype = wintypes.BOOL
    u32.IsWindowVisible.argtypes = [wintypes.HWND]
    u32.IsWindowVisible.restype = wintypes.BOOL
    u32.IsWindow.argtypes = [wintypes.HWND]
    u32.IsWindow.restype = wintypes.BOOL
    u32.IsIconic.argtypes = [wintypes.HWND]
    u32.IsIconic.restype = wintypes.BOOL
    u32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    u32.GetWindowTextLengthW.restype = ctypes.c_int
    u32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    u32.GetWindowTextW.restype = ctypes.c_int
    u32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    u32.GetWindowRect.restype = wintypes.BOOL
    CALLBACK = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def windows() -> list[tuple[int, str]]:
    """List visible top-level windows; prefer MapleStory and Discord."""
    if sys.platform != 'win32':
        return []
    found = []
    @CALLBACK
    def cb(hwnd, _):
        if not u32.IsWindowVisible(hwnd) or u32.IsIconic(hwnd):
            return True
        size = u32.GetWindowTextLengthW(hwnd)
        if size < 3:
            return True
        buf = ctypes.create_unicode_buffer(size + 1)
        u32.GetWindowTextW(hwnd, buf, len(buf))
        title = buf.value.strip()
        if not title or title.casefold().startswith('fm rush'):
            return True
        rect = wintypes.RECT()
        if not u32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return True
        if rect.right - rect.left < 250 or rect.bottom - rect.top < 150:
            return True
        found.append((int(hwnd), title))
        return True
    u32.EnumWindows(cb, 0)
    def order(pair):
        title = pair[1].lower()
        return (0 if ('maplestory' in title or 'maple story' in title) else 1 if 'discord' in title else 2, title)
    return sorted(found, key=order)


def window_rect(hwnd: int) -> tuple[int, int, int, int] | None:
    if sys.platform != 'win32' or not u32.IsWindow(hwnd):
        return None
    rect = wintypes.RECT()
    # DWM extended bounds exclude the invisible resize margin and usually
    # align better to the Graphics Capture frame than GetWindowRect.
    try:
        dwm=ctypes.windll.dwmapi
        if dwm.DwmGetWindowAttribute(hwnd,9,ctypes.byref(rect),ctypes.sizeof(rect)) == 0:
            return rect.left, rect.top, rect.right-rect.left, rect.bottom-rect.top
    except Exception:
        pass
    if not u32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return None
    return rect.left, rect.top, rect.right-rect.left, rect.bottom-rect.top


class WindowFrames:
    """A latest-frame-only WGC capture buffer. No video is recorded or stored."""
    def __init__(self, hwnd: int, interval_ms: int = 16):
        self.hwnd = hwnd
        self.interval_ms = max(16, int(interval_ms))
        self._last_copied = 0.0
        self._lock = threading.Lock()
        self._frame = None
        self._version = 0
        self._timestamp = 0.0
        self._running = False
        self._capture_control = None
        self.error = ''
        self._capture = None
        self._dark=False
        self._loading_epoch=0
        self._loading_at=None

    def set_interval(self,interval_ms):
        self.interval_ms=max(16,int(interval_ms))

    @property
    def loading_epoch(self):
        with self._lock:return self._loading_epoch

    @property
    def loading_started(self):
        with self._lock:return self._loading_at

    def start(self):
        from windows_capture import WindowsCapture
        # Do not capture cursor. Window-HWND capture excludes other windows and
        # avoids the infinite recursive preview shown in the user's recording.
        self._capture = WindowsCapture(window_hwnd=self.hwnd,
                                       cursor_capture=False,
                                       draw_border=False,
                                       minimum_update_interval=16)

        @self._capture.event
        def on_frame_arrived(frame, control):
            try:
                # Watch sparse loading tiles even when idle frame copies slow down.
                import numpy as np
                now=time.perf_counter();a=frame.frame_buffer
                h,w=a.shape[:2]
                dark=sum(float(a[int((y-.06)*h):int((y+.06)*h):16,
                                 int((x-.06)*w):int((x+.06)*w):16,:3].mean())<24
                         for x,y in ((.25,.25),(.75,.25),(.5,.5),(.25,.7),(.75,.7)))>=4
                transition=dark!=self._dark
                if dark and not self._dark:
                    with self._lock:self._loading_epoch+=1;self._loading_at=now
                self._dark=dark
                if not transition and now-self._last_copied<self.interval_ms/1000.:return
                self._last_copied=now
                bgr = np.array(a[:, :, :3], copy=True, order="C")
                with self._lock:
                    self._frame = bgr
                    self._timestamp = now
                    self._version += 1
            except Exception as exc:
                self.error = f'Frame conversion: {exc}'

        @self._capture.event
        def on_closed():
            self._running = False
            self.error = 'The selected window closed or capture ended.'

        self._capture_control = self._capture.start_free_threaded()
        self._running = True

    def latest(self, after: int = -1):
        with self._lock:
            if self._version == after or self._frame is None:
                return None
            return self._version, self._timestamp, self._frame

    def peek(self, after=-1):
        return self.latest(after)

    def stop(self):
        self._running = False
        if self._capture_control is not None:
            try:
                self._capture_control.stop()
            except Exception:
                pass
            self._capture_control = None
        self._capture = None
        with self._lock:
            self._frame = None

    @property
    def running(self):
        return self._running
