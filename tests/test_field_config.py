import json
import tempfile
from copy import deepcopy
from pathlib import Path

from field_config import (
    CoordinateSource,
    calculate_distance_m,
    load_field_config,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

EXAMPLE_FILE = (
    PROJECT_ROOT
    / "field_config.example.json"
)


def load_example_data() -> dict:
    with EXAMPLE_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def load_temporary_config(
    data: dict,
):
    with tempfile.TemporaryDirectory() as temp_directory:
        file_path = (
            Path(temp_directory)
            / "field_config.json"
        )

        with file_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
            )

        return load_field_config(file_path)


def assert_rejected(
    data: dict,
    expected_message: str,
) -> None:
    try:
        load_temporary_config(data)

    except ValueError as error:
        message = str(error)

        assert expected_message in message, (
            f"Beklenen hata bulunamadı.\n"
            f"Beklenen: {expected_message}\n"
            f"Gerçek: {message}"
        )

        return

    raise AssertionError(
        "Geçersiz saha dosyası kabul edildi."
    )


def test_valid_organizer_config() -> None:
    config = load_field_config(EXAMPLE_FILE)

    assert (
        config.coordinate_source
        == CoordinateSource.ORGANIZER_PROVIDED
    )

    assert config.field_name == "prova_sahasi"
    assert len(config.search_polygon) == 4

    pole_distance_m = calculate_distance_m(
        config.pole_1,
        config.pole_2,
    )

    assert pole_distance_m > 100.0


def test_field_surveyed_source() -> None:
    data = load_example_data()

    data["coordinate_source"] = (
        "FIELD_SURVEYED"
    )

    config = load_temporary_config(data)

    assert (
        config.coordinate_source
        == CoordinateSource.FIELD_SURVEYED
    )


def test_invalid_coordinate_source_rejected() -> None:
    data = load_example_data()

    data["coordinate_source"] = "PHONE_GUESS"

    assert_rejected(
        data,
        "Geçersiz coordinate_source",
    )


def test_target_coordinates_rejected() -> None:
    data = load_example_data()

    data["target_positions"] = {
        "mavi_altigen": {
            "lat": 39.0,
            "lon": 32.0,
        }
    }

    assert_rejected(
        data,
        "Hedef koordinatları",
    )


def test_invalid_latitude_rejected() -> None:
    data = load_example_data()

    data["pole_1"]["lat"] = 120.0

    assert_rejected(
        data,
        "en fazla 90.0",
    )


def test_duplicate_polygon_point_rejected() -> None:
    data = load_example_data()

    data["search_polygon"][1] = deepcopy(
        data["search_polygon"][0]
    )

    assert_rejected(
        data,
        "aynı köşeyi",
    )


def test_invalid_altitude_order_rejected() -> None:
    data = load_example_data()

    data["altitudes"]["drop_m"] = 22.0
    data["altitudes"]["search_m"] = 20.0

    assert_rejected(
        data,
        "drop_m",
    )


def test_altitude_above_limit_rejected() -> None:
    data = load_example_data()

    data["altitudes"]["mission_m"] = 121.0

    assert_rejected(
        data,
        "güvenlik irtifası",
    )


def test_poles_too_close_rejected() -> None:
    data = load_example_data()

    data["pole_2"] = deepcopy(
        data["pole_1"]
    )

    assert_rejected(
        data,
        "Direkler arasındaki mesafe",
    )


def main() -> None:
    test_valid_organizer_config()
    test_field_surveyed_source()
    test_invalid_coordinate_source_rejected()
    test_target_coordinates_rejected()
    test_invalid_latitude_rejected()
    test_duplicate_polygon_point_rejected()
    test_invalid_altitude_order_rejected()
    test_altitude_above_limit_rejected()
    test_poles_too_close_rejected()

    print("SAHA YAPILANDIRMA TESTLERI BASARILI")


if __name__ == "__main__":
    main()