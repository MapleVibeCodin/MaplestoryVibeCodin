"""Explicit listing choices, skip safety, fade start and channel-menu anchors."""
from pathlib import Path
import tempfile
import unittest
import cv2
import numpy as np
from deal_archive import DealArchive
from test_deal_archive import listing
from channel_overlay import locate_channel
from fm_entry_gate import SnapshotGate
from room_text_reader import entry_readable

ROOT=Path(__file__).parent
class ManualChaseTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.archive=DealArchive(Path(self.temp.name)/'archive.db',manual_selection=True)
        self.addCleanup(self.archive.close)
    def test_page_is_available_without_assigning_any_seller(self):
        self.archive.apply_visible([listing('First'),listing('Second')],'page',1)
        self.assertEqual(self.archive.live_names(),('First','Second'))
        self.assertIsNone(self.archive.current());self.assertEqual(self.archive.selected_names(),())
        key=self.archive.live_pending()[1][0];self.archive.select(key)
        self.assertEqual(self.archive.selected_names(),('Second',))
        self.archive.apply_visible([listing('First'),listing('Second'),listing('NewSeller')],'page',2)
        self.assertEqual(self.archive.selected_names(),('Second',))
    def test_skip_another_card_keeps_choice_skip_choice_clears_without_advancing(self):
        self.archive.apply_visible([listing('First'),listing('Second')],'page',1)
        first,second=[key for key,_ in self.archive.live_pending()]
        self.archive.select(first);self.archive.skip(second)
        self.assertEqual(self.archive.selected_names(),('First',))
        self.archive.skip(first)
        self.assertIsNone(self.archive.current());self.assertEqual(self.archive.selected_names(),())
        self.assertTrue(self.archive.records[first]['skipped'])
        self.archive.reopen(first);self.assertEqual(self.archive.selected_names(),('First',))
    def test_purchase_clear_does_not_take_another_deal_and_old_receipt_survives_rotation(self):
        self.archive.apply_visible([listing('First'),listing('Second')],'page',1)
        self.archive.select(self.archive.live_pending()[0][0])
        self.archive.apply_visible([listing('Second')],'page',2)
        self.assertEqual(self.archive.current()[1].ign,'First')
        self.assertEqual(self.archive.selected_names(),())
        self.archive.complete_current();self.assertIsNone(self.archive.current())
        self.assertEqual(self.archive.live_names(),('Second',))
    def test_restart_waits_for_a_fresh_choice(self):
        key,_=self.archive.record(listing());self.archive.select(key)
        other=DealArchive(self.archive.path,manual_selection=True)
        try:self.assertIsNone(other.current())
        finally:other.close()
    def test_early_fade_can_start_before_the_old_brightness_gate(self):
        gate=SnapshotGate(first_visible=True,visible_level=26)
        self.assertFalse(gate.observe(np.zeros((768,1366,3),np.uint8)))
        frame=np.full((768,1366,3),32,np.uint8);frame[300:500,400:900]=90
        self.assertTrue(gate.observe(frame));self.assertTrue(entry_readable(frame))
    def test_unreadable_early_view_does_not_start_a_recovery_backlog(self):
        import time
        from unittest.mock import patch
        from room_text_reader import RoomTextReader
        reader=RoomTextReader.__new__(RoomTextReader)
        reader.producer=object();reader.scene_started=time.monotonic()
        reader.visual_focus=None;reader.visual_attempts=0;reader.visual_frame=None;reader.labels=[]
        reader.update=lambda image:self.fail('Early fade blocked on generic recovery')
        frame=np.full((768,1366,3),32,np.uint8);frame[300:500,400:900]=90
        with patch('room_text_reader.selected_proposals',return_value=[]):
            self.assertEqual(reader.read(frame,['Target']),{})
        self.assertEqual(reader.last_diagnostic['method'],'early fade quick attempt')

    def test_priority_miss_tries_next_frame_without_the_recovery_delay(self):
        from unittest.mock import Mock, patch
        from room_text_reader import RoomTextReader
        reader=RoomTextReader.__new__(RoomTextReader)
        reader.producer=object()
        reader.scene_started=100.
        reader.visual_focus=None
        reader.visual_attempts=0
        reader.visual_frame=None
        reader.labels=[]
        reader.update=Mock(side_effect=AssertionError('Recovery blocked the priority pass'))
        reader.recognizer=Mock(return_value=[('Other',.99,[])])
        frame=np.full((768,1366,3),90,np.uint8)
        with patch('room_text_reader.time.monotonic',return_value=100.01) as clock, \
             patch('room_text_reader.selected_proposals',return_value=[(.6,(40,40,100,55),False)]) as propose:
            self.assertEqual(reader.read(frame,['Target']),{})
            clock.return_value=100.02
            self.assertEqual(reader.read(frame,['Target']),{})
            self.assertEqual(reader.read(frame.copy(),['Target']),{})
        self.assertEqual(propose.call_count,2)
        self.assertEqual(reader.recognizer.call_count,2)
        reader.update.assert_not_called()


class ChannelMenuTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image=cv2.imread(str(ROOT/'Screenshot 2026-11-17 152902.png'))
    def test_all_forty_channels_have_their_actual_cell(self):
        for channel in range(1,41):
            row,col=divmod(channel-1,8)
            self.assertEqual(locate_channel(self.image,channel),(407+70*col,385+22*row,474+70*col,405+22*row))
    def test_titlebar_offset_and_scaled_capture_keep_the_right_channel(self):
        shifted=self.image[36:]
        self.assertEqual(locate_channel(shifted,40),(897,437,964,457))
        resized=cv2.resize(self.image,None,fx=1.25,fy=1.25)
        actual=locate_channel(resized,21)
        self.assertIsNotNone(actual)
        self.assertTrue(all(abs(a-b)<=3 for a,b in zip(actual,(859,536,943,561))),actual)
    def test_no_marker_when_menu_is_closed_or_channel_invalid(self):
        image=cv2.imread(str(ROOT/'regression_samples/cernia.png'))
        self.assertIsNone(locate_channel(image,40))
        for channel in (0,41,None):self.assertIsNone(locate_channel(self.image,channel))

class BrowserChoiceBridgeTests(unittest.TestCase):
    def test_click_transport_queues_intent_without_assigning_incoming_listings(self):
        import json,queue
        from urllib.request import Request,urlopen
        from henefm_bridge import BrowserBridge
        with tempfile.TemporaryDirectory() as tmp:
            archive=DealArchive(Path(tmp)/'archive.db',manual_selection=True)
            out=queue.Queue();bridge=BrowserBridge(out,archive)
            try:
                bridge.start()
                raw=dict(ign='Seller',item='Work Gloves',listing_id='menu-test',cc=40,fm=9,
                         _choice_session='tab',_choice_revision=1)
                req=Request('http://127.0.0.1:18773/select',data=json.dumps(raw).encode(),
                    headers={'Content-Type':'application/json','X-FM-Rush-Bridge':'v17-browser-view'})
                with urlopen(req) as response:self.assertTrue(json.load(response)['ok'])
                event=out.get(timeout=1)
                self.assertEqual(event[0:2],('browser_choice','select'))
                self.assertEqual(event[3:],('tab',1))
                self.assertIsNone(archive.current())
            finally:bridge.stop();archive.close()
