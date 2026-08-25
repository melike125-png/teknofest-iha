from math import atan2, cos, hypot, radians, sin, sqrt


TARGET_BLUE_HEXAGON = "mavi_altigen"
TARGET_RED_TRIANGLE = "kirmizi_ucgen"

PAYLOAD_RED = "kirmizi_yuk"
PAYLOAD_BLUE = "mavi_yuk"


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
    """İki GPS koordinatı arasındaki mesafeyi metre olarak hesaplar."""

    earth_radius_m = 6_371_000.0

    lat_1_rad = radians(lat_1)
    lat_2_rad = radians(lat_2)

    delta_lat = radians(lat_2 - lat_1)
    delta_lon = radians(lon_2 - lon_1)

    value = (
        sin(delta_lat / 2) ** 2
        + cos(lat_1_rad)
        * cos(lat_2_rad)
        * sin(delta_lon / 2) ** 2
    )

    angle = 2 * atan2(
        sqrt(value),
        sqrt(1 - value),
    )

    return earth_radius_m * angle


class Mission2Rules:
    """
    Görev 2 hedef seçim kuralları.

    - İlk doğrulanan hedef seçilir.
    - İki hedef aynı anda doğrulanırsa yakın olan seçilir.
    - Güven oranı hedefler arasında öncelik belirlemek için kullanılmaz.
    - Seçilen hedef tamamlanana kadar hedef kilidi korunur.
    """

    def __init__(
        self,
        required_confirmations: int = 5,
        frame_width: int = 640,
        frame_height: int = 480,
        min_distance_difference_m: float = 0.75,
        min_center_difference_px: float = 25.0,
    ):
        if required_confirmations < 1:
            raise ValueError(
                "required_confirmations en az 1 olmalıdır."
            )

        self.required_confirmations = required_confirmations

        self.frame_center_x = frame_width / 2
        self.frame_center_y = frame_height / 2

        # Mesafe farkı bundan küçükse ölçüm belirsiz kabul edilir.
        self.min_distance_difference_m = (
            min_distance_difference_m
        )

        # Piksel farkı bundan küçükse iki hedef yaklaşık eşit kabul edilir.
        self.min_center_difference_px = (
            min_center_difference_px
        )

        # Bu değerler saha testleriyle hedefe özel ayarlanacak.
        self.confidence_limits = {
            TARGET_BLUE_HEXAGON: 0.40,
            TARGET_RED_TRIANGLE: 0.40,
        }

        self.completed_targets = {
            TARGET_BLUE_HEXAGON: False,
            TARGET_RED_TRIANGLE: False,
        }

        self.confirmation_counts = {
            TARGET_BLUE_HEXAGON: 0,
            TARGET_RED_TRIANGLE: 0,
        }

        self.active_target: str | None = None

    def get_payload_for_target(
        self,
        target_name: str,
    ) -> str:
        if target_name not in TARGET_TO_PAYLOAD:
            raise ValueError(
                f"Bilinmeyen hedef: {target_name}"
            )

        return TARGET_TO_PAYLOAD[target_name]

    def is_target_pending(
        self,
        target_name: str,
    ) -> bool:
        return (
            target_name in VALID_TARGETS
            and not self.completed_targets[target_name]
        )

    def _get_best_detection_per_target(
        self,
        detections: list[dict],
    ) -> dict[str, dict]:
        """
        Aynı hedef için birden fazla kutu varsa
        en yüksek güvenli kutuyu alır.

        Güven burada yalnızca geçerlilik kontrolüdür;
        hedefler arasında seçim puanı değildir.
        """

        best_detections: dict[str, dict] = {}

        for detection in detections:
            target_name = detection.get("class_name")

            if not self.is_target_pending(target_name):
                continue

            confidence = float(
                detection.get("confidence", 0.0)
            )

            if confidence < self.confidence_limits[target_name]:
                continue

            previous = best_detections.get(target_name)

            if (
                previous is None
                or confidence
                > float(previous.get("confidence", 0.0))
            ):
                best_detections[target_name] = detection

        return best_detections

    def _calculate_center_distance_px(
        self,
        detection: dict,
    ) -> float:
        box = detection.get("box")

        if box is None or len(box) != 4:
            return float("inf")

        x_1, y_1, x_2, y_2 = box

        target_center_x = (x_1 + x_2) / 2
        target_center_y = (y_1 + y_2) / 2

        return hypot(
            target_center_x - self.frame_center_x,
            target_center_y - self.frame_center_y,
        )

    def _select_simultaneous_target(
        self,
        confirmed_targets: list[str],
        detections: dict[str, dict],
    ) -> str | None:
        """
        İki hedef aynı anda doğrulanırsa seçim yapar.

        Öncelik:
        1. Geçerli metre cinsinden mesafe
        2. Görüntü merkezine uzaklık
        3. Hâlâ belirsizse karar vermeden bekleme
        """

        distance_values = []

        for target_name in confirmed_targets:
            value = detections[target_name].get("distance_m")

            if not isinstance(value, (int, float)):
                distance_values = []
                break

            if value < 0:
                distance_values = []
                break

            distance_values.append(
                (float(value), target_name)
            )

        if len(distance_values) == len(confirmed_targets):
            distance_values.sort()

            nearest_distance, nearest_target = (
                distance_values[0]
            )

            second_distance = distance_values[1][0]

            if (
                second_distance - nearest_distance
                >= self.min_distance_difference_m
            ):
                return nearest_target

        center_values = [
            (
                self._calculate_center_distance_px(
                    detections[target_name]
                ),
                target_name,
            )
            for target_name in confirmed_targets
        ]

        center_values.sort()

        nearest_center, nearest_target = center_values[0]
        second_center = center_values[1][0]

        if (
            second_center - nearest_center
            >= self.min_center_difference_px
        ):
            return nearest_target

        # Ölçüm belirsizse rastgele veya sabit hedef seçilmez.
        # Sonraki karelerde ayrım oluşması beklenir.
        return None

    def select_first_confirmed_target(
        self,
        detections: list[dict],
    ) -> str | None:
        """
        İlk güvenilir hedefi seçer ve hedef kilidini korur.
        """

        if (
            self.active_target is not None
            and self.is_target_pending(self.active_target)
        ):
            return self.active_target

        best_detections = (
            self._get_best_detection_per_target(
                detections
            )
        )

        for target_name in VALID_TARGETS:
            if target_name in best_detections:
                self.confirmation_counts[target_name] += 1
            else:
                self.confirmation_counts[target_name] = 0

        confirmed_targets = [
            target_name
            for target_name in VALID_TARGETS
            if (
                self.confirmation_counts[target_name]
                >= self.required_confirmations
            )
        ]

        if not confirmed_targets:
            return None

        if len(confirmed_targets) == 1:
            selected_target = confirmed_targets[0]
        else:
            selected_target = (
                self._select_simultaneous_target(
                    confirmed_targets,
                    best_detections,
                )
            )

        if selected_target is None:
            return None

        self.active_target = selected_target
        self._reset_confirmation_counts()

        return self.active_target

    def mark_target_completed(
        self,
        target_name: str,
    ) -> bool:
        if target_name not in VALID_TARGETS:
            raise ValueError(
                f"Bilinmeyen hedef: {target_name}"
            )

        if self.completed_targets[target_name]:
            return False

        if (
            self.active_target is not None
            and target_name != self.active_target
        ):
            raise ValueError(
                "Aktif olmayan hedef tamamlandı olarak işaretlenemez."
            )

        self.completed_targets[target_name] = True
        self.active_target = None
        self._reset_confirmation_counts()

        return True

    def release_target_lock(self) -> None:
        """Release a mapping-only target without marking its payload complete."""
        self.active_target = None
        self._reset_confirmation_counts()

    def _reset_confirmation_counts(self) -> None:
        for target_name in VALID_TARGETS:
            self.confirmation_counts[target_name] = 0

    def all_targets_completed(self) -> bool:
        return all(self.completed_targets.values())

    def get_status(self) -> dict:
        active_payload = None

        if self.active_target is not None:
            active_payload = self.get_payload_for_target(
                self.active_target
            )

        return {
            "active_target": self.active_target,
            "active_payload": active_payload,
            "completed_targets": self.completed_targets.copy(),
            "confirmation_counts": self.confirmation_counts.copy(),
        }
