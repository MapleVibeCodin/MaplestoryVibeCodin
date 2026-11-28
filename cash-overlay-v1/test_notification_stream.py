import json
import tempfile
import unittest
from pathlib import Path
from notification_stream import SourceTail,consensus,breakdown

class StreamTests(unittest.TestCase):
    def test_incremental_and_partial(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'rows';t=SourceTail(p)
            self.assertEqual(t.poll(),[])
            p.write_bytes(b'{"id":1}\n{"id":')
            self.assertEqual(t.poll(),[{'id':1}]);old=t.offset
            self.assertEqual(t.poll(),[{'id':1}]);self.assertEqual(t.offset,old)
            with p.open('ab') as f:f.write(b'2}\n')
            self.assertEqual(t.poll(),[{'id':1},{'id':2}])
            p.write_bytes(b'')
            with self.assertRaises(ValueError):t.poll()
    def test_bad_row_keeps_index(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'rows';p.write_bytes(b'bad\n[]\n{"id":3}\n')
            self.assertEqual(SourceTail(p).poll(),[{'invalid_source':True},{'invalid_source':True},{'id':3}])
    def test_consensus(self):
        a=('mesos',13);b=('mesos',18)
        self.assertEqual(consensus(a,None,a),a)
        self.assertIsNone(consensus(a,b,a));self.assertIsNone(consensus(None,None,a))
        self.assertEqual(consensus(a,a),a)
    def test_breakdown_keeps_repeated_arrivals(self):
        r=[{'born':10,'event':['item','Echopus Leg',1,'etc']},{'born':10,'event':['item','Echopus Leg',1,'etc']},{'born':72,'event':['shared_exp',7]},{'born':73,'event':None}]
        b=breakdown(r,10,73);self.assertEqual(b['species_drop_units'],{'Echopus':2});self.assertTrue(b['party_evidence']);self.assertIsNone(b['personal_kills']);self.assertEqual(b['minute_bins'][1]['delivered_rows'],2)
if __name__=='__main__':unittest.main()
