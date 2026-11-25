import random
import unittest
from metascan_fast import row_mask, scale3, negative_retry_due

class ExactPixelTests(unittest.TestCase):
    def test_4000_random_masks_and_scaling(self):
        rng=random.Random(123)
        for i in range(4000):
            p=rng.randbytes(3*rng.randint(0,158))
            c=rng.randrange(256);s=bool(i%2);d=rng.randrange(-20,21)
            expected=bytes(0 if (r<145+d if s else (r+g+b)//3<c) else 255
                           for b,g,r in zip(p[0::3],p[1::3],p[2::3]))
            self.assertEqual(row_mask(p,c,s,d),expected)
            self.assertEqual(row_mask(bytearray(p),c,s,d),expected)
            self.assertEqual(scale3(expected),b''.join(bytes([v])*3 for v in expected))
    def test_negative_retry_bounded_and_positive_unchanged(self):
        negative={'hits':[]}
        self.assertFalse(negative_retry_due(negative,10,11.99))
        self.assertTrue(negative_retry_due(negative,10,12))
        self.assertFalse(negative_retry_due({'hits':[('MATCH',())]},0,100))
        self.assertFalse(negative_retry_due(None,0,100))

if __name__=='__main__':unittest.main()
