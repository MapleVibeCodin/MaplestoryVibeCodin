import unittest,itertools
from species_report import bounds,analyze,canon,digest
class SpeciesTests(unittest.TestCase):
    def test_dp_against_bruteforce(self):
        vs=(3,5,7)
        for x in range(1,81):
            a=[(*p,sum(p)) for p in itertools.product(*(range(x//v+1) for v in vs)) if sum(i*v for i,v in zip(p,vs))==x]
            self.assertEqual(bounds(x,vs),(tuple(map(min,zip(*a))),tuple(map(max,zip(*a)))) if a else None)
    def test_large_and_unmatched(self):
        self.assertIsNone(bounds(10001,(45,69,107,133)))
        self.assertIsNone(bounds(1,(45,69,107,133)))
        self.assertEqual(bounds(214,(107,133)),((2,0,2),(2,0,2)))
    def test_corrupt_journal(self):
        r=dict(sequence=1,previous_sha256=None,kind='launch')
        b=canon(dict(r,sha256='bad'))
        with self.assertRaises(ValueError):analyze(lambda _:b,lambda _:False)
    def test_empty(self):
        r=dict(sequence=1,previous_sha256=None,kind='launch')
        b=canon(dict(r,sha256=digest(canon(r))))
        self.assertEqual(analyze(lambda _:b,lambda _:False),[])
if __name__=='__main__':unittest.main()
