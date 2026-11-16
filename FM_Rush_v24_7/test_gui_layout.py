import os
import unittest
try: import tkinter as tk
except ImportError: tk=None
from fm_rush import FMApp
from deal_parser import parse_deal

@unittest.skipIf(os.name!='nt' and not os.environ.get('DISPLAY'),'No GUI display available')
class TestGUI(unittest.TestCase):
    @unittest.skipIf(tk is None, 'No Tk')
    def test_popouts_and_resize(self):
        app=FMApp()
        try:
            app.root.update_idletasks();app.root.update()
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
