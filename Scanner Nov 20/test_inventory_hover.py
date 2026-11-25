"""Offline hover and shifted shop gate checks."""
import unittest
from shop_inventory import inventory_tooltip_visible,tooltip_blocked_rows,locate_shop,GREEN,ORANGE,pick_rows,RowOCRCache,section_fingerprints,SCALE
from camera_alignment import room_title_present,_ROOM_PREFIX_BITS,_ROOM_BRACKET_BITS
from shop_inventory import displayed_buy_step,price_in_display_bucket,sold_row_mask,sold_line_cutoff,stable_sold_hits,selected_row_mask,row_ink,stable_item_hits

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
    def test_room_title_real_mask_fixtures(self):
        # Actual native FM4 PNG and entrance video masks, independent of
        # the template sampled from FM9 video. No account or seller pixels.
        native=(147580708233393733694,221367684528231940102,261829095619404285830,226610112519440769414,226871325150414451134,239553460601601388934,222268643591044215174,235815471253019632006,155759485921842545030)
        entrance=(147580708233393733694,221367684528231940102,262405556373856241542,226610112519440769414,226871325150414451134,239553460601601388934,222268643591044215174,236103701629171872134,151111771106385625478)
        entrance_bracket=(504,24,24,24,504,24,24,24,504)
        def make(prefix,bracket,x,y):
            buf,w,h,s=frame(200,120)
            for dy,(p,b) in enumerate(zip(prefix,bracket)):
                row=p|(b<<70)
                for dx in range(79):
                    if row&(1<<dx):
                        i=(y+dy)*s+(x+dx)*3;buf[i:i+3]=bytes((240,240,240))
            return buf,w,h,s
        self.assertFalse(room_title_present(*frame(200,120)))
        self.assertTrue(room_title_present(*make(native,_ROOM_BRACKET_BITS,51,44)))
        self.assertTrue(room_title_present(*make(_ROOM_PREFIX_BITS,_ROOM_BRACKET_BITS,48,42)))
        self.assertFalse(room_title_present(*make(entrance,entrance_bracket,50,44)))
        self.assertFalse(room_title_present(*make(native,(0,)*9,50,44)))
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
class VideoSoldRowTests(unittest.TestCase):
    def test_brown_pilfer_faded_row(self):
        buf,w,h,s=frame(204,263)
        # Native crop measurements from 03-42-22 recording: pale row
        # median BGR (248,243,242); adjacent active row (227,216,204).
        for row,bg in ((0,(248,243,242)),(1,(227,216,204)),(2,(248,243,242))):
            for y in range(23+row*40,23+(row+1)*40):
                for x in range(40,198):
                    i=y*s+x*3;buf[i:i+3]=bytes(bg)
            for y in range(28+row*40,34+row*40):
                for x in range(55,80):
                    i=y*s+x*3;buf[i:i+3]=bytes((215,215,215) if row!=1 else (40,40,40))
        f=(buf,w,h,s)
        self.assertTrue(sold_row_mask(f,0))
        self.assertFalse(sold_row_mask(f,1))
        self.assertTrue(sold_row_mask(f,2))
        self.assertGreater(sold_line_cutoff(f,30),215)
        self.assertLess(sold_line_cutoff(f,30),244)
    def test_brown_pilfer_sold_candidate_with_unreadable_price(self):
        lines=[{'y':5*SCALE,'text':'AznFireghost'},{'y':33*SCALE,'text':'Brown Pilfer'},
               {'y':73*SCALE,'text':"Arwen's Glass Shoe"},{'y':92*SCALE,'text':'1 for 70,000 mesos'}]
        self.assertEqual(pick_rows(lines,[True,False,True,False,False,False],'AznFireghost','Brown Pilfer',70000)[0],[(0,'SOLD_CHECK')])
    def test_other_row_hover_does_not_discard_sold_target(self):
        before={-1:b'seller',0:b'pilfer',1:b'shoe',2:b'scroll'}
        after={-1:b'seller',0:b'pilfer',1:b'hover'}
        self.assertEqual(stable_sold_hits([(0,'SOLD')],before,after),[(0,'SOLD_CHECK')])
        self.assertEqual(stable_sold_hits([(0,'MATCH')],before,after),[])
        self.assertEqual(stable_sold_hits([(0,'SOLD')],before,{-1:b'seller',0:b'changed'}),[])
        self.assertEqual(stable_sold_hits([(0,'SOLD')],before,{-1:b'other',0:b'pilfer'}),[])

