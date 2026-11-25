"""Run from scanner folder: python -m unittest test_auto_lock."""
import tempfile
import unittest
from pathlib import Path
from deal_archive import DealArchive
from deal_parser import Deal
from profit_filter import ProfitDecision

def deal(name, sold=False):
    return Deal(17,1,'Item','',name,10000,ProfitDecision(True,20000,200,'test'),listing_id=name,sold=sold)

class AutoLockTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.a=DealArchive(Path(self.tmp.name)/'archive.sqlite3',manual_selection=True,auto_lock=True)
    def tearDown(self):
        self.a.close()
        self.tmp.cleanup()
    def visible(self,revision,*deals):
        return self.a.apply_visible(deals,'test',revision)
    def target(self,name,locked=True):
        self.assertEqual(self.a.current()[1].ign,name)
        self.assertEqual(self.a.chase_locked,locked)
    def test_lock_unlock(self):
        a,b,c,d=map(deal,'ABCD')
        self.visible(1,a,b)
        self.target('A')
        self.visible(2,c,b)
        self.target('A')
        self.a.unlock()
        self.target('C',False)
        self.visible(3,c,b)
        self.assertFalse(self.a.chase_locked)
        self.visible(4,deal('sold',True),d,c)
        self.target('D')
        self.assertFalse(self.visible(3,a))
        self.target('D')
    def test_empty_and_skip(self):
        self.visible(1)
        self.assertIsNone(self.a.current())
        self.visible(2,deal('A'))
        self.target('A')
        self.a.skip(self.a.current()[0])
        self.visible(3,deal('A'))
        self.assertFalse(self.a.chase_locked)
        self.visible(4,deal('B'))
        self.target('B')

    def test_batched_durable_writes_and_age_only_noop(self):
        from dataclasses import replace
        statements=[]
        self.a.db.set_trace_callback(statements.append)
        self.a.auto_lock=False
        self.a.manual_selection=False
        self.visible(1,deal('A'),deal('B'),deal('C'))
        self.assertEqual(sum(s.strip().upper()=='COMMIT' for s in statements),1)
        self.assertEqual(sum("INSERT OR REPLACE INTO settings VALUES ('focus'" in s for s in statements),1)
        statements.clear()
        self.visible(2,replace(deal('A'),raw_text='Seen 3s'),deal('B'),deal('C'))
        self.assertFalse(any(s.strip().upper().startswith('INSERT') for s in statements))

    def test_batch_rolls_back_memory_on_failure(self):
        from unittest.mock import patch
        original=self.a.record
        def record(d):
            if d.ign=='B':raise ValueError('simulated failure')
            return original(d)
        with patch.object(self.a,'record',side_effect=record):
            with self.assertRaises(ValueError):self.visible(1,deal('A'),deal('B'))
        self.assertEqual(self.a.records,{})
        self.assertEqual(self.a.pending(),[])
        self.assertIsNone(self.a.current())
