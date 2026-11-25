import random
import unittest
from unittest.mock import patch
from metascan_fast import purple_run, crop_bgr
from shop_inventory import ShopInventoryTracker, GREEN, ORANGE, tooltip_blocked_rows, sold_row_mask, nearby_exact_gate
from camera_alignment import room_title_present, _ROOM_PREFIX_BITS, _ROOM_BRACKET_BITS

class FastCaptureTests(unittest.TestCase):
    def test_tooltip_exact_random_and_boundaries(self):
        rng=random.Random(19)
        def reference(p):
            run=0
            for i in range(0,len(p),3):
                b,g,r=p[i:i+3]
                run=run+1 if 40<b and r<145 and g<145 and b-r>28 and b-g>23 else 0
                if run>=12:return True
            return False
        for i in range(5000):
            p=bytearray(rng.randbytes(158*3))
            if i%5==0:
                start=rng.randrange(146)
                p[start*3:(start+12)*3]=bytes((124,74,68))*12
            self.assertEqual(purple_run(bytes(p)),reference(p))
        self.assertFalse(purple_run(bytes((124,74,68))*11))
        self.assertTrue(purple_run(bytes((124,74,68))*12))
        self.assertFalse(purple_run(bytes((20,20,20))*158))
    def test_crop_padding_and_clipping(self):
        data=bytes(range(24))
        self.assertEqual(crop_bgr((data,3,2,12),1,0,2,2),(data[3:9]+data[15:21],2,2,6))
        self.assertIsNone(crop_bgr((data,3,2,12),2,0,2,2))
    def combined(self,dx=0,dy=0):
        w,h,s=224,338,672
        b=bytearray(bytes((227,217,205))*w*h)
        shift_y=dy
        for dy,pattern in ((0,GREEN),(31,ORANGE),(51,ORANGE)):
            at=(3+shift_y+dy)*s+(142+dx)*3
            b[at-3:at]=bytes((17,179,151)) if dy==0 else bytes((28,117,216))
            b[at:at+len(pattern)]=pattern
        return bytes(b),w,h,s
    def test_paired_one_capture_and_exact_inventory(self):
        t=ShopInventoryTracker.__new__(ShopInventoryTracker)
        f=self.combined()
        with patch('shop_inventory.capture_client',return_value=f) as capture:
            quality,rows,actual=t._capture_pair((10,20,1366,768),(568,214))
        self.assertEqual(quality,'exact')
        self.assertEqual(actual,(568,214))
        self.assertEqual(rows,crop_bgr(f,2,73,204,263))
        capture.assert_called_once_with((436,231,224,338),allow_crop=True)
    def test_pair_rejects_missing_gate_and_failed_capture(self):
        t=ShopInventoryTracker.__new__(ShopInventoryTracker)
        for bad in (None,(bytes(224*338*3),224,338,672)):
            with patch('shop_inventory.capture_client',return_value=bad):
                self.assertEqual(t._capture_pair((0,0,1366,768),(568,214)),(None,None,None))
    def test_room_crop_preserves_full_search_bounds(self):
        w,h=200,120
        b=bytearray(w*h*3)
        for y,(p,q) in enumerate(zip(_ROOM_PREFIX_BITS,_ROOM_BRACKET_BITS),50):
            bits=p|(q<<70)
            for x in range(79):
                if bits>>x&1:b[(y*w+56+x)*3:(y*w+56+x)*3+3]=b'\xff'*3
        full=(bytes(b),w,h,w*3)
        self.assertTrue(room_title_present(*full))
        self.assertEqual(room_title_present(*crop_bgr(full,0,0,135,59)),room_title_present(*full))

    def production_tracker(self,item='item'):
        # Exercise the paired production branch, not the compatibility fixture path.
        import test_inventory_hover
        t=test_inventory_hover.TrackerGeometryTests().ready(False,item)
        t._paired_capture=True
        t._anchors={(1366,768):(568,214)}
        return t

    def test_paired_production_scan_two_captures(self):
        t=self.production_tracker()
        f=self.combined()
        with patch('shop_inventory.capture_client',return_value=f) as capture:
            t._scan(t._key)
        self.assertEqual(capture.call_count,2)
        self.assertEqual(t._latest['hits'][0][0],'MATCH')
        self.assertEqual(t._latest['timing']['paired_roi_captures'],2)

    def test_paired_production_scan_rejects_closed_shop(self):
        t=self.production_tracker()
        with patch('shop_inventory.capture_client',side_effect=[self.combined(),None]) as capture:
            t._scan(t._key)
        self.assertEqual(capture.call_count,2)
        self.assertIsNone(t._latest)
        self.assertIsNone(t._digest)

    def test_paired_geometry_never_confirms_scroll(self):
        t=self.production_tracker('Scroll for Gloves for ATT 60%')
        f=crop_bgr(self.combined(),2,73,204,263)
        with patch.object(t,'_capture_pair',return_value=('geometry',f,(568,214))) as capture:
            t._scan(t._key)
        self.assertEqual(capture.call_count,1)
        self.assertEqual(t._latest['hits'],[])
        self.assertIn('waiting for exact scroll gate',t._latest['status'])

    def test_all_shifted_exact_anchors(self):
        t=ShopInventoryTracker.__new__(ShopInventoryTracker)
        for dx in range(-2,3):
            for dy in range(-2,3):
                f=self.combined(dx,dy)
                with patch('shop_inventory.capture_client',return_value=f) as capture:
                    quality,rows,actual=t._capture_pair((0,0,1366,768),(568,214))
                self.assertEqual(quality,'exact')
                self.assertEqual(actual,(568+dx,214+dy))
                self.assertEqual(rows,crop_bgr(f,2+dx,73+dy,204,263))
                self.assertEqual(capture.call_count,1)

    def test_shift_after_ocr_rejects_old_position(self):
        t=self.production_tracker()
        with patch('shop_inventory.capture_client',side_effect=[self.combined(),self.combined(-1)]):
            t._scan(t._key)
        self.assertIsNone(t._latest)

    def test_current_screenshot_price_and_sold_cases(self):
        # Manually transcribed visible rows, not an OCR success claim.
        from shop_inventory import pick_rows, SCALE
        def lines(rows):
            return [{'text':text,'y':(28+i*40+offset)*SCALE}
                    for i,(name,price) in enumerate(rows)
                    for text,offset in ((name,9),(f'1 for {price:,} mesos',27))]
        hecklers=lines([('Shoes Speed Scroll: Inter...',131000),('Heckler',1500),('Heckler',14500),
                        ('Heckler',14500),('Eagle Crow',9500),('Green Legolier',7000)])
        self.assertEqual(pick_rows(hecklers,[False]*6,None,'Heckler',1500)[0],[(1,'MATCH')])
        self.assertEqual(pick_rows(hecklers,[False]*6,None,'Heckler',14500)[0],[])
        self.assertEqual(pick_rows(hecklers,[False]*6,None,'Heckler',1501)[0],[])
        pan=lines([('Blue Moonlight',500000),('Pan Lid',20000),('Gold Moon Shoes',27000),
                   ('Brown Pierre Shoes',25000),('Blue Jangoon Shoes',25000),('Maroon Jangoon Shoes',25000)])
        self.assertEqual(pick_rows(pan,[False,True,False,False,False,False],None,'Pan Lid',20000)[0],[(1,'SOLD')])
        dark=lines([('Dark Shadow',39999),('Magical Destruction Bow',277777),('Magical Destruction Bow',277777),
                    ('Bamboo Sword',177777),('Staff Magic Attack Scroll:...',26666),('Rotten Mushmom Cap',188888)])
        self.assertEqual(pick_rows(dark,[True,False,False,False,False,False],None,'Dark Shadow',39999)[0],[(0,'SOLD')])
        self.assertEqual(pick_rows(dark,[True,False,False,False,False,False],None,'Dark Shadow',40000)[0],[])
        coat=lines([('Cat Lolita Gloves',55000),('Elizabeth Gloves',55000),('Mushroom Hair Pin',52000),
                    ('Fluffy Cat Hood',80000),('Chained Princess Coat',100000),('Love Gloves',374000)])
        self.assertEqual(pick_rows(coat,[True,False,False,True,False,False],None,'Chained Princess Coat',100000)[0],[(4,'MATCH')])
        unrelated=lines([('Pink Sweater',45000),('Pink Sweater',45000),('Prep School Uniform Pants',40000),('Tweed Headband',45000)])
        self.assertEqual(pick_rows(unrelated,[False,False,True,False,False,False],None,'Chained Princess Coat',100000)[0],[])

    def test_six_additional_shop_transcriptions(self):
        from shop_inventory import pick_rows, SCALE
        def lines(rows):
            return [{'text':text,'y':(28+i*40+offset)*SCALE}
                    for i,(name,price) in enumerate(rows)
                    for text,offset in ((name,9),(f'1 for {price:,} mesos',27))]
        dagger=lines([('Dagger Attack Scroll: Inter...',439999),('Leather',99),
                     ("Pig's Head",99),('Horny Mushroom Cap',25),
                     ('Green Mushroom Cap',20),('Stiff Feather',16)])
        for item,price in [('Dagger Attack Scroll: Intermediate',439999),
                           ('Dagger Attack Scroll: Intermediate',440000)]:
            self.assertEqual(pick_rows(dagger,[False]*6,None,item,price)[0],[])
        pan=lines([('Pet Equip Speed Scroll: L...',90000),('Pan Lid',130000),
                   ('Pan Lid',130000),('Pan Lid',180000),('Pan Lid',90000),('Pan Lid',80000)])
        for price,row in [(180000,3),(90000,4),(80000,5)]:
            self.assertEqual(pick_rows(pan,[False]*6,None,'Pan Lid',price)[0],[(row,'MATCH')])
        self.assertEqual(pick_rows(pan,[False]*6,None,'Pan Lid',130000)[0],[])
        nx=lines([('Tania Sword',800000),('Blue Book Bag',50000),('Blue Book Bag',50000),
                  ('White Toy Shades',50000),('Pink Layered Skirt',40000),('Pink Layered Skirt',40000)])
        self.assertEqual(pick_rows(nx,[False]*6,None,'Tania Sword',800000)[0],[(0,'MATCH')])
        self.assertEqual(pick_rows(nx,[False]*6,None,'Pan Lid',90000)[0],[])
        for name,price in [('Blue Book Bag',50000),('Pink Layered Skirt',40000)]:
            self.assertEqual(pick_rows(nx,[False]*6,None,name,price)[0],[])
        earrings=lines([('Emerald Earrings',1899999),("Lion's Fang",433333),
                        ('Emerald Earrings',49999),('Green Napoleon',65555),
                        ('Rower',83333),('Gloves Crit. Rate Scroll: C...',54999)])
        for price,row in [(1899999,0),(49999,2)]:
            self.assertEqual(pick_rows(earrings,[False,False,False,True,False,False],None,'Emerald Earrings',price)[0],[(row,'MATCH')])
        self.assertEqual(pick_rows(earrings,[False,False,False,True,False,False],None,'Polearm Attack Scroll: Intermediate',200000)[0],[])
        joya=lines([('Wizard Wand',13500),('Pet Equip Jump Scroll: Int...',21000),
                    ('Shoes Jump Scroll: Inter...',190000),("Pig's Head",100),
                    ('Dark Distinction',5999),('Red Avenger',11999)])
        self.assertEqual(pick_rows(joya,[True,True,False,True,False,True],None,'Dark Distinction',5999)[0],[(4,'MATCH')])
        self.assertEqual(pick_rows(joya,[True,True,False,True,False,True],None,'Polearm Attack Scroll: Intermediate',200000)[0],[])
        polearm=lines([('Polearm Attack Scroll: Int...',200000),('Hat Accuracy Scroll: Great...',10000),
                       ('Overall Armor DEX Scroll: ...',10000),('Earring LUK Scroll: Inter...',120000),
                       ('Brown Bamboo Hat',5000),('Sap of Ancient Tree',500)])
        self.assertEqual(pick_rows(polearm,[True,False,True,False,False,False],None,'Polearm Attack Scroll: Intermediate',200000)[0],[])

    def duplicate_lines(self,name='Dark Avenger',price=75000):
        from shop_inventory import SCALE
        return [{'text':text,'y':(28+i*40+offset)*SCALE}
                for i in (0,1) for text,offset in ((name,9),(f'1 for {price:,} mesos',27))]

    def test_duplicate_candidates_only_when_explicitly_enabled(self):
        from shop_inventory import pick_rows
        lines=self.duplicate_lines()
        self.assertEqual(pick_rows(lines,[False]*6,None,'Dark Avenger',75000)[0],[])
        self.assertEqual(pick_rows(lines,[False]*6,None,'Dark Avenger',75000,show_duplicates=True)[0],
                         [(0,'AMBIGUOUS'),(1,'AMBIGUOUS')])
        self.assertEqual(pick_rows(lines,[False]*6,None,'Dark Avenger',75001,show_duplicates=True)[0],[])
        self.assertEqual(pick_rows(lines,[True]*6,None,'Dark Avenger',75000,show_duplicates=True)[0],[])
        self.assertEqual(pick_rows(lines[:2],[False]*6,None,'Dark Avenger',75000,show_duplicates=True)[0],[(0,'MATCH')])
        scroll='Dagger Attack Scroll: Intermediate'
        self.assertEqual(pick_rows(self.duplicate_lines(scroll),[False]*6,None,scroll,75000,show_duplicates=True)[0],[])

    def test_production_duplicate_candidates_exact_gate(self):
        t=self.production_tracker('Dark Avenger')
        t._key=(1,(0,0,1366,768),'listing','seller','Dark Avenger',75000,0,1)
        t._row_cache.recognize=lambda *a:(self.duplicate_lines(),[False]*6,True)
        with patch('shop_inventory.capture_client',return_value=self.combined()) as capture:
            t._scan(t._key)
        self.assertEqual(capture.call_count,2)
        self.assertEqual([mode for mode,box in t._latest['hits']],['AMBIGUOUS','AMBIGUOUS'])
        self.assertIn('verify stats',t._latest['status'])

    def test_geometry_duplicates_stay_unhighlighted(self):
        t=self.production_tracker('Dark Avenger')
        t._key=(1,(0,0,1366,768),'listing','seller','Dark Avenger',75000,0,1)
        t._row_cache.recognize=lambda *a:(self.duplicate_lines(),[False]*6,True)
        frame=crop_bgr(self.combined(),2,73,204,263)
        with patch.object(t,'_capture_pair',return_value=('geometry',frame,(568,214))):
            t._scan(t._key)
        self.assertEqual(t._latest['hits'],[])

if __name__=='__main__':unittest.main()
