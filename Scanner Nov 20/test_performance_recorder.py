import unittest
from performance_recorder import Transition,dark_fraction,summarize,PerformanceRecorder,summarize_transitions,read_integrity,atomic_report,RotatingLog
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import uuid
import json
import queue
from pathlib import Path

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

class PurchaseEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        with patch('threading.Thread.start'):
            self.r=PerformanceRecorder(self.tmp.name,purchase_source_verified=True)
        self.client=(0,0,1366,768)
        self.r.observe(None,None,1,self.client,True,False,None,unlocked=True)
        self.segment=self.r.active
        self.token=uuid.uuid4().hex
    def observe(self,kind,token=None,segment=None):
        return self.r.observe_purchase(kind,token or self.token,segment=segment or self.segment)
    def events(self):
        return [x for x in list(self.r.events.queue) if x['event'].startswith('purchase_')]
    def test_source_disabled(self):
        self.r.purchase_source_verified=False
        self.assertFalse(self.observe('submitted'))
        self.assertEqual(self.events(),[])
    def test_confirmation_needs_submission(self):
        self.assertFalse(self.observe('confirmed'))
        self.assertEqual(self.events(),[])
    def test_confirmed_once(self):
        self.assertTrue(self.observe('submitted'))
        self.assertFalse(self.observe('submitted'))
        self.assertTrue(self.observe('confirmed'))
        self.assertFalse(self.observe('confirmed'))
        self.assertEqual([e['event'] for e in self.events()],['purchase_attempt','purchase_outcome'])
        self.assertEqual(self.events()[-1]['outcome'],'confirmed')
    def test_explicit_failure(self):
        self.assertTrue(self.observe('submitted'))
        self.assertTrue(self.observe('failed'))
        self.assertEqual(self.events()[-1]['outcome'],'failed')
    def test_canceled_separate(self):
        self.observe('submitted')
        self.observe('canceled')
        self.assertEqual(self.events()[-1]['outcome'],'canceled')
    def test_focus_gap_unknown(self):
        self.observe('submitted')
        self.r.observe(None,None,1,self.client,False,False,None,unlocked=True)
        self.assertEqual(self.events()[-1]['outcome'],'unknown')
        self.assertEqual(self.events()[-1]['reason'],'focus_gap')
        self.assertFalse(self.observe('confirmed'))
    def test_timeout_unknown(self):
        self.observe('submitted')
        with patch('performance_recorder.time.perf_counter',return_value=self.r.purchase_pending[2]+11):
            self.assertFalse(self.observe('confirmed'))
        self.assertEqual(self.events()[-1]['reason'],'receipt_timeout')
    def test_segment_change_unknown(self):
        self.observe('submitted')
        self.r.end('scope_change')
        self.assertEqual(self.events()[-1]['outcome'],'unknown')
        self.assertFalse(self.observe('confirmed'))
    def test_wrong_segment_and_token_rejected(self):
        self.assertFalse(self.observe('submitted',segment='wrong'))
        self.assertFalse(self.observe('submitted',token='not-a-token'))
        self.observe('submitted')
        self.assertFalse(self.observe('confirmed',token=uuid.uuid4().hex))
        self.assertEqual(len(self.events()),1)
    def test_superseded_unknown(self):
        self.observe('submitted')
        token2=uuid.uuid4().hex
        self.assertTrue(self.observe('submitted',token=token2))
        self.assertEqual(self.events()[1]['outcome'],'unknown')
        self.assertFalse(self.observe('confirmed'))
        self.assertTrue(self.observe('confirmed',token=token2))
    def test_sold_and_generic_marker_not_purchase(self):
        self.r.marker('purchase_attempt',purchase_id=self.token)
        self.r.marker('purchase_outcome',purchase_id=self.token,outcome='confirmed')
        self.r.observe('a',SimpleNamespace(cc=1,fm=2,sold=True),1,self.client,True,False,
                       {'status':'sold / unavailable','hits':[]},unlocked=True)
        self.assertEqual(self.events(),[])

