import unittest,tempfile,zipfile
from pathlib import Path
from compact_capture import EvidencePolicy,export_session
class CompactTests(unittest.TestCase):
    def test_scene_burst(self):
        p=EvidencePolicy()
        self.assertTrue(p.scene(0)); self.assertTrue(p.scene(7.75))
        self.assertTrue(p.scene(8));self.assertFalse(p.scene(8.25))
        self.assertTrue(p.scene(120));self.assertTrue(p.scene(121))
        self.assertTrue(p.scene(132,reference=True));self.assertTrue(p.scene(133,full=True))
    def test_regions(self):
        p=EvidencePolicy();r=[("inventory_use",(0,0,4,4)),("status",(0,0,2,2))]
        self.assertEqual(p.regions(r,0),r);self.assertEqual(p.regions(r,1),[])
        self.assertEqual(p.regions(r,5),r[1:])
        self.assertEqual(p.regions(r,6,changed=True),r[:1])
    def test_export(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);s=root/"session";s.mkdir();(s/"f.json").write_text("{}")
            (s/"tmp.part").write_text("incomplete");z=export_session(s,root/"out")
            with zipfile.ZipFile(z) as f:self.assertEqual(f.namelist(),["f.json"]);self.assertIsNone(f.testzip())
            self.assertTrue((s/"f.json").is_file())
if __name__=="__main__":unittest.main()
