import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from evidence_journal import Journal,read_journal,classify_messages,potion_delta,scope,trusted_scope,summarize,verified_frame
import hashlib
class JournalTests(unittest.TestCase):
    def test_chain_and_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"j.jsonl";j=Journal(p);j.append("start",1);j.append("stop",2)
            rows,errors=read_journal(p);self.assertEqual(len(rows),2);self.assertFalse(errors)
            p.write_text(p.read_text().replace('"start"','"changed"'))
            self.assertTrue(read_journal(p)[1])
    def test_frame_hash(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"f.png";p.write_bytes(b"abc")
            row=dict(file=p.name,image_sha256=hashlib.sha256(b"abc").hexdigest())
            self.assertTrue(verified_frame(d,row));p.write_bytes(b"xyz")
            self.assertFalse(verified_frame(d,row))
            self.assertFalse(verified_frame(d,dict(row,file="../f.png")))
    def test_separate_exp(self):
        lines=classify_messages([SimpleNamespace(kind="exp",amount=89,born=1),SimpleNamespace(kind="bonus",amount=12,born=1)])
        c=dict(map="A",segment="a",level=44,job="Assassin",party=2)
        r=summarize([dict(kind="visual_messages",scope=c,lines=lines)])[0]
        self.assertEqual((r["normal_exp_total"],r["party_bonus_total"]),(89,12))
        self.assertIsNone(r["confirmed_kills"]);self.assertIsNone(r["observed_pickup_mesos"])
    def test_counts_only(self):
        self.assertEqual(potion_delta({1:100,2:10},{1:95,2:13,3:20}),
                         [dict(item_id=1,before=100,after=95,net_decrease=5),dict(item_id=2,before=10,after=13,net_decrease=-3)])
    def test_scope(self):
        c=dict(active=True,map="A",segment="a",monotonic=10,party=1,party_confirmed=False)
        self.assertIsNone(scope(c)["party"]);self.assertIsNone(trusted_scope(c,13));self.assertIsNotNone(trusted_scope(c,11))
        self.assertIsNone(scope(dict(c,map_uncertain=True)))
    def test_pickup_no_double_count(self):
        c=dict(map="A",segment="a")
        rows=[dict(kind="accepted_pickups",scope=c,messages=[["mesos",20],["item","Orange Potion",3,"Use"]]),
              dict(kind="visual_messages",scope=c,lines=[dict(kind="mesos",amount=20)])]
        r=summarize(rows)[0];self.assertEqual(r["observed_pickup_mesos"],20);self.assertEqual(r["items"][0]["quantity"],3)
if __name__=="__main__":unittest.main()
