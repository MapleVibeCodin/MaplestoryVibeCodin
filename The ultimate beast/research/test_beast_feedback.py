import json,queue,threading,tempfile,time,unittest
from pathlib import Path
from beast_feedback import NoScreenshots,writer_loop,build_report,finish_report

class FakeLog:
    def __init__(self,path): self.path=path
    def __enter__(self): self.out=self.path.open('x',encoding='utf-8');return self
    def write(self,s): self.out.write(s);self.out.flush()
    def __exit__(self,*args): self.out.close()

class FakeRecorder:
    def __init__(self,path):
        self.folder=path;self.file=path/'test.jsonl';self.stop=threading.Event();self.events=queue.Queue(2048);self._written=0;self.error=None;self.enabled=True;self.dropped=0
    def _health(self,out,final=False): out.write(json.dumps({'event':'recorder_health','t':time.perf_counter(),'final':final})+'\n')

class Tests(unittest.TestCase):
    def test_no_screenshots(self):
        r=NoScreenshots('unused');r.set_enabled(True);r.observe(1,(1,2,3,4));r.close();self.assertFalse(r.enabled);self.assertEqual(r.saved,0)
    def test_report(self):
        rows=[{'event':'lock_observed','t':1,'attempt':'a','cc':20,'fm':1},{'event':'beast_phase','t':1.1,'attempt':'a','stage':'route'},{'event':'beast_phase','t':2,'attempt':'a','stage':'scan'},{'event':'inventory_observed','t':2.1,'attempt':'a','state':'candidate'},{'event':'beast_phase','t':2.2,'attempt':'a','stage':'item_ready'},{'event':'inventory_timing','t':2.1,'attempt':'a','row_recognition_ms':12,'used_ocr':True,'name_cache_hits':2},{'event':'attempt_end','t':3,'attempt':'a'},{'event':'lock_observed','t':4,'attempt':'b'},{'event':'attempt_end','t':5,'attempt':'b'}]
        r=build_report(rows);self.assertEqual(r['locked_attempts'],2);self.assertEqual(r['candidate_attempts'],1);self.assertEqual(r['first_candidate_ms']['p50'],1100);self.assertEqual(r['runs'][0]['purchase_outcome'],'unknown');self.assertEqual(r['runs'][0]['phase_ms']['route'],900);self.assertEqual(r['ocr_scans'],1);self.assertEqual(r['name_cache_hits'],2);self.assertFalse(r['final_health'])
    def test_writer_and_export(self):
        with tempfile.TemporaryDirectory() as d:
            r=FakeRecorder(Path(d)/'performance');r.worker=threading.Thread(target=writer_loop,args=(r,FakeLog));r.worker.start()
            for i in range(500): r.events.put_nowait({'event':'test','t':time.perf_counter(),'i':i})
            r.stop.set();r.worker.join(3);self.assertFalse(r.worker.is_alive());self.assertEqual(r._written,500);self.assertIsNone(r.error)
            p=finish_report(r);a=json.loads(p.read_text());self.assertEqual(a['events'],502);self.assertTrue(a['final_health']);self.assertEqual(a['invalid_lines'],0)
    def test_writer_failure(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'performance';p.write_text('not a dir');r=FakeRecorder(p);writer_loop(r,FakeLog);self.assertTrue(r.stop.is_set());self.assertFalse(r.enabled);self.assertIsNotNone(r.error)
    def test_empty(self):
        self.assertEqual(build_report([])['first_candidate_ms'],{'n':0})

if __name__=='__main__': unittest.main()
