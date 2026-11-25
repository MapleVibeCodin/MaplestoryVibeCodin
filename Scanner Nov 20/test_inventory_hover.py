"""Offline hover and shifted shop gate checks."""
import unittest
from shop_inventory import inventory_tooltip_visible,tooltip_blocked_rows,locate_shop,GREEN,ORANGE,pick_rows,RowOCRCache,section_fingerprints,SCALE
from camera_alignment import room_title_present,_ROOM_TITLE
from shop_inventory import displayed_buy_step,price_in_display_bucket,sold_row_mask,sold_line_cutoff,stable_sold_hits

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
if __name__=='__main__':unittest.main()
