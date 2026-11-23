"""MapleStory window discovery and screen-space geometry on Windows."""
from __future__ import annotations
import ctypes
from ctypes import wintypes
import sys

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
    u32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    u32.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
    u32.WindowFromPoint.argtypes = [wintypes.POINT]
    u32.WindowFromPoint.restype = wintypes.HWND
    u32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
    u32.GetAncestor.restype = wintypes.HWND
    CALLBACK = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def windows() -> list[tuple[int, str]]:
    """List visible top-level windows; prefer MapleStory."""
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
        return (0 if ('maplestory' in title or 'maple story' in title) else 1, title)
    return sorted(found, key=order)


def window_rect(hwnd: int) -> tuple[int, int, int, int] | None:
    if sys.platform != 'win32' or not u32.IsWindow(hwnd):
        return None
    rect = wintypes.RECT()
    # DWM extended bounds exclude the invisible resize margin.
    try:
        dwm=ctypes.windll.dwmapi
        if dwm.DwmGetWindowAttribute(hwnd,9,ctypes.byref(rect),ctypes.sizeof(rect)) == 0:
            return rect.left, rect.top, rect.right-rect.left, rect.bottom-rect.top
    except Exception:
        pass
    if not u32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return None
    return rect.left, rect.top, rect.right-rect.left, rect.bottom-rect.top


def window_client_rect(hwnd: int) -> tuple[int, int, int, int] | None:
    """Screen-space client rectangle, excluding the title bar and borders."""
    if sys.platform != 'win32':
        return None
    bounds = wintypes.RECT()
    origin = wintypes.POINT()
    if not u32.GetClientRect(hwnd, ctypes.byref(bounds)) or not u32.ClientToScreen(hwnd, ctypes.byref(origin)):
        return None
    return origin.x, origin.y, bounds.right, bounds.bottom


def window_at_point(x: int, y: int) -> int | None:
    if sys.platform != 'win32':
        return None
    hwnd = u32.WindowFromPoint(wintypes.POINT(x, y))
    return u32.GetAncestor(hwnd, 2) if hwnd else None
