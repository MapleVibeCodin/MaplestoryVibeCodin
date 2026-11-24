"""Click-through Windows overlays aligned to the MapleStory window."""
import sys
import ctypes
import tkinter as tk
from game_window import window_at_point, window_rect

class OverlayPin:
    def __init__(self,master,interval_ms=80):
        self.window=tk.Toplevel(master)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.attributes('-topmost',True)
        self.color='#010203'
        self.window.configure(bg=self.color)
        self.canvas=tk.Canvas(self.window,bg=self.color,highlightthickness=0)
        self.canvas.pack(fill='both',expand=True)
        self.data=None
        self.closed=False
        self.ready=False
        self.drawn=None;self.last_rect=None;self.visible=False
        if sys.platform=='win32':
            self.window.attributes('-transparentcolor',self.color)
            self.window.update_idletasks()
            user=ctypes.windll.user32
            from ctypes import wintypes
            user.GetParent.argtypes=[wintypes.HWND];user.GetParent.restype=wintypes.HWND
            self.hwnd=user.GetParent(self.window.winfo_id()) or self.window.winfo_id()
            get_style=user.GetWindowLongW;set_style=user.SetWindowLongW
            get_style.argtypes=[wintypes.HWND,ctypes.c_int];get_style.restype=ctypes.c_long
            set_style.argtypes=[wintypes.HWND,ctypes.c_int,ctypes.c_long];set_style.restype=ctypes.c_long
            set_style(self.hwnd,-20,get_style(self.hwnd,-20)|0x80000|0x20|0x08000000|0x80)
            user.SetWindowPos.argtypes=[wintypes.HWND,wintypes.HWND,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_uint]
            user.IsIconic.argtypes=[wintypes.HWND]
            user.GetForegroundWindow.restype=wintypes.HWND
            self.ready=True
        self.interval_ms=interval_ms
        self.timer=self.window.after(self.interval_ms,self.follow)

    def show_many(self,hwnd,size,hits):
        self.data=(hwnd,size,dict(hits)) if hits else None
        if not hits:self.window.withdraw();self.visible=False;self.drawn=None
        else:self.follow(schedule=False)

    def hide(self):
        self.data=None
        self.window.withdraw();self.visible=False;self.drawn=None

    def can_show(self, hwnd, rect, size, hits):
        return ctypes.windll.user32.GetForegroundWindow()==hwnd

    def follow(self,schedule=True):
        if self.closed:return
        if self.data and self.ready:
            hwnd,(sw,sh),hits=self.data
            user=ctypes.windll.user32
            rect=window_rect(hwnd)
            if rect and not user.IsIconic(hwnd) and self.can_show(hwnd, rect, (sw, sh), hits):
                left,top,w,h=rect
                if rect!=self.last_rect:
                    self.window.geometry(f'{w}x{h}{left:+d}{top:+d}');self.last_rect=rect
                drawing=(w,h,sw,sh,tuple(sorted((name,tuple(hit['box']),hit['mode']) for name,hit in hits.items())))
                if drawing!=self.drawn:
                    self.draw_markers(w,h,sw,sh,hits);self.drawn=drawing
                if not self.visible:self.window.deiconify();self.visible=True
                user.SetWindowPos(self.hwnd,-1,left,top,w,h,0x0010|0x0040)
            elif self.visible:self.window.withdraw();self.visible=False
        if schedule:self.timer=self.window.after(self.interval_ms,self.follow)

    def close(self):
        self.closed=True
        try:self.window.after_cancel(self.timer)
        except tk.TclError:pass
        self.window.destroy()


class ShopPreviewPin(OverlayPin):
    def can_show(self, hwnd, rect, size, hits):
        if super().can_show(hwnd, rect, size, hits):
            return True
        left, top, width, height = rect
        sw, sh = size
        for hit in hits.values():
            l, t, r, b = hit['box']
            if any(window_at_point(round(left + x * width / sw),
                                   round(top + y * height / sh)) != hwnd
                   for x in (l, (l + r) / 2, r) for y in (t, (t + b) / 2, b)):
                return False
        return bool(hits)

    def draw_markers(self, w, h, sw, sh, hits):
        canvas = self.canvas
        canvas.delete('all')
        for hit in hits.values():
            l, t, r, b = hit['box']
            box = (l * w / sw, t * h / sh, r * w / sw, b * h / sh)
            canvas.create_rectangle(*box, outline='#161616', width=6)
            canvas.create_rectangle(*box, outline='#ff1744', width=3)
