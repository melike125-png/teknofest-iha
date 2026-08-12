from mission2_rules import (
    Mission2Rules,
    TARGET_BLUE_HEXAGON,
    TARGET_RED_TRIANGLE,
    PAYLOAD_RED,
    PAYLOAD_BLUE,
)


def detection(
    class_name: str,
    confidence: float,
    box: tuple,
    distance_m: float | None = None,
) -> dict:
    result = {
        "class_name": class_name,
        "confidence": confidence,
        "box": box,
    }

    if distance_m is not None:
        result["distance_m"] = distance_m

    return result


def main():
    # -------------------------------------------------
    # Tek hedef önce görünürse
    # -------------------------------------------------
    rules = Mission2Rules(
        required_confirmations=2
    )

    red_frame = [
        detection(
            TARGET_RED_TRIANGLE,
            0.80,
            (290, 210, 350, 270),
        )
    ]

    assert (
        rules.select_first_confirmed_target(
            red_frame
        )
        is None
    )

    first_target = (
        rules.select_first_confirmed_target(
            red_frame
        )
    )

    assert first_target == TARGET_RED_TRIANGLE
    assert (
        rules.get_payload_for_target(first_target)
        == PAYLOAD_BLUE
    )

    # Kilitlendikten sonra başka hedefe geçmemeli.
    blue_frame = [
        detection(
            TARGET_BLUE_HEXAGON,
            0.99,
            (300, 220, 360, 280),
        )
    ]

    assert (
        rules.select_first_confirmed_target(
            blue_frame
        )
        == TARGET_RED_TRIANGLE
    )

    rules.mark_target_completed(
        TARGET_RED_TRIANGLE
    )

    # -------------------------------------------------
    # İki hedef aynı anda görünürse:
    # Güven değil, merkez yakınlığı kullanılmalı.
    # -------------------------------------------------
    simultaneous_rules = Mission2Rules(
        required_confirmations=2,
        min_center_difference_px=25,
    )

    simultaneous_frame = [
        # Güveni daha düşük ama merkeze yakın.
        detection(
            TARGET_RED_TRIANGLE,
            0.78,
            (290, 210, 350, 270),
        ),
        # Güveni daha yüksek ama görüntünün kenarında.
        detection(
            TARGET_BLUE_HEXAGON,
            0.99,
            (500, 300, 620, 420),
        ),
    ]

    assert (
        simultaneous_rules.select_first_confirmed_target(
            simultaneous_frame
        )
        is None
    )

    selected_target = (
        simultaneous_rules.select_first_confirmed_target(
            simultaneous_frame
        )
    )

    assert selected_target == TARGET_RED_TRIANGLE

    print(
        "Yüksek güvenli fakat uzaktaki altıgen seçilmedi."
    )
    print(
        "Merkeze yakın kırmızı üçgen seçildi."
    )

    # -------------------------------------------------
    # Gerçek mesafe bilgisi varsa o önceliklidir.
    # -------------------------------------------------
    distance_rules = Mission2Rules(
        required_confirmations=2,
        min_distance_difference_m=0.75,
    )

    distance_frame = [
        detection(
            TARGET_RED_TRIANGLE,
            0.75,
            (500, 300, 600, 400),
            distance_m=2.0,
        ),
        detection(
            TARGET_BLUE_HEXAGON,
            0.99,
            (290, 210, 350, 270),
            distance_m=4.0,
        ),
    ]

    assert (
        distance_rules.select_first_confirmed_target(
            distance_frame
        )
        is None
    )

    selected_by_distance = (
        distance_rules.select_first_confirmed_target(
            distance_frame
        )
    )

    assert (
        selected_by_distance
        == TARGET_RED_TRIANGLE
    )

    # -------------------------------------------------
    # Fark çok küçükse rastgele karar verilmemeli.
    # -------------------------------------------------
    ambiguous_rules = Mission2Rules(
        required_confirmations=2,
        min_center_difference_px=25,
    )

    ambiguous_frame = [
        detection(
            TARGET_RED_TRIANGLE,
            0.80,
            (250, 210, 310, 270),
        ),
        detection(
            TARGET_BLUE_HEXAGON,
            0.95,
            (330, 210, 390, 270),
        ),
    ]

    assert (
        ambiguous_rules.select_first_confirmed_target(
            ambiguous_frame
        )
        is None
    )

    assert (
        ambiguous_rules.select_first_confirmed_target(
            ambiguous_frame
        )
        is None
    )

    print(
        "Belirsiz eşzamanlı durumda sistem bekledi."
    )

    print(
        "PROFESYONEL HEDEF SEÇİM TESTİ BAŞARILI"
    )


if __name__ == "__main__":
    main()