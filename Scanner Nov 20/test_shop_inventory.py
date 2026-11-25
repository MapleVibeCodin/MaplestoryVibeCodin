import unittest
from shop_inventory import locate_shop, pick_rows, GREEN, ORANGE, SCALE, prepare_ocr, inventory_fingerprint, InventoryCache, ShopInventoryTracker

class InventoryTests(unittest.TestCase):
    def test_button_signature(self):
        w,h=140,100;stride=w*3;b=bytearray(stride*h)
        x,y=20,10
        for dy,pattern in ((0,GREEN),(31,ORANGE),(51,ORANGE)):
            at=(y+dy)*stride+x*3
            b[at-3:at]=bytes((17,179,151)) if dy==0 else bytes((28,117,216))
            b[at:at+len(pattern)]=pattern
        # A second set of lower highlights without the leading colored edge
        # must not make the detector ambiguous.
        for dy,pattern in ((13,GREEN),(44,ORANGE),(64,ORANGE)):
            at=(y+dy)*stride+(x-1)*3;b[at:at+len(pattern)]=pattern
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

    def test_sold_divider_and_status(self):
        w,h=204,263;stride=w*3;b=bytearray(bytes((227,217,205))*w*h)
        y=23+40
        for yy in range(y,y+40):
            b[yy*stride:(yy+1)*stride]=bytes((248,245,242))*w
        b[(y+36)*stride+40*3:(y+36)*stride+198*3]=bytes((180,180,180))*158
        bmp,sold=prepare_ocr((bytes(b),w,h,stride))
        self.assertEqual(sold,[False,True,False,False,False,False])
        width=162*SCALE; height=(28+6*40)*SCALE; pitch=(width*3+3)&~3
        row=54+(height-1-(28+40+36)*SCALE)*pitch
        self.assertEqual(bmp[row:row+width*3],b'\xff'*(width*3))
        lines=[{'text':'Euphye','y':9*SCALE},{'text':'Frog Word Bubble Ring','y':(28+40+9)*SCALE},{'text':'1 for 175,000 mesos','y':(28+40+27)*SCALE}]
        self.assertEqual(pick_rows(lines,sold,'Euphye','Frog Word Bubble Ring',175000)[0],[(1,'SOLD')])

    def test_native_fingerprint_and_cache(self):
        w,h=204,263;stride=w*3
        pixels=bytearray(bytes((227,217,205))*w*h)
        frame=lambda:(bytes(pixels),w,h,stride)
        first=inventory_fingerprint(frame())
        cache=InventoryCache(2)
        cache.put(first,[{'text':'seller','y':9*SCALE}],[False]*6)
        # Animated item icon, outline edge and unused region are ignored.
        for x,y in ((10,40),(1,40),(201,40),(150,8)):
            pixels[y*stride+x*3]=0
        self.assertEqual(inventory_fingerprint(frame()),first)
        self.assertIsNotNone(cache.get(first))
        # A changed price/name pixel invalidates cached recognition.
        pixels[65*stride+80*3]=0
        second=inventory_fingerprint(frame())
        self.assertNotEqual(first,second)
        self.assertIsNone(cache.get(second))
        cache.put(second,[],[False]*6)
        cache.put(b'third',[],[False]*6)
        self.assertIsNone(cache.get(first))

    def test_cached_anchor_fast_gate(self):
        from unittest.mock import patch
        tracker=ShopInventoryTracker()
        tracker._anchors[(1366,768)]=(568,214)
        w,h=85,53;stride=w*3
        b=bytearray(stride*h)
        for dy,pattern in ((0,GREEN),(31,ORANGE),(51,ORANGE)):
            at=dy*stride+5*3
            b[at-3:at]=bytes((17,179,151)) if dy==0 else bytes((28,117,216))
            b[at:at+len(pattern)]=pattern
        with patch('shop_inventory.capture_client',return_value=(bytes(b),w,h,stride)) as capture:
            self.assertEqual(tracker._find_anchor((10,20,1366,768)),(568,214))
            capture.assert_called_once_with((573,234,85,53),allow_crop=True)
        tracker.close()
