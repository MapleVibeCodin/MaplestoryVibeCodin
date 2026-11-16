"""Exercise the GUI controller without requiring a display or game capture."""
from pathlib import Path
import tempfile
import unittest
from fm_rush import FMApp
from deal_archive import DealArchive
from test_deal_archive import listing

class Value:
    def __init__(self):self.value=''
    def set(self,value):self.value=value
    def get(self):return self.value

class DealSelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.app=FMApp.__new__(FMApp)
        a=self.app;a.archive=DealArchive(Path(self.temp.name)/'archive.sqlite3')
        a.displayed_listing=None;a.scan_names=();a.shop_target='';a.shop_generation=0
        a.conf={'start_channel':20};a.shop=a.grid=a.map=None;a.shop_running=True;a.web_only=False
        for name in ['ccfm','keys','item','stats','ign','profit','buy']:setattr(a,name,Value())
    def tearDown(self):self.app.archive.close();self.temp.cleanup()

    def test_new_deals_keep_previous_item_and_route_while_all_names_are_searched(self):
        self.app.set_target(1,3,deal=listing(),source='WEB')
        first=self.app.displayed_listing
        self.app.set_target(2,4,deal=listing('Oral',cc=2,fm=4),source='WEB')
        self.assertEqual(self.app.displayed_listing,first)
        self.assertEqual(self.app.shop_target,'Mora')
        self.assertEqual((self.app.current_cc,self.app.current_fm),(1,3))
        self.assertEqual(self.app.scan_names,('Mora','Oral'))
        self.app.complete_deal()
        self.assertEqual(self.app.shop_target,'Oral')
        self.assertEqual((self.app.current_cc,self.app.current_fm),(2,4))
        self.assertEqual(self.app.scan_names,('Oral',))

    def test_marker_from_old_capture_session_is_not_drawn(self):
        import queue
        from unittest.mock import Mock
        a=self.app;a.events=queue.Queue();a.shop_events=queue.Queue();a.shop_session=2
        a.schedule=lambda *args:None;a.shop=Mock();a.shop.winfo_exists.return_value=True
        a.scan_names=('Mora',)
        a.shop_events.put(('shop_epoch',1,('shops_frame',(1000,600),{'Mora':{'box':(1,2,3,4),'mode':'EXACT'}},'old')))
        a.pump()
        a.shop.draw_matches.assert_not_called()

    def test_paused_capture_does_not_redraw_queued_markers(self):
        import queue
        from unittest.mock import Mock
        a=self.app;a.events=queue.Queue();a.shop_events=queue.Queue();a.shop_running=False
        a.schedule=lambda *args:None;a.shop=Mock();a.shop.winfo_exists.return_value=True
        a.scan_names=('Mora',)
        a.shop_events.put(('shops_frame',(1000,600),{'Mora':{'box':(1,2,3,4),'mode':'EXACT'}},'old'))
        a.pump()
        a.shop.draw_matches.assert_not_called()
