import unittest
from route_logic import PORTALS,ROPE_X,START_POINT,ROW_Y
from henefm_bridge import parse_browser_deal
from test_browser_bridge import OK

class MapAlignment(unittest.TestCase):
    def test_rope_center_between_all_requested_pairs(self):
        for left,right in [(18,19),(14,15),(9,10),(3,4)]:
            self.assertEqual((PORTALS[left][0]+PORTALS[right][0])/2,ROPE_X)
        self.assertEqual(START_POINT[0],ROPE_X)

    def test_upper_rows_centered_and_all_twenty_rooms_present(self):
        self.assertEqual(set(PORTALS),set(range(1,21)))
        for rooms in [range(1,7),range(7,13),range(13,17),range(17,21)]:
            self.assertEqual(sum(PORTALS[n][0] for n in rooms)/len(rooms),ROPE_X)

    def test_large_valid_profit_percent_not_rejected(self):
        self.assertIsNotNone(parse_browser_deal({**OK,'profit_percent':1500}))
        for pct in [-1,14.99]:
            self.assertIsNotNone(parse_browser_deal({**OK,'profit_percent':pct}))
        for pct in [float('nan'),float('inf')]:
            self.assertIsNone(parse_browser_deal({**OK,'profit_percent':pct}))
