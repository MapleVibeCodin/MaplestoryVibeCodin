import unittest
from unittest.mock import patch
import shop_inventory as inv


class ItemFirstTests(unittest.TestCase):
    def test_padded_observation_and_single_capture(self):
        w,h=220,334
        stride=w*3+4
        buf=bytearray(stride*h)
        for dy,strip,prefix in [(0,inv.GREEN,bytes((17,179,151))),
                                (31,inv.ORANGE,bytes((28,117,216))),
                                (51,inv.ORANGE,bytes((28,117,216)))]:
            i=(1+dy)*stride+140*3
            buf[i-3:i]=prefix
            buf[i:i+len(strip)]=strip
        # Row contents, including the first and last inventory scan lines.
        buf[71*stride:71*stride+612]=bytes([123])*612
        buf[333*stride:333*stride+612]=bytes([234])*612
        frame=(bytes(buf),w,h,stride)
        client=(17,19,1366,768)
        t=inv.ShopInventoryTracker.__new__(inv.ShopInventoryTracker)
        t._anchors={(1366,768):(568,214)}
        with patch.object(inv,'capture_client',return_value=frame) as capture:
            anchor=t._find_anchor(client)
            self.assertEqual(anchor,(568,214))
            crop=t._inventory_frame(client,anchor)
            capture.assert_called_once_with((445,232,220,334),allow_crop=True)
        self.assertEqual(crop[1:],(204,263,612))
        self.assertEqual(crop[0][:612],bytes([123])*612)
        self.assertEqual(crop[0][-612:],bytes([234])*612)
        self.assertIsNone(t._observation)

    def test_geometry_reuses_same_capture(self):
        frame=(bytes(220*334*3),220,334,660)
        client=(0,0,1366,768)
        t=inv.ShopInventoryTracker.__new__(inv.ShopInventoryTracker)
        t._anchors={(1366,768):(568,214)}
        with patch.object(inv,'capture_client',return_value=frame) as capture, patch.object(inv,'geometry_present',return_value=True) as geometry:
            self.assertIsNone(t._find_anchor(client))
            anchor=t._find_geometry_anchor(client)
            self.assertEqual(anchor,(568,214))
            self.assertEqual(t._inventory_frame(client,anchor)[1:],(204,263,612))
            capture.assert_called_once()
            self.assertEqual(geometry.call_args.args[0][1:],(204,334,612))

    def test_name_only_never_green(self):
        line=lambda row,text: {'y':(33+40*row)*inv.SCALE,'text':text}
        name='Brown Dress Shoes'
        rows=[line(2,name),{'y':(52+80)*inv.SCALE,'text':'1 for 999 mesos'}]
        self.assertEqual(inv.locate_exact_name(rows,[False]*6,name,set()),[(2,'ROW_CHECK')])
        self.assertEqual(inv.locate_exact_name(rows,[False]*6,name,{2}),[])
        self.assertEqual(inv.locate_exact_name(rows,[False,False,True,False,False,False],name,set()),[])
        self.assertEqual(inv.locate_exact_name(rows+[line(1,name)],[False]*6,name,set()),[])
        self.assertEqual(inv.locate_exact_name(rows+[line(1,'Brown Dress Sh...')],[False]*6,name,set()),[])
        self.assertEqual(inv.locate_exact_name([line(1,'Scroll for Gloves for ATT 60%')],[False]*6,'Scroll for Gloves for ATT 60%',set()),[])
        self.assertEqual(inv.locate_exact_name([line(1,'Brown Dress Sh...')],[False]*6,name,set()),[])

    def test_invalid_capture_bounds(self):
        frame=(bytes(220*334*3),220,334,660)
        self.assertIsNone(inv.crop_observation(frame,135,1,86,53))
        self.assertIsNone(inv.crop_observation(frame,0,71,204,264))
        self.assertIsNone(inv.crop_observation((b'',220,334,660),0,0,204,263))


if __name__=='__main__':
    unittest.main()
