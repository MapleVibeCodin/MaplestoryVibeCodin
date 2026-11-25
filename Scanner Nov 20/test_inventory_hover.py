"""Offline hover and shifted shop gate checks."""
import unittest
from shop_inventory import inventory_tooltip_visible,tooltip_blocked_rows,locate_shop,GREEN,ORANGE,pick_rows,RowOCRCache,section_fingerprints,SCALE
from camera_alignment import room_title_present,_ROOM_TITLE
from shop_inventory import displayed_buy_step,price_in_display_bucket

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
    def test_hover_only_blocks_covered_rows(self):
        buf,w,h,s=frame(204,263)
        for row in (2,4,5):
            for y in range(26+row*40,34+row*40):
                for x in range(115,198):
                    i=y*s+x*3;buf[i:i+3]=bytes((132,85,83))
        self.assertEqual(tooltip_blocked_rows((buf,w,h,s)),{2,3,4,5})
    def test_room_title_two_aligned_strips(self):
        buf,w,h,s=frame(200,120)
        self.assertFalse(room_title_present(buf,w,h,s))
        for dy,strip in zip((0,3),_ROOM_TITLE):
            i=(48+dy)*s+110*3;buf[i:i+len(strip)]=strip
        self.assertTrue(room_title_present(buf,w,h,s))
        buf[(51)*s+110*3]=0
        self.assertFalse(room_title_present(buf,w,h,s))
    def test_exact_scroll_and_price(self):
        seller='cappin'; item='Scroll for Gloves for ATT 60%'
        lines=[{'y':5*SCALE,'text':seller}]
        for i,(name,price) in enumerate(((item,40000),('Scroll for Gloves for ATT 10%',40000),('Scroll for Gloves for DEX 60%',40000),(item,41000))):
            lines.extend([{'y':(28+i*40+5)*SCALE,'text':name},{'y':(28+i*40+24)*SCALE,'text':f'1 for {price:,} mesos'}])
        self.assertEqual(pick_rows(lines,[False]*6,seller,item,40000)[0],[(0,'MATCH')])
        self.assertEqual(pick_rows(lines,[False]*6,seller,'Scroll for Gloves for ATT',40000)[0],[])
        self.assertEqual(pick_rows(lines,[False]*6,'wrong seller',item,40000)[0],[])
        lines.extend([{'y':(28+4*40+5)*SCALE,'text':item},{'y':(28+4*40+24)*SCALE,'text':'1 for 40,000 mesos'}])
        self.assertEqual(pick_rows(lines,[False]*6,seller,item,40000)[0],[])
    def test_partial_row_cache(self):
        class OCR:
            def recognize(self,png):return [{'y':5*SCALE,'text':'seller'},{'y':33*SCALE,'text':'item'}]
        buf,w,h,s=frame(204,263)
        f=(buf,w,h,s)
        sections=tuple(x for x in section_fingerprints(f) if x[0] in (-1,0))
        lines,sold,_=RowOCRCache().recognize(f,OCR(),sections)
        self.assertEqual([x['text'] for x in lines],['seller','item'])
        self.assertEqual(len(sold),6)
    def test_rounded_candidates_and_strict_scroll(self):
        name='Chained Princess Face Accessory'
        lines=[{'y':5*SCALE,'text':'Super'},{'y':33*SCALE,'text':name},{'y':52*SCALE,'text':'1 for 127,777 mesos'}]
        step=displayed_buy_step('Profit\n17.7K\nBuy\n127.8K\nTime to resell',127800)
        self.assertEqual(step,100)
        self.assertEqual(pick_rows(lines,[False]*6,'Super',name,127800,buy_step=step)[0],[(0,'PRICE_CHECK')])
        self.assertEqual(pick_rows(lines,[True]*6,'Super',name,127800,buy_step=step)[0],[(0,'SOLD_CHECK')])
        lines[1]['text']='Chained Princess Face A...'
        self.assertEqual(pick_rows(lines,[True]*6,'Super',name,127800,buy_step=step)[0],[])
        name='Scroll for Gloves for ATT 60%'
        lines[1]['text']=name
        self.assertEqual(pick_rows(lines,[False]*6,'Super',name,127800,buy_step=step)[0],[])
        self.assertEqual(displayed_buy_step('Buy 127,800',127800),0)
        self.assertFalse(price_in_display_bucket(127850,127800,100))
    def test_sold_unreadable_price(self):
        lines=[{'y':5*SCALE,'text':'Nanamico'},{'y':33*SCALE,'text':'Blood Avarice'}]
        self.assertEqual(pick_rows(lines,[True]*6,'Nanamico','Blood Avarice',100000)[0],[(0,'SOLD_CHECK')])
        self.assertEqual(pick_rows(lines,[False]*6,'Nanamico','Blood Avarice',100000)[0],[])
if __name__=='__main__':unittest.main()
