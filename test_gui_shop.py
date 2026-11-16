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

if __name__=='__main__':unittest.main()
