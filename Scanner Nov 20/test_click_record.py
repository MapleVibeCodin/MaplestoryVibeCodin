import json
import tempfile
import unittest
from pathlib import Path
from henefm_bridge import save_clicked_record

class ClickRecordTests(unittest.TestCase):
    def test_repeated_clicks_and_snapshot(self):
        data={'deal':{'listing_id':'1234abcd','item':'Test item','ign':'Seller','cc':1,'fm':4,
                      'buy_mesos':20000,'raw_text':'Original listing','sold':False}}
        with tempfile.TemporaryDirectory() as folder:
            a=save_clicked_record(data,folder)
            b=save_clicked_record(data,folder)
            self.assertNotEqual(a,b)
            self.assertEqual(a.parent,Path(folder)/'Click records')
            self.assertEqual(json.loads(a.read_text(encoding='utf-8'))['deal'],data['deal'])
    def test_invalid_record(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):save_clicked_record({'deal':{}},folder)
