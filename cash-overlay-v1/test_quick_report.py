import unittest
from quick_report import summarize,solutions
def frame(t,x,map_name=None,**kw):
    return dict(monotonic=t,context=dict(monotonic=t,exp=x,exp_confident=True,exp_estimated=False,level=44,map=map_name,map_uncertain=not bool(map_name),**kw))
class QuickTests(unittest.TestCase):
    def test_unknown_map_retains_exp(self):
        r=summarize([frame(t,100+t) for t in range(61)])
        self.assertEqual(r["exp_observed_hr"],3600);self.assertEqual(r["map_frame_counts"],{"UNKNOWN":61})
    def test_gap_and_reset(self):
        r=summarize([frame(0,100),frame(1,110),frame(10,500),frame(11,510),frame(12,900,recording_epoch=1)])
        self.assertEqual(r["exp_observed_delta"],20);self.assertEqual(r["gap_count"],1)
    def test_wallet_own_clock(self):
        r=summarize([frame(0,100,wallet=100,wallet_observed_at=0),frame(60,200,wallet=200,wallet_observed_at=60)])
        self.assertEqual(r["wallet_change_hr"],6000);self.assertIsNone(r["exp_observed_delta"])
    def test_unique_and_ambiguous(self):
        m=[dict(name="Raffle",exp=85),dict(name="Aqumander",exp=98)]
        self.assertEqual(solutions(183,m),{"Raffle":1,"Aqumander":1})
        self.assertIsNone(solutions(99,m))
        self.assertIsNone(solutions(100,[dict(name="A",exp=50),dict(name="B",exp=100)]))
    def test_conditional_counts(self):
        refs={"maps":{"a":{"name":"A","monsters":[dict(name="Raffle",exp=85),dict(name="Aqumander",exp=98)]}}}
        r=summarize([frame(0,100,"A",party=1,party_confirmed=True),frame(1,283,"A",party=1,party_confirmed=True)],refs)
        self.assertEqual(r["conditional_monster_counts"],{"Raffle":1,"Aqumander":1})
        r=summarize([frame(0,100),frame(1,283)],refs)
        self.assertEqual(r["unresolved_exp"],183)
    def test_lite_metadata(self):
        import tempfile,json,hashlib
        from pathlib import Path
        from evidence_journal import Journal
        from quick_report import report_folder
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d); j=Journal(folder/"evidence_journal.jsonl")
            for i in range(61):
                name=f"{i:04d}.png"
                m=dict(frame(i,100+i),image=name)
                raw=json.dumps(m).encode()
                (folder/name).with_suffix(".json").write_bytes(raw)
                if i==0:(folder/name).write_bytes(b"pixel")
                j.append("frame",i,file=name,image_sha256=hashlib.sha256(b"pixel").hexdigest(),sidecar_sha256=hashlib.sha256(raw).hexdigest())
            r=report_folder(folder)
            self.assertEqual(r["metadata_verified"],61)
            self.assertEqual(r["missing_image_bytes"],60)
            self.assertEqual(r["exp_observed_hr"],3600)
            (folder/"0001.json").write_text("{}")
            r=report_folder(folder)
            self.assertEqual(r["invalid_sidecars"],1)
            self.assertEqual(r["metadata_verified"],60)
    def test_negative(self):
        r=summarize([frame(0,100),frame(1,90),frame(2,100)])
        self.assertEqual(r["exp_observed_delta"],10);self.assertEqual(r["exp_negative_changes"],1)
if __name__=="__main__":unittest.main()
