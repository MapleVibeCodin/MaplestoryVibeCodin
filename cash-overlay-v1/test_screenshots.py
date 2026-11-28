import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from screenshots import ScreenshotStore

PNG = b"\x89PNG\r\n\x1a\n" + b"test-data"
class ScreenshotTests(unittest.TestCase):
    def test_distinct_paths_even_same_timestamp(self):
        with tempfile.TemporaryDirectory() as d:
            s = ScreenshotStore(d, min_free=0)
            when = datetime(2026, 11, 28, tzinfo=timezone.utc)
            a = s.save(PNG, when)
            b = s.save(PNG, when)
            self.assertNotEqual(a,b)
            self.assertEqual(a.read_bytes(),PNG)
            self.assertEqual(b.read_bytes(),PNG)
            self.assertFalse(list(s.folder.glob("*.part")))
    def test_relaunch_preserves_prior(self):
        with tempfile.TemporaryDirectory() as d:
            a = ScreenshotStore(d, min_free=0)
            p = a.save(PNG)
            b = ScreenshotStore(d, min_free=0)
            self.assertNotEqual(a.folder,b.folder)
            self.assertTrue(p.exists())
    def test_low_space_no_deletion(self):
        with tempfile.TemporaryDirectory() as d:
            s = ScreenshotStore(d, min_free=0)
            p = s.save(PNG)
            s.min_free = 10**30
            self.assertIsNone(s.save(PNG))
            self.assertTrue(p.exists())
    def test_reject_non_png(self):
        with tempfile.TemporaryDirectory() as d:
            s = ScreenshotStore(d,min_free=0)
            with self.assertRaises(ValueError): s.save(b"not png")
            self.assertFalse(list(s.folder.iterdir()))

if __name__ == "__main__":
    unittest.main()
