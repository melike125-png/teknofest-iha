import json
import tempfile
from pathlib import Path

from field_config import FieldConfig


def valid_data() -> dict:
    return {
        "name": "test",
        "start_line": {
            "left": {"lat": 39.0, "lon": 32.0},
            "right": {"lat": 39.0, "lon": 32.00005},
        },
        "pole_1": {"lat": 39.0002, "lon": 32.0003},
        "pole_2": {"lat": 39.0014, "lon": 32.0003},
        "search_polygon": [
            {"lat": 39.0003, "lon": 32.0004},
            {"lat": 39.0003, "lon": 32.0015},
            {"lat": 39.0006, "lon": 32.0015},
            {"lat": 39.0006, "lon": 32.0004},
        ],
        "landing_point": {"lat": 39.00005, "lon": 32.00012},
        "mission_altitude_m": 25,
        "search_altitude_m": 20,
        "drop_altitude_m": 10,
    }


def main():
    config = FieldConfig.from_dict(valid_data())
    assert config.name == "test"
    assert len(config.search_polygon) == 4
    assert config.pole_distance_m > 100

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "field.json"
        path.write_text(json.dumps(valid_data()), encoding="utf-8")
        loaded = FieldConfig.load(path)
        assert loaded == config

    forbidden = valid_data()
    forbidden["target_positions"] = {"mavi_altigen": [39.0, 32.0]}
    try:
        FieldConfig.from_dict(forbidden)
    except ValueError as error:
        assert "Hedef koordinatlari" in str(error)
    else:
        raise AssertionError("Hedef koordinati reddedilmeliydi.")

    invalid_altitude = valid_data()
    invalid_altitude["drop_altitude_m"] = 30
    try:
        FieldConfig.from_dict(invalid_altitude)
    except ValueError:
        pass
    else:
        raise AssertionError("Gecersiz irtifa sirasi reddedilmeliydi.")

    print("SAHA AYARI TESTLERI BASARILI")


if __name__ == "__main__":
    main()

