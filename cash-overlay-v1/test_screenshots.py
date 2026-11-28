import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from screenshots import ScreenshotStore, encode_lossless, lossless_webp
from scene_analysis import screenshot_files

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

    def test_real_webp_pixel_equality(self):
        import cv2
        import numpy as np
        img = np.random.default_rng(17).integers(0,256,(73,91,3),dtype=np.uint8)
        encoded = encode_lossless(img)
        self.assertTrue(lossless_webp(encoded), "Expected functioning lossless WebP encoder")
        decoded = cv2.imdecode(np.frombuffer(encoded,np.uint8),cv2.IMREAD_UNCHANGED)
        self.assertTrue(np.array_equal(img,decoded))
        with tempfile.TemporaryDirectory() as d:
            s = ScreenshotStore(d,min_free=0)
            p = s.save(encoded)
            self.assertEqual(p.suffix,".webp")
            self.assertEqual(p.read_bytes(),encoded)
            old = s.save(PNG)
            self.assertEqual(old.suffix,".png")
            self.assertEqual(set(screenshot_files(Path(d))),{p,old})

    def test_lossy_webp_rejected(self):
        import cv2
        import numpy as np
        img = np.random.default_rng(18).integers(0,256,(64,64,3),dtype=np.uint8)
        ok, packed = cv2.imencode(".webp",img,[cv2.IMWRITE_WEBP_QUALITY,75])
        self.assertTrue(ok)
        self.assertFalse(lossless_webp(packed.tobytes()))
        with tempfile.TemporaryDirectory() as d:
            s = ScreenshotStore(d,min_free=0)
            with self.assertRaises(ValueError): s.save(packed.tobytes())

    def test_png_fallback(self):
        from unittest.mock import patch
        import cv2
        import numpy as np
        img = np.zeros((16,16,3),dtype=np.uint8)
        original = cv2.imencode
        def encode(ext,*args,**kwargs):
            return (False,None) if ext == ".webp" else original(ext,*args,**kwargs)
        with patch("cv2.imencode",side_effect=encode):
            data = encode_lossless(img)
        self.assertTrue(data.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertTrue(np.array_equal(cv2.imdecode(np.frombuffer(data,np.uint8),-1),img))

if __name__ == "__main__":
    unittest.main()
