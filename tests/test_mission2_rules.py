from mission2_rules import (
    PAYLOAD_BLUE,
    PAYLOAD_RED,
    TARGET_BLUE_HEXAGON,
    TARGET_RED_TRIANGLE,
    get_payload_for_target,
    select_nearest_pending_target,
)


def main():
    vehicle_position = {
        "lat": 39.000000,
        "lon": 32.000000,
    }

    # Testte kırmızı üçgen dronea daha yakın.
    target_positions = {
        TARGET_BLUE_HEXAGON: {
            "lat": 39.000500,
            "lon": 32.000000,
        },
        TARGET_RED_TRIANGLE: {
            "lat": 39.000100,
            "lon": 32.000000,
        },
    }

    completed_targets = {
        TARGET_BLUE_HEXAGON: False,
        TARGET_RED_TRIANGLE: False,
    }

    assert (
        get_payload_for_target(TARGET_BLUE_HEXAGON)
        == PAYLOAD_RED
    )

    assert (
        get_payload_for_target(TARGET_RED_TRIANGLE)
        == PAYLOAD_BLUE
    )

    first_selection = select_nearest_pending_target(
        vehicle_position=vehicle_position,
        target_positions=target_positions,
        completed_targets=completed_targets,
    )

    assert first_selection is not None
    assert (
        first_selection["target_name"]
        == TARGET_RED_TRIANGLE
    )
    assert (
        first_selection["payload_name"]
        == PAYLOAD_BLUE
    )

    print("İlk seçilen hedef:", first_selection["target_name"])
    print("Bırakılacak yük:", first_selection["payload_name"])
    print(
        "Uzaklık:",
        round(first_selection["distance_m"], 2),
        "metre",
    )

    completed_targets[TARGET_RED_TRIANGLE] = True

    second_selection = select_nearest_pending_target(
        vehicle_position=vehicle_position,
        target_positions=target_positions,
        completed_targets=completed_targets,
    )

    assert second_selection is not None
    assert (
        second_selection["target_name"]
        == TARGET_BLUE_HEXAGON
    )
    assert (
        second_selection["payload_name"]
        == PAYLOAD_RED
    )

    print("İkinci seçilen hedef:", second_selection["target_name"])
    print("Bırakılacak yük:", second_selection["payload_name"])

    print("EN YAKIN HEDEF SEÇİM TESTİ BAŞARILI")


if __name__ == "__main__":
    main()