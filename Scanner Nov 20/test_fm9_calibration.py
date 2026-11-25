import unittest
from shop_position import entry_portal_point, entry_shop_point, shop_marker

class FM9CalibrationTests(unittest.TestCase):
    def test_room_specific_anchor(self):
        self.assertEqual(entry_portal_point(9,(1366,768)),(633,488))
        self.assertEqual(entry_portal_point(9,(1280,720)),(698,509))
        self.assertEqual(entry_portal_point(8,(1366,768)),(741,492))
    def test_synthetic_right_edge_pin(self):
        # Illustrative pin, not exact CSS percentages from the screenshot.
        size=(1366,768)
        pin={'theme':'cave','left':91.0,'top':86.0}
        old=entry_shop_point(pin,9,size,(741,533))
        new=entry_shop_point(pin,9,size)
        self.assertEqual(new,(old[0]-108,old[1]-45))
        client=(0,0,*size)
        self.assertIsNone(shop_marker(old,client,client))
        self.assertIsNotNone(shop_marker(new,client,client))
