"""Safe, serializable dynamic Mission 2 plan generation.

This module only builds plans.  It deliberately does not upload missions to
the flight controller; real MAVLink upload is enabled only after dry tests.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from json import dump
from pathlib import Path

from field_config import FieldConfig
from target_map import TargetFix


class ScenarioMode(str, Enum):
    FIELD_COORDINATES = "FIELD_COORDINATES"
    MISSION_PLANNER_TEMPLATE = "MISSION_PLANNER_TEMPLATE"


@dataclass(frozen=True)
class PlannedWaypoint:
    role: str
    command: str
    lat: float | None = None
    lon: float | None = None
    alt_m: float | None = None
    source_sequence: int | None = None
    target_name: str | None = None


@dataclass(frozen=True)
class DynamicMissionPlan:
    scenario: ScenarioMode
    waypoints: tuple[PlannedWaypoint, ...]

    def save(self, path: str | Path) -> None:
        with Path(path).open("w", encoding="utf-8") as file:
            dump(
                {
                    "scenario": self.scenario.value,
                    "waypoints": [asdict(item) for item in self.waypoints],
                },
                file,
                indent=2,
                ensure_ascii=False,
            )


class DynamicMissionBuilder:
    def __init__(self, mission_altitude_m: float = 25.0) -> None:
        self.mission_altitude_m = float(mission_altitude_m)

    @staticmethod
    def _target_waypoints(
        ordered_targets: tuple[str, ...],
        target_fixes: dict[str, TargetFix],
        altitude_m: float,
    ) -> list[PlannedWaypoint]:
        if any(name not in target_fixes for name in ordered_targets):
            raise RuntimeError("Iki hedef haritalanmadan dinamik rota olusturulamaz.")
        return [
            PlannedWaypoint(
                role=f"TARGET_{index}",
                command="NAV_WAYPOINT",
                lat=target_fixes[name].lat,
                lon=target_fixes[name].lon,
                alt_m=altitude_m,
                target_name=name,
            )
            for index, name in enumerate(ordered_targets, start=1)
        ]

    def build_field_plan(
        self,
        field: FieldConfig,
        target_fixes: dict[str, TargetFix],
        ordered_targets: tuple[str, ...],
    ) -> DynamicMissionPlan:
        items = self._target_waypoints(
            ordered_targets,
            target_fixes,
            field.mission_altitude_m,
        )

        finish_lat = (field.start_line.left.lat + field.start_line.right.lat) / 2.0
        finish_lon = (field.start_line.left.lon + field.start_line.right.lon) / 2.0

        items.extend(
            [
                PlannedWaypoint(
                    role="SEARCH_EXIT",
                    command="NAV_WAYPOINT",
                    lat=field.search_polygon[0].lat,
                    lon=field.search_polygon[0].lon,
                    alt_m=field.mission_altitude_m,
                ),
                PlannedWaypoint(
                    role="FINISH_CROSS",
                    command="NAV_WAYPOINT",
                    lat=finish_lat,
                    lon=finish_lon,
                    alt_m=field.mission_altitude_m,
                ),
                PlannedWaypoint(
                    role="LAND_APPROACH",
                    command="NAV_WAYPOINT",
                    lat=field.landing_point.lat,
                    lon=field.landing_point.lon,
                    alt_m=max(8.0, field.drop_altitude_m),
                ),
                PlannedWaypoint(
                    role="LAND",
                    command="NAV_LAND",
                    lat=field.landing_point.lat,
                    lon=field.landing_point.lon,
                    alt_m=0.0,
                ),
            ]
        )
        return DynamicMissionPlan(ScenarioMode.FIELD_COORDINATES, tuple(items))

    def build_template_plan(
        self,
        route: dict,
        target_fixes: dict[str, TargetFix],
        ordered_targets: tuple[str, ...],
    ) -> DynamicMissionPlan:
        required = (
            "search_exit_waypoint",
            "finish_line_crossed_waypoint",
            "landing_approach_waypoint",
            "landing_waypoint",
        )
        missing = [name for name in required if name not in route]
        if missing:
            raise ValueError("Mission Planner sablonu eksik: " + ", ".join(missing))

        items = self._target_waypoints(
            ordered_targets,
            target_fixes,
            self.mission_altitude_m,
        )
        for role, key, command in (
            ("SEARCH_EXIT", "search_exit_waypoint", "TEMPLATE_WAYPOINT"),
            ("FINISH_CROSS", "finish_line_crossed_waypoint", "TEMPLATE_WAYPOINT"),
            ("LAND_APPROACH", "landing_approach_waypoint", "TEMPLATE_WAYPOINT"),
            ("LAND", "landing_waypoint", "TEMPLATE_LAND"),
        ):
            items.append(
                PlannedWaypoint(
                    role=role,
                    command=command,
                    source_sequence=int(route[key]),
                )
            )
        return DynamicMissionPlan(
            ScenarioMode.MISSION_PLANNER_TEMPLATE,
            tuple(items),
        )

