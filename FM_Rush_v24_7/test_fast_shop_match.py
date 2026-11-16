import unittest
from fast_shop_match import candidates, pick_unique, StickyResult, Hit, overlap


def box(x,y,w=76,h=18):
    return [[x,y],[x+w,y],[x+w,y+h],[x,y+h]]

class TestFastShopMatch(unittest.TestCase):
    def test_four_character_fragment(self):
        hits=candidates(['pork', 'otherstuff'],[box(30,60),box(200,70)],[.9,.95],'porkypork')
        self.assertEqual(len(hits),1)
        self.assertEqual(hits[0].mode,'PARTIAL4')
        self.assertEqual(hits[0].box,(30,60,106,78))

    def test_short_random_three_char_not_accepted(self):
        self.assertEqual(candidates(['por'],[box(40,60)],[.98],'porkypork'),[])
        self.assertTrue(overlap('porkypork','orky',4))

    def test_exact_beats_partial_and_ambiguity(self):
        hs=candidates(['pork', 'porkypork'],[box(10,20),box(200,20)],[.95,.95],'porkypork')
        best=pick_unique(hs)
        self.assertIsNotNone(best)
        self.assertEqual(best.mode,'EXACT')
        self.assertEqual(best.box[0],200)
        same=candidates(['pork', 'pork'],[box(10,20),box(200,20)],[.95,.95],'porkypork')
        self.assertIsNone(pick_unique(same))

    def test_persistent_pin_and_new_target_reset(self):
        s=StickyResult()
        s.set_target('porkypork')
        self.assertIsNone(s.box)
        s.found(Hit('pork',(10,30,70,54),.9,'PARTIAL4'))
        self.assertEqual(s.mode,'PARTIAL')
        s.missed()
        self.assertEqual(s.mode,'LAST SEEN')
        self.assertEqual(s.box,(10,30,70,54))
        s.set_target('AnotherSeller')
        self.assertIsNone(s.box)
        self.assertEqual(s.mode,'SEARCHING')

if __name__=='__main__': unittest.main()
