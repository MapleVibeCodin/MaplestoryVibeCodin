"""Identity checks remain strict when redundant recognition crops are skipped."""
import unittest
import numpy as np
from name_finder import NameFinder


class VerificationWorkTests(unittest.TestCase):
    def verify(self,target,score,reads):
        finder=NameFinder.__new__(NameFinder)
        finder.last_diagnostic={'candidates':[]}
        calls=[]
        def recognize(crops):
            calls.append(len(crops))
            return reads.pop(0),0.
        finder.recognizer=recognize
        frame=np.full((100,200,3),100,np.uint8)
        hits=finder._verify(frame,target,[(score,(20,20,90,35))])
        return hits,calls

    def test_strong_long_exact_name_needs_only_context_read(self):
        hits,calls=self.verify('MapleShop',.8,[[('MapleShop',.99)]])
        self.assertEqual(len(hits),1)
        self.assertEqual(hits[0].mode,'EXACT')
        self.assertEqual(calls,[1])

    def test_short_name_still_requires_agreeing_tight_read(self):
        hits,calls=self.verify('Mora',.8,[[('Mora',.99)],[('Moro',.99)]])
        self.assertEqual(hits,[])
        self.assertEqual(calls,[1,1])

    def test_weak_proposal_still_requires_two_exact_reads(self):
        hits,calls=self.verify('MapleShop',.5,[[('MapleShop',.99)],[('MapleShap',.99)]])
        self.assertEqual(hits,[])
        self.assertEqual(calls,[1,1])

    def test_unrelated_or_longer_name_does_not_get_another_ocr_pass(self):
        hits,calls=self.verify('MapleShop',.8,[[('MapleShopLong',.99)]])
        self.assertEqual(hits,[])
        self.assertEqual(calls,[1])
