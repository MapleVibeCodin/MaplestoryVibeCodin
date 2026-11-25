"""Regression checks for the independent screenshot recorder."""
import struct
import tempfile
import unittest
import zlib
from datetime import datetime
from pathlib import Path
from shop_screenshot import ShopOpenState, crop, encode_png, save_png, gate_quality
from shop_inventory import GREEN, ORANGE


class ScreenshotTests(unittest.TestCase):
    def test_one_per_open(self):
        s=ShopOpenState()
        self.assertTrue(s.observe(True))
        s.mark_saved()
        for _ in range(100):
            self.assertFalse(s.observe(True))
        self.assertFalse(s.observe(False))
        self.assertFalse(s.observe(True))
        self.assertFalse(s.observe(False))
        self.assertFalse(s.observe(False))
        self.assertTrue(s.observe(True))

    def test_capture_failure_not_close(self):
        s=ShopOpenState()
        s.mark_saved()
        for _ in range(5):
            self.assertFalse(s.observe(None))
        self.assertFalse(s.observe(True))

    def test_retry_before_enqueue(self):
        s=ShopOpenState()
        self.assertTrue(s.observe(True))
        self.assertTrue(s.observe(True))
        s.mark_saved()
        self.assertFalse(s.observe(True))

    def test_png_native_rgb_and_padding(self):
        frame=(bytes([3,2,1,6,5,4,99,99,9,8,7,12,11,10,99,99]),2,2,8)
        png=encode_png(frame)
        self.assertEqual(png[:8],b'\x89PNG\r\n\x1a\n')
        self.assertEqual(struct.unpack('>II',png[16:24]),(2,2))
        pos=8; data=b''
        while pos<len(png):
            n=struct.unpack('>I',png[pos:pos+4])[0]
            kind=png[pos+4:pos+8]; payload=png[pos+8:pos+8+n]
            self.assertEqual(struct.unpack('>I',png[pos+8+n:pos+12+n])[0],
                             zlib.crc32(kind+payload)&0xffffffff)
            if kind==b'IDAT':data+=payload
            pos+=12+n
        self.assertEqual(zlib.decompress(data),bytes([0,1,2,3,4,5,6,0,7,8,9,10,11,12]))
        self.assertEqual(crop(frame,1,0,1,2),(bytes([6,5,4,12,11,10]),1,2,3))
        self.assertIsNone(crop(frame,1,0,2,2))

    def test_invalid_frame(self):
        with self.assertRaises(ValueError):
            encode_png((b'abc',2,2,6))

    def test_unique_atomic_files(self):
        with tempfile.TemporaryDirectory() as d:
            stamp=datetime(2026,11,26,1,2,3)
            frame=(b'\x03\x02\x01',1,1,3)
            a=save_png(d,frame,stamp,'exact')
            b=save_png(d,frame,stamp,'exact')
            self.assertNotEqual(a,b)
            self.assertEqual(a.parent.name,'2026-11-26')
            self.assertEqual(a.read_bytes(),encode_png(frame))
            self.assertEqual(len(list(Path(d).rglob('*.png'))),2)
            self.assertFalse(list(Path(d).rglob('*.part')))

    def test_exact_gate_on_saved_frame(self):
        w,h=400,400; stride=w*3
        buf=bytearray(stride*h)
        ax,ay=160,10
        for dy,strip,lead in [(0,GREEN,b'\x11\xb3\x97'),
                              (31,ORANGE,b'\x1c\x75\xd8'),
                              (51,ORANGE,b'\x1c\x75\xd8')]:
            at=(ay+dy)*stride+ax*3
            buf[at-3:at]=lead
            buf[at:at+len(strip)]=strip
        self.assertEqual(gate_quality((bytes(buf),w,h,stride),(ax,ay)),'exact')
        self.assertEqual(gate_quality((bytes(buf),w,h,stride),(ax+1,ay)),'exact')
        self.assertIsNone(gate_quality((bytes(stride*h),w,h,stride),(ax,ay)))


if __name__=='__main__':
    unittest.main()
