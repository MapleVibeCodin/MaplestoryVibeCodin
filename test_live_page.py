"""Only the current rendered page drives scanning; history stays durable."""
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from deal_archive import DealArchive, LIVE_PAGE_LEASE_SECONDS
from test_deal_archive import listing

class LivePageTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'archive.sqlite3';self.archive=DealArchive(self.path)
        self.addCleanup(self.archive.close)
    def test_current_two_replace_fifty_archived_sellers(self):
        for i in range(50):self.archive.record(listing('Old'+str(i)))
        self.assertEqual(self.archive.live_names(),())
        first=listing('languiwhisp',listing_id='a'*16,fm=15)
        second=listing('Hammy',listing_id='b'*16,fm=9)
        self.archive.apply_visible([first,second],'page',1)
        self.assertEqual(self.archive.live_names(),('languiwhisp','Hammy'))
        self.assertEqual(len(self.archive.records),52)
        self.assertEqual(self.archive.current()[1].ign,'languiwhisp')
        self.archive.apply_visible([listing('NextSeller',listing_id='c'*16)],'page',2)
        self.assertEqual(self.archive.live_names(),('NextSeller',))
        self.assertEqual(len(self.archive.records),53)
        # Still working on the first deal: BOUGHT remains possible off-page.
        self.assertEqual(self.archive.current()[1].ign,'languiwhisp')

    def test_empty_page_clears_active_set_but_not_history(self):
        self.archive.apply_visible([listing('Hammy')],'page',1)
        self.archive.apply_visible([],'page',2)
        self.assertEqual(self.archive.live_names(),())
        self.assertEqual(len(self.archive.records),1)

    def test_closed_or_disconnected_page_expires_without_deleting_archive(self):
        now=time.monotonic();self.archive.apply_visible([listing('Hammy')],'page',1,now=now)
        self.assertTrue(self.archive.live_pending(now=now+LIVE_PAGE_LEASE_SECONDS-1))
        self.assertFalse(self.archive.live_pending(now=now+LIVE_PAGE_LEASE_SECONDS+1))
        self.assertEqual(len(self.archive.records),1)

    def test_old_snapshot_and_late_individual_delivery_cannot_reactivate_seller(self):
        self.archive.apply_visible([listing('OldSeller')],'page',1)
        self.archive.apply_visible([listing('Hammy')],'page',3)
        self.assertFalse(self.archive.apply_visible([listing('OldSeller')],'page',2))
        self.archive.record(listing('LateSeller'))
        self.assertEqual(self.archive.live_names(),('Hammy',))

    def test_restart_does_not_scan_saved_history_until_new_snapshot(self):
        self.archive.apply_visible([listing('Hammy')],'page',1)
        restored=DealArchive(self.path)
        try:
            self.assertEqual(restored.live_names(),())
            self.assertEqual(len(restored.records),1)
        finally:restored.close()

    def test_completed_item_stays_completed_on_heartbeat_and_next_is_live(self):
        self.archive.record(listing('OldSeller'))
        self.archive.apply_visible([listing('Hammy'),listing('OtherLive')],'page',1)
        self.archive.complete_current()
        self.assertEqual(self.archive.current()[1].ign,'OtherLive')
        self.archive.apply_visible([listing('Hammy'),listing('OtherLive')],'page',2)
        self.assertEqual(self.archive.live_names(),('OtherLive',))
        self.archive.complete_current();self.assertIsNone(self.archive.current())

    def test_failed_archive_write_keeps_previous_live_set(self):
        self.archive.apply_visible([listing('Hammy')],'page',1)
        with patch.object(self.archive,'record',side_effect=OSError('disk full')):
            with self.assertRaises(OSError):self.archive.apply_visible([listing('OtherLive')],'page',2)
        self.assertEqual(self.archive.live_names(),('Hammy',))

    def test_http_replaces_page_and_rejects_invalid_or_untrusted_snapshots(self):
        import http.client,json,queue
        from henefm_bridge import BrowserBridge,HOST,PORT
        from test_browser_bridge import OK
        events=queue.Queue();bridge=BrowserBridge(events,self.archive);bridge.start()
        def send(body,origin='chrome-extension://test'):
            c=http.client.HTTPConnection(HOST,PORT,timeout=2)
            c.request('POST','/visible',json.dumps(body),headers={'Content-Type':'application/json',
                'X-FM-Rush-Bridge':'v17-browser-view','Origin':origin})
            r=c.getresponse();status=r.status;r.read();c.close();return status
        snapshot={'session':'page','revision':1,'deals':[{**OK,'listing_id':'a'*16,'ign':'Hammy'}]}
        try:
            self.assertEqual(send(snapshot),200)
            self.assertEqual(self.archive.live_names(),('Hammy',))
            self.assertEqual(events.get_nowait(),('browser_visible',))
            self.assertEqual(send({**snapshot,'revision':2,'deals':[{}]}),422)
            self.assertEqual(send({**snapshot,'revision':2,'deals':[]},'https://evil.example'),403)
            self.assertEqual(self.archive.live_names(),('Hammy',))
            with patch.object(self.archive,'record',side_effect=OSError('disk full')):
                self.assertEqual(send({**snapshot,'revision':2}),503)
            self.assertEqual(self.archive.live_names(),('Hammy',))
            self.assertEqual(send({**snapshot,'revision':3,'deals':[]}),200)
            self.assertEqual(self.archive.live_names(),())
        finally:bridge.stop()
