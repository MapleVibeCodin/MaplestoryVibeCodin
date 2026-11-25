import random
import unittest
from unittest.mock import patch
from metascan_fast import count_bgr_below
from performance_recorder import dark_fraction
from shop_inventory import sold_row_mask
from native_item_fast import decode_columns, decode_run, load_atlas
from transition_screenshot import Blackout

class SpeedTests(unittest.TestCase):
    def test_dark_exact_random_padded_frames(self):
        rng=random.Random(176)
        for i in range(4000):
            w=rng.randrange(1,33);h=rng.randrange(1,33);s=w*3+rng.randrange(4)
            buf=rng.randbytes(s*h) if i%2 else bytes(rng.randrange(30) for _ in range(s*h))
            expected=sum(max(buf[j:j+3])<=16 for y in range(h) for j in range(y*s,y*s+w*3,3))/(w*h)
            self.assertEqual(dark_fraction((buf,w,h,s)),expected)
    def test_sold_predicate_boundaries(self):
        rng=random.Random(9)
        w,h,s=204,263,612
        for trial in range(100):
            data=bytearray(bytes((248,243,242))*w*h)
            for k in range(trial%33):
                j=(27+k)*s+194*3;data[j:j+3]=bytes((204,216,227))
            for k in range(trial%20):
                j=25*s+(41+k)*3;data[j:j+3]=bytes((0,0,0))
            f=(bytes(data),w,h,s)
            expected=(trial%33<=8 and trial%20<12)
            self.assertEqual(sold_row_mask(f,0),expected)
    def test_exact_native_l(self):
        self.assertEqual(decode_columns((0,2044,1024,1024,1024,1024,1024,0)),'L')
    def test_cached_decoder_preserves_other_runs(self):
        atlas,widths=load_atlas()
        def reference(run):
            ways={len(run):{''}}
            for k in range(len(run)-1,-1,-1):
                cand=set()
                for w in widths:
                    if k+w>len(run):break
                    for char in atlas.get(run[k:k+w],()):
                        for suffix in ways.get(k+w,()):
                            cand.add(char+suffix)
                            if len(cand)>1:break
                        if len(cand)>1:break
                    if len(cand)>1:break
                ways[k]=cand
            return next(iter(ways[0])) if len(ways[0])==1 else '?'
        rng=random.Random(5);keys=list(atlas)
        for _ in range(2000):
            run=tuple(x for key in rng.choices(keys,k=rng.randint(1,3)) for x in key)
            if run!=(2044,1024,1024,1024,1024,1024):
                self.assertEqual(decode_run(run),reference(run))
    def test_unknown_does_not_arm_nonconsecutive_dark(self):
        s=Blackout()
        s.observe(False);s.observe(True);s.observe(None);s.observe(True)
        self.assertFalse(s.observe(False))
    def test_dark_count_channel_boundaries(self):
        p=bytes((16,16,16,17,16,16,16,17,16,16,16,17))
        self.assertEqual(count_bgr_below(p,17),1)

if __name__=='__main__':unittest.main()
