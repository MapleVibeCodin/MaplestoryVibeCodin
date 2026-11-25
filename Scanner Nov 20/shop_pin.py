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
        self.timer=None

    def show_many(self,hwnd,size,hits):
        self.data=(hwnd,size,dict(hits)) if hits else None
        if not hits:self.hide()
        else:
            self.follow(schedule=False)
            if self.timer is None:self.timer=self.window.after(self.interval_ms,self.follow)

    def hide(self):
        self.data=None
        if self.timer is not None:
            self.window.after_cancel(self.timer);self.timer=None
        if self.visible:self.window.withdraw()
        self.visible=False;self.drawn=None

    def can_show(self, hwnd, rect, size, hits):
        return ctypes.windll.user32.GetForegroundWindow()==hwnd

    def follow(self,schedule=True):
        if self.closed:return
        if schedule:self.timer=None
        if self.data and self.ready:
            hwnd,(sw,sh),hits=self.data
            user=ctypes.windll.user32
            rect=window_rect(hwnd)
            if rect and not user.IsIconic(hwnd) and self.can_show(hwnd, rect, (sw, sh), hits):
                left,top,w,h=rect
                moved=rect!=self.last_rect
                if moved:
                    self.window.geometry(f'{w}x{h}{left:+d}{top:+d}');self.last_rect=rect
                drawing=(w,h,sw,sh,tuple(sorted((name,tuple(hit['box']),hit['mode']) for name,hit in hits.items())))
                changed=drawing!=self.drawn
                if changed:
                    self.draw_markers(w,h,sw,sh,hits);self.drawn=drawing
                shown=not self.visible
                if shown:self.window.deiconify();self.visible=True
                foreground=user.GetForegroundWindow()
                focus_changed=foreground!=getattr(self,'_last_foreground',None)
                self._last_foreground=foreground
                if moved or changed or shown or focus_changed:
                    user.SetWindowPos(self.hwnd,-1,left,top,w,h,0x0010|0x0040)
            elif self.visible:self.window.withdraw();self.visible=False
        if schedule and self.data:self.timer=self.window.after(self.interval_ms,self.follow)

    def close(self):
        self.closed=True
        try:
            if self.timer is not None:self.window.after_cancel(self.timer)
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


# Previously measured native entrance portal coordinates. Bottom row not calibrated.
ENTRANCE_DOORS = {
    17:(488,248),18:(635,248),19:(802,248),20:(954,248),
    13:(488,488),14:(635,488),15:(802,488),16:(954,488),
    7:(306,728),8:(454,728),9:(607,728),
    10:(810,728),11:(965,728),12:(1127,728),
}
ENTRANCE_ROPE_X = 712
ENTRANCE_WARP = (1256, 728)

def entrance_marker(room, translation, client, window):
    """Visible portal outline or edge direction; no guessed lower-row doors."""
    if not 1<=room<=20:return {}
    left,top,w,h=client
    ox,oy=left-window[0],top-window[1]
    label=f'FM {room}' if room>=7 else f'FM {room} · DOWN WARP'
    if translation is None:
        return {label:{'box':(ox+w-245,oy+12,ox+w-12,oy+45),'mode':'LABEL'}}
    x,y=ENTRANCE_DOORS.get(room,ENTRANCE_WARP)
    dx,dy=translation
    x+=dx;y+=dy
    l,t,r,b=(x-58,y-157,x+58,y-5) if room>=7 else (x-24,y-75,x+24,y-7)
    if 4<=l<r<=w-4 and 4<=t<b<=h-4:
        return {label:{'box':(ox+l,oy+t,ox+r,oy+b),'mode':'PORTAL'}}
    directions=[]
    if l<4:directions.append('LEFT')
    if r>w-4:directions.append('RIGHT')
    if t<4:directions.append('UP')
    if b>h-4:directions.append('DOWN')
    return {label+' · '+ ' / '.join(directions):{'box':(ox+w-300,oy+12,ox+w-12,oy+45),'mode':'LABEL'}}


class EntranceGuidePin(OverlayPin):
    """Green click-through portal overlay, only over the focused game."""
    def draw_markers(self,w,h,sw,sh,hits):
        c=self.canvas;c.delete('all')
        for name,hit in hits.items():
            l,t,r,b=hit['box']
            l,t,r,b=l*w/sw,t*h/sh,r*w/sw,b*h/sh
            if hit['mode']=='PORTAL':
                c.create_rectangle(l,t,r,b,outline='#17231b',width=7)
                c.create_rectangle(l,t,r,b,outline='#72ff86',width=3)
                x=(l+r)/2;y=max(14,t-15)
                c.create_text(x+1,y+1,text=name,fill='#17231b',font=('Segoe UI',14,'bold'))
                c.create_text(x,y,text=name,fill='#72ff86',font=('Segoe UI',14,'bold'))
            else:
                c.create_rectangle(l,t,r,b,fill='#15241c',outline='#72ff86',width=2)
                c.create_text((l+r)/2,(t+b)/2,text=name,fill='#72ff86',
                              font=('Segoe UI',10,'bold'),width=max(1,r-l-8))


class ItemInventoryPin(OverlayPin):
    """Click-through row border; no purchase or cursor action."""
    def draw_markers(self,w,h,sw,sh,hits):
        c=self.canvas;c.delete('all')
        for hit in hits.values():
            l,t,r,b=hit['box']
            box=(l*w/sw,t*h/sh,r*w/sw,b*h/sh)
            color={'MATCH':'#72ff86','AMBIGUOUS':'#ffdb3d','SOLD':'#ff9960','PRICE_CHECK':'#ffdb3d','SOLD_CHECK':'#ff9960','ROW_CHECK':'#ffdb3d','FAST_NAME':'#ffdb3d','FAST_PRICE':'#36e6ff','FAST_SOLD':'#ff9960'}.get(hit['mode'],'#ffdb3d')
            c.create_rectangle(*box,outline='#161616',width=4)
            c.create_rectangle(*box,outline=color,width=2)
