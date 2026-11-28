import tempfile
import unittest
from pathlib import Path
from cash_core import CashLedger, rate, append_snapshot

class CashTests(unittest.TestCase):
    def test_observed_only(self):
        a=CashLedger()
        a.tick(0,True,"A")
        for n in range(1,61): a.tick(n,True,"A")
        self.assertIsNone(a.snapshot()["raw_hr"])
        a.add([("mesos",1000),("item","Raffle Petal",10,"Etc"),("item","Unknown",2,"Etc")],{"raffle petal":40})
        s=a.snapshot()
        self.assertEqual(s["raw_hr"],60000)
        self.assertEqual(s["raw_plus_known_npc_hr"],84000)
        self.assertEqual(s["unknown_units"],2)
    def test_no_paused_or_stalled_time(self):
        a=CashLedger()
        a.tick(0,True,"A");a.tick(1,True,"A");a.tick(10,True,"A")
        a.tick(11,False,"A");a.add([("mesos",99)],{})
        a.tick(12,True,"A");a.tick(13,True,"A")
        self.assertEqual(a.seconds,2)
        self.assertEqual(a.raw,0)
    def test_wallet_is_separate(self):
        a=CashLedger();a.tick(10,True,"A")
        a.wallet(9980,10,10);a.wallet(10020,11,11)
        a.add([("mesos",40)],{})
        self.assertEqual(a.snapshot()["wallet_change"],40)
        self.assertEqual(a.raw,40)
        self.assertEqual(a.npc,0)
        a.wallet(999999,2,20)
        self.assertEqual(a.snapshot()["wallet_change"],40)
    def test_consumables_count_only(self):
        a=CashLedger();a.tick(0,True,"A")
        a.add([("item","Orange Potion",3,"Use"),("item","Raffle Petal",2,"Etc")],{"orange potion":150,"raffle petal":40})
        self.assertEqual(a.npc,80)
        self.assertEqual(a.unknown,{})
    def test_csv(self):
        a=CashLedger();a.tick(0,True,"A");a.add([("mesos",5)],{})
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"a.csv";append_snapshot(p,a);append_snapshot(p,a)
            self.assertEqual(len(p.read_text().splitlines()),3)
    def test_short_rate(self):
        self.assertIsNone(rate(1000,59))
        self.assertEqual(rate(0,60),0)

if __name__=="__main__":
    unittest.main()
