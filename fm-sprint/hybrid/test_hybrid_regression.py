"""Section 4: adapter/guard boundaries, synthetic only; no Windows calls."""
import random
import unittest
from unittest.mock import Mock
from exact_cache import ExactRowCache
from hybrid_cache import HybridCache
from visual_bank import VerifiedVisualBank
from visual_excerpt import visual_key
from pinned_excerpt import name_row_fingerprint, exact_name_rows
import pinned_excerpt as old
from test_exact_cache import frame, prepare, OCR
from test_visual_bank import reviewed
from test_visual_signature import image


class RegressionTests(unittest.TestCase):
    def test_empty_bank_differential_600_scans(self):
        rng=random.Random(20261127)
        old.prepare_name_ocr=prepare
        for limit in (0,2,512):
            base=old.NameOCRCache(limit)
            sig=Mock(side_effect=AssertionError('empty visual bank must not compute signatures'))
            hybrid=HybridCache(ExactRowCache(name_row_fingerprint,prepare,limit=limit),VerifiedVisualBank(),sig)
            a,b=OCR(),OCR()
            for _ in range(200):
                f=frame([rng.randrange(12) for _ in range(6)],rng.randrange(255))
                rows=[rng.randrange(6) for _ in range(rng.randrange(9))]
                x=base.recognize(f,rows,a)
                y=hybrid.recognize(f,rows,b,allow_visual=True,visual_eligible=range(6))
                self.assertEqual(x,y);self.assertEqual(list(x[0]),list(y[0]))
                self.assertEqual(list(base.entries.items()),list(hybrid.exact.entries.items()))
                self.assertEqual(a.calls,b.calls)
            sig.assert_not_called()

    def test_real_signature_reuses_review_across_selected_background(self):
        bank=VerifiedVisualBank();f=image();s=image(selected=True)
        self.assertNotEqual(name_row_fingerprint(f,0),name_row_fingerprint(s,0))
        self.assertTrue(bank.qualify(visual_key(f,0),reviewed()))
        h=HybridCache(ExactRowCache(name_row_fingerprint,prepare),bank,visual_key)
        o=Mock();o.recognize.side_effect=AssertionError('visual hit should bypass OCR')
        for sample in (f,s):
            result=h.recognize(sample,[0],o,allow_visual=True,visual_eligible=[0])
            self.assertEqual(result,({0:'Blue Glove'},1,0,False))
            self.assertEqual(exact_name_rows(result[0],'Blue Glove'),[0])
        self.assertFalse(h.exact.entries);o.recognize.assert_not_called()

    def test_duplicate_or_truncated_name_abstains(self):
        for second in ('Very Long Item Name','Very Long Item...'):
            bank=VerifiedVisualBank();bank.qualify(b'a'*20,reviewed('Very Long Item Name'))
            h=HybridCache(ExactRowCache(name_row_fingerprint,prepare),bank,lambda f,r:b'a'*20 if r==0 else None)
            f=frame([1,2,3,4,5,6]);h.exact.store(name_row_fingerprint(f,1),second)
            names,*_=h.recognize(f,[0,1],OCR(),allow_visual=True,visual_eligible=[0])
            self.assertEqual(exact_name_rows(names,'Very Long Item Name'),[])

    def test_excluded_row_does_not_use_visual_even_if_signature_would_match(self):
        bank=VerifiedVisualBank();bank.qualify(b'a'*20,reviewed())
        sig=Mock(return_value=b'a'*20)
        h=HybridCache(ExactRowCache(name_row_fingerprint,prepare),bank,sig)
        for i in range(3):
            f=frame([i+1,2,3,4,5,6])
            names,*_=h.recognize(f,[0],OCR(),allow_visual=True,visual_eligible=[])
            self.assertNotEqual(names[0],'Blue Glove')
        sig.assert_not_called()


if __name__=='__main__':
    unittest.main()
