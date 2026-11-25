import unittest
from shop_inventory import locate_shop, pick_rows, GREEN, ORANGE, SCALE

class InventoryTests(unittest.TestCase):
    def test_button_signature(self):
        w,h=140,100;stride=w*3;b=bytearray(stride*h)
        x,y=20,10
        for dy,pattern in ((0,GREEN),(31,ORANGE),(51,ORANGE)):
            at=(y+dy)*stride+x*3;b[at:at+len(pattern)]=pattern
        self.assertEqual(locate_shop(bytes(b),w,h,stride),(x,y))
    def test_sold_and_duplicate(self):
        lines=[{'text':'Suzanoo','y':9*SCALE}]
        for i in (0,5):
            lines.extend([{'text':'Bazlud','y':(28+i*40+9)*SCALE},
                          {'text':'1 for 12,000 mesos','y':(28+i*40+27)*SCALE}])
        self.assertEqual(pick_rows(lines,[True]*6,'Suzanoo','Bazlud',12000)[0],[(0,'SOLD'),(5,'SOLD')])
        self.assertEqual(pick_rows(lines,[False]*6,'Suzanoo','Bazlud',12000)[0],[(0,'AMBIGUOUS'),(5,'AMBIGUOUS')])
        self.assertEqual(pick_rows(lines,[False]*6,'Other','Bazlud',12000)[0],[])
        self.assertEqual(pick_rows(lines,[False]*6,'Suzanoo','Bazlud',13000)[0],[])
