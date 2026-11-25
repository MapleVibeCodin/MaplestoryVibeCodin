import unittest
from vision_guard import parse_price_line, highlight_expired, revalidate_changed_hits

class VisionGuardTests(unittest.TestCase):
    def test_valid_price(self):
        for text, price in [('1 for 40,000 mesos',40000),('1 for 40000 mesos',40000),('for 1,000,000 mesos',1000000),('2,000 for 9 mesos',9)]:
            with self.subTest(text=text): self.assertEqual(parse_price_line(text),price)
    def test_invalid_price(self):
        for text in ['1 for 4,00,00 mesos','1 for 40,,000 mesos','1 for 4O,000 mesos','1 for 40,0000 mesos','1 for 40,000 mesos extra','1 for -100 mesos','0 for 100 mesos','1 for ４０,０００ mesos','1 for 40.000 mesos']:
            with self.subTest(text=text): self.assertIsNone(parse_price_line(text))
    def test_expiry(self):
        match={'hits':[('MATCH',(0,0,1,1))]}
        for age,expected in [(0,False),(.34,False),(.36,True),(8,True),(-1,True)]:
            with self.subTest(age=age): self.assertEqual(highlight_expired(match,10,10+age),expected)
        self.assertTrue(highlight_expired(match,None,10))
        self.assertFalse(highlight_expired({'hits':[]},None,10))
    def test_unrelated_row_hidden(self):
        before={-1:b'seller',0:b'target',1:b'other'};after={-1:b'seller',0:b'target'}
        self.assertEqual(revalidate_changed_hits([(0,'MATCH')],before,after,False),[(0,'ROW_CHECK')])
        self.assertEqual(revalidate_changed_hits([(0,'MATCH')],before,after,True),[])
        self.assertEqual(revalidate_changed_hits([(0,'SOLD')],before,after,False),[(0,'SOLD_CHECK')])
    def test_changed_identity_and_duplicate(self):
        before={-1:b'seller',0:b'target',1:b'other'}
        for after in [{-1:b'other',0:b'target'},{-1:b'seller',0:b'changed'},{0:b'target'},{-1:b'seller'}]:
            with self.subTest(after=after): self.assertEqual(revalidate_changed_hits([(0,'MATCH')],before,after,False),[])
        self.assertEqual(revalidate_changed_hits([(0,'MATCH'),(1,'SOLD')],before,before,False),[])
        self.assertEqual(revalidate_changed_hits([(0,'MATCH')],{0:b'target'},{0:b'target'},False),[])

if __name__=='__main__':unittest.main()
