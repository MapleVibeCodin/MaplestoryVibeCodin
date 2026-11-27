import unittest
import struct
import time
from unittest.mock import patch
import shop_inventory as inv


def synthetic_frame():
    w,h=204,263
    stride=w*3
    pixels=bytearray([227,217,205]*(w*h))
    for row in range(inv.ROWS):
        y0=inv.NAME_ROW_TOP+row*inv.STEP
        # Unique dark pixel glyph-like patterns in the name band.
        for x in range(40+row,55+row):
            for dy in range((x+row)%4,15,4):
                i=(y0+dy)*stride+x*3
                pixels[i:i+3]=b'\x00\x00\x00'
        # Dark pixels below the name band represent a price and must not enter
        # the compact item-name OCR image or its cache key.
        py=47+row*inv.STEP
        i=py*stride+120*3
        pixels[i:i+3]=b'\x00\x00\x00'
    return bytes(pixels),w,h,stride


class FakeOCR:
    def __init__(self,names):
        self.names=names
        self.calls=0
        self.last_png=None
    def recognize(self,png):
        self.calls+=1;self.last_png=png
        return [{'text':self.names[slot],'y':(slot*inv.NAME_ROW_SLOT+8)*inv.SCALE}
                for slot in range(len(self.names)) if self.names[slot]]


class NameOnlyPreparationTests(unittest.TestCase):
    def test_only_name_bands_are_cropped(self):
        frame=synthetic_frame()
        png,layout=inv.prepare_name_ocr(frame,(1,4))
        width,height=struct.unpack('>II',png[16:24])
        self.assertEqual((width,height),(158*3,(2*inv.NAME_ROW_HEIGHT+inv.NAME_ROW_GAP)*3))
        self.assertEqual(layout,{0:1,1:4})
    def test_name_cache_hits_ignore_price_pixels(self):
        frame=synthetic_frame()
        ocr=FakeOCR(['Potion','Hat','Brown Dress Shoes','Cape','Gloves','Boots'])
        cache=inv.NameOCRCache()
        names,hits,misses,used=cache.recognize(frame,range(6),ocr)
        self.assertEqual(names[2],'Brown Dress Shoes')
        self.assertEqual((hits,misses,used),(0,6,True))
        self.assertEqual(ocr.calls,1)
        # Change only price-band pixels. Name-only fingerprint should hit cache.
        buf,w,h,stride=frame
        changed=bytearray(buf)
        changed[47*stride+120*3:47*stride+120*3+3]=b'\xff\xff\xff'
        names2,hits2,misses2,used2=cache.recognize((bytes(changed),w,h,stride),range(6),ocr)
        self.assertEqual(names2,names)
        self.assertEqual((hits2,misses2,used2),(6,0,False))
        self.assertEqual(ocr.calls,1)
    def test_exact_name_unique_only(self):
        names={0:'Potion',2:'Brown Dress Shoes',4:'Cape'}
        self.assertEqual(inv.exact_name_rows(names,'Brown Dress Shoes'),[2])
        self.assertEqual(inv.exact_name_rows(names,'Brown Dress Shoes',{2}),[])
        self.assertEqual(inv.exact_name_rows({1:'Brown Dress Shoes',3:'Brown Dress Shoes'},'Brown Dress Shoes'),[])
        self.assertEqual(inv.exact_name_rows({1:'Brown Dress Sh...'},'Brown Dress Shoes'),[])
        self.assertEqual(inv.exact_name_rows({1:'Brown Dress Shoes'},' brown   dress shoes '),[1])
        self.assertEqual(inv.exact_name_rows({1:'Brown Dress Shoes',3:'Brown Dress Sh...'},'Brown Dress Shoes'),[])
    def test_empty_ocr_read_is_retried(self):
        frame=synthetic_frame()
        ocr=FakeOCR(['','','','','',''])
        cache=inv.NameOCRCache()
        names,hits,misses,used=cache.recognize(frame,range(6),ocr)
        self.assertEqual(ocr.calls,1)
        self.assertEqual(len(cache.entries),0)
        ocr.names=['Potion','Hat','Brown Dress Shoes','Cape','Gloves','Boots']
        names,hits,misses,used=cache.recognize(frame,range(6),ocr)
        self.assertEqual(ocr.calls,2)
        self.assertEqual(names[2],'Brown Dress Shoes')

    def test_numpy_and_python_fallback_have_same_png_dimensions(self):
        frame=synthetic_frame()
        if inv.np is None:self.skipTest('NumPy unavailable')
        with patch.object(inv,'np',None):
            png,layout=inv.prepare_name_ocr(frame,(0,5))
        self.assertEqual(struct.unpack('>II',png[16:24]),(158*3,(2*20+8)*3))
        self.assertEqual(layout,{0:0,1:5})
        numpy_png,_=inv.prepare_name_ocr(frame,(0,5))
        self.assertEqual(png,numpy_png)


