import unittest
from unittest.mock import Mock
from exact_cache import ExactRowCache
from visual_bank import VerifiedVisualBank
from hybrid_cache import HybridCache
from test_visual_bank import key, reviewed
from test_exact_cache import frame, prepare, OCR
from pinned_excerpt import name_row_fingerprint


def setup():
    exact=ExactRowCache(name_row_fingerprint,prepare)
    bank=VerifiedVisualBank()
    sig=Mock(side_effect=lambda f,r:key(r+1))
    return HybridCache(exact,bank,sig),OCR()


class HybridTests(unittest.TestCase):
    def test_cold_empty_bank_bypasses_signature(self):
        h,o=setup();f=frame([1,2,3,4,5,6])
        self.assertEqual(h.recognize(f,[0,1],o,allow_visual=True,visual_eligible=[0,1])[1:],(0,2,True))
        h.signature.assert_not_called()
        self.assertEqual(h.last_scan.ocr_rows,2)
        self.assertFalse(h.bank)

    def test_exact_hit_never_invokes_signature_or_ocr(self):
        h,o=setup();f=frame([1,2,3,4,5,6])
        h.recognize(f,[0],o);h.bank.qualify(key(1),reviewed())
        self.assertEqual(h.recognize(f,[0],o,allow_visual=True,visual_eligible=[0])[0],{0:'Item 1'})
        h.signature.assert_not_called();self.assertEqual(len(o.calls),1)
        self.assertEqual(h.last_scan.raw_hits,1)

    def test_mixed_exact_visual_and_ocr(self):
        h,o=setup();f=frame([1,2,3,4,5,6]);h.recognize(f,[0],o)
        h.bank.qualify(key(2),reviewed('Known 2'))
        result=h.recognize(f,[2,0,1],o,allow_visual=True,visual_eligible=[0,1,2])
        self.assertEqual(result,({0:'Item 1',1:'Known 2',2:'Item 3'},2,1,True))
        self.assertEqual(o.calls[-1],(3,));self.assertEqual(h.signature.call_count,2)
        t=h.last_scan
        self.assertEqual((t.raw_hits,t.visual_hits,t.signature_attempts,t.rejected,t.ocr_rows,t.ocr_calls),(1,1,2,1,1,1))
        self.assertEqual(dict(t.provenance),{0:'raw_ocr_cache',1:'verified_visual',2:'ocr'})
        self.assertNotIn(name_row_fingerprint(f,1),h.exact.entries)

    def test_visual_invalidation_cannot_leave_poisoned_raw_cache(self):
        h,o=setup();f=frame([1,2,3,4,5,6]);h.bank.qualify(key(1),reviewed('Wrong label'))
        self.assertEqual(h.recognize(f,[0],o,allow_visual=True,visual_eligible=[0])[0],{0:'Wrong label'})
        self.assertFalse(h.exact.entries);self.assertFalse(o.calls)
        h.bank.invalidate(key(1))
        self.assertEqual(h.recognize(f,[0],o,allow_visual=True,visual_eligible=[0])[0],{0:'Item 1'})
        self.assertEqual(len(o.calls),1)

    def test_explicit_opt_in_and_row_eligibility(self):
        for kwargs in ({},{'allow_visual':True},{'allow_visual':False,'visual_eligible':[0]}):
            h,o=setup();h.bank.qualify(key(1),reviewed())
            self.assertEqual(h.recognize(frame([1,2,3,4,5,6]),[0],o,**kwargs)[0],{0:'Item 1'})
            h.signature.assert_not_called()

    def test_blank_retry_no_visual_learning(self):
        h,o=setup();f=frame([0,2,3,4,5,6])
        for _ in range(2):
            self.assertEqual(h.recognize(f,[0],o)[0],{0:''})
            self.assertEqual(dict(h.last_scan.provenance),{0:'ocr_blank'})
        self.assertFalse(h.exact.entries);self.assertFalse(h.bank)
        self.assertEqual(len(o.calls),2)

    def test_exception_clears_previous_telemetry(self):
        h,o=setup();f=frame([1,2,3,4,5,6]);h.recognize(f,[0],o)
        o.recognize=Mock(side_effect=RuntimeError('ocr failed'))
        with self.assertRaises(RuntimeError):h.recognize(f,[1],o)
        self.assertIsNone(h.last_scan)


if __name__=='__main__':
    unittest.main()
