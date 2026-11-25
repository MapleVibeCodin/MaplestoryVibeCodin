import unittest
from performance_recorder import Transition,dark_fraction,summarize

class RecorderTests(unittest.TestCase):
    def test_pixels(self):
        self.assertEqual(dark_fraction((bytes(12),2,2,6)),1)
        self.assertEqual(dark_fraction((bytes([255]*12),2,2,6)),0)
        self.assertIsNone(dark_fraction(None))
    def test_two_sample_transition(self):
        d=Transition()
        for t in (0,.05):self.assertEqual(d.observe(t,False),[])
        self.assertEqual(d.observe(.10,True),[])
        self.assertEqual(d.observe(.15,True)[0][0],'black_start')
        self.assertEqual(d.observe(.20,False),[])
        self.assertAlmostEqual(d.observe(.25,False)[0][2]['duration_ms'],100)
    def test_initial_black_unknown(self):
        d=Transition()
        for t in (0,.05):self.assertEqual(d.observe(t,True),[])
        for t in (.10,.15):self.assertEqual(d.observe(t,False),[])
    def test_gap_interrupts(self):
        d=Transition()
        for t in (0,.05):d.observe(t,False)
        for t in (.10,.15):d.observe(t,True)
        d.observe(.2,None)
        self.assertEqual(d.observe(.25,False),[])
        self.assertEqual(d.observe(.30,False),[])
    def test_long_gap_interrupts(self):
        d=Transition()
        for t in (0,.05):d.observe(t,False)
        for t in (.10,.15):d.observe(t,True)
        self.assertEqual(d.observe(.60,False),[])
        self.assertEqual(d.observe(.65,False),[])
    def test_summary_no_false_success(self):
        base={'attempt':'a','session':'s','version':'24.58.0','schema':1}
        rows=[{**base,'event':'lock_observed','t':1},
              {**base,'event':'pointer_result','t':1.2,'ok':True,'kind':'shop','total_ms':8},
              {**base,'event':'scene_observed','t':1.4,'scene':'shop'},
              {**base,'event':'inventory_observed','t':1.5,'state':'unique_match'},
              {**base,'event':'inventory_observed','t':1.6,'state':'target_unavailable'}]
        r=summarize(rows)
        self.assertEqual(r['attempt_count'],1)
        self.assertEqual(r['attempts'][0]['outcome'],'unknown')
        self.assertEqual(r['metrics']['shop_pointer_to_observed_shop_ms']['median'],200)
        self.assertEqual(r['metrics']['lock_to_first_item_match_ms']['median'],500)
    def test_inventory_timing_metrics(self):
        base={'attempt':'a','session':'s','version':'24.63.0','schema':1}
        rows=[{**base,'event':'lock_observed','t':1},
              {**base,'event':'scanner_gate','t':1.1,'state':'room_confirmed'},
              {**base,'event':'inventory_timing','t':1.2,'total_ms':110,'row_recognition_ms':90,'used_ocr':True,'visible_rows':6},
              {**base,'event':'inventory_timing','t':1.3,'total_ms':8,'row_recognition_ms':1,'used_ocr':False,'visible_rows':5}]
        report=summarize(rows)
        self.assertEqual(report['metrics']['inventory_scan_ms']['n'],2)
        self.assertEqual(report['metrics']['inventory_row_recognition_ms:ocr']['median'],90)
        self.assertEqual(report['metrics']['inventory_row_recognition_ms:cache']['median'],1)
        self.assertEqual(report['attempts'][0]['timeline'][1]['state'],'room_confirmed')
if __name__=='__main__':unittest.main()
