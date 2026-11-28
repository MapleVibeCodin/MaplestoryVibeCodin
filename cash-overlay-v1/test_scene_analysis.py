import tempfile
import unittest
import json
from pathlib import Path
from screenshots import ScreenshotStore
from scene_analysis import distance, nearest, suppress, gap_bounds, template_hits

class SceneTests(unittest.TestCase):
    def test_meta(self):
        with tempfile.TemporaryDirectory() as d:
            s=ScreenshotStore(d,min_free=0)
            p=s.save(b"\x89PNG\r\n\x1a\nfixture")
            s.metadata(p,{"exp":123,"wallet":None})
            self.assertEqual(json.loads(p.with_suffix(".json").read_text()),{"exp":123,"wallet":None})
    def test_distance(self):
        self.assertEqual(distance((0,0),(3,4)),5)
        self.assertIsNone(nearest({"x":0,"y":0},[]))
    def test_gap(self):
        self.assertEqual(gap_bounds(0,1,7,8),[6,8])
        with self.assertRaises(ValueError): gap_bounds(5,1,7,8)
    def test_suppress(self):
        a=dict(kind="monster",x=10,y=10,w=20,h=20,score=.99)
        b={**a,"x":12,"score":.91}
        c={**b,"kind":"player"}
        self.assertEqual(len(suppress([a,b,c])),2)
    def test_synthetic_match(self):
        import numpy as np
        rng=np.random.default_rng(12)
        tpl=rng.integers(0,256,(10,12,3),dtype=np.uint8)
        img=np.zeros((90,100,3),dtype=np.uint8)
        img[20:30,30:42]=tpl
        hits=template_hits(img,tpl,"monster","fixture",.98)
        self.assertEqual(len(hits),1)
        self.assertEqual((hits[0]["x"],hits[0]["y"]),(36,25))
if __name__=="__main__": unittest.main()
