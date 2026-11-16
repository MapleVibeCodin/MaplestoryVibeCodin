import unittest
from native_ocr import winocr_hits

class TestWindowsOCRConversion(unittest.TestCase):
    def test_word_coordinates_and_name(self):
        data={'lines':[{'text':'porkypork','words':[{'text':'porkypork','bounding_rect':{'x':110,'y':45,'width':82,'height':15}}]}]}
        hits=winocr_hits(data,'porkypork',0,80)
        self.assertEqual(len(hits),1)
        self.assertEqual(hits[0].box,(110,125,192,140))

    def test_partial_4_letters(self):
        data={'lines':[{'text':'pork','words':[{'text':'pork','bounding_rect':{'x':24,'y':12,'width':42,'height':17}}]}]}
        hits=winocr_hits(data,'porkypork')
        self.assertEqual(len(hits),1)
        self.assertEqual(hits[0].mode,'PARTIAL4')

    def test_unrelated_text_is_ignored(self):
        data={'lines':[{'text':'AnotherShop','words':[{'text':'AnotherShop','bounding_rect':{'x':24,'y':12,'width':90,'height':17}}]}]}
        self.assertEqual(winocr_hits(data,'porkypork'),[])

if __name__=='__main__':unittest.main()