class FastTargetScanTests(unittest.TestCase):
    def tracker(self):
        frame=synthetic_frame()
        client=(0,0,1366,768)
        key=(123,client,'listing','seller','Brown Dress Shoes',100000,0,1)
        t=inv.ShopInventoryTracker.__new__(inv.ShopInventoryTracker)
        t._lock=__import__('threading').Lock()
        t._key=key;t._latest=None;t._digest=None;t._observed_at=None
        t._busy=True;t._closed=False;t._next=0;t._generation=1;t._request_at=time.perf_counter()-0.01
        t._ocr_failures=0;t._name_cache=type('Cache',(),{'recognize':lambda self,frame,rows,ocr:({2:'Brown Dress Shoes'},0,len(rows),True)})()
        t._ocr=object();t._find_anchor=lambda client:(568,214)
        t._inventory_frame=lambda client,anchor:frame
        return t,frame
    def test_unique_item_published_after_one_observation(self):
        t,frame=self.tracker()
        sections=tuple((i,bytes([i+1])*20) for i in range(-1,6))
        with patch('shop_inventory.tooltip_blocked_rows',return_value=set()),patch('shop_inventory.tooltip_prefixes',return_value={}),patch('shop_inventory.section_fingerprints',return_value=sections):
            t._scan(t._key)
        self.assertEqual(t._latest['hits'],[('ROW_CHECK',(429,387,628,425))])
        self.assertIn('Exact item name',t._latest['status'])
        self.assertEqual(t._latest['timing']['fast_path'],'name_only')
        self.assertIsNotNone(t._latest['timing']['shop_open_to_target_ms'])
        self.assertFalse(t._busy)
    def test_ambiguous_or_blocked_name_does_not_highlight(self):
        t,frame=self.tracker()
        t._name_cache=type('Cache',(),{'recognize':lambda self,frame,rows,ocr:({1:'Brown Dress Shoes',3:'Brown Dress Shoes'},0,len(rows),True)})()
        sections=tuple((i,bytes([i+1])*20) for i in range(-1,6))
        with patch('shop_inventory.tooltip_blocked_rows',return_value=set()),patch('shop_inventory.tooltip_prefixes',return_value={}),patch('shop_inventory.section_fingerprints',return_value=sections):
            t._scan(t._key)
        self.assertEqual(t._latest['hits'],[])
        self.assertIn('Multiple exact item names',t._latest['status'])
    def test_sold_row_is_not_targeted(self):
        t,frame=self.tracker()
        t._name_cache=type('Cache',(),{'recognize':lambda self,frame,rows,ocr:
            ({2:'Brown Dress Shoes'} if 2 in rows else {},0,len(rows),True)})()
        sections=tuple((i,bytes([i+1])*20) for i in range(-1,6))
        with patch('shop_inventory.tooltip_blocked_rows',return_value=set()),patch('shop_inventory.tooltip_prefixes',return_value={}),patch('shop_inventory.section_fingerprints',return_value=sections),patch('shop_inventory.sold_row_mask',side_effect=lambda frame,row:row==2):
            t._scan(t._key)
        self.assertEqual(t._latest['hits'],[])

    def test_blocked_row_is_not_recognized(self):
        t,frame=self.tracker()
        sections=tuple((i,bytes([i+1])*20) for i in (-1,0,1,3,4,5))
        with patch('shop_inventory.tooltip_blocked_rows',return_value={2}),patch('shop_inventory.tooltip_prefixes',return_value={}),patch('shop_inventory.section_fingerprints',return_value=sections):
            t._scan(t._key)
        self.assertEqual(t._latest['hits'],[])


if __name__=='__main__':
    unittest.main()
