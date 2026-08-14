"""Rule-driven course gates for the international rotary-wing Mission 2."""

from __future__ import annotations

from enum import Enum


class CourseState(str, Enum):
    PRE_FLIGHT = "PRE_FLIGHT"
    TRANSIT_TO_POLE_2 = "TRANSIT_TO_POLE_2"
    SEARCH_ACTIVE = "SEARCH_ACTIVE"
    EXIT_ROUTE = "EXIT_ROUTE"
    FINISH_LINE_CROSSED = "FINISH_LINE_CROSSED"
    COMPLETE = "COMPLETE"
    ABORT = "ABORT"


class Mission2CourseGate:
    """Prevents target search and payload release before the legal course gate."""

    def __init__(self) -> None:
        self.state = CourseState.PRE_FLIGHT
        self.pole_2_outside_confirmed = False
        self.released_payloads: set[str] = set()
        self.abort_reason: str | None = None

    @property
    def camera_search_authorized(self) -> bool:
        return (
            self.state == CourseState.SEARCH_ACTIVE
            and self.pole_2_outside_confirmed
        )

    @property
    def payload_release_authorized(self) -> bool:
        return self.camera_search_authorized and len(self.released_payloads) < 2

    def start_mission(self) -> None:
        if self.state != CourseState.PRE_FLIGHT:
            raise RuntimeError("Gorev yalnizca PRE_FLIGHT durumundan baslatilabilir.")
        self.state = CourseState.TRANSIT_TO_POLE_2

    def confirm_pole_2_passage(self, outside_confirmed: bool) -> bool:
        if self.state != CourseState.TRANSIT_TO_POLE_2:
            return False
        if not outside_confirmed:
            return False

        self.pole_2_outside_confirmed = True
        self.state = CourseState.SEARCH_ACTIVE
        return True

    def record_payload_release(self, payload_name: str) -> None:
        if not self.payload_release_authorized:
            raise RuntimeError("Yuk birakma icin saha gecidi yetkisi yok.")
        if payload_name in self.released_payloads:
            raise RuntimeError("Ayni yuk ikinci kez birakilamaz.")

        self.released_payloads.add(payload_name)
        if len(self.released_payloads) == 2:
            self.state = CourseState.EXIT_ROUTE

    def confirm_finish_line_crossed(self) -> None:
        if self.state != CourseState.EXIT_ROUTE:
            raise RuntimeError("Iki yuk tamamlanmadan bitis cizgisine gecilemez.")
        self.state = CourseState.FINISH_LINE_CROSSED

    def confirm_landed(self) -> None:
        if self.state != CourseState.FINISH_LINE_CROSSED:
            raise RuntimeError("Bitis cizgisi gecilmeden gorev tamamlanamaz.")
        self.state = CourseState.COMPLETE

    def abort(self, reason: str) -> None:
        self.abort_reason = reason.strip() or "belirtilmedi"
        self.state = CourseState.ABORT

