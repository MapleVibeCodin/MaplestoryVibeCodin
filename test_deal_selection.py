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

    def test_new_live_deals_keep_previous_item_and_route_while_only_live_names_are_searched(self):
        self.app.archive.apply_visible([listing(),listing('Oral',cc=2,fm=4)],'page',1)
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

    def test_room_names_include_other_channels_and_unknown_rooms_only(self):
        self.app.scan_by_room={3:('Mora','Oral'),4:('Elsewhere',),None:('Unknown','Mora')}
        self.assertEqual(self.app.names_for_room(3),('Mora','Oral','Unknown'))

    def test_fifty_archived_names_do_not_expand_live_scan_set(self):
        for i in range(50):self.app.archive.record(listing('Old'+str(i)))
        self.app.archive.apply_visible([listing('languiwhisp',fm=15),listing('Hammy',fm=9)],'page',1)
        self.app.sync_archive()
        self.assertEqual(self.app.scan_names,('languiwhisp','Hammy'))
        self.assertEqual(self.app.names_for_room(9),('Hammy',))
        # A rotated-out working item is retained for BOUGHT, but never scanned.
        previous=self.app.shop_target
        self.app.archive.apply_visible([listing('NextSeller',fm=9)],'page',2)
        self.app.sync_archive()
        self.assertEqual(self.app.scan_names,('NextSeller',))
        self.assertEqual(self.app.shop_target,previous)
        self.assertEqual(self.app.names_for_room(15),())

    def test_first_live_page_rechecks_entry_once_and_rotations_do_not_rearm(self):
        from unittest.mock import Mock
        self.app.shop_thread=Mock();self.app.shop_thread.is_alive.return_value=True
        self.app.archive.apply_visible([listing('Hammy')],'page',1);self.app.sync_archive()
        self.app.shop_thread.entry_check.set.assert_called_once()
        self.app.archive.apply_visible([listing('NextSeller')],'page',2);self.app.sync_archive()
        self.app.shop_thread.entry_check.set.assert_called_once()
