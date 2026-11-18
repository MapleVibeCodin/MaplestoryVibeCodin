from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from trade_ledger import TradeLedger,quote,amount
from test_deal_archive import listing

class TradingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'ledger.sqlite3';self.ledger=TradeLedger(self.path);self.addCleanup(self.ledger.close)
    def setup_cash(self,slots=(0,0)):
        self.ledger.configure('2M',['fkable','unfkable'],list(slots))
    def deal(self,**kwargs):
        return listing(buy_mesos=100000,raw_text='Resell at\n120K\nAverage sale\n121K\nTime to resell\nabout 3 h',**kwargs)

    def test_explicit_price_eta_quantity_and_unknown_values(self):
        self.assertEqual(quote(self.deal().raw_text)['list_price'],120000)
        self.assertEqual(quote('Resell at 100K Time to resell under an hour')['eta_hours'],1)
        self.assertEqual(quote('Resell at 100K Time to resell about 2 days')['eta_hours'],48)
        self.assertEqual(quote('2 items · 200K total')['offered_quantity'],2)
        self.assertIsNone(quote('Profit +15K 15% Buy 100K')['list_price'])
        self.assertIsNone(quote('Resell at — Time to resell unknown')['eta_hours'])
        for value in ['nan','-1','1.2','2Mmesos']:
            with self.assertRaises(ValueError):amount(value)

    def test_purchase_debits_once_and_record_survives_restart(self):
        self.setup_cash();item,new=self.ledger.purchase('source',self.deal(),quantity=2)
        self.assertTrue(new);self.assertEqual(self.ledger.cash(),1800000)
        duplicate,new=self.ledger.purchase('source',self.deal(),quantity=2)
        self.assertFalse(new);self.assertEqual(duplicate['id'],item['id']);self.assertEqual(self.ledger.cash(),1800000)
        restored=TradeLedger(self.path)
        try:self.assertEqual(restored.items()[0]['stats'],self.deal().stats);self.assertEqual(restored.cash(),1800000)
        finally:restored.close()

    def test_sale_does_not_become_buyer_cash_until_collection(self):
        self.setup_cash();item,_=self.ledger.purchase('source',self.deal())
        self.ledger.listed(item['id'],'fkable',120000)
        self.ledger.sold(item['id'],116400)
        self.assertEqual(self.ledger.cash(),1900000)
        self.assertEqual(self.ledger.stores()['fkable']['collectable'],116400)
        self.ledger.collect('fkable',actual_received=116000)
        self.assertEqual(self.ledger.cash(),2016000)
        self.assertEqual(self.ledger.collect('fkable'),0)
        self.assertFalse(self.ledger.sold(item['id'],116400));self.assertEqual(self.ledger.cash(),2016000)

    def test_cash_reconcile_accounts_for_purchases_before_first_setup(self):
        self.ledger.purchase('source',self.deal());self.assertIsNone(self.ledger.cash())
        self.setup_cash();self.assertEqual(self.ledger.cash(),2000000)
        self.ledger.configure('1.7M',['fkable','unfkable'],[0,0]);self.assertEqual(self.ledger.cash(),1700000)

    def test_real_cash_transfer_from_untracked_old_stock_can_be_recorded(self):
        self.setup_cash();self.ledger.collect('fkable',actual_received=500000)
        self.assertEqual(self.ledger.cash(),2500000)

    def test_slot_planning_respects_two_eighteen_slot_shops(self):
        self.setup_cash((17,18));item,_=self.ledger.purchase('one',self.deal())
        self.assertEqual(item['target_store'],'fkable')
        another,_=self.ledger.purchase('two',self.deal())
        self.assertIsNone(another['target_store'])
        with self.assertRaises(ValueError):self.ledger.assign(another['id'],'fkable')
        self.assertEqual(self.ledger.stores()['fkable']['planned_slots'],18)

    def test_unknown_existing_stock_does_not_get_an_automatic_shop_assignment(self):
        item,_=self.ledger.purchase('source',self.deal())
        self.assertIsNone(item['target_store']);self.assertFalse(self.ledger.stores()['fkable']['known'])

    def test_relisting_keeps_original_age_and_does_not_automatically_cut_price(self):
        self.setup_cash();item,_=self.ledger.purchase('source',self.deal())
        with patch('trade_ledger.time.time',return_value=1000):self.ledger.listed(item['id'],'fkable',120000)
        with patch('trade_ledger.time.time',return_value=1000+86400):self.ledger.listed(item['id'],'fkable',120000)
        refreshed=self.ledger.get(item['id']);self.assertEqual(refreshed['first_listed_at'],1000)
        self.assertTrue(self.ledger.review(refreshed,now=1000+86400)['review_due'])
        self.assertEqual(refreshed['list_price'],120000)

    def test_cash_and_slow_turnover_warnings_do_not_hide_options(self):
        self.setup_cash();deal=listing(buy_mesos=1700000,raw_text='Resell at 2M Time to resell about 16 h')
        rec=self.ledger.recommendation(deal)
        self.assertIn('Uses cash reserve',rec['notes']);self.assertIn('Slow turnover estimate',rec['notes'])
        self.assertEqual(rec['list_price'],2000000)

    def test_failed_purchase_transaction_does_not_charge_cash(self):
        self.setup_cash()
        with patch.object(self.ledger,'_event',side_effect=OSError('disk full')):
            with self.assertRaises(OSError):self.ledger.purchase('source',self.deal())
        self.assertEqual(self.ledger.cash(),2000000);self.assertEqual(self.ledger.items(),[])

    def test_correcting_quantity_reconciles_cash_and_can_be_voided_once(self):
        self.setup_cash();item,_=self.ledger.purchase('source',self.deal())
        self.ledger.correct_purchase(item['id'],2,'90K');self.assertEqual(self.ledger.cash(),1820000)
        self.assertTrue(self.ledger.void_purchase(item['id']));self.assertEqual(self.ledger.cash(),2000000)
        self.assertFalse(self.ledger.void_purchase(item['id']));self.assertEqual(self.ledger.cash(),2000000)
        again,new=self.ledger.purchase('source',self.deal());self.assertTrue(new)
        self.assertEqual(again['id'],item['id']);self.assertEqual(self.ledger.cash(),1900000)

    def test_shop_rename_keeps_inventory_and_sale_proceeds_attached(self):
        self.setup_cash();item,_=self.ledger.purchase('source',self.deal())
        self.ledger.configure('1.9M',['SellerA','SellerB'],[0,0])
        self.assertEqual(self.ledger.get(item['id'])['target_store'],'SellerA')

    def test_existing_stock_import_does_not_double_charge_or_invent_age(self):
        self.setup_cash((18,0))
        row=dict(stock_id='old1',item='Old Gloves',stats='ATT 2',quantity='1',unit_cost='',list_price='120K',seller='fkable',listed_hours='')
        self.assertEqual(self.ledger.import_existing([row]),1)
        self.assertEqual(self.ledger.cash(),2000000)
        item=self.ledger.items()[0];self.assertIsNone(item['unit_cost']);self.assertIsNone(item['first_listed_at'])
        self.assertIsNone(self.ledger.review(item)['estimated_profit'])
        self.assertEqual(self.ledger.stores()['fkable']['planned_slots'],18)
        self.assertEqual(self.ledger.import_existing([row]),0)

    def test_existing_stock_batch_validation_is_atomic(self):
        self.setup_cash()
        with self.assertRaises(ValueError):
            self.ledger.import_existing([dict(item='Valid',seller='fkable'),dict(item='Wrong',seller='Unknown')])
        self.assertEqual(self.ledger.items(),[]);self.assertEqual(self.ledger.cash(),2000000)

    def test_explicit_consumable_lot_uses_one_shop_slot(self):
        self.setup_cash()
        deal=listing(buy_mesos=1000,raw_text='Use · Consumable Resell at 1200 Time to resell about 1 h')
        item,_=self.ledger.purchase('scrolls',deal,quantity=100)
        self.assertEqual(item['slots'],1);self.assertEqual(self.ledger.cash(),1900000)
        self.assertEqual(self.ledger.stores()['fkable']['planned_slots'],1)

    def test_identical_existing_rows_without_ids_keep_their_multiplicity(self):
        self.setup_cash()
        row=dict(item='Gloves',seller='fkable',quantity='1')
        self.assertEqual(self.ledger.import_existing([row,row]),2)
        self.assertEqual(self.ledger.stores()['fkable']['planned_slots'],2)
        self.assertEqual(self.ledger.import_existing([row,row]),0)

    def test_multi_item_holding_time_uses_displayed_whole_lot_estimate(self):
        self.setup_cash()
        deal=listing(buy_mesos=10000,raw_text='Resell at 20K Time to resell about 1 h all 2: about 4 h 2 items · 20K total')
        item,_=self.ledger.purchase('lot',deal,quantity=2)
        self.assertEqual(item['eta_hours'],4)
        self.assertEqual(self.ledger.recommendation(deal)['hours'],4)

    def test_relisting_imported_stock_keeps_unknown_original_age_unknown(self):
        self.setup_cash()
        self.ledger.import_existing([dict(item='Old',seller='fkable',list_price='20K')])
        item=self.ledger.items()[0];self.ledger.listed(item['id'],'fkable',20000)
        self.assertIsNone(self.ledger.get(item['id'])['first_listed_at'])
