"""Here3 ile olculen Direk 1 ve Direk 2 koordinatlari.

Bu dosya yalnizca direk merkezlerini saklar. Hedef koordinatlari ve Mission
Planner rota noktalarinin burada bulunmasina izin verilmez.
"""

from __future__ import annotations

import json
import math
import statistics
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Mapping


EARTH_RADIUS_M = 6_371_000.0


@dataclass(frozen=True)
class PolePoint:
    lat: float
    lon: float

    @classmethod
    def from_dict(cls, value: object, name: str) -> "PolePoint":
        if not isinstance(value, dict):
            raise ValueError(f"{name} bir koordinat nesnesi olmalidir.")
        try:
            lat = float(value["lat"])
            lon = float(value["lon"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"{name} icin gecerli lat/lon gerekli.") from error
        if not -90.0 <= lat <= 90.0:
            raise ValueError(f"{name}.lat gecersiz.")
        if not -180.0 <= lon <= 180.0:
            raise ValueError(f"{name}.lon gecersiz.")
        return cls(lat=lat, lon=lon)


@dataclass(frozen=True)
class PoleCoordinates:
    pole_1: PolePoint
    pole_2: PolePoint

    @classmethod
    def from_dict(cls, data: object) -> "PoleCoordinates":
        if not isinstance(data, dict):
            raise ValueError("Direk koordinat dosyasi bir JSON nesnesi olmalidir.")
        return cls(
            pole_1=PolePoint.from_dict(data.get("pole_1"), "pole_1"),
            pole_2=PolePoint.from_dict(data.get("pole_2"), "pole_2"),
        )

    @classmethod
    def load(cls, path: str | Path = "pole_coordinates.json") -> "PoleCoordinates":
        with Path(path).open("r", encoding="utf-8") as file:
            return cls.from_dict(json.load(file))

    def save(self, path: str | Path = "pole_coordinates.json") -> None:
        with Path(path).open("w", encoding="utf-8") as file:
            json.dump(
                {
                    "pole_1": asdict(self.pole_1),
                    "pole_2": asdict(self.pole_2),
                },
                file,
                indent=2,
            )
            file.write("\n")


def _distance_m(lat_1: float, lon_1: float, lat_2: float, lon_2: float) -> float:
    lat_1_rad = math.radians(lat_1)
    lat_2_rad = math.radians(lat_2)
    d_lat = lat_2_rad - lat_1_rad
    d_lon = math.radians(lon_2 - lon_1)
    value = (
        math.sin(d_lat / 2.0) ** 2
        + math.cos(lat_1_rad) * math.cos(lat_2_rad) * math.sin(d_lon / 2.0) ** 2
    )
    return 2.0 * EARTH_RADIUS_M * math.asin(math.sqrt(value))


def robust_pole_fix(
    samples: Iterable[Mapping[str, object]],
    *,
    minimum_samples: int = 10,
    minimum_satellites: int = 6,
    maximum_outlier_radius_m: float = 3.0,
) -> tuple[PolePoint, int, float]:
    """Gecerli 3D-fix orneklerinden aykiri degerleri atip ortanca dondurur."""

    valid: list[tuple[float, float]] = []
    for sample in samples:
        try:
            fix_type = int(sample.get("fix_type", 0))
            satellites = int(sample.get("satellites", 0))
            lat = float(sample["lat"])
            lon = float(sample["lon"])
        except (KeyError, TypeError, ValueError):
            continue
        if fix_type >= 3 and satellites >= minimum_satellites and lat and lon:
            valid.append((lat, lon))

    if len(valid) < minimum_samples:
        raise RuntimeError(
            f"Yeterli Here3 ornegi yok: {len(valid)}/{minimum_samples}."
        )

    center_lat = statistics.median(item[0] for item in valid)
    center_lon = statistics.median(item[1] for item in valid)
    distances = [
        _distance_m(center_lat, center_lon, lat, lon) for lat, lon in valid
    ]
    median_distance = statistics.median(distances)
    radius = max(maximum_outlier_radius_m, median_distance * 3.0)
    filtered = [
        point for point, distance in zip(valid, distances) if distance <= radius
    ]
    if len(filtered) < minimum_samples:
        raise RuntimeError(
            f"Aykiri degerlerden sonra yeterli ornek yok: "
            f"{len(filtered)}/{minimum_samples}."
        )

    lat = statistics.median(item[0] for item in filtered)
    lon = statistics.median(item[1] for item in filtered)
    spread = max(_distance_m(lat, lon, a, b) for a, b in filtered)
    return PolePoint(lat=lat, lon=lon), len(filtered), spread
