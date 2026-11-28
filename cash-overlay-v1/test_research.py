import unittest
import numpy as np
import cv2
from research_analysis import TrackLinker,camera_shift,trusted_context,reference_for,compare,reviewed_combat
from pathlib import Path
import tempfile,json
class ResearchTests(unittest.TestCase):
    def test_motion(self):
        rng=np.random.default_rng(12)
        a=rng.integers(0,256,(480,640,3),dtype=np.uint8)
        b=cv2.warpAffine(a,np.float32([[1,0,12],[0,1,-7]]),(640,480))
        s=camera_shift(a,b)
        self.assertIsNotNone(s)
        self.assertAlmostEqual(s[0],12,delta=2)
        self.assertAlmostEqual(s[1],-7,delta=2)
    def test_blank_unknown(self):
        a=np.zeros((180,240,3),np.uint8)
        self.assertIsNone(camera_shift(a,a))
    def test_tracks_not_kills(self):
        l=TrackLinker();d=dict(kind="monster",species="A",x=40,y=50)
        p,e=l.step(0,[d]);self.assertFalse(e[0]["confirmed_spawn"])
        p2,e=l.step(.25,[{**d,"x":50}]);self.assertEqual(p[0]["track_id"],p2[0]["track_id"])
        self.assertEqual(p2[0]["observed_speed_px_s"],40)
        p,e=l.step(.5,[]);self.assertFalse(e[0]["confirmed_kill"])
    def test_gap(self):
        l=TrackLinker();d=dict(kind="monster",species="A",x=40,y=50)
        p,_=l.step(0,[d]);p2,e=l.step(2,[d]);self.assertNotEqual(p[0]["track_id"],p2[0]["track_id"])
    def test_context(self):
        self.assertEqual(trusted_context(dict(context={"map":"A"},context_age_seconds=-.1)),{})
        self.assertEqual(trusted_context(dict(context={"map":"A","map_uncertain":True},context_age_seconds=0)),{})
    def test_reference(self):
        refs=json.loads(Path(__file__).with_name("meow_reference.json").read_text())
        ref=reference_for("Primeval Forest I",refs)
        self.assertEqual(compare(ref,88949,952,7)["modeled_capacity_at_known_combat_population"],11)
        self.assertEqual(compare(ref,88949)["exp_pct_realistic"],100)
        self.assertIsNone(compare(ref)["modeled_capacity_at_known_combat_population"])
    def test_review(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"review.csv";p.write_text("map,species,confirmed,attack_lo,attack_hi,death_lo,death_hi,evidence\nA,B,yes,0,.25,1,1.25,frames\n")
            row=reviewed_combat(p)[0]
            self.assertEqual((row["ttk_lower_s"],row["ttk_upper_s"]),(.75,1.25))
if __name__=="__main__": unittest.main()
