"""Large click-through Windows shop markers, positioned in selected-window pixels."""
import sys
import ctypes
import tkinter as tk
from window_capture import window_rect

class ShopPin:
    def __init__(self,master):
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
        self.timer=self.window.after(80,self.follow)

    def show(self,hwnd,size,box,name,likely=False):
        self.show_many(hwnd,size,{name:{'box':box,'mode':'CONFUSABLE' if likely else 'EXACT'}})

    def show_many(self,hwnd,size,hits):
        self.data=(hwnd,size,dict(hits)) if hits else None
        if not hits:self.window.withdraw();self.visible=False;self.drawn=None
        else:self.follow(schedule=False)

    def hide(self):
        self.data=None
        self.window.withdraw();self.visible=False;self.drawn=None

    def draw_markers(self,w,h,sw,sh,hits):
        c=self.canvas;c.delete('all')
        sx,sy=w/sw,h/sh
        groups=[]
        for name,hit in hits.items():
            x,y,r,b=hit['box']
            group=None
            for candidate in groups:
                l,t,q,d=candidate['box']
                intersection=max(0,min(r,q)-max(x,l))*max(0,min(b,d)-max(y,t))
                union=(r-x)*(b-y)+(q-l)*(d-t)-intersection
                if union>0 and intersection/union>.55:group=candidate;break
            if group is None:groups.append({'box':hit['box'],'names':[name],'likely':hit['mode']!='EXACT'})
            else:group['names'].append(name);group['likely']=True
        for hit in groups:
            name=' / '.join(hit['names'])
            x,y,r,b=hit['box'];cx=(x+r)/2*sx
            left=max(6,cx-58*sx);right=min(w-6,cx+58*sx)
            top=max(2,y*sy-95*sy);bottom=min(h-6,b*sy+16*sy)
            likely=hit['likely']
            for color,width in [('#000000',14),('#ffffff',10),('#ff1744',7)]:
                c.create_rectangle(left,top,right,bottom,outline=color,width=width,
                                   dash=(12,5) if likely else ())
            end=max(6,top-5);start=max(2,end-62)
            for color,width in [('#000000',18),('#ffffff',13),('#ff1744',9)]:
                c.create_line(cx,start,cx,end,fill=color,width=width,
                              arrow='last',arrowshape=(24,30,16))
            label=name+(' · CHECK NAME' if likely else ' · HERE')
            tx=min(max(80,cx),max(80,w-80));ty=(max(16,top-82) if top>=100 else min(h-18,bottom+24))
            text=c.create_text(tx,ty,text=label,fill='white',font=('Segoe UI',14,'bold'),width=min(450,w-20),justify='center')
            bounds=c.bbox(text)
            if bounds:
                l,t,r,b=bounds
                badge=c.create_rectangle(l-7,t-4,r+7,b+4,fill='#a12d00' if likely else '#d00025',outline='white',width=2)
                c.tag_lower(badge,text)

    def follow(self,schedule=True):
        if self.closed:return
        if self.data and self.ready:
            hwnd,(sw,sh),hits=self.data
            user=ctypes.windll.user32
            rect=window_rect(hwnd)
            if rect and not user.IsIconic(hwnd) and user.GetForegroundWindow()==hwnd:
                left,top,w,h=rect
                if rect!=self.last_rect:
                    self.window.geometry(f'{w}x{h}{left:+d}{top:+d}');self.last_rect=rect
                drawing=(w,h,sw,sh,tuple(sorted((name,tuple(hit['box']),hit['mode']) for name,hit in hits.items())))
                if drawing!=self.drawn:
                    self.draw_markers(w,h,sw,sh,hits);self.drawn=drawing
                if not self.visible:self.window.deiconify();self.visible=True
                user.SetWindowPos(self.hwnd,-1,left,top,w,h,0x0010|0x0040)
            elif self.visible:self.window.withdraw();self.visible=False
        if schedule:self.timer=self.window.after(80,self.follow)

    def close(self):
        self.closed=True
        try:self.window.after_cancel(self.timer)
        except tk.TclError:pass
        self.window.destroy()
