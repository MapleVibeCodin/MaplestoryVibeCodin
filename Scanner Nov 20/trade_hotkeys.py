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
        shop_shortcuts = []
        try:
            ctrl_alt = 0x0002 | 0x0001
            shift = 0x0004
            shortcuts = (
                (2, 'F', ctrl_alt, 'trade_find'),
                (3, 'N', ctrl_alt, 'trade_next'),
                (4, 'M', ctrl_alt, 'trade_move_pointer'),
                (5, 'C', ctrl_alt, 'trade_move_channel'),
                (6, '1', shift, 'trade_lock'),
                (7, '2', shift, 'trade_unlock'),
                (8, 'J', ctrl_alt, 'trade_move_pointer'),
            )
            for key_id, key, modifiers, action in shortcuts:
                label = 'Shift' if modifiers == shift else 'Ctrl+Alt'
                shortcut = f'{label}+{key}'
                if user.RegisterHotKey(None, key_id, 0x4000 | modifiers, ord(key)):
                    registered.append((key_id, action))
                    if action == 'trade_move_pointer':
                        shop_shortcuts.append(shortcut)
                elif action != 'trade_move_pointer':
                    self.post(('status', f'Hotkey unavailable · {shortcut}'))
            self.post(('shop_pointer_shortcuts', tuple(shop_shortcuts)))
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
