"""Yarisma hazirliginda Here3 ile Direk 1/2 koordinati toplama araci."""

from __future__ import annotations

import argparse
import time

from cube_mavlink import CubeMavlink
from pole_coordinates import PoleCoordinates, PolePoint, robust_pole_fix


def capture_pole(
    cube: CubeMavlink,
    name: str,
    duration_s: float,
    sample_interval_s: float,
) -> PolePoint:
    print(f"\n{name}: Here3 sabit tutuluyor, {duration_s:.0f} saniye olculuyor...")
    samples = []
    deadline = time.monotonic() + duration_s
    while time.monotonic() < deadline:
        sample = cube.get_gps(timeout=2)
        samples.append(sample)
        if sample.get("lat") is not None:
            print(
                f"\rFix={sample.get('fix_type')}  "
                f"Uydu={sample.get('satellites')}  "
                f"Ornek={len(samples)}",
                end="",
                flush=True,
            )
        time.sleep(sample_interval_s)
    print()

    point, count, spread = robust_pole_fix(samples)
    print(
        f"{name} KAYDEDILDI -> lat={point.lat:.7f} lon={point.lon:.7f} "
        f"| kullanilan={count} | yayilim={spread:.2f} m"
    )
    return point


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="pole_coordinates.json")
    parser.add_argument("--duration", type=float, default=30.0)
    parser.add_argument("--interval", type=float, default=0.2)
    args = parser.parse_args()

    if args.duration < 5:
        raise SystemExit("Olcum suresi en az 5 saniye olmali.")

    cube = CubeMavlink()
    print(f"Cube baglantisi bekleniyor: {cube.port} @ {cube.baud}")
    cube.connect(timeout=15)
    print("Cube baglandi. Here3 icin 3D Fix bekleyin.")

    input("Direk 1 merkezinde hazirsaniz ENTER'a basin...")
    pole_1 = capture_pole(cube, "DIREK 1", args.duration, args.interval)
    input("Direk 2 merkezinde hazirsaniz ENTER'a basin...")
    pole_2 = capture_pole(cube, "DIREK 2", args.duration, args.interval)

    coordinates = PoleCoordinates(pole_1=pole_1, pole_2=pole_2)
    coordinates.save(args.output)
    print(f"\nTAMAMLANDI -> {args.output}")
    print(f"Direk 1: {pole_1.lat:.7f}, {pole_1.lon:.7f}")
    print(f"Direk 2: {pole_2.lat:.7f}, {pole_2.lon:.7f}")


if __name__ == "__main__":
    main()
