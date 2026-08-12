from __future__ import annotations

import json
import math
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


EARTH_RADIUS_M = 6_371_000.0

FORBIDDEN_TARGET_KEYS = {
    "target",
    "targets",
    "target_position",
    "target_positions",
    "target_coordinate",
    "target_coordinates",
    "mavi_altigen",
    "kirmizi_ucgen",
    "mavi_kare",
    "kirmizi_kare",
    "blue_hexagon",
    "red_triangle",
    "blue_square",
    "red_square",
}


class CoordinateSource(str, Enum):
    ORGANIZER_PROVIDED = "ORGANIZER_PROVIDED"
    FIELD_SURVEYED = "FIELD_SURVEYED"


@dataclass(frozen=True)
class GeoPoint:
    lat: float
    lon: float


@dataclass(frozen=True)
class StartLine:
    left: GeoPoint
    right: GeoPoint


@dataclass(frozen=True)
class AltitudeSettings:
    mission_m: float
    search_m: float
    drop_m: float


@dataclass(frozen=True)
class RouteSettings:
    pole_clearance_m: float
    search_line_spacing_m: float


@dataclass(frozen=True)
class SafetySettings:
    maximum_altitude_m: float
    minimum_battery_percent: float
    maximum_horizontal_speed_m_s: float
    maximum_drop_speed_m_s: float


@dataclass(frozen=True)
class FieldConfig:
    schema_version: int
    field_name: str
    coordinate_source: CoordinateSource

    start_line: StartLine
    takeoff_point: GeoPoint
    pole_1: GeoPoint
    pole_2: GeoPoint
    search_polygon: tuple[GeoPoint, ...]
    landing_point: GeoPoint

    altitudes: AltitudeSettings
    route: RouteSettings
    safety: SafetySettings


def calculate_distance_m(
    point_a: GeoPoint,
    point_b: GeoPoint,
) -> float:
    lat_a = math.radians(point_a.lat)
    lat_b = math.radians(point_b.lat)

    delta_lat = math.radians(
        point_b.lat - point_a.lat
    )

    delta_lon = math.radians(
        point_b.lon - point_a.lon
    )

    value = (
        math.sin(delta_lat / 2.0) ** 2
        + math.cos(lat_a)
        * math.cos(lat_b)
        * math.sin(delta_lon / 2.0) ** 2
    )

    value = min(1.0, max(0.0, value))

    angle = 2.0 * math.atan2(
        math.sqrt(value),
        math.sqrt(1.0 - value),
    )

    return EARTH_RADIUS_M * angle


def _find_forbidden_target_keys(
    value: Any,
    path: str = "root",
) -> list[str]:
    found: list[str] = []

    if isinstance(value, dict):
        for key, child_value in value.items():
            normalized_key = str(key).strip().lower()

            if normalized_key in FORBIDDEN_TARGET_KEYS:
                found.append(f"{path}.{key}")

            found.extend(
                _find_forbidden_target_keys(
                    child_value,
                    f"{path}.{key}",
                )
            )

    elif isinstance(value, list):
        for index, child_value in enumerate(value):
            found.extend(
                _find_forbidden_target_keys(
                    child_value,
                    f"{path}[{index}]",
                )
            )

    return found


