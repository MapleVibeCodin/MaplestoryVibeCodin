"""Guard historical room corrections without pretending they are raw image replays."""
import unittest
from shop_position import (
    room_theme, entry_portal_point, entry_shop_point, shop_marker,
    shop_offscreen_notice, read_shop_position,
)

GRASS={1:11,2:44,3:48,4:50,5:45,6:8,13:47,14:48,15:40,16:0}
CAVE={7:121,9:149,11:97,17:97}
FINE={4:45,5:48,11:66,18:48}

class PriorShopPlacementTests(unittest.TestCase):
    def test_all_twenty_room_anchors_and_resolution_specific_offsets(self):
        for w,h in ((1280,720),(1366,768)):
            for room in range(1,21):
                with self.subTest(room=room,size=(w,h)):
                    theme='grass' if room in GRASS else 'cave'
                    self.assertEqual(room_theme(room),theme)
                    anchor=(w-225,h-GRASS[room]) if theme=='grass' else (w//2+58,h//2+CAVE.get(room,108))
                    if room==9 and (w,h)==(1366,768):anchor=(633,488)
                    self.assertEqual(entry_portal_point(room,(w,h)),anchor)
                    for left,top in ((0,0),(50,50),(100,100),(91,86)):
                        pin={'theme':theme,'left':left,'top':top}
                        baseline=entry_shop_point(pin,room,(w,h),anchor)
                        default=entry_shop_point(pin,room,(w,h))
                        delta=FINE.get(room,0) if (w,h)==(1366,768) else 0
                        self.assertEqual(default,(baseline[0],baseline[1]+delta))

    def test_original_platform_corrections(self):
        for room,delta in ((2,148),(4,142),(6,184),(16,192)):
            for size in ((1280,720),(1366,768)):
                with self.subTest(room=room,size=size):
                    w,h=size
                    pin={'theme':'grass','left':50,'top':50}
                    before=entry_shop_point(pin,room,size,(w-225,h-192))
                    after=entry_shop_point(pin,room,size)
                    self.assertEqual(after,(before[0],before[1]+delta+(FINE.get(room,0) if size==(1366,768) else 0)))

    def test_partial_shop_signs_not_dropped(self):
        client=(17,42,1366,768);window=(15,4,1370,808)
        for point in ((-20,300),(1390,300),(600,100),(600,880)):
            with self.subTest(point=point):
                box=shop_marker(point,client,window)
                self.assertIsNotNone(box)
                l,t,r,b=box
                self.assertLess(l,r);self.assertLess(t,b)
                self.assertGreaterEqual(l,4);self.assertLessEqual(r,1366)
                self.assertGreaterEqual(t,40);self.assertLessEqual(b,804)

    def test_offscreen_direction_and_wrong_theme(self):
        size=(1366,768);client=(0,0,*size)
        for point,word in (((600,50),'above'),((600,1000),'below'),((-100,300),'left'),((1500,300),'right')):
            self.assertIsNone(shop_marker(point,client,client))
            self.assertIn(word,shop_offscreen_notice(point,size))
        self.assertIsNone(read_shop_position({'theme':'cave','left':50,'top':50},4))
        self.assertIsNone(entry_shop_point({'theme':'grass','left':50,'top':50},18,size))
