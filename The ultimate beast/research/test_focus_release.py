import unittest
from fm_sprint import focus_release_pointer

class Fake:
    def __init__(self):
        self.t=0.;self.jobs=[];self.game=True;self.scanner=False;self.valid=True
        self.focus_calls=0;self.moves=0;self.result=[];self.move_ok=True
    def schedule(self,delay,fn):self.jobs.append((delay,fn))
    def focus(self):self.focus_calls+=1
    def move(self):self.moves+=1;return self.move_ok
    def begin(self):focus_release_pointer(schedule=self.schedule,now=lambda:self.t,
        valid=lambda:self.valid,game_focused=lambda:self.game,scanner_focused=lambda:self.scanner,
        focus_scanner=self.focus,move=self.move,done=lambda *x:self.result.append(x))
    def tick(self):
        delay,fn=self.jobs.pop(0);self.t+=delay/1000;fn()
    def release(self):self.game=False;self.scanner=True

class FocusTests(unittest.TestCase):
    def test_focused_game_never_moves_until_release(self):
        f=Fake();f.begin();f.tick();self.assertEqual(f.moves,0)
        f.release();f.tick();self.assertEqual(f.moves,1);self.assertEqual(f.result,[(True,'moved')])
    def test_no_manual_unfocus_request(self):
        f=Fake();f.begin();self.assertEqual(f.focus_calls,1);f.release();f.tick();self.assertFalse(f.jobs)
    def test_focus_timeout(self):
        f=Fake();f.begin()
        while f.jobs:f.tick()
        self.assertEqual(f.moves,0);self.assertEqual(f.result,[(False,'focus_timeout')])
    def test_cancel_when_target_changes(self):
        f=Fake();f.begin();f.valid=False;f.release();f.tick();self.assertEqual(f.moves,0)
        self.assertEqual(f.result,[(False,'target_changed')])
    def test_invalid_before_focus(self):
        f=Fake();f.valid=False;f.begin();self.assertEqual(f.focus_calls,0)
    def test_third_party_focus(self):
        f=Fake();f.begin();f.game=False;f.tick();self.assertEqual(f.moves,0)
        self.assertEqual(f.result,[(False,'other_window_focused')])
    def test_move_failure(self):
        f=Fake();f.begin();f.release();f.move_ok=False;f.tick();self.assertEqual(f.result,[(False,'move_failed')])
    def test_focus_failure(self):
        f=Fake();f.focus=lambda:(_ for _ in ()).throw(RuntimeError());f.begin();self.assertFalse(f.jobs)
        self.assertEqual(f.result,[(False,'focus_request_failed')])

if __name__=='__main__':unittest.main()
