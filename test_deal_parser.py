import unittest
from deal_parser import parse_deal,buy_price,parse_details
from profit_filter import filter_profit

SAMPLE='''HeneFM APP 2:29 AM
Green Napoleon
W.DEF 22 · DEX 3 · ACC 4 · 5 slots
Buy              Resell at        Profit
30K each          38.9K (cheapest other ask)  +15.7K (26%)
Sells in          Where
under an hour · 70 sold a day  CH 22 · FM 13 · porkypork
henefm.com/flips'''
class TestDealParser(unittest.TestCase):
    def test_qualified(self):
        deal=parse_deal(SAMPLE)
        self.assertEqual((deal.cc,deal.fm),(22,13))
        self.assertEqual(deal.item,'Green Napoleon')
        self.assertIn('W.DEF 22',deal.stats)
        self.assertEqual(deal.ign,'porkypork')
        self.assertEqual(deal.buy_mesos,30000)
        self.assertTrue(deal.profit.accepted)

    def test_buy_formats(self):
        for text,amount in [
            ('Buy at: 30K',30000),('Buy 30,000 each',30000),('Buy 0.01M',10000),
            ('Buy\n30K each\nResell at 60K',30000),
            ('Buy Resell at Profit\n50K 88K +20K (25%)',50000)]:
            self.assertEqual(buy_price(text),amount,text)

    def test_fail_closed(self):
        self.assertIsNone(buy_price('Resell at 50K Profit +10K (20%)'))
        self.assertIsNone(buy_price('BUY at an unknown value'))
        too_low=SAMPLE.replace('+15.7K (26%)','+7.7K (26%)')
        self.assertFalse(parse_deal(too_low).profit.accepted)
        self.assertFalse(filter_profit('Profit +12K (14%)').accepted)
        self.assertTrue(filter_profit('Profit +15,000 (15%)').accepted)

if __name__=='__main__':unittest.main()
