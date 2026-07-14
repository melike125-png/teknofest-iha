from math import atan2, cos, radians, sin, sqrt


TARGET_BLUE_HEXAGON = "mavi_altigen"
TARGET_RED_TRIANGLE = "kirmizi_ucgen"

PAYLOAD_RED = "kirmizi_yuk"
PAYLOAD_BLUE = "mavi_yuk"


# Ziyaret sırası sabit değildir.
# Sadece hedef ile bırakılacak yük eşleşmesi sabittir.
TARGET_TO_PAYLOAD = {
    TARGET_BLUE_HEXAGON: PAYLOAD_RED,
    TARGET_RED_TRIANGLE: PAYLOAD_BLUE,
}

VALID_TARGETS = frozenset(TARGET_TO_PAYLOAD)


def calculate_distance_m(
    lat_1: float,
    lon_1: float,
    lat_2: float,
    lon_2: float,
) -> float:
    """İki GPS koordinatı arasındaki yaklaşık uzaklığı metre olarak hesaplar."""

    earth_radius_m = 6_371_000.0

    lat_1_rad = radians(lat_1)
    lat_2_rad = radians(lat_2)

    delta_lat = radians(lat_2 - lat_1)
    delta_lon = radians(lon_2 - lon_1)

    a = (
        sin(delta_lat / 2) ** 2
        + cos(lat_1_rad)
        * cos(lat_2_rad)
        * sin(delta_lon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return earth_radius_m * c


def get_payload_for_target(target_name: str) -> str:
    """Hedefe bırakılması gereken yükü döndürür."""

    if target_name not in TARGET_TO_PAYLOAD:
        raise ValueError(f"Bilinmeyen hedef: {target_name}")

    return TARGET_TO_PAYLOAD[target_name]


def select_nearest_pending_target(
    vehicle_position: dict,
    target_positions: dict,
    completed_targets: dict,
) -> dict | None:
    """
    Konumu bilinen ve henüz tamamlanmamış hedeflerden
    dronea en yakın olanı seçer.

    Hedef konumu henüz bilinmiyorsa değerlendirmeye alınmaz.
    """

    vehicle_lat = vehicle_position.get("lat")
    vehicle_lon = vehicle_position.get("lon")

    if vehicle_lat is None or vehicle_lon is None:
        raise ValueError("Drone GPS konumu eksik.")

    candidates = []

    for target_name in VALID_TARGETS:
        if completed_targets.get(target_name, False):
            continue

        target_position = target_positions.get(target_name)

        if not target_position:
            continue

        target_lat = target_position.get("lat")
        target_lon = target_position.get("lon")

        if target_lat is None or target_lon is None:
            continue

        distance_m = calculate_distance_m(
            vehicle_lat,
            vehicle_lon,
            target_lat,
            target_lon,
        )

        candidates.append(
            {
                "target_name": target_name,
                "payload_name": get_payload_for_target(target_name),
                "distance_m": distance_m,
            }
        )

    if not candidates:
        return None

    return min(
        candidates,
        key=lambda candidate: candidate["distance_m"],
    )