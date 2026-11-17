import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from fm_rush import FMApp
from test_deal_archive import listing

@unittest.skipIf(os.name!='nt' and not os.environ.get('DISPLAY'),'No GUI display available')
class TradeDeskGUI(unittest.TestCase):
    def tearDown(self):
        import gc
        gc.collect()

    def test_two_seller_purchase_listing_sale_and_collection(self):
        with tempfile.TemporaryDirectory() as d,patch('fm_rush.ARCHIVE_DIR',Path(d)),patch('fm_rush.CONFIG',Path(d)/'config.json'):
            app=FMApp()
            try:
                app.ledger.configure('2M',['fkable','unfkable'],[0,0])
                app.archive.apply_visible([listing('First',item='Blue Starlight',buy_mesos=14000,raw_text='Resell at 20K Time to resell about 3 h'),
                    listing('Next',buy_mesos=85000,raw_text='Resell at 100K Time to resell about 1 h 2 items · 170K total')],'page',1)
                app.select_archived(app.archive.live_pending()[0][0]);app.root.update()
                self.assertEqual(len(app.shop.tabs.tabs()),3)
                self.assertEqual(app.grid.state(),'withdrawn');self.assertEqual(app.map.state(),'withdrawn')
                app.log_purchase();app.root.update()
                item=app.ledger.items()[0];self.assertEqual(app.ledger.cash(),1986000)
                self.assertIsNone(app.archive.current())
                app.select_archived(app.archive.live_pending()[0][0])
                self.assertEqual(app.buy_quantity.get(),'2')
                panel=app.shop.trade_panels
                app.shop.tabs.select(panel.inventory);panel.table.selection_set(item['id'])
                with patch('trade_desk.messagebox.askyesno',return_value=True):panel.listed()
                self.assertEqual(app.ledger.get(item['id'])['status'],'listed')
                panel.table.selection_set(item['id'])
                with patch('trade_desk.messagebox.askyesno',return_value=True):panel.sold()
                self.assertEqual(app.ledger.cash(),1986000)
                with patch('trade_desk.simpledialog.askstring',return_value='19400'):panel.collect('fkable')
                self.assertEqual(app.ledger.cash(),2005400)
                self.assertEqual(panel.table.get_children(),())
            finally:app.close()
