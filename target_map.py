"""Mission 2 target geolocation storage.

Target coordinates are captured only after visual centering.  Multiple GPS
samples are reduced with a median so a single noisy sample cannot move the
generated waypoint.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from json import dump
from pathlib import Path
from statistics import median
from typing import Iterable


@dataclass(frozen=True)
class TargetFix:
    target_name: str
    lat: float
    lon: float
    alt_m: float
    confidence: float
    sample_count: int
    simulated: bool
    captured_at: str


class TargetMap:
    def __init__(self, required_targets: Iterable[str]) -> None:
        self.required_targets = tuple(required_targets)
        if len(set(self.required_targets)) != len(self.required_targets):
            raise ValueError("Hedef isimleri benzersiz olmalidir.")
        self._fixes: dict[str, TargetFix] = {}

    def is_mapped(self, target_name: str) -> bool:
        return target_name in self._fixes

    @property
    def all_mapped(self) -> bool:
        return all(name in self._fixes for name in self.required_targets)

    @property
    def mapped_count(self) -> int:
        return len(self._fixes)

    def get(self, target_name: str) -> TargetFix | None:
        return self._fixes.get(target_name)

    def as_dict(self) -> dict[str, TargetFix]:
        return self._fixes.copy()

    def record(
        self,
        target_name: str,
        samples: Iterable[dict],
        confidence: float,
        *,
        simulated: bool = False,
    ) -> TargetFix:
        if target_name not in self.required_targets:
            raise ValueError(f"Bilinmeyen hedef: {target_name}")
        if self.is_mapped(target_name):
            raise RuntimeError(f"Hedef zaten haritalandi: {target_name}")

        valid_samples = []
        for sample in samples:
            if not sample or not sample.get("ok", False):
                continue
            if int(sample.get("fix_type", 0) or 0) < 3 and not simulated:
                continue
            lat = sample.get("lat")
            lon = sample.get("lon")
            alt = sample.get("alt", 0.0)
            if lat is None or lon is None:
                continue
            valid_samples.append((float(lat), float(lon), float(alt or 0.0)))

        if not valid_samples:
            raise RuntimeError("Hedef koordinati icin gecerli GPS ornegi yok.")

        fix = TargetFix(
            target_name=target_name,
            lat=median(item[0] for item in valid_samples),
            lon=median(item[1] for item in valid_samples),
            alt_m=median(item[2] for item in valid_samples),
            confidence=float(confidence),
            sample_count=len(valid_samples),
            simulated=bool(simulated),
            captured_at=datetime.now(timezone.utc).isoformat(),
        )
        self._fixes[target_name] = fix
        return fix

    def save(self, path: str | Path) -> None:
        output = {
            "all_mapped": self.all_mapped,
            "targets": {
                name: asdict(fix)
                for name, fix in self._fixes.items()
            },
        }
        with Path(path).open("w", encoding="utf-8") as file:
            dump(output, file, indent=2, ensure_ascii=False)

