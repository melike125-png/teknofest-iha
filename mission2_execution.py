"""Two-stage target mapping and payload execution coordinator."""

from __future__ import annotations

from enum import Enum

from dynamic_mission import DynamicMissionPlan
from target_map import TargetFix, TargetMap


class ExecutionStage(str, Enum):
    MAPPING = "MAPPING"
    PAYLOAD_EXECUTION = "PAYLOAD_EXECUTION"
    LANDING_ROUTE = "LANDING_ROUTE"
    COMPLETE = "COMPLETE"
    ABORT = "ABORT"


class Mission2ExecutionCoordinator:
    def __init__(self, required_targets: tuple[str, ...]) -> None:
        self.required_targets = tuple(required_targets)
        self.target_map = TargetMap(self.required_targets)
        self.stage = ExecutionStage.MAPPING
        self.mapping_order: list[str] = []
        self.payload_index = 0
        self.released_targets: set[str] = set()
        self.plan: DynamicMissionPlan | None = None
        self.abort_reason: str | None = None

    @property
    def expected_payload_target(self) -> str | None:
        if self.stage != ExecutionStage.PAYLOAD_EXECUTION:
            return None
        if self.payload_index >= len(self.mapping_order):
            return None
        return self.mapping_order[self.payload_index]

    @property
    def payload_release_authorized(self) -> bool:
        target = self.expected_payload_target
        return (
            self.stage == ExecutionStage.PAYLOAD_EXECUTION
            and self.target_map.all_mapped
            and self.plan is not None
            and target is not None
            and target not in self.released_targets
        )

    def record_mapped_target(self, fix: TargetFix) -> None:
        if self.stage != ExecutionStage.MAPPING:
            raise RuntimeError("Haritalama asamasi tamamlandi.")
        if not self.target_map.is_mapped(fix.target_name):
            raise RuntimeError("Hedef once TargetMap icine kaydedilmelidir.")
        if fix.target_name not in self.mapping_order:
            self.mapping_order.append(fix.target_name)

    def activate_plan(self, plan: DynamicMissionPlan) -> None:
        if self.stage != ExecutionStage.MAPPING:
            raise RuntimeError("Plan yalnizca haritalama sonunda etkinlestirilebilir.")
        if not self.target_map.all_mapped:
            raise RuntimeError("Iki hedef haritalanmadan plan etkinlestirilemez.")
        if len(self.mapping_order) != len(self.required_targets):
            raise RuntimeError("Hedef ziyaret sirasi eksik.")
        self.plan = plan
        self.stage = ExecutionStage.PAYLOAD_EXECUTION

    def mark_payload_released(self, target_name: str) -> None:
        if not self.payload_release_authorized:
            raise RuntimeError("Yuk birakma yetkisi yok.")
        if target_name != self.expected_payload_target:
            raise RuntimeError("Yanlis hedef icin yuk birakma engellendi.")

        self.released_targets.add(target_name)
        self.payload_index += 1
        if self.payload_index >= len(self.mapping_order):
            self.stage = ExecutionStage.LANDING_ROUTE

    def mark_landed(self) -> None:
        if self.stage != ExecutionStage.LANDING_ROUTE:
            raise RuntimeError("Iki yuk birakilmadan inis tamamlanamaz.")
        self.stage = ExecutionStage.COMPLETE

    def abort(self, reason: str) -> None:
        self.abort_reason = reason.strip() or "belirtilmedi"
        self.stage = ExecutionStage.ABORT

