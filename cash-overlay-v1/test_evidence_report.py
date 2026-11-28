import unittest
from evidence_report import active_intervals,summarize,compare
def row(t,exp=10,active=True,party=1,at=None,seg="x",level=44,folder="s",raw=0):
    return {"image":folder+"/frame.png","metadata":{"monotonic":t,"context":{
        "monotonic":t if at is None else at,"map":"A","segment":seg,"level":level,"party":party,"party_confirmed":True,
        "job":"Assassin","active":active,"exp":exp,"exp_confident":True,"raw_mesos":raw,"cash_ledger":{"observed_raw":raw}}}}
class EvidenceTests(unittest.TestCase):
    def test_pause_gap_and_reset(self):
        r=list(active_intervals([row(0),row(1,20),row(2,30,False),row(3,40),row(4,50),row(8,70),row(9,80,seg="y")]))
        self.assertEqual([x["exp_delta"] for x in r],[10,10])
    def test_duplicate_context(self):
        r=list(active_intervals([row(0),row(.25,at=0),row(.5,at=0),row(1,20)]))
        self.assertEqual(len(r),1)
        self.assertEqual(r[0]["seconds"],1)
    def test_party_level_and_session_boundary(self):
        self.assertEqual(list(active_intervals([row(0),row(1,party=2),row(2,party=2,level=45),row(3,party=2,level=45,folder="b")])),[])
    def test_future_and_stale(self):
        self.assertEqual(list(active_intervals([row(0,at=1),row(1,at=-3),row(2)])),[])
    def test_rates_and_missing(self):
        rows=[row(i,exp=10*i,raw=i) for i in range(61)]
        x=summarize(active_intervals(rows))[0]
        self.assertEqual(x["exp_hr"],36000)
        self.assertEqual(x["pickup_hr"],3600)
        rows[5]["metadata"]["context"]["exp_confident"]=False
        x=summarize(active_intervals(rows))[0]
        self.assertIsNone(x["exp_hr"])
        self.assertEqual(x["exp_seconds"],58)
    def test_unreadable_and_missing_ledger(self):
        a,b,c=row(0),row(1),row(2)
        b["unreadable"]=True
        self.assertEqual(list(active_intervals([a,b,c])),[])
        b.pop("unreadable");b["metadata"]["context"].pop("cash_ledger")
        self.assertTrue(all(x["pickup_delta"] is None for x in active_intervals([a,b,c])))
    def test_comparison(self):
        a={"results":[{"level":44,"party":"solo","rows":[["A",200,100,3,4,1,True,[41,47]]]}]}
        x=compare(dict(map="A",level=44,party=1,job="Assassin",exp_hr=150),a)
        self.assertEqual(x["local_exp_pct"],150)
if __name__=="__main__": unittest.main()