class VideoSelectedRowTests(unittest.TestCase):
    def test_brown_dress_shoes_orange_selection(self):
        buf,w,h,s=frame(204,263)
        # Measured median BGR from the 03-46-13 clip, at 15.5s.
        for row,bg in ((0,(227,216,204)),(4,(40,152,230)),(5,(124,75,70))):
            for y in range(23+row*40,23+(row+1)*40):
                for x in range(40,198):
                    i=y*s+x*3;buf[i:i+3]=bytes(bg)
        f=(buf,w,h,s)
        self.assertTrue(selected_row_mask(f,4))
        self.assertFalse(selected_row_mask(f,0))
        self.assertFalse(selected_row_mask(f,5))
        self.assertFalse(sold_row_mask(f,4))
        self.assertFalse(row_ink(40,152,230,145,True))
        self.assertTrue(row_ink(15,20,30,145,True))
        self.assertFalse(row_ink(255,255,255,145,True))
    def test_49999_rounded_50k(self):
        lines=[{'y':5*SCALE,'text':'Desires'},{'y':(33+4*40)*SCALE,'text':'Brown Dress Shoes'},
               {'y':(52+4*40)*SCALE,'text':'1 for 49,999 mesos'}]
        step=displayed_buy_step('Buy 50K',50000)
        self.assertEqual(pick_rows(lines,[False]*6,'Desires','Brown Dress Shoes',50000,buy_step=step)[0],[(4,'PRICE_CHECK')])
        self.assertEqual(pick_rows(lines,[False]*6,'Desires','Brown Dress Shoes',50000)[0],[])
    def test_active_row_independent_revalidation(self):
        before={-1:b'seller',0:b'other',4:b'shoes',5:b'other2'}
        after={-1:b'seller',0:b'changed',4:b'shoes'}
        self.assertEqual(stable_item_hits([(4,'MATCH')],before,after),[(4,'ROW_CHECK')])
        self.assertEqual(stable_item_hits([(4,'PRICE_CHECK')],before,after),[(4,'PRICE_CHECK')])
        self.assertEqual(stable_item_hits([(4,'MATCH')],before,{-1:b'seller',4:b'sold'}),[])
        self.assertEqual(stable_item_hits([(4,'MATCH')],before,{-1:b'wrong',4:b'shoes'}),[])
        self.assertEqual(stable_item_hits([(4,'MATCH')],before,{-1:b'seller'}),[])

class ArmedInventoryTests(unittest.TestCase):
    def setUp(self):
        import ast
        import pathlib
        from types import SimpleNamespace
        tree=ast.parse(pathlib.Path(__file__).with_name('fm_rush.py').read_text(encoding='utf-8'))
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='FMApp')
        nodes=[n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name in ('inventory_target','refresh_overlays')]
        ns={}
        exec(compile(ast.Module(body=nodes,type_ignores=[]),'fm_rush.py','exec'),ns)
        self.target=ns['inventory_target']
        self.refresh=ns['refresh_overlays']
        self.deal=SimpleNamespace(cc=38,fm=10,ign='Pillarious',item='Ghost Costume',buy_mesos=66700,shop_position=None)
        self.archive=SimpleNamespace(chase_locked=False)
        self.app=SimpleNamespace(archive=self.archive,displayed_listing='current',manual_override_at=None)
        self.current=('current',self.deal)
    def test_armed_displayed_listing(self):
        self.assertIs(self.target(self.app,self.current),self.deal)
        self.assertFalse(self.archive.chase_locked)
    def test_no_stale_or_manual_listing(self):
        self.assertIsNone(self.target(self.app,None))
        self.assertIsNone(self.target(self.app,('other',self.deal)))
        self.app.manual_override_at=1
        self.assertIsNone(self.target(self.app,self.current))
    def test_locked_listing_unchanged(self):
        self.archive.chase_locked=True
        self.app.displayed_listing=None
        self.assertIs(self.target(self.app,self.current),self.deal)
    def test_room_only_armed_overlay_without_navigation(self):
        from types import SimpleNamespace as NS
        class Var:
            def __init__(self):self.value=''
            def get(self):return self.value
            def set(self,value):self.value=value
        class Pin:
            def __init__(self):self.visible=False
            def hide(self):self.visible=False
            def show_many(self,*args):self.visible=True
        calls=[]
        room=[True]
        ns=self.refresh.__globals__
        ns.update(window_rect=lambda h:(0,0,1366,768),window_client_rect=lambda h:(0,0,1366,768),
                  ENTRY_CLIENTS={(1366,768)},window_has_focus=lambda h:True,
                  capture_client=lambda *a,**k:(b'',1,1,3),room_title_present=lambda *a:room[0])
        self.app.inventory_target=lambda current:self.target(self.app,current)
        self.app.web_only=False
        self.app.shop=NS(selected_hwnd=lambda:1,notice=Var(),offscreen_notice=Var())
        self.app._inventory=NS(get=lambda h,c,d:(calls.append(d) or {'hits':[('SOLD_CHECK',(1,2,3,4))],'status':'Sold candidate'}),reset=lambda:calls.append('reset'))
        self.app._entrance_camera=NS(get=lambda *a:None,reset=lambda:None)
        self.app._portal_alignment=None
        for name in ('item','entrance','channel','shop'):
            setattr(self.app,name+'_pin',Pin())
            setattr(self.app,'_'+name+'_preview',None)
        self.refresh(self.app,self.current)
        self.assertEqual(calls,[self.deal])
        self.assertTrue(self.app.item_pin.visible)
        self.assertFalse(self.app.shop_pin.visible)
        self.assertFalse(self.app.channel_pin.visible)
        self.assertFalse(self.archive.chase_locked)
        room[0]=False
        self.refresh(self.app,self.current)
        self.assertEqual(calls,[self.deal,'reset'])
        self.assertFalse(self.app.item_pin.visible)

