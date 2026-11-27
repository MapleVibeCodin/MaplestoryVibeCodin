import unittest
from dataclasses import replace
from visual_bank import Review, VerifiedVisualBank


def key(i):
    return i.to_bytes(20, 'big')


def reviewed(name='Blue Glove'):
    return Review(name, 'episode-1', 'review-1', native=True, complete=True, unobscured=True)


class BankTests(unittest.TestCase):
    def test_independent_provenance_required(self):
        bank=VerifiedVisualBank()
        for method in ('ocr','cached-ocr','catalog-from-ocr',''):
            self.assertFalse(bank.qualify(key(1),replace(reviewed(),method=method)))
        self.assertFalse(bank)
        self.assertTrue(bank.qualify(key(1),reviewed()))
        self.assertEqual(bank.lookup(key(1),eligible=True),reviewed())

    def test_blank_truncation_corruption_and_missing_proof(self):
        bank=VerifiedVisualBank()
        for name in ('','  ','Blue Glove...','Blue Glove…','Blue\ufffdGlove','Blue\nGlove'):
            self.assertFalse(bank.qualify(key(1),reviewed(name)))
        for field in ('native','complete','unobscured'):
            self.assertFalse(bank.qualify(key(1),replace(reviewed(),**{field:False})))
        self.assertFalse(bank.qualify(key(1),replace(reviewed(),source_id='')))
        self.assertFalse(bank.qualify(key(1),replace(reviewed(),review_id='')))
        self.assertFalse(bank.qualify(b'bad',reviewed()))

    def test_collision_quarantine(self):
        bank=VerifiedVisualBank()
        self.assertTrue(bank.qualify(key(1),reviewed()))
        self.assertFalse(bank.qualify(key(1),reviewed('Red Glove')))
        self.assertIsNone(bank.lookup(key(1),eligible=True))
        self.assertFalse(bank.qualify(key(1),reviewed()))

    def test_normalized_same_label_preserves_provenance(self):
        bank=VerifiedVisualBank()
        bank.qualify(key(1),reviewed())
        self.assertTrue(bank.qualify(key(1),replace(reviewed('BLUE  GLOVE'),review_id='second')))
        self.assertEqual(bank.lookup(key(1),eligible=True).review_id,'review-1')

    def test_occluded_lookup_abstains(self):
        bank=VerifiedVisualBank();bank.qualify(key(1),reviewed())
        self.assertIsNone(bank.lookup(key(1),eligible=False))
        self.assertIsNone(bank.lookup(key(1),eligible=None))
        self.assertIsNotNone(bank.lookup(key(1),eligible=True))

    def test_eviction(self):
        bank=VerifiedVisualBank(limit=2)
        bank.qualify(key(1),reviewed());bank.qualify(key(2),reviewed())
        bank.lookup(key(1),eligible=True);bank.qualify(key(3),reviewed())
        self.assertIsNone(bank.lookup(key(2),eligible=True))
        self.assertEqual(len(bank.entries),2)

    def test_conflict_bound_disables_instead_of_forgetting(self):
        bank=VerifiedVisualBank(limit=2,conflict_limit=1)
        bank.qualify(key(1),reviewed());bank.invalidate(key(1))
        bank.qualify(key(2),reviewed());bank.invalidate(key(2))
        self.assertTrue(bank.disabled);self.assertFalse(bank)
        self.assertFalse(bank.qualify(key(3),reviewed()))
        self.assertIsNone(bank.lookup(key(1),eligible=True))
        self.assertEqual(len(bank.conflicts),1)


if __name__=='__main__':
    unittest.main()
