"""Small click-through Windows marker, positioned in selected-window pixels."""
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
        self.data=(hwnd,size,box,name,likely)
        self.follow(schedule=False)

    def hide(self):
        self.data=None
        self.window.withdraw()

    def follow(self,schedule=True):
        if self.closed:return
        if self.data and self.ready:
            hwnd,(sw,sh),(x,y,r,b),name,likely=self.data
            user=ctypes.windll.user32
            rect=window_rect(hwnd)
            if rect and not user.IsIconic(hwnd) and user.GetForegroundWindow()==hwnd:
                left,top,w,h=rect
                sx,sy=w/sw,h/sh
                px=round(left+x*sx)-10;py=round(top+y*sy)-36
                rw=max(36,round((r-x)*sx)+20);rh=max(12,round((b-y)*sy)+12)
                ww=max(rw,len(name)*9+95);hh=rh+38
                self.window.geometry(f'{ww}x{hh}{px:+d}{py:+d}')
                c=self.canvas;c.delete('all')
                color='#ffcc00' if likely else '#00ffd0'
                c.create_rectangle(3,30,rw-3,hh-3,outline='#000000',width=6)
                c.create_rectangle(3,30,rw-3,hh-3,outline=color,width=3)
                c.create_text(5,12,anchor='w',text=name+(' ? CHECK' if likely else ' HERE'),fill=color,font=('Segoe UI',11,'bold'))
                self.window.deiconify()
                user.SetWindowPos(self.hwnd,-1,px,py,ww,hh,0x0010|0x0040)
            else:self.window.withdraw()
        if schedule:self.timer=self.window.after(80,self.follow)

    def close(self):
        self.closed=True
        try:self.window.after_cancel(self.timer)
        except tk.TclError:pass
        self.window.destroy()