class RecordedMinimapTests(unittest.TestCase):
    def test_four_recorded_title_masks(self):
        # Actual thresholded ROI rows extracted from two lossless PNGs and two video frames.
        fixtures=[{"source":"image(20261125-162743).png","client_origin":[18,42],"expected_room":True,"roi":[44,38,91,21],"rows":["0x870e0c838199c68d1b180","0x0","0x0","0x0","0x0","0x0","0x600020006000e3800000f80","0x610030006000e3800000180","0x71c078c66f3cf181831e180","0x687031236362d1824486180","0x68183131e370d58264c6f80","0x647033f1e36cd587efc6180","0x7d8030326366dd8060c6180","0x600033226366cd864c86180","0x600021c6636cc9838706180","0x0","0x0","0x0","0x0","0x0","0x0"]},{"source":"image(20261125-164333).png","client_origin":[18,42],"expected_room":False,"roi":[44,38,91,21],"rows":["0x870e0c838199c68d1b180","0x0","0x0","0x0","0x0","0x0","0x1f820006000e3800000f80","0x1830006000e3800000180","0x6c1878c66f3cf181831e180","0x4c1831236362d1824486180","0x4df83131e370d58264c6f80","0x4c1833f1e36cd587efc6180","0x4c1830326366dd8060c6180","0x4c1833226366cd864c86180","0x4df821c6636cc9838706180","0x0","0x0","0x0","0x0","0x0","0x0"]},{"source":"03-55-12.mp4 @ 2.8s","expected_room":True,"roi":[44,38,91,21],"rows":["0x820c0c838198c60d1b180","0x0","0x0","0x0","0x0","0x0","0x300000006000e3800000f80","0x4d0030006000e3800000180","0x4dc078c66f3cf381839e180","0x4c7031236362d1824486180","0x4c183131e370d58264c6f80","0x707033f1e364d587efc6180","0x418030326366dd8060c6180","0x4c0033326366cd866cc6180","0x380020c66364c9810306180","0x0","0x0","0x0","0x0","0x0","0x0"]},{"source":"03-55-12.mp4 @ 0s","expected_room":False,"roi":[44,38,91,21],"rows":["0x830e0c838198c6cd1b180","0x0","0x0","0x0","0x0","0x0","0x1f820006000e3800000f80","0x1830006000e3800000180","0x6c1878e66f3cf381c31e180","0x4c1831236362d1824486180","0x4df83131e370d58264c6f80","0x4c1833f1e36cd587efc6180","0x4c1830326366dd8060c6180","0x4c1833326366cd866cc6180","0x4df820c4636cc9810206180","0x0","0x0","0x0","0x0","0x0","0x0"]}]
        for f in fixtures:
            with self.subTest(source=f['source']):
                buf,w,h,s=frame(200,120)
                x,y,rw,rh=f['roi']
                for dy,row in enumerate(f['rows']):
                    bits=int(row,16)
                    for dx in range(rw):
                        if bits&(1<<dx):
                            i=(y+dy)*s+(x+dx)*3;buf[i:i+3]=bytes((240,240,240))
                self.assertEqual(room_title_present(buf,w,h,s),f['expected_room'])

