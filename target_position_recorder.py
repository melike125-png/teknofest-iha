import json
import os
from statistics import median

from mission2_rules import VALID_TARGETS, calculate_distance_m


class TargetPositionRecorder:
    """
    Kamera hedef üzerinde merkezlendiğinde alınan GPS örneklerinden
    hedefin yaklaşık konumunu hesaplar.

    Kamera gövdeye sabit ve aşağı bakıyor kabul edilir.
    Fiziksel kamera ofseti daha sonra kalibrasyonla eklenecektir.
    """

    def __init__(
        self,
        required_samples: int = 5,
        max_sample_spread_m: float = 2.0,
        output_file: str = "mission2_target_positions.json",
    ):
        if required_samples < 3:
            raise ValueError("required_samples en az 3 olmalıdır.")

        if max_sample_spread_m <= 0:
            raise ValueError("max_sample_spread_m pozitif olmalıdır.")

        self.required_samples = required_samples
        self.max_sample_spread_m = max_sample_spread_m
        self.output_file = output_file

        self.samples = {
            target_name: []
            for target_name in VALID_TARGETS
        }

        self.target_positions = {}

    def add_centered_sample(
        self,
        target_name: str,
        vehicle_position: dict,
        is_centered: bool,
    ) -> dict:
        """
        Hedef merkezdeyse GPS örneğini kabul eder.

        Yeterli örnek toplandığında:
        - medyan koordinatı hesaplar,
        - örneklerin birbirine yakınlığını kontrol eder,
        - hedef konumunu kaydeder.
        """

        if target_name not in VALID_TARGETS:
            return {
                "accepted": False,
                "completed": False,
                "message": f"Bilinmeyen hedef: {target_name}",
            }

        if not is_centered:
            self.samples[target_name].clear()

            return {
                "accepted": False,
                "completed": False,
                "message": "Hedef merkezde değil; örnek sayacı sıfırlandı.",
            }

        lat = vehicle_position.get("lat")
        lon = vehicle_position.get("lon")

        if lat is None or lon is None:
            return {
                "accepted": False,
                "completed": False,
                "message": "Geçerli GPS konumu yok.",
            }

        if target_name in self.target_positions:
            return {
                "accepted": False,
                "completed": True,
                "message": "Bu hedefin konumu daha önce kaydedildi.",
                "position": self.target_positions[target_name],
            }

        sample = {
            "lat": float(lat),
            "lon": float(lon),
        }

        self.samples[target_name].append(sample)

        sample_count = len(self.samples[target_name])

        if sample_count < self.required_samples:
            return {
                "accepted": True,
                "completed": False,
                "sample_count": sample_count,
                "required_samples": self.required_samples,
                "message": "GPS örneği kabul edildi.",
            }

        position = self._calculate_position(target_name)

        if position is None:
            self.samples[target_name].clear()

            return {
                "accepted": False,
                "completed": False,
                "message": (
                    "GPS örnekleri fazla dağınık; "
                    "örnekler temizlendi ve tekrar toplanacak."
                ),
            }

        self.target_positions[target_name] = position
        self.samples[target_name].clear()
        self.save()

        return {
            "accepted": True,
            "completed": True,
            "message": "Hedef konumu başarıyla kaydedildi.",
            "position": position,
        }

    def _calculate_position(self, target_name: str) -> dict | None:
        samples = self.samples[target_name]

        median_lat = median(
            sample["lat"]
            for sample in samples
        )

        median_lon = median(
            sample["lon"]
            for sample in samples
        )

        maximum_distance = 0.0

        for sample in samples:
            distance = calculate_distance_m(
                median_lat,
                median_lon,
                sample["lat"],
                sample["lon"],
            )

            maximum_distance = max(
                maximum_distance,
                distance,
            )

        if maximum_distance > self.max_sample_spread_m:
            return None

        return {
            "lat": median_lat,
            "lon": median_lon,
            "sample_count": len(samples),
            "maximum_sample_spread_m": maximum_distance,
        }

    def has_position(self, target_name: str) -> bool:
        return target_name in self.target_positions

    def all_positions_known(self) -> bool:
        return all(
            target_name in self.target_positions
            for target_name in VALID_TARGETS
        )

    def get_positions(self) -> dict:
        return {
            target_name: position.copy()
            for target_name, position
            in self.target_positions.items()
        }

    def save(self) -> None:
        with open(
            self.output_file,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                self.target_positions,
                file,
                indent=4,
                ensure_ascii=False,
            )

    def load(self) -> bool:
        if not os.path.exists(self.output_file):
            return False

        with open(
            self.output_file,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        valid_positions = {}

        for target_name, position in data.items():
            if target_name not in VALID_TARGETS:
                continue

            if (
                position.get("lat") is None
                or position.get("lon") is None
            ):
                continue

            valid_positions[target_name] = position

        self.target_positions = valid_positions

        return bool(self.target_positions)