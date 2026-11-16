from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from PIL import Image
from bought_screenshots import save_bought_screenshot
from deal_archive import DealArchive
from fm_rush import FMApp
from test_deal_archive import listing

ID='0123456789abcdef'
KEY='a'*24

class BoughtTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.downloads=Path(self.temp.name)/'Downloads'
        self.source=self.downloads/'FM_Rush_Item_Screenshots'
        self.folder=self.source/'IGN_Mora'/'2026-11-16';self.folder.mkdir(parents=True)
        self.png=self.folder/f'card_{ID}.png'
        Image.new('RGB',(240,100),'green').save(self.png)
        self.deal=listing(listing_id=ID)
        self.target=self.downloads/'Bought'

    def test_exact_listing_not_newer_other_listing_and_one_flat_folder(self):
        Image.new('RGB',(240,100),'red').save(self.folder/f'wrong_{ID}0.png')
        Image.new('RGB',(240,100),'blue').save(self.folder/'latest_abcdef0123456789.png')
        result=save_bought_screenshot(self.deal,KEY,self.source,self.target)
        self.assertEqual(result.parent,self.target)
        self.assertEqual(result.read_bytes(),self.png.read_bytes())
        self.assertIn('Work Gloves_Mora_100mesos',result.name)
        self.assertEqual(save_bought_screenshot(self.deal,KEY,self.source,self.target),result)
        self.assertEqual(len(list(self.target.iterdir())),1)

    def test_chrome_duplicate_download_suffix_and_safe_name(self):
        self.png.rename(self.folder/f'card_{ID} (1).png')
        result=save_bought_screenshot(listing(item='../Bad:Gloves',listing_id=ID),KEY,self.source,self.target)
        self.assertEqual(result.parent,self.target)
        self.assertTrue(result.is_file())

    def test_missing_and_corrupt_png_do_not_create_purchase_file(self):
        self.png.unlink()
        with self.assertRaises(FileNotFoundError):save_bought_screenshot(self.deal,KEY,self.source,self.target)
        self.png.write_bytes(b'broken download')
        with self.assertRaises(OSError):save_bought_screenshot(self.deal,KEY,self.source,self.target)
        self.assertFalse(self.target.exists())
        with self.assertRaises(ValueError):save_bought_screenshot(listing(),KEY,self.source,self.target)

    def make_app(self):
        app=FMApp.__new__(FMApp);app.archive=DealArchive(Path(self.temp.name)/'deals.sqlite3')
        self.addCleanup(app.archive.close)
        app.conf={};app.shop=None;app.status=Mock();app.sync_archive=Mock();app.save=Mock()
        app.archive.record(self.deal)
        return app

    def test_bought_saves_then_advances_and_survives_restart(self):
        app=self.make_app();key=app.archive.current()[0]
        next_key,_=app.archive.record(listing('Oral',listing_id='abcdef0123456789'))
        with patch('fm_rush.downloads_folder',return_value=self.downloads):app.bought_deal()
        self.assertEqual(app.archive.current()[0],next_key)
        record=app.archive.records[key]
        self.assertTrue(record['done']);self.assertGreater(record['bought_at'],0)
        self.assertEqual(Path(record['bought_screenshot']).read_bytes(),self.png.read_bytes())
        restored=DealArchive(app.archive.path)
        try:self.assertEqual(restored.records[key],record)
        finally:restored.close()
        app.archive.undo_complete()
        with patch('fm_rush.downloads_folder',return_value=self.downloads):app.bought_deal()
        self.assertEqual(len(list(self.target.iterdir())),1)

    def test_copy_failure_keeps_current_deal_pending(self):
        app=self.make_app();key=app.archive.current()[0]
        with patch('fm_rush.save_bought_screenshot',side_effect=OSError('disk full')),patch('fm_rush.messagebox.showerror') as error:
            app.bought_deal()
        error.assert_called_once();self.assertEqual(app.archive.current()[0],key)
        self.assertFalse(app.archive.records[key]['done'])
        app.sync_archive.assert_not_called()

    def test_cancel_missing_screenshot_folder_keeps_pending(self):
        app=self.make_app();self.png.unlink();key=app.archive.current()[0]
        with patch('fm_rush.downloads_folder',return_value=self.downloads),patch('fm_rush.filedialog.askdirectory',return_value=''):
            app.bought_deal()
        self.assertEqual(app.archive.current()[0],key)
        self.assertFalse(self.target.exists())

    def test_custom_browser_download_folder_is_remembered(self):
        app=self.make_app();custom=Path(self.temp.name)/'Custom'
        self.source.rename(custom)
        with patch('fm_rush.downloads_folder',return_value=self.downloads),patch('fm_rush.filedialog.askdirectory',return_value=str(custom)):
            app.bought_deal()
        self.assertEqual(app.conf['screenshot_folder'],str(custom))
        app.save.assert_called_once();self.assertTrue(list(self.target.glob('*.png')))

    def test_archive_failure_after_copy_is_retryable_without_duplicate_png(self):
        import sqlite3
        app=self.make_app();key=app.archive.current()[0]
        with patch('fm_rush.downloads_folder',return_value=self.downloads),patch.object(app.archive,'_save',side_effect=sqlite3.OperationalError('disk full')),patch('fm_rush.messagebox.showerror') as error:
            app.bought_deal()
        error.assert_called_once();self.assertEqual(app.archive.current()[0],key)
        self.assertEqual(len(list(self.target.glob('*.png'))),1)
        with patch('fm_rush.downloads_folder',return_value=self.downloads):app.bought_deal()
        self.assertIsNone(app.archive.current())
        self.assertEqual(len(list(self.target.glob('*.png'))),1)