class TransitionObservationTests(unittest.TestCase):
    @staticmethod
    def gate(t,state):
        return {'t':t,'event':'transition_gate_sample','state':state}
    @staticmethod
    def start(t):
        return {'t':t,'event':'black_start'}
    @staticmethod
    def end(t,d=1000,association='unclassified'):
        return {'t':t,'event':'black_end','duration_ms':d,'association':association}
    def test_entrance_to_room_visual_only(self):
        r=summarize_transitions([self.gate(0,'entrance'),self.start(.5),self.end(1.5),self.gate(1.6,'room_confirmed')])
        self.assertEqual(len(r),1)
        self.assertEqual(r[0]['scene_change'],'entrance_to_room')
        self.assertEqual(r[0]['loading_ms'],1000)
        self.assertEqual(r[0]['readiness_ms'],100)
        self.assertNotIn('channel',r[0])
    def test_room_to_entrance(self):
        r=summarize_transitions([self.gate(0,'room_confirmed'),self.start(.5),self.end(1.5),self.gate(2,'entrance')])
        self.assertEqual(r[0]['scene_change'],'room_to_entrance')
    def test_shortcut_hint_not_channel_confirmation(self):
        r=summarize_transitions([self.gate(0,'room_confirmed'),self.start(.5),
             self.end(1.5,association='channel_shortcut_recent'),self.gate(2,'room_confirmed')])
        self.assertEqual(r[0]['association'],'channel_shortcut_recent')
        self.assertEqual(r[0]['scene_change'],'same_scene')
    def test_old_source_not_assumed(self):
        r=summarize_transitions([self.gate(0,'entrance'),self.start(2),self.end(3),self.gate(3.1,'room_confirmed')])
        self.assertIsNone(r[0]['source'])
        self.assertEqual(r[0]['scene_change'],'unknown')
    def test_unclassified_invalidates_source(self):
        r=summarize_transitions([self.gate(0,'entrance'),self.gate(.2,'unclassified'),self.start(.5),
                                 self.end(1.5),self.gate(2,'room_confirmed')])
        self.assertEqual(r[0]['scene_change'],'unknown')
    def test_focus_gap_interrupts(self):
        r=summarize_transitions([self.gate(0,'entrance'),self.start(.5),{'event':'sampling_gap','t':1},
                                 self.end(1.5),self.gate(2,'room_confirmed')])
        self.assertTrue(all(x['status']=='incomplete' and x['loading_ms'] is None for x in r))
    def test_no_destination_preserves_loading(self):
        r=summarize_transitions([self.start(.5),self.end(1.5),{'event':'attempt_end','t':2}])
        self.assertEqual(r[0]['loading_ms'],1000)
        self.assertIsNone(r[0]['readiness_ms'])
    def test_late_destination_not_associated(self):
        r=summarize_transitions([self.start(.5),self.end(1.5),self.gate(5,'room_confirmed')])
        self.assertIsNone(r[0]['destination'])
        self.assertEqual(r[0]['reason'],'destination_timeout')
    def test_bad_duration_rejected(self):
        r=summarize_transitions([self.start(.5),self.end(1.5,200)])
        self.assertEqual(r[0]['reason'],'duration_mismatch')
        self.assertIsNone(r[0]['loading_ms'])
    def test_missing_start_and_end(self):
        r=summarize_transitions([self.end(1),self.start(2)])
        self.assertEqual([x['reason'] for x in r],['unpaired_black_end','missing_black_end'])
    def test_next_loading_cannot_supply_previous_destination(self):
        r=summarize_transitions([self.start(.5),self.end(1.5),self.start(2),self.end(3),self.gate(3.1,'room_confirmed')])
        self.assertIsNone(r[0]['destination'])
        self.assertEqual(r[1]['destination'],'room_confirmed')
    def test_gate_heartbeat_and_focus_invalidation(self):
        with TemporaryDirectory() as tmp:
            with patch('threading.Thread.start'):
                r=PerformanceRecorder(tmp)
            r.observe(None,None,1,(0,0,1366,768),True,False,None,unlocked=True)
            with patch('performance_recorder.time.perf_counter',side_effect=[1,1.1,2.1,2.2]):
                r.observe_gate('entrance',(1366,768))
                r.observe_gate('entrance',(1366,768))
                r.observe_gate('entrance',(1366,768))
                r.context=None
                r.observe_gate('entrance',(1366,768))
            events=[x for x in r.events.queue if x['event']=='transition_gate_sample']
            self.assertEqual([x['state'] for x in events],['entrance','entrance','unavailable'])
    def test_export_transition_fields(self):
        base={'session':'s','attempt':'a','version':'24.63.4-lab4','schema':1}
        rows=[dict(base,**x) for x in [{'t':0,'event':'unlocked_observed'},self.gate(.1,'entrance'),
              self.start(.5),self.end(1.5),self.gate(1.7,'room_confirmed')]]
        report=summarize(rows)
        self.assertEqual(report['metrics']['visual_loading_ms']['median'],1000)
        self.assertEqual(report['metrics']['black_to_observed_scene_ms']['median'],200)
        self.assertEqual(len(report['attempts'][0]['transition_observations']),1)

class IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder=Path(self.tmp.name)
    def event(self,seq,event,t,session='s',attempt='a',**fields):
        row={'schema':1,'version':'24.63.4-lab5','session':session,'attempt':attempt,
             'event':event,'t':t,**fields}
        if seq is not None:row['seq']=seq
        else:row['version']='24.63.4'
        return row
    def health(self,last,written,dropped=0,session='s',final=True):
        return {'schema':1,'version':'24.63.4-lab5','session':session,'event':'recorder_health',
                't':9,'last_seq':last,'written':written,'dropped':dropped,'final':final}
    def complete(self,session='s'):
        return [self.event(1,'lock_observed',1,session=session),self.event(2,'attempt_end',2,session=session)]
    def write(self,name,rows,tail=b''):
        (self.folder/name).write_bytes(b''.join(json.dumps(r).encode()+b'\n' for r in rows)+tail)
    def read(self):
        return read_integrity(self.folder)
    def test_complete_finalized(self):
        self.write('a.jsonl',self.complete()+[self.health(2,2)])
        rows,audit=self.read()
        self.assertEqual(len(rows),2)
        self.assertEqual(audit['sessions'][0]['coverage'],'finalized')
    def test_copy_deduplication(self):
        records=self.complete()+[self.health(2,2)]
        self.write('a.jsonl',records);self.write('b.jsonl',records)
        rows,audit=self.read()
        self.assertEqual(len(rows),2)
        self.assertEqual(audit['duplicates_removed'],2)
    def test_conflicting_sequence_quarantined(self):
        self.write('a.jsonl',self.complete()+[self.event(2,'attempt_end',3),self.health(2,2)])
        rows,audit=self.read()
        self.assertEqual(rows,[])
        self.assertIn('conflicting_sequence',audit['sessions'][0]['reasons'])
    def test_missing_sequence_and_reported_drops(self):
        self.write('a.jsonl',[self.event(1,'lock_observed',1),self.event(3,'attempt_end',3),self.health(3,2,1)])
        rows,audit=self.read()
        self.assertEqual(rows,[])
        self.assertEqual(audit['sessions'][0]['sequence_gaps_lower_bound'],1)
    def test_trailing_drop_detected_by_final_health(self):
        self.write('a.jsonl',self.complete()+[self.health(3,2,1)])
        rows,audit=self.read()
        self.assertEqual(rows,[])
        self.assertEqual(audit['sessions'][0]['sequence_gaps_lower_bound'],1)
    def test_malformed_valid_json_quarantined(self):
        self.write('a.jsonl',self.complete()+[{"event":"black_end"},self.health(2,2)])
        rows,audit=self.read()
        self.assertEqual(rows,[])
        self.assertEqual(audit['invalid_lines'],1)
    def test_truncated_tail_preserved(self):
        self.write('a.jsonl',self.complete(),b'{"schema":')
        before=(self.folder/'a.jsonl').read_bytes()
        rows,audit=self.read()
        self.assertEqual(rows,[])
        self.assertEqual(audit['files'][0]['partial_tail'],1)
        self.assertEqual((self.folder/'a.jsonl').read_bytes(),before)
    def test_bad_utf8_and_nonfinite(self):
        self.write('a.jsonl',self.complete(),b'\xff\n{"schema":NaN}\n')
        rows,audit=self.read()
        self.assertEqual(rows,[])
        self.assertEqual(audit['invalid_lines'],2)
    def test_invalid_metric_rejected(self):
        self.write('a.jsonl',self.complete()+[self.event(3,'inventory_timing',3,total_ms=-1)])
        rows,audit=self.read()
        self.assertEqual(rows,[])
        self.assertEqual(audit['invalid_lines'],1)
    def test_open_segment_not_counted_as_completed(self):
        self.write('a.jsonl',self.complete()+[self.event(3,'unlocked_observed',3,attempt='b')])
        rows,audit=self.read()
        self.assertEqual(len(rows),2)
        self.assertEqual(audit['incomplete_segments'],1)
        self.assertEqual(audit['excluded_segments'],1)
        self.assertEqual(audit['sessions'][0]['coverage'],'open_or_interrupted')
    def test_legacy_closed_remains_readable(self):
        self.write('a.jsonl',[self.event(None,'lock_observed',1),self.event(None,'attempt_end',2)])
        rows,audit=self.read()
        self.assertEqual(len(rows),2)
        self.assertEqual(audit['sessions'][0]['coverage'],'legacy_unverified')
        self.assertIsNone(audit['sessions'][0]['sequence_gaps_lower_bound'])
    def test_other_session_survives_corrupt_file(self):
        self.write('bad.jsonl',self.complete('bad'),b'bad\n')
        self.write('good.jsonl',self.complete('good')+[self.health(2,2,session='good')])
        rows,audit=self.read()
        self.assertEqual({r['session'] for r in rows},{'good'})
    def test_orphan_purchase_segment_excluded(self):
        self.write('a.jsonl',[self.event(1,'lock_observed',1),self.event(2,'purchase_outcome',2,
            purchase_id=uuid.uuid4().hex,outcome='confirmed',confidence='verified_ui'),
            self.event(3,'attempt_end',3),self.health(3,3)])
        rows,audit=self.read()
        self.assertEqual(rows,[])
        self.assertEqual(audit['sessions'][0]['invalid_segments'],1)
    def test_queue_full_consumes_sequence(self):
        with patch('threading.Thread.start'):
            r=PerformanceRecorder(self.folder)
        r.events=queue.Queue(maxsize=1)
        r.active='a'
        r._emit('lock_observed',at=1)
        r._emit('scene_observed',at=2,scene='shop')
        self.assertEqual(r.dropped,1)
        self.assertEqual(r.events.get_nowait()['seq'],1)
        r._emit('attempt_end',at=3)
        self.assertEqual(r.events.get_nowait()['seq'],3)
    def test_atomic_failure_preserves_old_report(self):
        p=self.folder/'report.json'
        p.write_text('old')
        with self.assertRaises(ValueError):atomic_report(p,{'bad':float('nan')})
        self.assertEqual(p.read_text(),'old')
        self.assertEqual(list(self.folder.glob('.fm-report-*.tmp')),[])
        atomic_report(p,{'ok':True})
        self.assertEqual(json.loads(p.read_text()),{'ok':True})
    def test_raw_log_overwrite_refused(self):
        p=self.folder/'raw.jsonl'
        p.write_text('original')
        with self.assertRaises(ValueError):atomic_report(p,{'ok':True})
        self.assertEqual(p.read_text(),'original')
    def test_writer_failure_isolation(self):
        self.write('a.jsonl',self.complete()+[self.health(2,2)])
        rows,audit=read_integrity(self.folder,failed_session='s')
        self.assertEqual(rows,[])
        self.assertIn('file_or_writer_error',audit['sessions'][0]['reasons'])

