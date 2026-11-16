import json
from pathlib import Path
import tempfile
import unittest
from deal_archive import DealArchive
from henefm_bridge import parse_browser_deal


def listing(ign='Mora',item='Work Gloves',**extra):
    raw=dict(cc=1,fm=3,ign=ign,item=item,buy_mesos=100,profit_mesos=1,profit_percent=1)
    raw.update(extra)
    return parse_browser_deal(raw)


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/'archive.sqlite3'
        self.archive=DealArchive(self.path)
    def tearDown(self):
        self.archive.close();self.temp.cleanup()

    def test_new_arrival_does_not_replace_working_deal(self):
        first,_=self.archive.record(listing())
        self.archive.record(listing('Oral'))
        self.assertEqual(self.archive.current()[0],first)
        self.assertEqual(self.archive.names(),('Mora','Oral'))

    def test_same_seller_multiple_items_search_once_and_complete_separately(self):
        self.archive.record(listing())
        self.archive.record(listing(item='Red Whip'))
        self.assertEqual(self.archive.names(),('Mora',))
        self.archive.complete_current()
        self.assertEqual(len(self.archive.pending()),1)
        self.assertEqual(self.archive.current()[1].item,'Red Whip')
        self.archive.complete_current()
        self.assertEqual(self.archive.names(),())
        self.assertEqual(len(self.archive.records),2)

    def test_restart_restores_focus_pending_and_completed_records(self):
        self.archive.record(listing())
        oral,_=self.archive.record(listing('Oral'))
        self.archive.select(oral)
        self.archive.close();self.archive=DealArchive(self.path)
        self.assertEqual(self.archive.current()[0],oral)
        self.assertEqual(set(self.archive.names()),{'Mora','Oral'})
        self.archive.complete_current()
        self.archive.record(listing('Oral'))
        self.assertEqual(self.archive.names(),('Mora',),'Resending a completed listing must not reopen it')

    def test_export_is_grouped_by_ign_and_preserves_sold_metadata(self):
        self.archive.record(listing(sold=True,raw_text='Visible source text'))
        output=Path(self.temp.name)/'export.json';self.archive.export_json(output)
        data=json.loads(output.read_text())['by_ign']['Mora'][0]
        self.assertTrue(data['deal']['sold'])
        self.assertEqual(data['deal']['raw_text'],'Visible source text')
        self.assertEqual(data['deal']['profit']['mesos'],1)

    def test_failed_write_is_retried_before_acknowledgment(self):
        from unittest.mock import patch
        import sqlite3
        with patch.object(self.archive,'_save',side_effect=sqlite3.OperationalError('disk full')):
            with self.assertRaises(sqlite3.Error):self.archive.record(listing())
        self.archive.record(listing())
        self.archive.close();self.archive=DealArchive(self.path)
        self.assertEqual(self.archive.names(),('Mora',))

    def test_done_can_be_undone_after_restart_without_losing_other_deals(self):
        first,_=self.archive.record(listing())
        self.archive.record(listing('Oral'));self.archive.complete_current()
        self.archive.close();self.archive=DealArchive(self.path)
        self.archive.undo_complete()
        self.assertEqual(self.archive.current()[0],first)
        self.assertEqual(set(self.archive.names()),{'Mora','Oral'})
