import queue
import unittest
from transition_screenshot import Blackout, TransitionScreenshotRecorder, classify

class TransitionScreenshotTests(unittest.TestCase):
    def test_first_bright_once_and_rearm(self):
        s=Blackout()
        self.assertFalse(s.observe(False))
        self.assertFalse(s.observe(True))
        self.assertFalse(s.observe(True))
        self.assertTrue(s.observe(False))
        s.consumed()
        self.assertFalse(s.observe(False))
        self.assertFalse(s.observe(True))
        self.assertFalse(s.observe(True))
        self.assertTrue(s.observe(False))
    def test_startup_black_and_focus_reset(self):
        s=Blackout()
        for value in (True,True,False):self.assertFalse(s.observe(value))
        s.observe(True);s.observe(True);s.reset()
        self.assertFalse(s.observe(False))
    def test_majority_and_unknown(self):
        self.assertIs(classify([1,1,0]),True)
        self.assertIs(classify([0,0,1]),False)
        self.assertIsNone(classify([0,1,None]))
        self.assertIsNone(classify([.85,.85,.85]))
    def test_capture_only_on_first_bright(self):
        r=TransitionScreenshotRecorder.__new__(TransitionScreenshotRecorder)
        client=(0,0,1280,720);r.request=(1,client);r.focused=lambda h:True;r.geometry=lambda h:client
        r.pending=queue.Queue();r.error=None
        calls=[];light=[255]
        def capture(rect,**kw):
            calls.append(rect);w,h=rect[2:];return bytes([light[0]])*(w*h*3),w,h,w*3
        r.capture=capture;s=Blackout()
        r._step(r.request,s)
        light[0]=0
        r._step(r.request,s);r._step(r.request,s)
        self.assertNotIn(client,calls)
        light[0]=255;r._step(r.request,s)
        self.assertEqual(calls.count(client),1)
        self.assertEqual(r.pending.qsize(),1)
        r._step(r.request,s)
        self.assertEqual(calls.count(client),1)
    def test_full_black_rejected(self):
        r=TransitionScreenshotRecorder.__new__(TransitionScreenshotRecorder)
        client=(0,0,1280,720);r.request=(1,client);r.focused=lambda h:True;r.geometry=lambda h:client
        r.pending=queue.Queue();r.error=None
        r.capture=lambda rect,**kw:(bytes([0 if rect==client else 255])*(rect[2]*rect[3]*3),rect[2],rect[3],rect[2]*3)
        s=Blackout();s.observe(False);s.observe(True);s.observe(True)
        r._step(r.request,s)
        self.assertEqual(r.pending.qsize(),0)
        self.assertTrue(s.armed)

if __name__=='__main__':unittest.main()
