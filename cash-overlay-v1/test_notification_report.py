import json
import tempfile
import unittest
import hashlib
from pathlib import Path
from unittest.mock import patch
from evidence_journal import Journal,read_journal,canonical
from minimap_report import report_minimap
from notification_report import parse,row_hash,results,summarize,source_rows,replay_batch

class Notifications(unittest.TestCase):
    def test_amounts_and_colour(self):
        self.assertEqual(parse("You received EXP (+34)","white",{}),("own_exp",34))
        self.assertEqual(parse("You received EXP (+15)","yellow",{}),("shared_exp",15))
        self.assertEqual(parse("Bonus EXP for PARTY (+5)","yellow",{}),("party_bonus_exp",5))
        self.assertEqual(parse("You have gained mesos (+1 3)","white",{}),("mesos",13))
        self.assertIsNone(parse("You received EXP (+344","white",{}))
    def test_catalog(self):
        items={"etc":{"echopus leg":["Echopus Leg"],"jr boogie horn":["Jr. Boogie Horn"]}}
        self.assertEqual(parse("Echopus Leg x1 eared. (Etc)","white",items),("item","Echopus Leg",1,"etc"))
        self.assertEqual(parse("Unknown drop x1 earned. (Etc)","white",items),("unmatched_item","unknown drop",1,"etc"))
        self.assertIsNone(parse("Echopus Leg x1 earned. (Etc)","yellow",items))
    def test_duplicate_timestamps_not_merged_and_summary(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);(folder/"message_evidence").mkdir()
            rows=[{"born":1,"colour":"white"},{"born":1,"colour":"white"}]
            (folder/"message_evidence"/"lines.jsonl").write_text("".join(json.dumps(r)+"\n" for r in rows))
            out=[dict(index=i,source_sha256=row_hash(r),status="accepted",event=["item","Echopus Leg",1,"etc"]) for i,r in enumerate(rows)]
            (folder/"notification_events.jsonl").write_text("".join(json.dumps(r)+"\n" for r in out))
            s=summarize(folder)
            self.assertEqual(s["groups"][0]["items"][0]["quantity"],2)
            self.assertEqual(s["groups"][0]["known_npc_value"],88)
            self.assertIsNone(s["groups"][0]["personal_kills"])
            rows[0]["born"]=2
            with self.assertRaises(ValueError):results(folder,rows)
    def test_reader_disagreement(self):
        rows=[dict(colour="white")]
        with patch("notification_report.read_image",return_value=object()),patch("notification_report.ocr_batch",side_effect=[{0:"You have gained mesos (+13)"},{0:"You have gained mesos (+18)"}]):
            self.assertIsNone(replay_batch(".",rows,0,"unused",{})[0]["event"])
    def test_adaptive_third_pass(self):
        rows=[dict(colour="white")]
        with patch("notification_report.read_image",return_value=object()),patch("notification_report.ocr_batch",side_effect=[{0:"You have gained mesos (+13)"},{0:"junk"},{0:"You have gained mesos (+13)"}]):
            out=replay_batch(".",rows,0,"unused",{})[0]
            self.assertEqual(out["event"],["mesos",13]);self.assertTrue(out["recovered_third_pass"])
    def test_real_journal_minimap_hash(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d); p=folder/"minimap_observations.jsonl";p.write_text("")
            j=Journal(folder/"evidence_journal.jsonl")
            with self.assertRaises(ValueError):j.append("bad",1,sha256="reserved")
            self.assertEqual(j.sequence,0)
            j.append("minimap_file",2,file=p.name,file_sha256=hashlib.sha256(p.read_bytes()).hexdigest())
            j.append("close",3)
            self.assertEqual(read_journal(j.path)[1],[])
            self.assertEqual(report_minimap(folder)["observations"],0)
            p.write_text("tampered")
            self.assertIn("error",report_minimap(folder))
    def test_legacy_minimap_collision(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);p=folder/"minimap_observations.jsonl";p.write_text("")
            j=Journal(folder/"evidence_journal.jsonl")
            original=dict(kind="minimap_file",monotonic=2,utc="test",sequence=1,previous_sha256=None,file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
            digest=hashlib.sha256(canonical(original)).hexdigest()
            j.path.write_text(json.dumps(dict(original,sha256=digest))+"\n")
            original_bytes=j.path.read_bytes()
            records,errors=read_journal(j.path)
            self.assertEqual(errors,[])
            self.assertTrue(records[0]["legacy_minimap_recovered"])
            self.assertTrue(report_minimap(folder)["legacy_minimap_recovered"])
            self.assertEqual(j.path.read_bytes(),original_bytes)
            p.write_text("tampered")
            self.assertTrue(read_journal(j.path)[1])
if __name__=="__main__":unittest.main()

