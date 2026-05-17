# targeting.py

from config import CENTER_TOLERANCE


class TargetingSystem:

    def __init__(self):
        pass

    def movement_level(self, error):

        abs_error = abs(error)

        if abs_error < 80:
            return "MERKEZE YAKIN"
        elif abs_error < 160:
            return "AZ"
        elif abs_error < 280:
            return "ORTA"
        else:
            return "COK"

    def calculate_direction(self, error_x, error_y):

        horizontal = ""
        vertical = ""

        x_level = self.movement_level(error_x)
        y_level = self.movement_level(error_y)

        if error_x > CENTER_TOLERANCE:
            horizontal = f"{x_level} SAGDA"
        elif error_x < -CENTER_TOLERANCE:
            horizontal = f"{x_level} SOLDA"

        if error_y > CENTER_TOLERANCE:
            vertical = f"{y_level} ASAGIDA"
        elif error_y < -CENTER_TOLERANCE:
            vertical = f"{y_level} YUKARIDA"

        return f"{horizontal} {vertical}".strip()

    def find_best_target(self, detections, current_target, frame):

        if current_target is None:
            return None

        frame_height, frame_width, _ = frame.shape

        frame_center_x = frame_width // 2
        frame_center_y = frame_height // 2

        best_detection = None
        best_area = 0

        for detection in detections:

            class_name = detection["class_name"]

            if class_name != current_target:
                continue

            x1, y1, x2, y2 = detection["box"]

            area = (x2 - x1) * (y2 - y1)

            if area > best_area:
                best_area = area
                best_detection = detection

        if best_detection is None:
            return None

        x1, y1, x2, y2 = best_detection["box"]

        target_center_x = (x1 + x2) // 2
        target_center_y = (y1 + y2) // 2

        error_x = target_center_x - frame_center_x
        error_y = target_center_y - frame_center_y

        is_centered = (
            abs(error_x) < CENTER_TOLERANCE and
            abs(error_y) < CENTER_TOLERANCE
        )

        direction = self.calculate_direction(error_x, error_y)

        return {
            "class_name": best_detection["class_name"],
            "confidence": best_detection["confidence"],
            "box": best_detection["box"],
            "target_center": (target_center_x, target_center_y),
            "frame_center": (frame_center_x, frame_center_y),
            "error_x": error_x,
            "error_y": error_y,
            "is_centered": is_centered,
            "direction": direction
        }