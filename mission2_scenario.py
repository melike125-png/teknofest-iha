"""Scenario selection for official coordinates or Mission Planner template."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from dynamic_mission import ScenarioMode
from field_config import FieldConfig
from pole_coordinates import PoleCoordinates


@dataclass(frozen=True)
class Mission2Scenario:
    mode: ScenarioMode
    field: FieldConfig | None = None
    route: dict | None = None
    poles: PoleCoordinates | None = None


def load_scenario(
    field_path: str | Path = "field_config.json",
    route_path: str | Path = "mission2_route.json",
    pole_path: str | Path = "pole_coordinates.json",
) -> Mission2Scenario:
    field_file = Path(field_path)
    if field_file.is_file():
        return Mission2Scenario(
            mode=ScenarioMode.FIELD_COORDINATES,
            field=FieldConfig.load(field_file),
        )

    route_file = Path(route_path)
    if not route_file.is_file():
        raise FileNotFoundError(
            "field_config.json yok; Mission Planner modu icin "
            "mission2_route.json gerekli."
        )
    with route_file.open("r", encoding="utf-8") as file:
        route = json.load(file)
    pole_file = Path(pole_path)
    poles = PoleCoordinates.load(pole_file) if pole_file.is_file() else None
    return Mission2Scenario(
        mode=ScenarioMode.MISSION_PLANNER_TEMPLATE,
        route=route,
        poles=poles,
    )
