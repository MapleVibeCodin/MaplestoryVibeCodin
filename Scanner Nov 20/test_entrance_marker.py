import unittest
from shop_pin import entrance_marker
class EntranceMarkerTests(unittest.TestCase):
    client=(10,40,1366,768)
    window=(10,0,1366,808)
    def test_visible_door(self):
        h=entrance_marker(17,(0,0),self.client,self.window)
        self.assertEqual(h['FM 17']['mode'],'PORTAL')
        self.assertEqual(h['FM 17']['box'],(430,131,546,283))
    def test_bottom_route(self):
        h=entrance_marker(4,(0,0),self.client,self.window)
        self.assertIn('FM 4 · DOWN WARP',h)
    def test_no_translation(self):
        self.assertEqual(entrance_marker(8,None,self.client,self.window)['FM 8']['mode'],'LABEL')
    def test_offscreen(self):
        h=entrance_marker(17,(0,-500),self.client,self.window)
        self.assertTrue(any('UP' in k and v['mode']=='LABEL' for k,v in h.items()))
