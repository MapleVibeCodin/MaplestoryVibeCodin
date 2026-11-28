import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from evidence_journal import Journal,read_journal,classify_messages,potion_delta,scope,trusted_scope,summarize,verified_frame,interval_metrics,audit_session
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
    def test_interval_alignment(self):
        c=dict(map="A",segment="a",level=44,job="Assassin",party=1)
        records=[dict(kind="accepted_pickups",monotonic=t,scope=c,messages=[["mesos",100],["item","Raffle Petal",2,"Etc"],["item","Orange Potion",3,"Use"]]) for t in (0,1,60,61)]
        r=interval_metrics(records,[dict(c,start=0,end=60)],{"raffle petal":40,"orange potion":150})[0]
        self.assertEqual(r["observed_pickup_mesos"],200)
        self.assertEqual(r["known_npc_value"],160)
        self.assertEqual(r["raw_plus_known_npc_hr"],21600)
    def test_audit_end_to_end(self):
        import json
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); src=root/"session"; dest=root/"analysis";src.mkdir();dest.mkdir()
            j=Journal(src/"evidence_journal.jsonl")
            c=dict(map="A",segment="a",level=44,job="Assassin",party=1)
            for i in (0,1):
                p=src/f"{i}.png";p.write_bytes(bytes([i]))
                j.append("frame",i,file=p.name,image_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),scope=c)
            j.append("accepted_pickups",1,scope=c,messages=[["mesos",100]])
            j.append("close",2)
            (dest/"active_intervals.jsonl").write_text(json.dumps(dict(c,session=str(src),start=0,end=1))+"\n")
            r=audit_session(src,dest)
            self.assertEqual(r["median_frame_gap_s"],1)
            self.assertTrue(r["clean_close"])
            self.assertEqual(r["active_message_metrics"][0]["observed_pickup_mesos"],100)
            self.assertFalse(r["frame_hash_mismatch"])
    def test_sampled_audit(self):
        import json
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); src=root/"session"; dest=root/"analysis";src.mkdir();dest.mkdir()
            j=Journal(src/"evidence_journal.jsonl")
            raw=b"{}"
            (src/"frame.json").write_bytes(raw)
            j.append("frame",1,file="frame.png",image_sha256=hashlib.sha256(b"image").hexdigest(),sidecar_sha256=hashlib.sha256(raw).hexdigest())
            (dest/"active_intervals.jsonl").write_text("")
            r=audit_session(src,dest)
            self.assertEqual(r["unavailable_images"],["frame.png"])
            self.assertEqual(r["frame_hash_mismatch"],[])
            self.assertTrue(r["active_metrics_withheld_for_sampled_images"])
            (src/"frame.json").write_bytes(b"wrong")
            r=audit_session(src,dest)
            self.assertEqual(r["frame_hash_mismatch"],["frame.png"])
    def test_pickup_no_double_count(self):
        c=dict(map="A",segment="a")
        rows=[dict(kind="accepted_pickups",scope=c,messages=[["mesos",20],["item","Orange Potion",3,"Use"]]),
              dict(kind="visual_messages",scope=c,lines=[dict(kind="mesos",amount=20)])]
        r=summarize(rows)[0];self.assertEqual(r["observed_pickup_mesos"],20);self.assertEqual(r["items"][0]["quantity"],3)
if __name__=="__main__":unittest.main()
