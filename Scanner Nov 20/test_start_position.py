import unittest
from route_logic import START_POINT, ROPE_POINTS, plan

class StartPositionTests(unittest.TestCase):
    def test_all_routes_start_on_middle_platform(self):
        self.assertEqual(START_POINT,(385,133))
        for room in range(1,21):
            self.assertEqual(plan(20,room).waypoints[0],START_POINT)
    def test_same_row(self):
        for room in range(13,17):
            p=plan(20,room)
            self.assertNotIn('DROP',p.route_text)
            self.assertNotIn('CLIMB',p.route_text)
            self.assertEqual(len(p.waypoints),3)
            self.assertEqual(p.waypoints[1][1],START_POINT[1])
    def test_lower_and_upper(self):
        for room in range(1,13):
            p=plan(20,room)
            self.assertEqual(p.waypoints[1],ROPE_POINTS['ROW2'])
            self.assertIn('DROP',p.route_text)
        for room in range(17,21):
            p=plan(20,room)
            self.assertEqual(p.waypoints[1],ROPE_POINTS['ROW4'])
            self.assertIn('CLIMB',p.route_text)
