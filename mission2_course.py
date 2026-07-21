from __future__ import annotations

from enum import Enum
from typing import Mapping

from mission2_rules import (
    TARGET_TO_PAYLOAD,
    VALID_TARGETS,
)


REQUIRED_DROP_CHECKS = (
    "target_centered",
    "altitude_safe",
    "horizontal_speed_safe",
    "attitude_safe",
    "telemetry_healthy",
    "payload_system_ready",
)


class CourseState(str, Enum):
    PRE_FLIGHT = "PRE_FLIGHT"
    TRANSIT_TO_POLE_2 = "TRANSIT_TO_POLE_2"
    SEARCH_ACTIVE = "SEARCH_ACTIVE"
    TARGET_LOCKED = "TARGET_LOCKED"
    DROP_AUTHORIZED = "DROP_AUTHORIZED"
    EXIT_ROUTE = "EXIT_ROUTE"
    FINISH_LINE_CROSSED = "FINISH_LINE_CROSSED"
    LANDING = "LANDING"
    COMPLETE = "COMPLETE"
    ABORT = "ABORT"


class Mission2CourseGate:
    """
    Görev 2 güvenlik durum makinesi.

    Bu sınıf doğrudan uçuş veya servo komutu göndermez.
    Yalnızca görevde hangi işlemlerin yapılabileceğine
    karar verir.
    """

    def __init__(self) -> None:
        self.state = CourseState.PRE_FLIGHT

        self.pole_2_outside_confirmed = False
        self.active_target: str | None = None

        self.released_payloads: set[str] = set()
        self.completed_targets: set[str] = set()

        self.abort_reason: str | None = None

    @property
    def camera_search_authorized(self) -> bool:
        return (
            self.pole_2_outside_confirmed
            and self.state
            in {
                CourseState.SEARCH_ACTIVE,
                CourseState.TARGET_LOCKED,
                CourseState.DROP_AUTHORIZED,
            }
        )

    @property
    def payload_release_authorized(self) -> bool:
        return (
            self.state == CourseState.DROP_AUTHORIZED
            and self.active_target is not None
            and len(self.released_payloads) < 2
        )

    @property
    def mission_aborted(self) -> bool:
        return self.state == CourseState.ABORT

    def _ensure_not_aborted(self) -> None:
        if self.mission_aborted:
            raise RuntimeError(
                "Görev ABORT durumunda; işlem yapılamaz."
            )

    def start_mission(self) -> None:
        self._ensure_not_aborted()

        if self.state != CourseState.PRE_FLIGHT:
            raise RuntimeError(
                "Görev yalnızca PRE_FLIGHT "
                "durumundan başlatılabilir."
            )

        self.state = CourseState.TRANSIT_TO_POLE_2

    def confirm_pole_2_passage(
        self,
        outside_confirmed: bool,
    ) -> bool:
        self._ensure_not_aborted()

        if self.state != CourseState.TRANSIT_TO_POLE_2:
            return False

        if not outside_confirmed:
            return False

        self.pole_2_outside_confirmed = True
        self.state = CourseState.SEARCH_ACTIVE

        return True

    def lock_target(
        self,
        target_name: str,
    ) -> bool:
        self._ensure_not_aborted()

        if not self.camera_search_authorized:
            return False

        if self.state != CourseState.SEARCH_ACTIVE:
            return False

        if target_name not in VALID_TARGETS:
            return False

        if target_name in self.completed_targets:
            return False

        self.active_target = target_name
        self.state = CourseState.TARGET_LOCKED

        return True

    def cancel_target_lock(
        self,
    ) -> bool:
        self._ensure_not_aborted()

        if self.state not in {
            CourseState.TARGET_LOCKED,
            CourseState.DROP_AUTHORIZED,
        }:
            return False

        self.active_target = None
        self.state = CourseState.SEARCH_ACTIVE

        return True

    def authorize_payload_release(
        self,
        target_name: str,
        payload_name: str,
        safety_checks: Mapping[str, bool],
    ) -> bool:
        self._ensure_not_aborted()

        if self.state != CourseState.TARGET_LOCKED:
            return False

        if self.active_target != target_name:
            return False

        expected_payload = TARGET_TO_PAYLOAD.get(
            target_name
        )

        if expected_payload != payload_name:
            return False

        if payload_name in self.released_payloads:
            return False

        for check_name in REQUIRED_DROP_CHECKS:
            if safety_checks.get(check_name) is not True:
                return False

        self.state = CourseState.DROP_AUTHORIZED

        return True

    def record_payload_release(
        self,
        target_name: str,
        payload_name: str,
    ) -> None:
        self._ensure_not_aborted()

        if not self.payload_release_authorized:
            raise RuntimeError(
                "Yük bırakma yetkisi bulunmuyor."
            )

        if self.active_target != target_name:
            raise RuntimeError(
                "Bırakılan yük aktif hedefle eşleşmiyor."
            )

        expected_payload = TARGET_TO_PAYLOAD.get(
            target_name
        )

        if expected_payload != payload_name:
            raise RuntimeError(
                "Hedef için yanlış renkli yük seçildi."
            )

        if payload_name in self.released_payloads:
            raise RuntimeError(
                "Aynı yük ikinci kez bırakılamaz."
            )

        self.released_payloads.add(payload_name)
        self.completed_targets.add(target_name)
        self.active_target = None

        if len(self.released_payloads) == 2:
            self.state = CourseState.EXIT_ROUTE
        else:
            self.state = CourseState.SEARCH_ACTIVE

    def confirm_finish_line_crossed(
        self,
    ) -> None:
        self._ensure_not_aborted()

        if self.state != CourseState.EXIT_ROUTE:
            raise RuntimeError(
                "İki yük tamamlanmadan bitiş "
                "çizgisi onaylanamaz."
            )

        self.state = CourseState.FINISH_LINE_CROSSED

    def start_landing(
        self,
    ) -> None:
        self._ensure_not_aborted()

        if self.state != CourseState.FINISH_LINE_CROSSED:
            raise RuntimeError(
                "Bitiş çizgisi geçilmeden iniş "
                "aşamasına geçilemez."
            )

        self.state = CourseState.LANDING

    def confirm_landed(
        self,
    ) -> None:
        self._ensure_not_aborted()

        if self.state != CourseState.LANDING:
            raise RuntimeError(
                "Araç LANDING durumunda değil."
            )

        self.state = CourseState.COMPLETE

    def abort(
        self,
        reason: str,
    ) -> None:
        if self.state == CourseState.COMPLETE:
            raise RuntimeError(
                "Tamamlanmış görev ABORT yapılamaz."
            )

        cleaned_reason = str(reason).strip()

        self.abort_reason = (
            cleaned_reason
            if cleaned_reason
            else "Neden belirtilmedi."
        )

        self.active_target = None
        self.state = CourseState.ABORT

    def get_status(self) -> dict:
        return {
            "state": self.state.value,
            "pole_2_outside_confirmed": (
                self.pole_2_outside_confirmed
            ),
            "camera_search_authorized": (
                self.camera_search_authorized
            ),
            "payload_release_authorized": (
                self.payload_release_authorized
            ),
            "active_target": self.active_target,
            "released_payloads": sorted(
                self.released_payloads
            ),
            "completed_targets": sorted(
                self.completed_targets
            ),
            "abort_reason": self.abort_reason,
        }