"""Faster timing still requires a brightness plateau, never a fade frame."""
import unittest
import numpy as np
from fm_entry_gate import SnapshotGate
from window_capture import WindowFrames

class FastGateTests(unittest.TestCase):
    def test_trigger_on_second_stable_sample_and_only_once(self):
        gate=SnapshotGate(settle_seconds=0.0)
        frame=lambda n:np.full((600,1000,3),n,np.uint8)
        self.assertFalse(gate.observe(frame(0),0.))
        self.assertTrue(gate.loading)
        for t,v in [(.016,40),(.032,80),(.048,130),(.064,180)]:
            self.assertFalse(gate.observe(frame(v),t))
        self.assertTrue(gate.observe(frame(180),.080))
        self.assertFalse(gate.loading)
        self.assertFalse(gate.observe(frame(180),.096))
        self.assertFalse(gate.observe(frame(0),.112))
        self.assertTrue(gate.invalidated)
        self.assertFalse(gate.observe(frame(180),.128))
        self.assertTrue(gate.observe(frame(180),.144))

    def test_capture_copy_rate_is_bounded(self):
        self.assertEqual(WindowFrames(1).interval_ms,16)
        self.assertEqual(WindowFrames(1,interval_ms=1).interval_ms,16)
        self.assertEqual(WindowFrames(1,interval_ms=100).interval_ms,100)
