import unittest
from shop_position import entry_portal_point, entry_shop_point

class FM11CalibrationTests(unittest.TestCase):
    def test_default_offset_and_manual_alignment(self):
        pin={'theme':'cave','left':40.0,'top':80.0}
        size=(1366,768)
        anchor=entry_portal_point(11,size)
        baseline=entry_shop_point(pin,11,size,anchor)
        self.assertEqual(entry_shop_point(pin,11,size),(baseline[0],baseline[1]+66))
        for room,size in ((11,(1280,720)),(10,(1366,768)),(12,(1366,768))):
            self.assertEqual(entry_shop_point(pin,room,size),
                             entry_shop_point(pin,room,size,entry_portal_point(room,size)))
