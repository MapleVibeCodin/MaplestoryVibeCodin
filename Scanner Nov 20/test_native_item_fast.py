import unittest
from unittest.mock import patch
from native_item_fast import load_atlas, decode_columns, pixel_columns, native_item_candidates, native_price, ocr_name_candidates
from shop_inventory import SCALE
import test_metascan_capture

def render_text(text):
    atlas,_=load_atlas()
    bychar={c:cols for cols,chars in atlas.items() for c in chars if len(c)==1}
    cols=[]
    for i,c in enumerate(text):
        if c==' ':cols.extend([0]*3);continue
        if cols and cols[-1]!=0:cols.append(0)
        cols.extend(bychar[c])
    return tuple(cols)

def frame_with_names():
    test=test_metascan_capture.FastCaptureTests()
    raw,w,h,s=test.combined()
    buf=bytearray(raw)
    for row,(name,price) in enumerate([('Dark Shadow Pants','1 for 64,999 mesos'),
                                       ('Dark Shadow Pants','1 for 69,999 mesos'),
                                       ('Dark Shadow Pants','1 for 74,999 mesos'),
                                       ('Marine Shadow Pants','1 for 8,888 mesos')]):
        for offset,text in ((4,name),(21,price)):
            cols=render_text(text)
            assert len(cols)<=158
            for x,bits in enumerate(cols):
                for y in range(14):
                    if bits>>y&1:
                        at=(73+23+row*40+offset+y)*s+(2+40+x)*3
                        buf[at:at+3]=b'\x00'*3
    return bytes(buf),w,h,s

class NativeTests(unittest.TestCase):
    def test_exact_atlas_decode(self):
        self.assertEqual(decode_columns(render_text('Dark Shadow Pants')),'Dark Shadow Pants')
        self.assertEqual(decode_columns(render_text('Marine Shadow Pants')),'Marine Shadow Pants')
        self.assertIsNone(native_price('1 for 6?,999 mesos'))
        self.assertEqual(native_price('1 for 1 5,555 mesos'),15555)

    def test_all_matching_names_and_price(self):
        from metascan_fast import crop_bgr
        f=crop_bgr(frame_with_names(),2,73,204,263)
        self.assertEqual(native_item_candidates(f,'Dark Shadow Pants',69999,lambda f,i:False),
                         [(0,'FAST_NAME'),(1,'FAST_PRICE'),(2,'FAST_NAME')])
        self.assertEqual(native_item_candidates(f,'Dark Shadow',69999,lambda f,i:False),[])
        self.assertEqual(native_item_candidates(f,'Dagger Attack Scroll: Intermediate',69999,lambda f,i:False),[])

    def test_production_native_skips_ocr(self):
        t=test_metascan_capture.FastCaptureTests().production_tracker('Dark Shadow Pants')
        t._native_fast=True
        t._key=(1,(0,0,1366,768),'listing','seller','Dark Shadow Pants',69999,0,1)
        f=frame_with_names()
        with patch('shop_inventory.capture_client',return_value=f) as capture, patch.object(t._row_cache,'recognize',side_effect=AssertionError('OCR must not run')):
            t._scan(t._key)
        self.assertEqual(capture.call_count,2)
        self.assertEqual([m for m,b in t._latest['hits']],['FAST_NAME','FAST_PRICE','FAST_NAME'])
        self.assertTrue(t._latest['timing']['native_fast'])

    def test_changed_native_frame_never_publishes(self):
        t=test_metascan_capture.FastCaptureTests().production_tracker('Dark Shadow Pants')
        t._native_fast=True
        t._key=(1,(0,0,1366,768),'listing','seller','Dark Shadow Pants',69999,0,1)
        with patch('shop_inventory.capture_client',side_effect=[frame_with_names(),test_metascan_capture.FastCaptureTests().combined()]):
            t._scan(t._key)
        self.assertEqual(t._latest['hits'],[])

    def test_ocr_name_only_fallback(self):
        lines=[{'text':'Dark Shadow Pants','y':37*SCALE},{'text':'1 for 64,999 mesos','y':55*SCALE}]
        self.assertEqual(ocr_name_candidates(lines,[False]*6,'Dark Shadow Pants',69999),[(0,'FAST_NAME')])
        self.assertEqual(ocr_name_candidates(lines,[False]*6,'Dark Shadow',69999),[])

    def test_real_dark_shadow_pants_native_columns(self):
        # Binary glyph column masks from 07-00-51 native shop screenshot.
        # No private chat, seller pixels, or full image are published.
        def unpack(s):
            return tuple(int(s[i:i+4],16) for i in range(0,len(s),4))
        self.assertEqual(decode_columns(unpack('0000000007fc0404040404040404020801f000000000032004900490029007e00000000007f000200010000007fc008000c00320041000000000000000000338044404440444044403980000000007fc00200010001007e000000000032004900490029007e00000000003e004100410042007fc0000000003e004100410041003e00000003001c0060001c0003001c0060001c00030000000000000000007fc0044004400440044003800000000032004900490029007e00000000007f000200010001007e00000001007fc0410000002600490049004900320')),'Dark Shadow Pants')
        self.assertEqual(native_price(decode_columns(unpack('000000000010000807fc000000000000000000000000001007f80014000003e004100410041003e00000000007f000200010000000000000000027804840484044403f800000000027804840484044403f8000000001c0000000000027804840484044403f800000000027804840484044403f800000000027804840484044403f80000000000000000000007f000200010001007e000200010001007e00000000003e004900490049002e000000000026004900490049003200000000003e004100410041003e00000000002600490049004900320'))),69999)

if __name__=='__main__':unittest.main()