class OverheadTests(unittest.TestCase):
    def test_rotation_preserves_whole_lines_and_bytes(self):
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/'session.jsonl'
            with RotatingLog(path,limit=20) as log:
                log.write('{"a":1}\n{"a":2}\n')
                log.write('{"a":3}\n')
                log.write('{"a":4}\n')
            files=sorted(Path(tmp).glob('*.jsonl'))
            self.assertEqual(len(files),2)
            self.assertEqual(b''.join(p.read_bytes() for p in files[::-1]),b'{"a":1}\n{"a":2}\n{"a":3}\n{"a":4}\n')
    def test_existing_history_never_overwritten(self):
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/'session.jsonl'
            path.write_bytes(b'original')
            with self.assertRaises(FileExistsError):
                with RotatingLog(path):pass
            self.assertEqual(path.read_bytes(),b'original')
    def test_export_limit_leaves_raw_unchanged(self):
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/'old.jsonl';path.write_bytes(b'x'*20)
            with patch('performance_recorder.MAX_EXPORT_BYTES',10):
                with self.assertRaises(ValueError):read_integrity(tmp)
            self.assertEqual(path.read_bytes(),b'x'*20)
    def test_rotated_parts_reconcile_sequence_health(self):
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/'s.jsonl'
            base={'schema':1,'version':'24.63.4-lab6','session':'s'}
            events=[dict(base,event='lock_observed',attempt='a',t=1,seq=1),
                    dict(base,event='attempt_end',attempt='a',t=2,seq=2),
                    dict(base,event='recorder_health',t=3,last_seq=2,written=2,dropped=0,final=True)]
            with RotatingLog(path,limit=150) as log:
                for row in events:log.write(json.dumps(row)+'\n')
            rows,integrity=read_integrity(tmp)
            self.assertEqual(len(rows),2)
            self.assertEqual(integrity['sessions'][0]['coverage'],'finalized')
    def test_row_limit_rejects_instead_of_partial_summary(self):
        with TemporaryDirectory() as tmp:
            (Path(tmp)/'a.jsonl').write_bytes(b'{}\n{}\n')
            with patch('performance_recorder.MAX_EXPORT_ROWS',1):
                with self.assertRaises(ValueError):read_integrity(tmp)

if __name__=='__main__':unittest.main()
