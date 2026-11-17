import os
import unittest
try:
    import tkinter
except ImportError:
    tkinter=None
from fm_rush import FMApp
from deal_parser import parse_deal
from PIL import Image

@unittest.skipIf(os.name!='nt' and not os.environ.get('DISPLAY'),'No GUI display available')
class TestShopUI(unittest.TestCase):
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

    @unittest.skipIf(tkinter is None,'Tk unavailable')
    def test_discord_only_persistent_highlight(self):
        app=FMApp()
        try:
            app.root.update_idletasks()
            self.assertTrue(app.shop.winfo_exists())
            self.assertTrue(app.shop.resizable())
            self.assertFalse(hasattr(app.shop,'name_entry'))
            raw='''HeneFM APP 2:29 AM\nGreen Napoleon\nW.DEF 22 · DEX 3 · ACC 4 · 5 slots\nBuy Resell at Profit\n30K each 38.9K +15.7K (26%)\nWhere\nCH 22 · FM 13 · porkypork'''
            deal=parse_deal(raw)
            self.assertTrue(deal.profit.accepted)
            app.set_target(deal.cc,deal.fm,deal=deal,source='DISCORD')
            self.assertEqual(app.shop_target,'')
            app.select_archived(app.archive.pending()[0][0])
            self.assertEqual(app.shop_target,'porkypork')
            app.set_target(1,2,deal=deal,source='MANUAL')
            self.assertEqual(app.shop_target,'porkypork')  # manual navigation/deal cannot change scanner target
            app.shop.draw(Image.new('RGB',(640,360),'#405678'),(640,360),
                          (200,80,280,100),'FOUND','pork',43,'OCR')
            self.assertEqual(app.shop.last_box,(200,80,280,100))
            app.shop.draw(Image.new('RGB',(640,360),'#405678'),(640,360),
                          (200,80,280,100),'LAST SEEN','pork',25,'')
            self.assertIn('CHECK NAME',app.shop.notice.get())
            app.shop.geometry('820x510+80+30')
            app.root.update_idletasks();app.root.update()
            app.shop.set_target('nextIGN',force=True)
            self.assertIsNone(app.shop.last_box)
            self.assertIsNotNone(app.shop.pin)
            self.assertIsNone(app.shop.pin.data)
        finally:
            app.close()

    def test_browser_click_selects_only_one_and_skip_does_not_spend_or_assign(self):
        from test_deal_archive import listing
        app=FMApp()
        try:
            app.archive.apply_visible([listing('First',cc=40),listing('Second',cc=21)],'page',1)
            app.sync_archive()
            self.assertEqual(app.scan_names,());self.assertIsNone(app.archive.current())
            first,second=[key for key,_ in app.archive.live_pending()]
            app.events.put(('browser_choice','select',second,'clicks',2))
            app.events.put(('browser_choice','select',first,'clicks',1))
            app.pump()
            self.assertEqual(app.scan_names,('Second',));self.assertEqual(app.current_cc,21)
            import time
            app.shop_events.put(('shops_frame',(1366,768),{'First':dict(box=(10,10,40,25),mode='CONFUSABLE',hold_until=time.monotonic()+120)},'old target'))
            app.pump();self.assertNotIn('First',app.shop.matches)
            app.events.put(('browser_choice','skip',first,'clicks',3));app.pump()
            self.assertEqual(app.scan_names,('Second',))
            app.events.put(('browser_choice','skip',second,'clicks',4));app.pump()
            self.assertEqual(app.scan_names,());self.assertEqual(app.shop_target,'')
            self.assertIsNone(app.archive.current());self.assertEqual(app.ledger.items(),[])
            app.events.put(('browser_choice','select',second,'clicks',5));app.pump()
            self.assertEqual(app.scan_names,('Second',))
        finally:app.close()

    def test_queue_refresh_keeps_verified_hold_and_does_not_claim_to_scan_archived_selection(self):
        import time
        app=FMApp()
        try:
            app.shop.set_focus('Old')
            app.shop.last_size=(1000,600)
            app.shop.matches={'Old':dict(box=(100,100,150,115),mode='EXACT',hold_until=time.monotonic()+120),
                              'Expired':dict(box=(300,100,350,115),mode='EXACT',hold_until=time.monotonic()-1),
                              'Live':dict(box=(500,100,550,115),mode='EXACT',hold_until=0)}
            app.shop.render_queue([],None,('Live',))
            self.assertEqual(set(app.shop.matches),{'Old'})
            self.assertIn('selected deal is off page',app.shop.target.get())
        finally:app.close()

if __name__=='__main__':unittest.main()
