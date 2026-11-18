import unittest
from scan_budget import (
    should_ocr, CAPTURE_PERIOD_S, SEARCH_OCR_PERIOD_S, STATIC_RETRY_S,
    VERIFY_PERIOD_S, LOST_OCR_PERIOD_S, PREVIEW_PERIOD_S
)

class TestScanBudget(unittest.TestCase):
    def test_capture_and_preview_caps(self):
        self.assertGreaterEqual(CAPTURE_PERIOD_S, 1/15)
        self.assertGreaterEqual(PREVIEW_PERIOD_S, 1/6)

    def test_new_alert_immediate(self):
        self.assertTrue(should_ocr(1.0,0.0,True,False,False))

    def test_animated_screen_is_throttled(self):
        self.assertFalse(should_ocr(10.1,10.0,True,False,False))
        self.assertTrue(should_ocr(10+SEARCH_OCR_PERIOD_S,10.0,True,False,False))

    def test_static_screen_not_scanned_repeatedly(self):
        self.assertFalse(should_ocr(11.0,10.0,False,False,False))
        self.assertTrue(should_ocr(10+STATIC_RETRY_S,10.0,False,False,False))

    def test_tracked_target_verification_capped(self):
        self.assertFalse(should_ocr(11.0,10.0,True,True,True))
        self.assertTrue(should_ocr(10+VERIFY_PERIOD_S,10.0,True,True,True))

    def test_lost_target_rechecks(self):
        self.assertFalse(should_ocr(10.1,10.0,True,False,True))
        self.assertTrue(should_ocr(10+LOST_OCR_PERIOD_S,10.0,True,False,True))

if __name__=='__main__': unittest.main()

class TestSearchDutyBudget(unittest.TestCase):
    def test_bursts_are_followed_by_cpu_cooldown(self):
        from scan_budget import ScanDutyBudget
        budget=ScanDutyBudget(fraction=.35)
        self.assertEqual(budget.remaining(0.),0.)
        budget.charge(.2,now=.2)
        self.assertGreater(budget.remaining(.3),0.)
        self.assertAlmostEqual(budget.ready_at,.2/.35)
        self.assertEqual(budget.remaining(budget.ready_at),0.)

    def test_repeated_searches_stay_within_worker_cpu_share(self):
        from scan_budget import ScanDutyBudget
        budget=ScanDutyBudget(fraction=.35)
        now=0.;cpu=0.
        for duration in (.04,.5,.02,.3,.15)*4:
            now+=budget.remaining(now)
            now+=duration;cpu+=duration
            budget.charge(duration,now)
            now+=budget.remaining(now)
        self.assertLessEqual(cpu/now,.35+1e-9)
