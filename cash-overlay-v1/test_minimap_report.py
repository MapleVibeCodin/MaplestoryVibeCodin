import unittest
from minimap_report import summarize
def row(t,xp,at=None,x=.2,red=None,map_name='A'):
    return dict(monotonic=t,context_at=t if at is None else at,exp=xp,map=map_name,epoch=0,segment=1,level=45,status='candidate',box=[4,71,204,105],rect=[0,0,1366,768],normalized_xy=[x,.5],self_xy=[x*204,52],red_xy=red,nearest_red_px=10 if red else None)
class ReportTests(unittest.TestCase):
    def test_repeat_ocr(self):
        rows=[row(0,100),row(.1,100,0),row(.2,100,0),row(.3,185),row(.4,185,.3)]
        g=summarize(rows)['maps']['A']
        self.assertEqual(g['zones']['left']['exp'],85)
    def test_mixed_zone(self):
        rows=[row(0,100),row(.1,100,0,x=.8),row(.2,185,x=.8)]
        self.assertEqual(summarize(rows)['maps']['A']['zones']['mixed_or_unknown']['exp'],85)
    def test_gap(self):
        rows=[row(0,100),row(1,185)]
        self.assertEqual(summarize(rows)['maps']['A']['unassigned_exp'],85)
    def test_map_change(self):
        rows=[row(0,100),row(.1,185,map_name='B')]
        self.assertEqual(summarize(rows)['maps']['B']['matched_exp'],0)
if __name__=='__main__':unittest.main()
