from mission2_rules import (
    Mission2Rules,
    TARGET_BLUE_HEXAGON,
    TARGET_RED_TRIANGLE,
    PAYLOAD_RED,
    PAYLOAD_BLUE,
)


def create_detection(
    class_name: str,
    confidence: float,
) -> dict:
    return {
        "class_name": class_name,
        "confidence": confidence,
        "box": (100, 100, 200, 200),
    }


def main():
    rules = Mission2Rules(
        required_confirmations=3
    )

    # Sabit hedef-yük eşleşmesi.
    assert (
        rules.get_payload_for_target(
            TARGET_BLUE_HEXAGON
        )
        == PAYLOAD_RED
    )

    assert (
        rules.get_payload_for_target(
            TARGET_RED_TRIANGLE
        )
        == PAYLOAD_BLUE
    )

    print("\nSENARYO 1:")
    print("Yalnızca kırmızı üçgen görüş alanında.")

    red_frame = [
        create_detection(
            TARGET_RED_TRIANGLE,
            0.91,
        )
    ]

    # İlk iki karede henüz kilitlenmemeli.
    assert (
        rules.select_first_confirmed_target(
            red_frame
        )
        is None
    )

    assert (
        rules.select_first_confirmed_target(
            red_frame
        )
        is None
    )

    # Üçüncü ardışık karede kırmızı üçgene kilitlenir.
    first_target = (
        rules.select_first_confirmed_target(
            red_frame
        )
    )

    assert first_target == TARGET_RED_TRIANGLE

    first_payload = rules.get_payload_for_target(
        first_target
    )

    assert first_payload == PAYLOAD_BLUE

    print("Aktif hedef:", first_target)
    print("Bırakılacak yük:", first_payload)

    # Mavi altıgen daha sonra görünse bile
    # aktif hedef değiştirilmemeli.
    blue_frame = [
        create_detection(
            TARGET_BLUE_HEXAGON,
            0.99,
        )
    ]

    assert (
        rules.select_first_confirmed_target(
            blue_frame
        )
        == TARGET_RED_TRIANGLE
    )

    print(
        "Aktif hedef kilidi korundu:",
        rules.active_target,
    )

    # İlk hedef tamamlandı.
    assert (
        rules.mark_target_completed(
            TARGET_RED_TRIANGLE
        )
        is True
    )

    print("\nSENARYO 2:")
    print("Kalan mavi altıgen aranıyor.")

    assert (
        rules.select_first_confirmed_target(
            blue_frame
        )
        is None
    )

    assert (
        rules.select_first_confirmed_target(
            blue_frame
        )
        is None
    )

    second_target = (
        rules.select_first_confirmed_target(
            blue_frame
        )
    )

    assert second_target == TARGET_BLUE_HEXAGON

    second_payload = rules.get_payload_for_target(
        second_target
    )

    assert second_payload == PAYLOAD_RED

    print("Aktif hedef:", second_target)
    print("Bırakılacak yük:", second_payload)

    assert (
        rules.mark_target_completed(
            TARGET_BLUE_HEXAGON
        )
        is True
    )

    assert rules.all_targets_completed() is True

    print("\nSENARYO 3:")
    print("İki hedef aynı anda görüş alanında.")

    simultaneous_rules = Mission2Rules(
        required_confirmations=2
    )

    simultaneous_frame = [
        create_detection(
            TARGET_RED_TRIANGLE,
            0.82,
        ),
        create_detection(
            TARGET_BLUE_HEXAGON,
            0.94,
        ),
    ]

    assert (
        simultaneous_rules.select_first_confirmed_target(
            simultaneous_frame
        )
        is None
    )

    simultaneous_target = (
        simultaneous_rules.select_first_confirmed_target(
            simultaneous_frame
        )
    )

    # İkisi aynı anda doğrulanırsa
    # güveni yüksek olan seçilir.
    assert simultaneous_target == TARGET_BLUE_HEXAGON

    print(
        "Aynı anda görüldüğünde seçilen:",
        simultaneous_target,
    )

    print(
        "\nİLK DOĞRULANAN HEDEF KURAL TESTİ BAŞARILI"
    )


if __name__ == "__main__":
    main()