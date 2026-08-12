from mission2_rules import (
    TARGET_BLUE_HEXAGON,
    TARGET_RED_TRIANGLE,
)
from targeting import TargetingSystem


def main():
    targeting = TargetingSystem()

    detections = [
        {
            "class_name": TARGET_BLUE_HEXAGON,
            "confidence": 0.98,
            "box": (450, 280, 610, 440),
        },
        {
            "class_name": TARGET_RED_TRIANGLE,
            "confidence": 0.76,
            "box": (290, 210, 350, 270),
        },
    ]

    red_target = targeting.find_target_by_name(
        detections=detections,
        target_name=TARGET_RED_TRIANGLE,
    )

    assert red_target is not None
    assert (
        red_target["class_name"]
        == TARGET_RED_TRIANGLE
    )

    blue_target = targeting.find_target_by_name(
        detections=detections,
        target_name=TARGET_BLUE_HEXAGON,
    )

    assert blue_target is not None
    assert (
        blue_target["class_name"]
        == TARGET_BLUE_HEXAGON
    )

    unknown_target = targeting.find_target_by_name(
        detections=detections,
        target_name="bilinmeyen_hedef",
    )

    assert unknown_target is None

    print("Kilitlenen hedef adına göre doğru kutu seçildi.")
    print("DİNAMİK TARGETING TESTİ BAŞARILI")


if __name__ == "__main__":
    main()