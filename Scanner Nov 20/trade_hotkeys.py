"""Windows global hotkeys enqueue app actions; never send game keystrokes."""
import sys
import threading

class TradeHotkeys(threading.Thread):
    def __init__(self,post):
        super().__init__(daemon=True);self.post=post;self.thread_id=None;self.stopping=threading.Event()
    def run(self):
        if sys.platform!='win32':return
        import ctypes
        from ctypes import wintypes
        user=ctypes.windll.user32;kernel=ctypes.windll.kernel32
        user.GetMessageW.argtypes=[ctypes.POINTER(wintypes.MSG),wintypes.HWND,wintypes.UINT,wintypes.UINT]
        self.thread_id=kernel.GetCurrentThreadId()
        registered=[]
        try:
            for key_id,key,action in [(2,ord('F'),'trade_find'),(3,ord('N'),'trade_next')]:
                if user.RegisterHotKey(None,key_id,0x4000|0x0002|0x0001,key):registered.append((key_id,action))
                else:self.post(('status','Hotkey unavailable: Ctrl+Alt+'+chr(key)+'; use the app button.'))
            msg=wintypes.MSG()
            while not self.stopping.is_set() and user.GetMessageW(ctypes.byref(msg),None,0,0)>0:
                if msg.message==0x0312:
                    for key_id,action in registered:
                        if msg.wParam==key_id:self.post((action,))
        finally:
            for key_id,_ in registered:user.UnregisterHotKey(None,key_id)
    def close(self):
        self.stopping.set()
        if self.thread_id:
            import ctypes
            ctypes.windll.user32.PostThreadMessageW(self.thread_id,0x0012,0,0)
