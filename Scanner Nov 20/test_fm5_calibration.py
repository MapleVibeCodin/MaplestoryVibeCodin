import unittest
from shop_position import entry_portal_point, entry_shop_point

class FM5CalibrationTests(unittest.TestCase):
    def test_native_default_offset(self):
        pin={'theme':'grass','left':40.0,'top':42.0}
        size=(1366,768)
        baseline=entry_shop_point(pin,5,size,entry_portal_point(5,size))
        result=entry_shop_point(pin,5,size)
        self.assertEqual(result,(baseline[0],baseline[1]+48))

    def test_other_resolution_and_room(self):
        pin={'theme':'grass','left':40.0,'top':42.0}
        for room,size in ((5,(1280,720)),(4,(1366,768)),(6,(1366,768))):
            self.assertEqual(entry_shop_point(pin,room,size),
                             entry_shop_point(pin,room,size,entry_portal_point(room,size)))
