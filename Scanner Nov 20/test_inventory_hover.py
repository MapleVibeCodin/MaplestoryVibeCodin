"""Offline hover and shifted shop gate checks."""
import unittest
from shop_inventory import inventory_tooltip_visible,locate_shop,GREEN,ORANGE

def frame(w,h):
    stride=(w*3+3)&~3
    return bytearray(stride*h),w,h,stride

class HoverTests(unittest.TestCase):
    def test_clean_and_tooltip(self):
        buf,w,h,s=frame(204,263)
        self.assertFalse(inventory_tooltip_visible((buf,w,h,s)))
        for y in range(105,125):
            for x in range(115,198):
                i=y*s+x*3;buf[i:i+3]=bytes((132,85,83))
        self.assertTrue(inventory_tooltip_visible((buf,w,h,s)))
    def test_small_icon_not_tooltip(self):
        buf,w,h,s=frame(204,263)
        for y in range(28,60):
            for x in range(2,30):
                i=y*s+x*3;buf[i:i+3]=bytes((132,85,83))
        self.assertFalse(inventory_tooltip_visible((buf,w,h,s)))
    def test_shifted_gate(self):
        for x,y in ((5,0),(9,4),(13,8)):
            buf,w,h,s=frame(93,61)
            for dy,color,start in ((0,GREEN,(17,179,151)),(31,ORANGE,(28,117,216)),(51,ORANGE,(28,117,216))):
                i=(y+dy)*s+x*3;buf[i-3:i]=bytes(start);buf[i:i+len(color)]=color
            self.assertEqual(locate_shop(buf,w,h,s),(x,y))
if __name__=='__main__':unittest.main()
