import os
import unittest
try: import tkinter as tk
except ImportError: tk=None
from fm_rush import FMApp
from deal_parser import parse_deal

@unittest.skipIf(os.name!='nt' and not os.environ.get('DISPLAY'),'No GUI display available')
class TestGUI(unittest.TestCase):
    def tearDown(self):
        import gc
        gc.collect()

    def setUp(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        for field,path in [('ARCHIVE_DIR',Path(self.temp.name)/'archives'),('CONFIG',Path(self.temp.name)/'config.json')]:
            patcher=patch('fm_rush.'+field,path);patcher.start();self.addCleanup(patcher.stop)

    def test_compact_strip_fits_below_game_and_inventory_opens_on_screen(self):
        from unittest.mock import patch
        with patch('fm_rush.FMApp.work_area',return_value=(0,0,1920,1020)), \
             patch('fm_rush.FMApp.selected_game_rect',return_value=(34,46,1275,807)):
            app=FMApp()
            try:
                app.root.update()
                self.assertEqual(app.shop.state(),'withdrawn')
                self.assertEqual((app.root.winfo_x(),app.root.winfo_y()),(34,857))
                self.assertLessEqual(app.root.winfo_y()+app.root.winfo_height()+app.title_margin(),1020)
                self.assertLessEqual(app.root.winfo_x()+app.root.winfo_width(),1309)

                app.open_inventory()
                app.root.update()
                self.assertEqual(app.shop.tabs.select(),str(app.shop.trade_panels.inventory))
                self.assertLess(app.shop.winfo_x()+app.shop.winfo_width(),1310)
                app.shop.withdraw()
                app.conf['shop_geom']='1100x650+1700+990'
                app.open_shop()
                app.root.update()
                self.assertLessEqual(app.shop.winfo_x()+app.shop.winfo_width(),1920)
                self.assertLessEqual(app.shop.winfo_y()+app.shop.winfo_height()+app.title_margin(),1020)
            finally:
                app.close()

    @unittest.skipIf(tk is None, 'No Tk')
    def test_popouts_and_resize(self):
        app=FMApp()
        try:
            app.root.update_idletasks();app.root.update()
            app.open_grid();app.open_map()
            app.root.update_idletasks()
            self.assertTrue(app.grid.winfo_exists())
            self.assertTrue(app.map.winfo_exists())
            self.assertTrue(app.grid.winfo_geometry())
            self.assertEqual(len(app.grid_canvas.find_withtag('c20')),2)
            self.assertEqual(len(app.map_canvas.find_withtag('fm13')),2)
            app.grid.geometry('600x350+100+70')
            app.map.geometry('640x480+750+90')
            app.root.update_idletasks();app.root.update()
            self.assertEqual(len(app.grid_canvas.find_withtag('c40')),2)
            self.assertEqual(len(app.map_canvas.find_withtag('fm20')),2)
            raw='''HeneFM APP 2:29 AM\nGreen Napoleon\nW.DEF 22 · DEX 3 · ACC 4 · 5 slots\nBuy Resell at Profit\n30K each 38.9K  +15.7K (26%)\nWhere\nCH 22 · FM 13 · porkypork'''
            deal=parse_deal(raw)
            self.assertTrue(deal.profit.accepted)
            app.set_target(deal.cc,deal.fm,deal=deal)
            self.assertEqual(app.buy.get(),'BUY AT: 30,000 MESOS')
            self.assertEqual(app.current_cc,22)
            self.assertIn('→',app.keys.get())
            # No on-game overlay anywhere in UI or imports.
            self.assertFalse(hasattr(app,'marker'))
            self.assertFalse(hasattr(app,'crosshair_on'))
            app.grid.withdraw();app.open_grid()
            self.assertEqual(app.grid.state(),'normal')
        finally:
            app.close()

if __name__=='__main__':unittest.main()
