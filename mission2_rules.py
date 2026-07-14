# mission2_rules.py

TARGET_BLUE_HEXAGON = "mavi_altigen"
TARGET_RED_TRIANGLE = "kirmizi_ucgen"

PAYLOAD_RED = "kirmizi_yuk"
PAYLOAD_BLUE = "mavi_yuk"


# Hedef sırası sabit değildir.
# Ancak hedefe bırakılacak yük kesin ve değişmezdir.
TARGET_TO_PAYLOAD = {
    TARGET_BLUE_HEXAGON: PAYLOAD_RED,
    TARGET_RED_TRIANGLE: PAYLOAD_BLUE,
}

VALID_TARGETS = frozenset(TARGET_TO_PAYLOAD.keys())


class Mission2Rules:
    """
    TEKNOFEST Görev 2 karar kuralları.

    - Hedef sırası sabit değildir.
    - İlk güvenilir biçimde doğrulanan hedef aktif hedef olur.
    - Aktif hedef tamamlanana kadar başka hedefe geçilmez.
    - Tamamlanan hedef tekrar seçilmez.
    """

    def __init__(self, required_confirmations: int = 5):
        if required_confirmations < 1:
            raise ValueError(
                "required_confirmations en az 1 olmalıdır."
            )

        self.required_confirmations = required_confirmations

        self.completed_targets = {
            TARGET_BLUE_HEXAGON: False,
            TARGET_RED_TRIANGLE: False,
        }

        self.active_target: str | None = None

        # Her hedefin ardışık doğrulanma sayacı.
        self.confirmation_counts = {
            TARGET_BLUE_HEXAGON: 0,
            TARGET_RED_TRIANGLE: 0,
        }

        # Aynı karede iki hedef görünürse güven karşılaştırması için.
        self.confidence_sums = {
            TARGET_BLUE_HEXAGON: 0.0,
            TARGET_RED_TRIANGLE: 0.0,
        }

        self.last_confidences = {
            TARGET_BLUE_HEXAGON: 0.0,
            TARGET_RED_TRIANGLE: 0.0,
        }

    def get_payload_for_target(self, target_name: str) -> str:
        """
        Algılanan hedefe bırakılacak doğru yükü döndürür.

        mavi_altigen  -> kirmizi_yuk
        kirmizi_ucgen -> mavi_yuk
        """

        if target_name not in TARGET_TO_PAYLOAD:
            raise ValueError(
                f"Bilinmeyen hedef: {target_name}"
            )

        return TARGET_TO_PAYLOAD[target_name]

    def is_target_pending(self, target_name: str) -> bool:
        """Hedef henüz tamamlanmadıysa True döndürür."""

        if target_name not in VALID_TARGETS:
            return False

        return not self.completed_targets[target_name]

    def get_pending_targets(self) -> set[str]:
        """Tamamlanmamış hedefleri döndürür."""

        return {
            target_name
            for target_name in VALID_TARGETS
            if self.is_target_pending(target_name)
        }

    def _get_best_detection_per_target(
        self,
        detections: list[dict],
    ) -> dict[str, dict]:
        """
        Aynı hedef için birden fazla kutu varsa
        güveni en yüksek kutuyu seçer.
        """

        best_detections: dict[str, dict] = {}

        for detection in detections:
            target_name = detection.get("class_name")

            if not self.is_target_pending(target_name):
                continue

            confidence = float(
                detection.get("confidence", 0.0)
            )

            current_best = best_detections.get(target_name)

            if (
                current_best is None
                or confidence
                > float(current_best.get("confidence", 0.0))
            ):
                best_detections[target_name] = detection

        return best_detections

    def select_first_confirmed_target(
        self,
        detections: list[dict],
    ) -> str | None:
        """
        İlk ardışık ve güvenilir biçimde doğrulanan hedefi seçer.

        Bir hedef aktif hâle geldiyse, tamamlanana kadar
        diğer hedef daha yüksek güvenle görülse bile değiştirilmez.
        """

        # Aktif hedef tamamlanmadıysa kilidi koru.
        if (
            self.active_target is not None
            and self.is_target_pending(self.active_target)
        ):
            return self.active_target

        best_detections = self._get_best_detection_per_target(
            detections
        )

        # Bu karede görünmeyen hedeflerin ardışık sayacı sıfırlanır.
        for target_name in VALID_TARGETS:
            detection = best_detections.get(target_name)

            if detection is None:
                self.confirmation_counts[target_name] = 0
                self.confidence_sums[target_name] = 0.0
                self.last_confidences[target_name] = 0.0
                continue

            confidence = float(
                detection.get("confidence", 0.0)
            )

            self.confirmation_counts[target_name] += 1
            self.confidence_sums[target_name] += confidence
            self.last_confidences[target_name] = confidence

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

        # İki hedef aynı karelerde birlikte doğrulanırsa,
        # ortalama güveni yüksek olan seçilir.
        def target_score(target_name: str) -> tuple:
            count = self.confirmation_counts[target_name]

            average_confidence = (
                self.confidence_sums[target_name] / count
                if count > 0
                else 0.0
            )

            return (
                average_confidence,
                self.last_confidences[target_name],
            )

        self.active_target = max(
            confirmed_targets,
            key=target_score,
        )

        self._reset_confirmation_progress()

        return self.active_target

    def mark_target_completed(
        self,
        target_name: str,
    ) -> bool:
        """
        Yük başarıyla bırakıldıktan sonra hedefi tamamlandı yapar.
        """

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

        self._reset_confirmation_progress()

        return True

    def _reset_confirmation_progress(self) -> None:
        """Bütün geçici algılama sayaçlarını temizler."""

        for target_name in VALID_TARGETS:
            self.confirmation_counts[target_name] = 0
            self.confidence_sums[target_name] = 0.0
            self.last_confidences[target_name] = 0.0

    def all_targets_completed(self) -> bool:
        """İki hedef de tamamlandıysa True döndürür."""

        return all(self.completed_targets.values())

    def get_status(self) -> dict:
        """Görev kural sisteminin güncel durumunu döndürür."""

        active_payload = None

        if self.active_target is not None:
            active_payload = self.get_payload_for_target(
                self.active_target
            )

        return {
            "active_target": self.active_target,
            "active_payload": active_payload,
            "completed_targets": self.completed_targets.copy(),
            "pending_targets": self.get_pending_targets(),
            "confirmation_counts": self.confirmation_counts.copy(),
            "required_confirmations": self.required_confirmations,
        }