"""Mission Planner / companion-computer hand-off for rotary-wing Mission 2.

The Mission Planner mission remains the primary flight plan.  Image processing
is authorized only after the configured outside passage of Pole 2.  A target
intervention stores the active mission item, enters GUIDED, and later resumes
AUTO from a safe following item.
"""

from __future__ import annotations

from dataclasses import dataclass

from mission2_course import CourseState, Mission2CourseGate


@dataclass(frozen=True)
class Mission2Waypoints:
    pole_2_outside: int
    search_exit: int
    finish_line_crossed: int

    def __post_init__(self) -> None:
        values = (
            self.pole_2_outside,
            self.search_exit,
            self.finish_line_crossed,
        )
        if any(value < 0 for value in values):
            raise ValueError("Waypoint numaralari negatif olamaz.")
        if not self.pole_2_outside < self.search_exit < self.finish_line_crossed:
            raise ValueError(
                "Waypoint sirasi Direk2 < tarama cikisi < bitis olmalidir."
            )


class Mission2Supervisor:
    def __init__(self, flight_controller, waypoints: Mission2Waypoints) -> None:
        self.flight_controller = flight_controller
        self.waypoints = waypoints
        self.course = Mission2CourseGate()
        self.saved_mission_sequence: int | None = None
        self.target_intervention_active = False

    @property
    def camera_search_authorized(self) -> bool:
        return (
            not self.target_intervention_active
            and self.course.camera_search_authorized
        )

    def start(self) -> None:
        self.course.start_mission()

    def update_mission_sequence(self, sequence: int | None) -> None:
        if sequence is None:
            return

        sequence = int(sequence)
        if (
            self.course.state == CourseState.TRANSIT_TO_POLE_2
            and sequence >= self.waypoints.pole_2_outside
        ):
            self.course.confirm_pole_2_passage(outside_confirmed=True)

        if (
            self.course.state == CourseState.SEARCH_ACTIVE
            and sequence >= self.waypoints.search_exit
        ):
            self.course.abort(
                "Iki yuk tamamlanmadan tarama alani terk edildi."
            )

        if (
            self.course.state == CourseState.EXIT_ROUTE
            and sequence >= self.waypoints.finish_line_crossed
        ):
            self.course.confirm_finish_line_crossed()

    def begin_target_intervention(self) -> bool:
        if not self.course.payload_release_authorized:
            return False

        return self._begin_guided_intervention()

    def begin_mapping_intervention(self) -> bool:
        """Pause AUTO to center/geolocate a target without payload authority."""
        if not self.course.camera_search_authorized:
            return False

        return self._begin_guided_intervention()

    def _begin_guided_intervention(self) -> bool:
        if self.target_intervention_active:
            return False

        sequence = self.flight_controller.get_mission_current()
        if sequence is None or sequence >= self.waypoints.search_exit:
            return False

        if not self.flight_controller.pause_auto_for_target():
            return False

        self.saved_mission_sequence = int(sequence)
        self.target_intervention_active = True
        return True

    def complete_payload_and_resume(self, payload_name: str) -> bool:
        if not self.target_intervention_active:
            return False
        if self.saved_mission_sequence is None:
            return False

        self.course.record_payload_release(payload_name)
        resume_sequence = min(
            self.saved_mission_sequence + 1,
            self.waypoints.search_exit,
        )

        if not self.flight_controller.resume_auto_mission(resume_sequence):
            self.course.abort("AUTO rotasina geri donulemedi.")
            return False

        self.saved_mission_sequence = None
        self.target_intervention_active = False
        return True

    def complete_mapping_and_resume(self) -> bool:
        """Return to AUTO after geolocating a target without releasing payload."""
        if not self.target_intervention_active:
            return False
        if self.saved_mission_sequence is None:
            return False

        resume_sequence = min(
            self.saved_mission_sequence + 1,
            self.waypoints.search_exit,
        )
        if not self.flight_controller.resume_auto_mission(resume_sequence):
            self.course.abort("Haritalama sonrasi AUTO rotasina donulemedi.")
            return False

        self.saved_mission_sequence = None
        self.target_intervention_active = False
        return True

    def confirm_landed(self) -> None:
        self.course.confirm_landed()
