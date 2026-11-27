"""Current-contract tests: actual Exact scanner method, synthetic captures, no live input."""
import os
import sys
import threading
import unittest
from unittest.mock import Mock, patch
from types import SimpleNamespace

sys.path.insert(1,os.environ['BEAST_PINNED_SCANNER'])
from beast_inventory import InventoryFallbackMixin
from shop_inventory import ShopInventoryTracker, SCALE, prepare_ocr

class Tracker(InventoryFallbackMixin, ShopInventoryTracker):
    pass

def rows(*pairs):
    lines=[]
    for i,(name,price) in enumerate(pairs):
        lines.append({'text':name,'y':(33+40*i)*SCALE})
        if price is not None:
            lines.append({'text':f'1 for {price:,} mesos','y':(52+40*i)*SCALE})
    return lines

def frame(changed=False,sold=()):
    w,h=204,263
    stride=w*3
    b=bytearray(bytes((227,216,204))*w*h)
    for row in sold:
        for y in range(23+row*40,23+(row+1)*40):
            for x in range(40,198):
                i=y*stride+x*3;b[i:i+3]=bytes((248,243,242))
    if changed:b[52*stride+80*3]=0
    return bytes(b),w,h,stride

class ExactIntegration(unittest.TestCase):
    def tracker(self,primary,secondary=None,*,geometry=False,item='Ribbon',price=30000,step=0,before=None,after=None):
        t=Tracker.__new__(Tracker)
        t._key=(1,(0,0,1366,768),'listing','seller',item,price,step,1)
        t._lock=threading.RLock();t._latest=None;t._digest=None;t._observed_at=None
        t._busy=True;t._closed=False;t._next=0;t._ocr_failures=0
        t._find_anchor=Mock(return_value=None if geometry else (568,214))
        t._find_geometry_anchor=Mock(return_value=(568,214))
        f=before or frame()
        t._inventory_frame=Mock(side_effect=[f,after or f])
        t._row_cache=SimpleNamespace(recognize=Mock(return_value=(primary,[False]*6,True)))
        t._ocr=SimpleNamespace(recognize=Mock(return_value=primary if secondary is None else secondary))
        return t
    def scan(self,t):
        t._scan(t._key)
        self.assertFalse(t._busy)
        if t._latest:
            self.assertNotIn('OCR unavailable',t._latest['status'])
        return t._latest['hits'] if t._latest else []
    def test_correct_positive_and_second_row(self):
        t=self.tracker(rows(('Ribbon',31000),('Ribbon',30000)))
        self.assertEqual(self.scan(t),[('MATCH',(429,347,628,385))])
        self.assertEqual(t._ocr.recognize.call_count,1)
        self.assertEqual(t._inventory_frame.call_count,2)
    def test_wrong_price_or_item_never_highlight(self):
        for pair in (('Ribbon',29999),('Ribbon',30001),('Ribbon',None),('Other',30000)):
            with self.subTest(pair=pair):
                self.assertEqual(self.scan(self.tracker(rows(pair))),[])
    def test_duplicate_active_rejected(self):
        self.assertEqual(self.scan(self.tracker(rows(('Ribbon',30000),('Ribbon',30000)))),[])
    def test_second_ocr_price_or_name_disagreement(self):
        for pair in (('Ribbon',30001),('Other',30000)):
            with self.subTest(pair=pair):
                self.assertEqual(self.scan(self.tracker(rows(('Ribbon',30000)),rows(pair))),[])
    def test_missing_or_rounded_listing_price(self):
        for price,step in ((None,0),(30000,1000)):
            with self.subTest(price=price,step=step):
                t=self.tracker(rows(('Ribbon',30000)),price=price,step=step)
                self.assertEqual(self.scan(t),[])
                t._row_cache.recognize.assert_not_called()
    def test_changed_price_pixels_reject_old_match(self):
        t=self.tracker(rows(('Ribbon',30000)),after=frame(changed=True))
        self.assertEqual(self.scan(t),[])
        self.assertIsNone(t._digest)
    def test_sold_pixels_never_highlight(self):
        t=self.tracker(rows(('Ribbon',30000)),before=frame(sold=(0,)))
        self.assertEqual(self.scan(t),[])
    def test_tooltip_row_never_highlight(self):
        t=self.tracker(rows(('Ribbon',30000)))
        with patch('beast_inventory.tooltip_blocked_rows',return_value={0}):
            self.assertEqual(self.scan(t),[])
    def test_geometry_exact_match_preserved(self):
        t=self.tracker(rows(('Ribbon',30000)),geometry=True)
        self.assertEqual(self.scan(t),[('ROW_CHECK',(429,307,628,345))])
    def test_strict_scroll_geometry_rejected(self):
        name='Scroll for Gloves for ATT 60%'
        t=self.tracker(rows((name,30000)),geometry=True,item=name)
        self.assertEqual(self.scan(t),[])
        t._inventory_frame.assert_not_called()
    def test_lost_geometry_clears(self):
        t=self.tracker(rows(('Ribbon',30000)),geometry=True)
        t._find_geometry_anchor=Mock(side_effect=[(568,214),None])
        self.assertEqual(self.scan(t),[])
        self.assertIsNone(t._latest)
    def test_seller_pixels_not_ocr(self):
        t=self.tracker(rows(('Ribbon',30000)))
        with patch('beast_inventory.prepare_ocr',wraps=prepare_ocr) as secondary:
            self.assertTrue(self.scan(t))
            self.assertEqual(set(secondary.call_args.args[1]),set(range(6)))
        self.assertEqual([i for i,_ in t._row_cache.recognize.call_args.args[2]],list(range(6)))

if __name__=='__main__':unittest.main()
