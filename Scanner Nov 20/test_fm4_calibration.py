import unittest
from shop_position import entry_portal_point, entry_shop_point, shop_marker

class FM4CalibrationTests(unittest.TestCase):
    def test_entry_calibration(self):
        self.assertEqual(entry_portal_point(4,(1366,768)), (1141,718))
        self.assertEqual(entry_portal_point(4,(1280,720)), (1055,670))
        self.assertEqual(entry_portal_point(3,(1366,768)), (1141,720))
        self.assertEqual(entry_portal_point(5,(1366,768)), (1141,723))
    def test_marker_shift(self):
        pin={'theme':'grass','left':50.0,'top':25.0}
        for size in ((1280,720),(1366,768)):
            new=entry_shop_point(pin,4,size)
            old=entry_shop_point(pin,4,size,(size[0]-225,size[1]-192))
            self.assertEqual(new,(old[0],old[1]+142+(45 if size==(1366,768) else 0)))
