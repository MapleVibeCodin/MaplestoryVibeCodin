import unittest
import numpy as np
from fm_entry_gate import EntryGate, minimap_signature, difference

class TestEntryGate(unittest.TestCase):
    def test_in_room_only_after_minimap_transition(self):
        entrance=np.full((600,1000,3),140,np.uint8)
        # Fixed minimap graphic (all channels share this map layout).
        entrance[94:156,20:135]=80
        entrance[105:120,40:90]=210
        room=entrance.copy()
        room[94:156,20:135]=200
        room[106:114,44:80]=40
        gate=EntryGate()
        gate.reset()
        self.assertFalse(gate.observe(entrance))
        self.assertFalse(gate.observe(entrance))
        self.assertFalse(gate.observe(entrance))
        self.assertFalse(gate.observe(room))
        self.assertTrue(gate.observe(room))
        self.assertFalse(gate.observe(room))
        self.assertTrue(gate.entered)

    def test_camera_movement_does_not_trigger(self):
        baseline=np.full((600,1000,3),130,np.uint8)
        baseline[94:156,20:135]=80
        moving=baseline.copy()
        moving[:,300:]=245   # giant scene motion outside minimap
        gate=EntryGate();gate.reset();gate.observe(baseline)
        for _ in range(5): self.assertFalse(gate.observe(moving))
        self.assertFalse(gate.entered)

    def test_loading_fade_does_not_trigger(self):
        baseline=np.full((600,1000,3),100,np.uint8)
        room=np.full((600,1000,3),230,np.uint8)
        gate=EntryGate();gate.reset();gate.observe(baseline)
        for _ in range(4): self.assertFalse(gate.observe(np.zeros_like(baseline)))
        self.assertFalse(gate.observe(room))
        self.assertTrue(gate.observe(room))

    def test_old_user_screenshots_have_visible_minimap_change(self):
        # Integrated screenshots are not bundled in the distributed app.
        from pathlib import Path
        import cv2
        root=Path(__file__).parent.parent
        a=root/'Screenshot 2026-11-12 040409.png'
        b=root/'Screenshot 2026-11-12 040451.png'
        if not a.exists() or not b.exists():
            self.skipTest('Reference screenshots not available beside test install')
        first=cv2.imread(str(a))[0:700,5:1180]
        second=cv2.imread(str(b))[0:700,5:1180]
        gap=difference(minimap_signature(first),minimap_signature(second))
        self.assertGreater(gap,.11)

if __name__=='__main__':unittest.main()
