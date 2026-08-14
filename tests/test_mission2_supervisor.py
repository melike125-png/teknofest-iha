import unittest

from mission2_course import CourseState
from mission2_supervisor import Mission2Supervisor, Mission2Waypoints


class FakeFlightController:
    def __init__(self):
        self.sequence = 0
        self.paused = False
        self.resumed_at = None

    def get_mission_current(self):
        return self.sequence

    def pause_auto_for_target(self):
        self.paused = True
        return True

    def resume_auto_mission(self, sequence):
        self.resumed_at = sequence
        return True


class Mission2SupervisorTests(unittest.TestCase):
    def test_rule_compliant_auto_guided_auto_flow(self):
        flight = FakeFlightController()
        supervisor = Mission2Supervisor(
            flight,
            Mission2Waypoints(4, 12, 18),
        )
        supervisor.start()

        supervisor.update_mission_sequence(3)
        self.assertFalse(supervisor.camera_search_authorized)
        self.assertFalse(supervisor.begin_target_intervention())

        supervisor.update_mission_sequence(4)
        self.assertTrue(supervisor.camera_search_authorized)

        flight.sequence = 7
        self.assertTrue(supervisor.begin_target_intervention())
        self.assertTrue(flight.paused)
        self.assertFalse(supervisor.camera_search_authorized)

        self.assertTrue(supervisor.complete_payload_and_resume("kirmizi_yuk"))
        self.assertEqual(flight.resumed_at, 8)
        self.assertEqual(supervisor.course.state, CourseState.SEARCH_ACTIVE)

        flight.sequence = 10
        self.assertTrue(supervisor.begin_target_intervention())
        self.assertTrue(supervisor.complete_payload_and_resume("mavi_yuk"))
        self.assertEqual(supervisor.course.state, CourseState.EXIT_ROUTE)

        supervisor.update_mission_sequence(18)
        self.assertEqual(
            supervisor.course.state,
            CourseState.FINISH_LINE_CROSSED,
        )
        supervisor.confirm_landed()
        self.assertEqual(supervisor.course.state, CourseState.COMPLETE)

    def test_search_exit_without_two_payloads_aborts(self):
        supervisor = Mission2Supervisor(
            FakeFlightController(),
            Mission2Waypoints(4, 12, 18),
        )
        supervisor.start()
        supervisor.update_mission_sequence(4)
        supervisor.update_mission_sequence(12)
        self.assertEqual(supervisor.course.state, CourseState.ABORT)


if __name__ == "__main__":
    unittest.main()
