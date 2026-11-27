"""Offline, no input/capture regression gate for Spatial build."""
import ast
import unittest
from pathlib import Path
from beast_spatial import edge_directions, clipped_directions, PointerAudit, CameraModeLatch

class Recorder:
    scope='locked'
    active='attempt-one'
    def __init__(self):self.rows=[]
    def _emit(self,event,**data):self.rows.append((event,data))

class SpatialTests(unittest.TestCase):
    def test_four_edges_and_diagonal(self):
        size=(1366,768)
        for point,expected in [((400,50),('ABOVE',)),((400,1000),('BELOW',)),
            ((-60,400),('LEFT',)),((1450,400),('RIGHT',)),((-60,50),('ABOVE','LEFT')),
            ((400,400),())]:
            with self.subTest(point=point):self.assertEqual(edge_directions(point,size),expected)
    def test_boundary_and_partial(self):
        self.assertEqual(edge_directions((400,96),(1366,768)),('ABOVE',))
        self.assertEqual(edge_directions((400,97),(1366,768)),())
        self.assertEqual(clipped_directions((400,97),(1366,768)),('ABOVE',))
        self.assertEqual(clipped_directions((10,400),(1280,720)),('LEFT',))
        self.assertEqual(clipped_directions((1275,400),(1280,720)),('RIGHT',))
    def test_correlated_terminal_once(self):
        rec=Recorder();audit=PointerAudit(rec,'shop',1.0)
        rec.active='different-attempt';audit.done('cancelled');audit.done('moved',ok=True)
        self.assertEqual([x[0] for x in rec.rows],['beast_pointer_request','beast_pointer_outcome'])
        self.assertEqual(rec.rows[0][1]['request_id'],rec.rows[1][1]['request_id'])
        self.assertEqual(rec.rows[1][1]['attempt'],'attempt-one')
        self.assertFalse(rec.rows[1][1]['ok'])
    def test_independent_requests_and_success(self):
        rec=Recorder();a=PointerAudit(rec,'shop',1);b=PointerAudit(rec,'channel',2)
        a.done('duplicate');b.done('moved',ok=True,total_ms=47.5)
        self.assertNotEqual(a.id,b.id)
        self.assertEqual(len(rec.rows),4)
        self.assertEqual(rec.rows[-1][1]['total_ms'],47.5)
        self.assertTrue(rec.rows[-1][1]['ok'])
    def test_unlocked_and_no_recorder(self):
        rec=Recorder();rec.scope='unlocked';PointerAudit(rec,'shop',1).done('unlocked')
        self.assertEqual(rec.rows,[])
        PointerAudit(None,'shop',1).done('unavailable')
    def test_camera_latch(self):
        latch=CameraModeLatch()
        self.assertEqual(latch.choose('a',None),('none',None))
        self.assertEqual(latch.choose('a',(252,128)),('landmark_estimate',(252,128)))
        for _ in range(50):
            self.assertEqual(latch.choose('a',None),('waiting_landmark',None))
            self.assertEqual(latch.choose('a',(252,128)),('landmark_estimate',(252,128)))
        self.assertEqual(latch.choose('b',None),('none',None))
    def test_exact_price_guard(self):
        import os,sys
        sys.path.insert(1,os.environ['BEAST_PINNED_SCANNER'])
        from shop_inventory import pick_rows
        from beast_inventory import exact_active_hits
        name='Pansy Earrings'
        def lines(prices):
            result=[]
            for i,price in enumerate(prices):
                result.append({'text':name,'y':(30+40*i)*3})
                if price is not None:result.append({'text':f'1 for {price:,} mesos','y':(49+40*i)*3})
            return result
        def match(prices,blocked=(),sold=(),target=30000):
            mask=[i in sold for i in range(6)]
            hits,_=pick_rows(lines(prices),mask,None,name,target,buy_step=0)
            return exact_active_hits(hits,blocked,None,lambda frame,row:row in sold)
        self.assertEqual(match([31000,30000]),[(1,'MATCH')])
        self.assertEqual(match([30000]),[(0,'MATCH')])
        for prices in ([31000],[29999],[30001],[None],[30000,30000],[]):
            with self.subTest(prices=prices):self.assertEqual(match(prices),[])
        self.assertEqual(match([30000],blocked=(0,)),[])
        self.assertEqual(match([30000],sold=(0,)),[])
        self.assertEqual(match([30000,31000],target=31000),[(1,'MATCH')])
        wrong,_=pick_rows(lines([30000]),[False]*6,None,'Blue Earrings',30000,buy_step=0)
        self.assertEqual(wrong,[])
        for mode in ('ROW_CHECK','PRICE_CHECK','SOLD','SOLD_CHECK'):
            self.assertEqual(exact_active_hits([(0,mode)],(),None,lambda frame,row:False),[])
    def test_exact_price_structure(self):
        root=Path(__file__).resolve().parent
        source=(root/'beast_inventory.py').read_text(encoding='utf-8')
        tree=ast.parse(source)
        self.assertIn("'fast_path':'exact_price'",source)
        self.assertIn("if geometry and strict:",source)
        self.assertIn("frame_after=self._inventory_frame(client,anchor)",source)
        self.assertIn("after!=sections or after_blocked!=blocked",source)
        self.assertIn("sold_before",source)
        self.assertNotIn("locate_exact_name",source)
        self.assertNotIn("self._name_cache.recognize",source)
        scan=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='_scan')
        calls=[n for n in ast.walk(scan) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='pick_rows']
        self.assertEqual(len(calls),2)
        for call in calls:
            self.assertTrue(any(k.arg=='buy_step' and isinstance(k.value,ast.Constant) and k.value.value==0 for k in call.keywords))
        wrapper=(root/'fm_sprint.py').read_text(encoding='utf-8')
        self.assertIn("class Tracker(InventoryFallbackMixin,shop_inventory.ShopInventoryTracker)",wrapper)
    def test_compile_and_structural_guard(self):
        root=Path(__file__).resolve().parent
        spatial=(root/'beast_spatial.py').read_text(encoding='utf-8')
        wrapper=(root/'fm_sprint.py').read_text(encoding='utf-8')
        tree=ast.parse(spatial);ast.parse(wrapper)
        pointer=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='move_pointer_to_target')
        calls=[n.func.id for n in ast.walk(pointer) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)]
        self.assertEqual(calls.count('move_cursor_on_screen'),1)
        self.assertNotIn('SendInput',spatial)
        for token in ("audit.done('preview_unavailable'","audit.done('window_changed'","audit.done('cancelled'",
                      "audit.done('archive_busy'","audit.done('duplicate'","self.beast_cancel_audit('superseded')",
                      "self._generation+=1","now-at<=self.max_age","if box is None or box[2]-box[0]<12"):
            self.assertIn(token,spatial)
        for token in ("class App(spatial_mixin(old),old.FMApp):","self.beast_cancel_audit('cancelled')",
                      "self.beast_spatial_close()","self.beast_reject(kind,'stopped',received)",
                      "super().move_pointer_to_target(kind,received=received)",
                      "(client[2]-160)//2"):
            self.assertIn(token,wrapper)
        self.assertIn("if args.navigate:p.error",wrapper)
if __name__=='__main__':unittest.main()
