import os

from mission2_rules import (
    TARGET_BLUE_HEXAGON,
    TARGET_RED_TRIANGLE,
)
from target_position_recorder import TargetPositionRecorder


TEST_FILE = "test_target_positions.json"


def main():
    if os.path.exists(TEST_FILE):
        os.remove(TEST_FILE)

    recorder = TargetPositionRecorder(
        required_samples=3,
        max_sample_spread_m=2.0,
        output_file=TEST_FILE,
    )

    blue_samples = [
        {"lat": 39.0000000, "lon": 32.0000000},
        {"lat": 39.0000005, "lon": 32.0000003},
        {"lat": 38.9999998, "lon": 31.9999999},
    ]

    result = recorder.add_centered_sample(
        target_name=TARGET_BLUE_HEXAGON,
        vehicle_position=blue_samples[0],
        is_centered=False,
    )

    assert result["accepted"] is False

    for sample in blue_samples:
        result = recorder.add_centered_sample(
            target_name=TARGET_BLUE_HEXAGON,
            vehicle_position=sample,
            is_centered=True,
        )

    assert result["completed"] is True
    assert recorder.has_position(
        TARGET_BLUE_HEXAGON
    )

    red_samples = [
        {"lat": 39.0001000, "lon": 32.0000000},
        {"lat": 39.0001003, "lon": 32.0000002},
        {"lat": 39.0000998, "lon": 31.9999999},
    ]

    for sample in red_samples:
        result = recorder.add_centered_sample(
            target_name=TARGET_RED_TRIANGLE,
            vehicle_position=sample,
            is_centered=True,
        )

    assert result["completed"] is True
    assert recorder.all_positions_known() is True
    assert os.path.exists(TEST_FILE)

    positions = recorder.get_positions()

    print("Kaydedilen hedef konumları:")
    print(positions)

    second_recorder = TargetPositionRecorder(
        required_samples=3,
        output_file=TEST_FILE,
    )

    assert second_recorder.load() is True
    assert second_recorder.all_positions_known() is True

    os.remove(TEST_FILE)

    print("HEDEF KONUM KAYIT TESTİ BAŞARILI")


if __name__ == "__main__":
    main()