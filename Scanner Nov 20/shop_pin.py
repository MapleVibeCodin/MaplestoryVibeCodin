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


# Measured in the supplied native entrance screenshot, client coordinates.
# The bottom row was not visible. Do not fabricate its portal rectangles.
ENTRANCE_DOORS = {
    17:(488,248),18:(635,248),19:(802,248),20:(954,248),
    13:(488,488),14:(635,488),15:(802,488),16:(954,488),
    7:(306,728),8:(454,728),9:(607,728),
    10:(810,728),11:(965,728),12:(1127,728),
}
ENTRANCE_ROPE_X = 712
ENTRANCE_WARP = (1256, 728)
TELEPORT_RANGE = 150

def entrance_route_hits(room, channel, translation, client, window):
    """Pure guide from the fixed waiting rope. Never inject game input."""
    if not (1 <= room <= 20 and 1 <= channel <= 40):
        return {}
    left,top,w,h = client
    wx,wy = left-window[0],top-window[1]
    target = ENTRANCE_DOORS.get(room, ENTRANCE_WARP)
    x,y = target
    distance = abs(x-ENTRANCE_ROPE_X)
    count,remaining = divmod(distance,TELEPORT_RANGE)
    direction = 'LEFT' if x<ENTRANCE_ROPE_X else 'RIGHT'
    horizontal = (f'{direction} TP x{count} + walk {remaining}px' if count
                  else f'{direction} walk ~{remaining}px')
    vertical = 'UP rope' if room>=17 else 'DOWN rope' if room>=13 else 'DOWN to FM 7-12'
    if room<=6:
        text = f'FM {room} | {vertical} > {horizontal} > down warp > LEFT to door | Then CH {channel}'
    else:
        text = f'FM {room} | {vertical} > {horizontal} > UP at door | Then CH {channel}'
    # These are reference-start distances, not live player position or guaranteed casts.
    hits = {text:{'box':(wx+max(8,w//2-410),wy+8,wx+min(w-8,w//2+410),wy+37),'mode':'BANNER'}}
    if translation is None:
        return hits
    dx,dy = translation
    def point(px,py):
        return wx+px+dx,wy+py+dy
    def inside(px,py):
        return 4 <= px+dx <= w-4 and 4 <= py+dy <= h-4
    # Only draw on-screen portions of the route; no assumed bottom-door positions.
    if room<=6:
        l,t,r,b=x-24,y-75,x+24,y-7
        label='DOWN WARP'
    else:
        l,t,r,b=x-58,y-157,x+58,y-5
        label=f'FM {room}'
    if inside(l,t) and inside(r,b):
        hits[label]={'box':(*point(l,t),*point(r,b)),'mode':'PORTAL'}
    # Direction arrows along the rope and platform, away from door labels.
    start_y=368
    end_y=y-30
    for name,a,b in (
        ('rope',(ENTRANCE_ROPE_X,start_y),(ENTRANCE_ROPE_X,end_y)),
        ('side',(ENTRANCE_ROPE_X,end_y),(x,end_y)),
    ):
        if inside(*a) and inside(*b) and a!=b:
            hits[name]={'box':(*point(*a),*point(*b)),'mode':'ARROW'}
    return hits


class EntranceGuidePin(OverlayPin):
    """Green, click-through entrance guidance. Only over focused game."""
    def draw_markers(self,w,h,sw,sh,hits):
        c=self.canvas;c.delete('all')
        sx,sy=w/sw,h/sh
        for name,hit in hits.items():
            if hit['mode']=='BANNER':
                continue
            l,t,r,b=hit['box']
            box=(l*sx,t*sy,r*sx,b*sy)
            if hit['mode']=='ARROW':
                for color,width in (('#17231b',9),('#72ff86',4)):
                    c.create_line(*box,fill=color,width=width,arrow='last',arrowshape=(11,15,7))
            elif hit['mode']=='PORTAL':
                c.create_rectangle(*box,outline='#15241c',width=7)
                c.create_rectangle(*box,outline='#72ff86',width=3)
        for name,hit in hits.items():
            if hit['mode']!='BANNER':
                continue
            l,t,r,b=hit['box']
            l,t,r,b=l*sx,t*sy,r*sx,b*sy
            c.create_rectangle(l,t,r,b,fill='#15241c',outline='#72ff86',width=2)
            c.create_text((l+r)/2,(t+b)/2,text=name,fill='#72ff86',
                          font=('Segoe UI',11,'bold'),width=max(1,r-l-12))