class TrackerFailureTests(unittest.TestCase):
    def tracker(self):
        from shop_inventory import ShopInventoryTracker
        import threading, time
        t=ShopInventoryTracker.__new__(ShopInventoryTracker)
        t._lock=threading.Lock();t._key=(1,(0,0,1366,768),'listing','seller','item',100,0,1)
        t._latest={'status':'Exact name + price','hits':[('MATCH',(1,2,3,4))]}
        t._digest=('previous',);t._observed_at=time.monotonic()
        t._busy=True;t._closed=False;t._next=0;t._generation=1;t._ocr_failures=0
        t._find_anchor=lambda client:(568,214)
        return t
    def test_initial_capture_failure_clears_hit(self):
        from unittest.mock import patch
        t=self.tracker()
        with patch('shop_inventory.capture_client',return_value=None):
            t._scan(t._key)
        self.assertEqual(t._latest['hits'],[])
        self.assertIsNone(t._digest)
        self.assertFalse(t._busy)
    def test_expiry_while_worker_busy(self):
        from types import SimpleNamespace
        t=self.tracker();t._observed_at=0
        d=SimpleNamespace(listing_id='listing',ign='seller',item='item',buy_mesos=100,raw_text='')
        self.assertEqual(t.get(1,(0,0,1366,768),d)['hits'],[])
        self.assertIsNone(t._digest)
    def test_generation_guard_rejects_old_publish(self):
        t=self.tracker();old=t._key;t.reset()
        t._publish(old,{'hits':[('MATCH',(1,2,3,4))]})
        self.assertIsNone(t._latest)
    def test_malformed_worker_capture_clears_and_recovers(self):
        from unittest.mock import patch
        t=self.tracker()
        with patch('shop_inventory.capture_client',side_effect=TypeError('bad frame')):
            t._scan(t._key)
        self.assertEqual(t._latest['hits'],[])
        self.assertIn('TypeError',t._latest['status'])
        self.assertFalse(t._busy)

class TrackerGeometryTests(TrackerFailureTests):
    def ready(self, geometry, item='item'):
        from types import SimpleNamespace
        t=self.tracker()
        t._key=(1,(0,0,1366,768),'listing','seller',item,100,0,1)
        t._latest=None;t._digest=None
        t._find_anchor=lambda client:None if geometry else (568,214)
        t._find_geometry_anchor=lambda client:(568,214)
        lines=[{'y':5*SCALE,'text':'seller'},{'y':33*SCALE,'text':item},
               {'y':52*SCALE,'text':'1 for 100 mesos'}]
        t._row_cache=SimpleNamespace(recognize=lambda *args:(lines,[False]*6,True))
        t._scroll_checks={}
        return t

    def test_geometry_only_cannot_publish_green(self):
        from unittest.mock import patch
        t=self.ready(True)
        with patch('shop_inventory.capture_client',return_value=frame(204,263)):
            t._scan(t._key)
        self.assertEqual(t._latest['hits'][0][0],'ROW_CHECK')
        self.assertTrue(t._latest['timing']['geometry_fallback'])
        self.assertTrue(t._digest[3])

    def test_exact_path_remains_green(self):
        from unittest.mock import patch
        t=self.ready(False)
        with patch('shop_inventory.capture_client',return_value=frame(204,263)):
            t._scan(t._key)
        self.assertEqual(t._latest['hits'][0][0],'MATCH')
        self.assertFalse(t._latest['timing']['geometry_fallback'])

    def test_geometry_cannot_accept_scroll(self):
        from unittest.mock import patch
        t=self.ready(True,'Scroll for Gloves for ATT 60%')
        with patch('shop_inventory.capture_client') as capture:
            t._scan(t._key)
        capture.assert_not_called()
        self.assertEqual(t._latest['hits'],[])

    def test_lost_geometry_invalidates_candidate(self):
        from unittest.mock import patch
        t=self.ready(True)
        with patch.object(t,'_find_geometry_anchor',side_effect=[(568,214),None]), patch('shop_inventory.capture_client',return_value=frame(204,263)):
            t._scan(t._key)
        self.assertIsNone(t._latest)
        self.assertIsNone(t._digest)

    def test_switch_to_geometry_invalidates_exact_cache(self):
        from unittest.mock import patch
        t=self.ready(False)
        with patch('shop_inventory.capture_client',return_value=frame(204,263)):
            t._scan(t._key)
            self.assertEqual(t._latest['hits'][0][0],'MATCH')
            t._find_anchor=lambda client:None
            t._scan(t._key)
        self.assertEqual(t._latest['hits'][0][0],'ROW_CHECK')
        self.assertTrue(t._digest[3])

if __name__=='__main__':unittest.main()
