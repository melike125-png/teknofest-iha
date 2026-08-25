"""Mission 2 field configuration.

Only known course geometry belongs in this file. Target coordinates are
deliberately excluded because the 2026 rules require the two rotary-wing
targets to be found by image processing after random placement.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mission2_rules import calculate_distance_m


@dataclass(frozen=True)
class GeoPoint:
    lat: float
    lon: float

    @classmethod
    def from_dict(cls, value: dict[str, Any], name: str) -> "GeoPoint":
        if not isinstance(value, dict):
            raise ValueError(f"{name} bir koordinat nesnesi olmalidir.")

        try:
            lat = float(value["lat"])
            lon = float(value["lon"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"{name} icin gecerli lat/lon gerekli.") from error

        if not -90.0 <= lat <= 90.0:
            raise ValueError(f"{name}.lat -90 ile 90 arasinda olmali.")
        if not -180.0 <= lon <= 180.0:
            raise ValueError(f"{name}.lon -180 ile 180 arasinda olmali.")

        return cls(lat=lat, lon=lon)


@dataclass(frozen=True)
class StartLine:
    left: GeoPoint
    right: GeoPoint


@dataclass(frozen=True)
class FieldConfig:
    name: str
    start_line: StartLine
    pole_1: GeoPoint
    pole_2: GeoPoint
    search_polygon: tuple[GeoPoint, ...]
    landing_point: GeoPoint
    mission_altitude_m: float
    search_altitude_m: float
    drop_altitude_m: float

    @property
    def pole_distance_m(self) -> float:
        return calculate_distance_m(
            self.pole_1.lat,
            self.pole_1.lon,
            self.pole_2.lat,
            self.pole_2.lon,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FieldConfig":
        if not isinstance(data, dict):
            raise ValueError("Saha ayari bir JSON nesnesi olmalidir.")

        forbidden_keys = {
            "targets",
            "target_positions",
            "blue_hexagon",
            "red_triangle",
            "mavi_altigen",
            "kirmizi_ucgen",
        }
        present_forbidden = forbidden_keys.intersection(data)
        if present_forbidden:
            names = ", ".join(sorted(present_forbidden))
            raise ValueError(
                "Hedef koordinatlari saha dosyasina girilemez: " + names
            )

        start_line_data = data.get("start_line")
        if not isinstance(start_line_data, dict):
            raise ValueError("start_line.left ve start_line.right gerekli.")

        polygon_data = data.get("search_polygon")
        if not isinstance(polygon_data, list) or len(polygon_data) < 4:
            raise ValueError("search_polygon en az dort kose icermeli.")

        altitudes = {}
        for key in (
            "mission_altitude_m",
            "search_altitude_m",
            "drop_altitude_m",
        ):
            try:
                altitudes[key] = float(data[key])
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError(f"{key} pozitif bir sayi olmali.") from error
            if altitudes[key] <= 0:
                raise ValueError(f"{key} pozitif bir sayi olmali.")

        if altitudes["drop_altitude_m"] > altitudes["search_altitude_m"]:
            raise ValueError("Birakma irtifasi tarama irtifasindan buyuk olamaz.")

        return cls(
            name=str(data.get("name", "isimsiz_saha")),
            start_line=StartLine(
                left=GeoPoint.from_dict(start_line_data.get("left"), "start_line.left"),
                right=GeoPoint.from_dict(start_line_data.get("right"), "start_line.right"),
            ),
            pole_1=GeoPoint.from_dict(data.get("pole_1"), "pole_1"),
            pole_2=GeoPoint.from_dict(data.get("pole_2"), "pole_2"),
            search_polygon=tuple(
                GeoPoint.from_dict(point, f"search_polygon[{index}]")
                for index, point in enumerate(polygon_data)
            ),
            landing_point=GeoPoint.from_dict(
                data.get("landing_point"), "landing_point"
            ),
            **altitudes,
        )

    @classmethod
    def load(cls, path: str | Path) -> "FieldConfig":
        with Path(path).open("r", encoding="utf-8") as file:
            return cls.from_dict(json.load(file))

