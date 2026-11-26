import unittest
from performance_recorder import Transition,dark_fraction,summarize,PerformanceRecorder
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

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
class UnlockedRecorderTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        with patch('threading.Thread.start'):
            self.r=PerformanceRecorder(self.tmp.name)
        self.client=(0,0,1366,768)
        self.deal=SimpleNamespace(cc=1,fm=2,sold=False)
    def observe(self,key=None,deal=None,focused=True,inventory=None,unlocked=True):
        self.r.observe(key,deal,1,self.client,focused,False,inventory,unlocked=unlocked)
    def rows(self):
        rows=[]
        while not self.r.events.empty():rows.append(self.r.events.get_nowait())
        return rows
    def test_no_target_unlocked_start_and_no_capture_on_observe(self):
        self.r.capture=lambda *a,**k:self.fail('observe must not capture')
        self.observe()
        self.assertEqual(self.r.scope,'unlocked')
        self.assertIsNotNone(self.r.context)
        self.assertEqual([x['event'] for x in self.rows()],['unlocked_observed','scene_observed'])
    def test_initial_unfocused_no_segment(self):
        self.observe(focused=False)
        self.assertIsNone(self.r.active)
        self.assertEqual(self.rows(),[])
        self.observe()
        self.assertIsNotNone(self.r.active)
    def test_focus_loss_same_segment_and_resume(self):
        self.observe()
        aid=self.r.active
        self.observe(focused=False)
        self.assertEqual(self.r.active,aid)
        self.assertIsNone(self.r.context)
        self.observe()
        self.assertEqual(self.r.active,aid)
        self.assertIsNotNone(self.r.context)
        self.assertEqual(sum(x['event']=='unlocked_observed' for x in self.rows()),1)
    def test_armed_inventory_uses_existing_timing(self):
        inv={'status':'','hits':[('MATCH',(0,0,1,1))],
             'timing':{'scan_id':1,'total_ms':2,'row_recognition_ms':1,'used_ocr':False,'visible_rows':1}}
        self.observe('a',self.deal,inventory=inv)
        self.observe('a',self.deal,inventory=inv)
        rows=self.rows()
        self.assertEqual(sum(x['event']=='inventory_timing' for x in rows),1)
        self.assertTrue(any(x['event']=='inventory_observed' and x['state']=='unique_match' for x in rows))
        self.assertTrue(rows[0]['target_present'])
        self.assertNotIn('cc',rows[0])
    def test_scope_switch_same_key_creates_distinct_segments(self):
        self.observe('a',self.deal)
        a=self.r.active
        self.observe('a',self.deal,unlocked=False)
        b=self.r.active
        self.observe('a',self.deal)
        c=self.r.active
        self.assertEqual(len({a,b,c}),3)
        result=summarize(self.rows())
        self.assertEqual(result['locked_attempt_count'],1)
        self.assertEqual(result['unlocked_segment_count'],2)
        self.assertTrue(all(x['outcome']=='unknown' for x in result['attempts']))
    def test_target_change_resets_segment(self):
        self.observe('a',self.deal)
        a=self.r.active
        self.observe('b',self.deal)
        self.assertNotEqual(a,self.r.active)
    def test_unlocked_late_pointer_and_skip_events_ignored(self):
        self.observe()
        self.r.marker('pointer_result',ok=True)
        self.r.marker('skip_requested')
        self.r.marker('scanner_gate',state='no_target')
        events=[x['event'] for x in self.rows()]
        self.assertNotIn('pointer_result',events)
        self.assertNotIn('skip_requested',events)
        self.assertIn('scanner_gate',events)
    def test_pause_and_resume(self):
        self.observe()
        a=self.r.active
        self.r.set_enabled(False)
        self.observe()
        self.assertIsNone(self.r.active)
        self.r.set_enabled(True)
        self.observe()
        self.assertNotEqual(a,self.r.active)
        self.assertEqual(sum(x['event']=='attempt_end' for x in self.rows()),1)
    def test_legacy_unlocked_metric_separation(self):
        base={'session':'s','version':'24.63.4-lab2','schema':1}
        rows=[{**base,'attempt':'u','event':'unlocked_observed','t':1},
              {**base,'attempt':'u','event':'scene_observed','scene':'shop','t':2},
              {**base,'attempt':'l','event':'lock_observed','t':3},
              {**base,'attempt':'l','event':'scene_observed','scene':'shop','t':3.5}]
        result=summarize(rows)
        self.assertEqual(result['metrics']['unlocked_to_first_shop_ms']['median'],1000)
        self.assertEqual(result['metrics']['lock_to_first_shop_ms']['median'],500)
    def test_same_attempt_id_different_sessions_not_merged(self):
        base={'attempt':'same','version':'24.63.4-lab2','schema':1,'event':'unlocked_observed','t':1}
        result=summarize([{**base,'session':'a'},{**base,'session':'b'}])
        self.assertEqual(result['unlocked_segment_count'],2)
    def test_no_target_no_fake_inventory(self):
        self.observe()
        self.observe()
        self.assertFalse(any(x['event']=='inventory_observed' for x in self.rows()))

if __name__=='__main__':unittest.main()
