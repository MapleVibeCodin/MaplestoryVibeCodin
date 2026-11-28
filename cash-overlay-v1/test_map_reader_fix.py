import unittest
from types import SimpleNamespace
from map_reader_fix import patch_reader_source,stable_map_timestamp
class MapReaderTests(unittest.TestCase):
    def test_hidden_guard(self):
        s="        if self.own_rect is None:\n            return None, None                   # wait until we know where this app's window is\n        wx, wy = 1, 2\n"
        self.assertEqual(patch_reader_source(s),"        wx, wy = 1, 2\n")
        with self.assertRaises(ValueError):patch_reader_source("different upstream")
    def test_stable_refresh(self):
        r=SimpleNamespace(map_box=(1,2,3,4),map_unread=False,map_print=True,map_look={"text":"A"},map_seen_at=100)
        self.assertEqual(stable_map_timestamp(r,"A",101),100)
        r.map_seen_at=160
        self.assertEqual(stable_map_timestamp(r,"A",161),160)
    def test_transition_and_stale(self):
        r=SimpleNamespace(map_box=(1,2,3,4),map_unread=True,map_print=True,map_look={"text":"A"},map_seen_at=100)
        self.assertIsNone(stable_map_timestamp(r,"A",101))
        r.map_unread=False
        self.assertIsNone(stable_map_timestamp(r,"A",104))
        self.assertIsNone(stable_map_timestamp(r,None,101))
        r.map_box=None
        self.assertIsNone(stable_map_timestamp(r,"A",101))
if __name__=="__main__":unittest.main()
