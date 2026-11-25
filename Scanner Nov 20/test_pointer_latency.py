"""Offline pointer regressions; no desktop/game, tkinter or OCR required."""
import ast
from pathlib import Path
import queue
import threading
import types
import unittest

METHODS={'_pointer_context','move_pointer_to_target','drain_trade_events','_watch_pointer'}

def harness(focused=True):
    source=Path(__file__).with_name('fm_rush.py').read_text(encoding='utf-8')
    tree=ast.parse(source)
    app=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='FMApp')
    selected=[n for n in app.body if isinstance(n,ast.FunctionDef) and n.name in METHODS]
    assert len(selected)==len(METHODS)
    cls=ast.ClassDef(name='App',bases=[],keywords=[],body=selected,decorator_list=[])
    module=ast.fix_missing_locations(ast.Module(body=[cls],type_ignores=[]))
    state=types.SimpleNamespace(now=1.0,focus=focused,window=(100,200,1366,768),
        client=(103,240,1366,768),moves=[],jobs=[],messages=[],refreshes=0,hwnd=99,pos=(120,230),events=[])
    def move(hwnd,x,y):
        state.moves.append((hwnd,x,y))
        state.pos=(x,y)
    ns={'time':types.SimpleNamespace(perf_counter=lambda:state.now),'queue':queue,
        'window_rect':lambda hwnd:state.window,'window_client_rect':lambda hwnd:state.client,
        'window_has_focus':lambda hwnd:state.focus,'move_cursor_on_screen':move,
        'cursor_screen_position':lambda:state.pos}
    exec(compile(module,str(Path(__file__)), 'exec'),ns)
    a=ns['App']()
    deal=types.SimpleNamespace(cc=4,fm=18,shop_position={'left':4,'top':5},sold=False)
    a.archive=types.SimpleNamespace(chase_locked=True,focus='a',lock=threading.RLock(),current=lambda:('a',deal))
    a.shop=types.SimpleNamespace(selected_hwnd=lambda:state.hwnd,notice=types.SimpleNamespace(get=lambda:'unavailable'))
    a.status=types.SimpleNamespace(set=state.messages.append,get=lambda:state.messages[-1] if state.messages else '')
    a.performance=types.SimpleNamespace(active='attempt',marker=lambda event,**data:state.events.append((event,data)))
    a._pointer_serial=0
    a._pointer_pending=None
    a._closing=False
    a._portal_alignment=None
    a._trade_events=queue.Queue()
    a._shop_preview=(99,state.window[2:],(10,20,30,40))
    a._channel_preview=(99,state.window[2:],4,(50,60,70,80),'GUIDE')
    def refresh(current):state.refreshes+=1
    a.refresh_overlays=refresh
    a.root=types.SimpleNamespace(state=lambda:'normal',focus_force=lambda:None)
    a.schedule=lambda ms,cb:state.jobs.append((ms,cb))
    def tick():
        delay,cb=state.jobs.pop(0)
        state.now+=delay/1000
        cb()
    return a,state,tick

class PointerLatencyTests(unittest.TestCase):
    def test_unfocused_moves_once(self):
        a,s,_=harness(False)
        a.move_pointer_to_target('shop')
        self.assertEqual(s.moves,[(99,120,230)])
        self.assertEqual(s.refreshes,1)
        self.assertIn('queue',s.messages[-1])

    def test_focus_readiness_preserves_box(self):
        a,s,tick=harness()
        a.move_pointer_to_target('channel')
        self.assertEqual(s.jobs[0][0],5)
        tick()
        self.assertFalse(s.moves)
        s.focus=False
        tick()
        self.assertEqual(s.moves,[(99,160,270)])
        self.assertEqual(s.refreshes,1)

    def test_focus_timeout(self):
        a,s,tick=harness()
        a.move_pointer_to_target('shop')
        for _ in range(20):
            if not s.jobs:break
            tick()
        self.assertFalse(s.moves)
        self.assertFalse(s.jobs)
        self.assertIn('kept focus',s.messages[-1])

    def test_geometry_change_rejected(self):
        a,s,tick=harness()
        a.move_pointer_to_target('shop')
        s.focus=False
        s.client=(104,240,1366,768)
        tick()
        self.assertFalse(s.moves)

    def test_unlock_rejected(self):
        a,s,tick=harness()
        a.move_pointer_to_target('shop')
        a.archive.chase_locked=False
        s.focus=False
        tick()
        self.assertFalse(s.moves)

    def test_superseded_request(self):
        a,s,tick=harness()
        a.move_pointer_to_target('shop')
        a.move_pointer_to_target('channel')
        s.focus=False
        tick();tick()
        self.assertEqual(s.moves,[(99,160,270)])

    def test_expired_request(self):
        a,s,_=harness(False)
        a._trade_events.put_nowait((s.now-.2,('trade_move_pointer',)))
        a.drain_trade_events()
        self.assertFalse(s.moves)
        self.assertEqual(s.refreshes,0)

    def test_no_preview(self):
        a,s,_=harness(False)
        a._shop_preview=None
        a.move_pointer_to_target('shop')
        self.assertFalse(s.moves)

    def test_pending_duplicate_keeps_first_request(self):
        a,s,tick=harness()
        a.move_pointer_to_target('shop')
        a.move_pointer_to_target('shop')
        self.assertEqual(s.refreshes,1)
        self.assertEqual(len(s.jobs),1)
        self.assertTrue(any(e=='pointer_duplicate' for e,_ in s.events))
        s.focus=False
        tick()
        self.assertEqual(s.moves,[(99,120,230)])

    def test_focus_and_displacement_are_read_only(self):
        a,s,tick=harness(False)
        a.move_pointer_to_target('shop')
        s.focus=True
        tick()
        self.assertTrue(any(e=='pointer_game_focus' and d['on_target'] for e,d in s.events))
        s.pos=(300,300)
        tick()
        self.assertTrue(any(e=='pointer_displaced' for e,_ in s.events))
        self.assertEqual(s.moves,[(99,120,230)])

    def test_watch_stops_on_unlock(self):
        a,s,tick=harness(False)
        a.move_pointer_to_target('shop')
        a.archive.chase_locked=False
        s.focus=True
        tick()
        self.assertFalse(s.jobs)
        self.assertFalse(any(e=='pointer_game_focus' for e,_ in s.events))

if __name__=='__main__':unittest.main()
