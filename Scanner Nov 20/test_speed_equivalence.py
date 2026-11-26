"""Differential tests for vectorized preprocessing; no live game required."""
import unittest
from unittest.mock import patch
import shop_inventory as inv


@unittest.skipIf(inv.np is None, "NumPy unavailable; original implementation remains active")
class SpeedEquivalenceTests(unittest.TestCase):
    def test_exact_pixels_and_tooltip_rows(self):
        np=inv.np
        rng=np.random.default_rng(77)
        frames=[rng.integers(0,256,(263,204,3),dtype=np.uint8) for _ in range(5)]
        for color in [(227,217,205),(248,243,242),(40,152,230),(124,75,70)]:
            a=np.empty((263,204,3),np.uint8);a[:]=color
            a[30:45,55:68]=0
            frames.append(a)
        # Precise run boundary and bridging of distinct blocked rows.
        for width in (11,12,13):
            a=np.full((263,204,3),227,np.uint8)
            a[26:29,40:40+width]=(124,75,70)
            a[106:109,40:52]=(124,75,70)
            frames.append(a)
        for pixels in frames:
            for pad in (0,4):
                buf=np.pad(pixels.reshape(263,612),((0,0),(0,pad))).tobytes()
                frame=(buf,204,263,612+pad)
                self.assertEqual(inv.tooltip_blocked_rows(frame),inv._tooltip_blocked_rows_python(frame))
                for sections,delta,prefixes in [(None,0,{}),({0,2,4},15,{}),({1,3},0,{1:152,3:100}),({-1},-10,{})]:
                    self.assertEqual(inv.prepare_ocr(frame,sections,threshold_delta=delta,prefixes=prefixes),
                                     inv._prepare_ocr_python(frame,sections,threshold_delta=delta,prefixes=prefixes))

    def test_dependency_fallback(self):
        frame=(bytes(263*204*3),204,263,612)
        expected=(inv._tooltip_blocked_rows_python(frame),inv._prepare_ocr_python(frame,{1}))
        with patch.object(inv,'np',None):
            self.assertEqual((inv.tooltip_blocked_rows(frame),inv.prepare_ocr(frame,{1})),expected)


if __name__=='__main__':
    unittest.main()
