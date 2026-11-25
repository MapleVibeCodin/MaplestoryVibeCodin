import unittest
from shop_position import entry_portal_point, entry_shop_point

class FM16CalibrationTests(unittest.TestCase):
    def test_fixed_entry_offset(self):
        pin={'theme':'grass','left':72.0,'top':42.0}
        for w,h in ((1366,768),(1280,720)):
            old=entry_shop_point(pin,16,(w,h),(w-225,h-192))
            new=entry_shop_point(pin,16,(w,h))
            self.assertEqual(entry_portal_point(16,(w,h)),(w-225,h))
            self.assertEqual(new,(old[0],old[1]+192))
            self.assertEqual(entry_portal_point(15,(w,h)),(w-225,h-40))
