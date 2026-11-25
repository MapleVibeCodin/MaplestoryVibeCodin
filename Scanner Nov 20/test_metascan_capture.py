import random
import unittest
from unittest.mock import patch
from metascan_fast import purple_run, crop_bgr
from shop_inventory import ShopInventoryTracker, GREEN, ORANGE, tooltip_blocked_rows, sold_row_mask
from camera_alignment import room_title_present, _ROOM_PREFIX_BITS, _ROOM_BRACKET_BITS

class FastCaptureTests(unittest.TestCase):
    def test_tooltip_exact_random_and_boundaries(self):
        rng=random.Random(19)
        def reference(p):
            run=0
            for i in range(0,len(p),3):
                b,g,r=p[i:i+3]
                run=run+1 if 40<b and r<145 and g<145 and b-r>28 and b-g>23 else 0
                if run>=12:return True
            return False
        for i in range(5000):
            p=bytearray(rng.randbytes(158*3))
            if i%5==0:
                start=rng.randrange(146)
                p[start*3:(start+12)*3]=bytes((124,74,68))*12
            self.assertEqual(purple_run(bytes(p)),reference(p))
        self.assertFalse(purple_run(bytes((124,74,68))*11))
        self.assertTrue(purple_run(bytes((124,74,68))*12))
        self.assertFalse(purple_run(bytes((20,20,20))*158))
    def test_crop_padding_and_clipping(self):
        data=bytes(range(24))
        self.assertEqual(crop_bgr((data,3,2,12),1,0,2,2),(data[3:9]+data[15:21],2,2,6))
        self.assertIsNone(crop_bgr((data,3,2,12),2,0,2,2))
    def combined(self):
        w,h,s=220,334,660
        b=bytearray(bytes((227,217,205))*w*h)
        for dy,pattern in ((0,GREEN),(31,ORANGE),(51,ORANGE)):
            at=(1+dy)*s+140*3
            b[at-3:at]=bytes((17,179,151)) if dy==0 else bytes((28,117,216))
            b[at:at+len(pattern)]=pattern
        return bytes(b),w,h,s
    def test_paired_one_capture_and_exact_inventory(self):
        t=ShopInventoryTracker.__new__(ShopInventoryTracker)
        f=self.combined()
        with patch('shop_inventory.capture_client',return_value=f) as capture:
            quality,rows=t._capture_pair((10,20,1366,768),(568,214))
        self.assertEqual(quality,'exact')
        self.assertEqual(rows,crop_bgr(f,0,71,204,263))
        capture.assert_called_once_with((438,233,220,334),allow_crop=True)
    def test_pair_rejects_missing_gate_and_failed_capture(self):
        t=ShopInventoryTracker.__new__(ShopInventoryTracker)
        for bad in (None,(bytes(220*334*3),220,334,660)):
            with patch('shop_inventory.capture_client',return_value=bad):
                self.assertEqual(t._capture_pair((0,0,1366,768),(568,214)),(None,None))
    def test_room_crop_preserves_full_search_bounds(self):
        w,h=200,120
        b=bytearray(w*h*3)
        for y,(p,q) in enumerate(zip(_ROOM_PREFIX_BITS,_ROOM_BRACKET_BITS),50):
            bits=p|(q<<70)
            for x in range(79):
                if bits>>x&1:b[(y*w+56+x)*3:(y*w+56+x)*3+3]=b'\xff'*3
        full=(bytes(b),w,h,w*3)
        self.assertTrue(room_title_present(*full))
        self.assertEqual(room_title_present(*crop_bgr(full,0,0,135,59)),room_title_present(*full))

if __name__=='__main__':unittest.main()