def _require_dict(
    value: Any,
    field_name: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(
            f"{field_name} bir JSON nesnesi olmalıdır."
        )

    return value


def _require_number(
    data: dict[str, Any],
    key: str,
    section_name: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    value = data.get(key)

    if isinstance(value, bool) or not isinstance(
        value,
        (int, float),
    ):
        raise ValueError(
            f"{section_name}.{key} sayısal olmalıdır."
        )

    number = float(value)

    if not math.isfinite(number):
        raise ValueError(
            f"{section_name}.{key} sonlu bir sayı olmalıdır."
        )

    if minimum is not None and number < minimum:
        raise ValueError(
            f"{section_name}.{key} en az {minimum} olmalıdır."
        )

    if maximum is not None and number > maximum:
        raise ValueError(
            f"{section_name}.{key} en fazla {maximum} olmalıdır."
        )

    return number


def _parse_point(
    value: Any,
    field_name: str,
) -> GeoPoint:
    data = _require_dict(value, field_name)

    lat = _require_number(
        data,
        "lat",
        field_name,
        minimum=-90.0,
        maximum=90.0,
    )

    lon = _require_number(
        data,
        "lon",
        field_name,
        minimum=-180.0,
        maximum=180.0,
    )

    return GeoPoint(lat=lat, lon=lon)


def _parse_start_line(
    value: Any,
) -> StartLine:
    data = _require_dict(value, "start_line")

    start_line = StartLine(
        left=_parse_point(
            data.get("left"),
            "start_line.left",
        ),
        right=_parse_point(
            data.get("right"),
            "start_line.right",
        ),
    )

    length_m = calculate_distance_m(
        start_line.left,
        start_line.right,
    )

    if length_m < 1.0:
        raise ValueError(
            "Başlangıç çizgisinin iki ucu "
            "birbirine çok yakın."
        )

    return start_line


def _parse_search_polygon(
    value: Any,
) -> tuple[GeoPoint, ...]:
    if not isinstance(value, list):
        raise ValueError(
            "search_polygon bir liste olmalıdır."
        )

    if len(value) < 3:
        raise ValueError(
            "search_polygon en az üç köşe içermelidir."
        )

    polygon = tuple(
        _parse_point(
            point_data,
            f"search_polygon[{index}]",
        )
        for index, point_data in enumerate(value)
    )

    unique_points = {
        (point.lat, point.lon)
        for point in polygon
    }

    if len(unique_points) != len(polygon):
        raise ValueError(
            "search_polygon aynı köşeyi "
            "birden fazla içeremez."
        )

    for index, point_a in enumerate(polygon):
        point_b = polygon[
            (index + 1) % len(polygon)
        ]

        distance_m = calculate_distance_m(
            point_a,
            point_b,
        )

        if distance_m < 1.0:
            raise ValueError(
                "Tarama alanındaki ardışık köşeler "
                "birbirine çok yakın."
            )

    return polygon


def _parse_altitudes(
    value: Any,
) -> AltitudeSettings:
    data = _require_dict(value, "altitudes")

    return AltitudeSettings(
        mission_m=_require_number(
            data,
            "mission_m",
            "altitudes",
            minimum=0.1,
        ),
        search_m=_require_number(
            data,
            "search_m",
            "altitudes",
            minimum=0.1,
        ),
        drop_m=_require_number(
            data,
            "drop_m",
            "altitudes",
            minimum=0.1,
        ),
    )


def _parse_route(
    value: Any,
) -> RouteSettings:
    data = _require_dict(value, "route")

    return RouteSettings(
        pole_clearance_m=_require_number(
            data,
            "pole_clearance_m",
            "route",
            minimum=1.0,
        ),
        search_line_spacing_m=_require_number(
            data,
            "search_line_spacing_m",
            "route",
            minimum=1.0,
        ),
    )


def _parse_safety(
    value: Any,
) -> SafetySettings:
    data = _require_dict(value, "safety")

    return SafetySettings(
        maximum_altitude_m=_require_number(
            data,
            "maximum_altitude_m",
            "safety",
            minimum=1.0,
            maximum=120.0,
        ),
        minimum_battery_percent=_require_number(
            data,
            "minimum_battery_percent",
            "safety",
            minimum=1.0,
            maximum=99.0,
        ),
        maximum_horizontal_speed_m_s=_require_number(
            data,
            "maximum_horizontal_speed_m_s",
            "safety",
            minimum=0.1,
        ),
        maximum_drop_speed_m_s=_require_number(
            data,
            "maximum_drop_speed_m_s",
            "safety",
            minimum=0.1,
        ),
    )


def _validate_field_config(
    config: FieldConfig,
) -> None:
    altitudes = config.altitudes

    if altitudes.drop_m >= altitudes.search_m:
        raise ValueError(
            "drop_m, search_m değerinden düşük olmalıdır."
        )

    if altitudes.search_m > altitudes.mission_m:
        raise ValueError(
            "search_m, mission_m değerinden "
            "yüksek olamaz."
        )

    if (
        altitudes.mission_m
        > config.safety.maximum_altitude_m
    ):
        raise ValueError(
            "mission_m güvenlik irtifası sınırını aşıyor."
        )

    pole_distance_m = calculate_distance_m(
        config.pole_1,
        config.pole_2,
    )

    if pole_distance_m < 20.0:
        raise ValueError(
            "Direkler arasındaki mesafe olağan dışı "
            f"derecede kısa: {pole_distance_m:.1f} m"
        )

    if (
        config.route.pole_clearance_m
        >= pole_distance_m / 2.0
    ):
        raise ValueError(
            "pole_clearance_m direkler arasındaki "
            "mesafeye göre çok büyük."
        )

    if (
        config.safety.maximum_drop_speed_m_s
        > config.safety.maximum_horizontal_speed_m_s
    ):
        raise ValueError(
            "maximum_drop_speed_m_s yatay hız "
            "sınırından büyük olamaz."
        )


def load_field_config(
    file_path: str | Path,
) -> FieldConfig:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Saha dosyası bulunamadı: {path.resolve()}"
        )

    if not path.is_file():
        raise ValueError(
            f"Saha yolu bir dosya değil: {path.resolve()}"
        )

    try:
        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            raw_data = json.load(file)

    except json.JSONDecodeError as error:
        raise ValueError(
            f"Saha dosyası geçerli JSON değil: {error}"
        ) from error

    data = _require_dict(raw_data, "root")

    forbidden_keys = _find_forbidden_target_keys(data)

    if forbidden_keys:
        raise ValueError(
            "Hedef koordinatları saha dosyasına "
            "girilemez. Yasak alanlar: "
            + ", ".join(forbidden_keys)
        )

    schema_version = data.get("schema_version")

    if schema_version != 1:
        raise ValueError(
            "Desteklenmeyen schema_version. "
            "Beklenen değer: 1"
        )

    field_name = data.get("field_name")

    if not isinstance(field_name, str):
        raise ValueError(
            "field_name metin olmalıdır."
        )

    field_name = field_name.strip()

    if not field_name:
        raise ValueError(
            "field_name boş olamaz."
        )

    source_value = data.get("coordinate_source")

    try:
        coordinate_source = CoordinateSource(
            source_value
        )
    except ValueError as error:
        valid_values = ", ".join(
            source.value
            for source in CoordinateSource
        )

        raise ValueError(
            "Geçersiz coordinate_source. "
            f"Geçerli değerler: {valid_values}"
        ) from error

    config = FieldConfig(
        schema_version=schema_version,
        field_name=field_name,
        coordinate_source=coordinate_source,
        start_line=_parse_start_line(
            data.get("start_line")
        ),
        takeoff_point=_parse_point(
            data.get("takeoff_point"),
            "takeoff_point",
        ),
        pole_1=_parse_point(
            data.get("pole_1"),
            "pole_1",
        ),
        pole_2=_parse_point(
            data.get("pole_2"),
            "pole_2",
        ),
        search_polygon=_parse_search_polygon(
            data.get("search_polygon")
        ),
        landing_point=_parse_point(
            data.get("landing_point"),
            "landing_point",
        ),
        altitudes=_parse_altitudes(
            data.get("altitudes")
        ),
        route=_parse_route(
            data.get("route")
        ),
        safety=_parse_safety(
            data.get("safety")
        ),
    )

    _validate_field_config(config)

    return config