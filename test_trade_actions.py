from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch
from deal_archive import DealArchive
from trade_ledger import TradeLedger
from fm_rush import FMApp
from test_deal_archive import listing

class TradeActionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.app=FMApp.__new__(FMApp);a=self.app
        a.archive=DealArchive(Path(self.temp.name)/'archive.sqlite3');self.addCleanup(a.archive.close)
        a.ledger=TradeLedger(Path(self.temp.name)/'ledger.sqlite3');self.addCleanup(a.ledger.close)
        a.ledger.configure('2M',['fkable','unfkable'],[0,0]);a.status=Mock()
        a.shop=Mock();a.shop.trade_panels.quantity.get.return_value='1'
        a.sync_archive=Mock()
    def test_hotkey_records_without_screenshot_or_filesystem_prompt(self):
        a=self.app;a.archive.apply_visible([listing(buy_mesos=100000,raw_text='Resell at 120K Time to resell about 3 h')],'page',1)
        with patch('fm_rush.save_bought_screenshot',side_effect=AssertionError('should not block')),patch('fm_rush.filedialog.askdirectory',side_effect=AssertionError('no prompt')):
            a.log_purchase()
        self.assertEqual(len(a.ledger.items()),1);self.assertEqual(a.ledger.cash(),1900000)
        self.assertIsNone(a.archive.current());self.assertEqual(a.ledger.items()[0]['list_price'],120000)
    def test_archive_failure_retry_does_not_debit_purchase_twice(self):
        a=self.app;a.archive.record(listing(buy_mesos=100000))
        with patch.object(a.archive,'complete_current',side_effect=OSError('busy')),patch('fm_rush.messagebox.showerror'):
            a.log_purchase()
        self.assertEqual(a.ledger.cash(),1900000)
        a.log_purchase();self.assertEqual(a.ledger.cash(),1900000);self.assertIsNone(a.archive.current())
    def test_double_hotkey_is_debounced_before_next_deal_is_charged(self):
        a=self.app;a.archive.apply_visible([listing(buy_mesos=100000),listing('Other',buy_mesos=200000)],'page',1)
        a.log_purchase();a.log_purchase()
        self.assertEqual(len(a.ledger.items()),1);self.assertEqual(a.ledger.cash(),1900000)
        self.assertEqual(a.archive.current()[1].ign,'Other')
    def test_switch_hotkey_cycles_only_current_page(self):
        a=self.app;a.archive.record(listing('Old'))
        a.archive.apply_visible([listing('First'),listing('Second')],'page',1)
        a.next_live_deal();self.assertEqual(a.archive.current()[1].ign,'Second')
        a.next_live_deal();self.assertEqual(a.archive.current()[1].ign,'First')
