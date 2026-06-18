# targeting.py

from config import (
    FRAME_WIDTH,
    FRAME_HEIGHT,
    CENTER_TOLERANCE_X,
    CENTER_TOLERANCE_Y,
    TARGET_BLUE_HEXAGON,
    TARGET_RED_TRIANGLE
)


class TargetingSystem:

    def __init__(self):

        # Kamera görüntüsünün merkez noktası.
        self.frame_center_x = FRAME_WIDTH // 2
        self.frame_center_y = FRAME_HEIGHT // 2

        # Görev sırası burada kesin olarak belirleniyor.
        # 1. önce mavi altıgen
        # 2. sonra kırmızı üçgen
        self.mission_order = [
            TARGET_BLUE_HEXAGON,
            TARGET_RED_TRIANGLE
        ]

    def get_current_mission_target(self, completed_targets):

        # Bu fonksiyon sıradaki hedefi bulur.
        # Eğer mavi_altigen henüz tamamlanmadıysa sıradaki hedef mavi_altigen olur.
        # Eğer mavi_altigen tamamlandıysa sıradaki hedef kirmizi_ucgen olur.

        for target_name in self.mission_order:

            if not completed_targets.get(target_name, False):
                return target_name

        # Bütün hedefler tamamlandıysa None döner.
        return None

    def calculate_target_center(self, box):

        x1, y1, x2, y2 = box

        target_center_x = int((x1 + x2) / 2)
        target_center_y = int((y1 + y2) / 2)

        return target_center_x, target_center_y

    def calculate_error(self, target_center_x, target_center_y):

        # Hedef, kamera merkezine göre kaç piksel sağda/solda/yukarıda/aşağıda?
        error_x = target_center_x - self.frame_center_x
        error_y = target_center_y - self.frame_center_y

        return error_x, error_y

    def check_centered(self, error_x, error_y):

        is_x_centered = abs(error_x) <= CENTER_TOLERANCE_X
        is_y_centered = abs(error_y) <= CENTER_TOLERANCE_Y

        return is_x_centered and is_y_centered

    def get_direction(self, error_x, error_y):

        directions = []

        if error_x > CENTER_TOLERANCE_X:
            directions.append("SAGA GIT")

        elif error_x < -CENTER_TOLERANCE_X:
            directions.append("SOLA GIT")

        if error_y > CENTER_TOLERANCE_Y:
            directions.append("GERI GIT")

        elif error_y < -CENTER_TOLERANCE_Y:
            directions.append("ILERI GIT")

        if len(directions) == 0:
            return "MERKEZDE"

        return " + ".join(directions)

    def calculate_area(self, box):

        x1, y1, x2, y2 = box

        width = max(0, x2 - x1)
        height = max(0, y2 - y1)

        return width * height

    def calculate_score(self, detection, box):

        confidence = detection.get("confidence", 0)

        area = self.calculate_area(box)

        frame_area = FRAME_WIDTH * FRAME_HEIGHT

        if frame_area == 0:
            area_ratio = 0
        else:
            area_ratio = area / frame_area

        # Güven oranı daha önemli, alan biraz daha az önemli.
        score = (confidence * 0.6) + (area_ratio * 0.4)

        return score

    def find_best_target(self, detections, completed_targets, frame=None):

        # Önce sıradaki hedefi belirliyoruz.
        current_mission_target = self.get_current_mission_target(completed_targets)

        # Eğer görevde sıradaki hedef kalmadıysa hedef aramıyoruz.
        if current_mission_target is None:
            return None

        best_target = None
        best_score = -1

        for detection in detections:

            class_name = detection.get("class_name")

            # EN ÖNEMLİ KISIM BURASI:
            # Sadece sıradaki hedef kabul edilecek.
            # Örneğin mavi_altigen tamamlanmadıysa,
            # kirmizi_ucgen görülse bile sistem onu görev hedefi olarak seçmeyecek.
            if class_name != current_mission_target:
                continue

            box = detection.get("box")

            if box is None:
                continue

            box = [int(value) for value in box]

            target_center_x, target_center_y = self.calculate_target_center(box)

            error_x, error_y = self.calculate_error(
                target_center_x,
                target_center_y
            )

            is_centered = self.check_centered(error_x, error_y)

            direction = self.get_direction(error_x, error_y)

            score = self.calculate_score(detection, box)

            if score > best_score:

                best_score = score

                best_target = {
                    "class_name": class_name,
                    "confidence": detection.get("confidence", 0),
                    "box": box,

                    # ui.py bunu bekliyor.
                    # Bu yüzden KeyError: 'target_center' hatası da çözülür.
                    "target_center": (target_center_x, target_center_y),

                    "center_x": target_center_x,
                    "center_y": target_center_y,
                    "error_x": error_x,
                    "error_y": error_y,
                    "is_centered": is_centered,
                    "direction": direction,
                    "score": score,
                    "current_mission_target": current_mission_target
                }

        return best_target