# ui.py

import cv2

from config import (
    TARGET_BLUE_HEXAGON,
    TARGET_RED_TRIANGLE,
    STABLE_LIMIT
)

DISPLAY_WIDTH = 1280
DISPLAY_HEIGHT = 720
PANEL_HEIGHT = 280


class UISystem:

    def __init__(self):
        pass

    def get_payload_info(self, current_target):

        if current_target == TARGET_BLUE_HEXAGON:
            return "kirmizi_yuk", "Servo 1"

        elif current_target == TARGET_RED_TRIANGLE:
            return "mavi_yuk", "Servo 2"

        else:
            return "yok", "yok"

    def draw_text(self, frame, text, x, y, color, scale=0.48, thickness=1):

        cv2.putText(
            frame,
            text,
            (x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            scale,
            color,
            thickness,
            cv2.LINE_AA
        )

    def _scale_target_data(self, target_data, scale_x, scale_y):

        if target_data is None:
            return None

        x1, y1, x2, y2 = target_data["box"]
        target_center_x, target_center_y = target_data["target_center"]

        return {
            **target_data,
            "box": (
                int(x1 * scale_x),
                int(y1 * scale_y),
                int(x2 * scale_x),
                int(y2 * scale_y),
            ),
            "target_center": (
                int(target_center_x * scale_x),
                int(target_center_y * scale_y),
            ),
            "error_x": int(target_data["error_x"] * scale_x),
            "error_y": int(target_data["error_y"] * scale_y),
        }

    def _get_direction_color(self, direction):

        direction_upper = str(direction).upper()

        if direction_upper in ("MERKEZDE", "CENTER"):
            return (0, 255, 0)

        if "HEDEF_YOK" in direction_upper or direction_upper == "YOK":
            return (0, 0, 255)

        movement_keys = (
            "SAG", "SOL", "YUKARI", "ASAGI",
            "LEFT", "RIGHT", "UP", "DOWN", "ARAMA"
        )

        if any(key in direction_upper for key in movement_keys):
            return (0, 255, 255)

        return (255, 255, 255)

    def _get_payload_color(self, payload_status):

        payload_upper = str(payload_status).upper()

        if "BIRAKILDI" in payload_upper:
            return (0, 255, 0)

        if "BEKLIYOR" in payload_upper:
            return (0, 255, 255)

        return (255, 255, 255)

    def draw_panel_row(
        self,
        frame,
        x,
        y,
        label,
        value,
        value_color,
        scale=0.55,
        thickness=1,
        label_color=(210, 210, 210)
    ):

        label_text = f"{label} : "
        self.draw_text(frame, label_text, x, y, label_color, scale, thickness)

        label_size, _ = cv2.getTextSize(
            label_text,
            cv2.FONT_HERSHEY_SIMPLEX,
            scale,
            thickness
        )

        value_x = x + label_size[0]
        self.draw_text(frame, str(value), value_x, y, value_color, scale, thickness)

    def _measure_panel_width(self, rows, panel_info, text_x, row_scale, row_thickness, title_scale, title_thickness):

        max_width = 0

        for label, value, _ in rows:
            row_text = f"{label} : {value}"
            row_size, _ = cv2.getTextSize(
                row_text,
                cv2.FONT_HERSHEY_SIMPLEX,
                row_scale,
                row_thickness
            )
            max_width = max(max_width, row_size[0])

        fps_text = f"FPS : {panel_info['fps']:.1f}"
        fps_size, _ = cv2.getTextSize(
            fps_text,
            cv2.FONT_HERSHEY_SIMPLEX,
            row_scale,
            row_thickness
        )
        max_width = max(max_width, fps_size[0])

        title_size, _ = cv2.getTextSize(
            "TEKNOFEST IHA GOREV SISTEMI",
            cv2.FONT_HERSHEY_SIMPLEX,
            title_scale,
            title_thickness
        )
        max_width = max(max_width, title_size[0])

        return max_width + text_x + 16

    def draw_mission_panel(self, frame, panel_info):

        panel_x1 = 10
        panel_y1 = 10
        panel_y2 = panel_y1 + PANEL_HEIGHT

        text_x = 24
        title_y = 36
        row_y = 62
        line_gap = 30
        title_scale = 0.55
        title_thickness = 1
        row_scale = 0.42
        row_thickness = 1

        rows = [
            ("GOREV DURUMU", panel_info["mission_state"], (0, 255, 255)),
            ("GOREV HEDEFI", panel_info["searched_target"], (255, 255, 0)),
            ("TAKIP EDILEN", panel_info["selected_target"], (0, 255, 0)),
            ("GUVEN ORANI", panel_info["confidence_text"], (255, 255, 255)),
            ("YON", panel_info["direction"], self._get_direction_color(panel_info["direction"])),
            ("KARARLILIK", panel_info["stability"], (0, 255, 0)),
            (
                "YUK DURUMU",
                panel_info["payload_status"],
                self._get_payload_color(panel_info["payload_status"])
            ),
        ]

        panel_x2 = panel_x1 + self._measure_panel_width(
            rows,
            panel_info,
            text_x,
            row_scale,
            row_thickness,
            title_scale,
            title_thickness
        )

        cv2.rectangle(
            frame,
            (panel_x1, panel_y1),
            (panel_x2, panel_y2),
            (40, 40, 40),
            -1
        )

        cv2.rectangle(
            frame,
            (panel_x1, panel_y1),
            (panel_x2, panel_y2),
            (170, 170, 170),
            1
        )

        self.draw_text(
            frame,
            "TEKNOFEST IHA GOREV SISTEMI",
            text_x,
            title_y,
            (0, 190, 255),
            scale=title_scale,
            thickness=title_thickness
        )

        y = row_y

        for label, value, value_color in rows:
            self.draw_panel_row(
                frame,
                text_x,
                y,
                label,
                value,
                value_color,
                scale=row_scale,
                thickness=row_thickness
            )
            y += line_gap

        self.draw_panel_row(
            frame,
            text_x,
            y,
            "FPS",
            f"{panel_info['fps']:.1f}",
            (255, 255, 255),
            scale=row_scale,
            thickness=row_thickness
        )

    def draw(
        self,
        frame,
        target_data,
        current_target,
        status,
        direction,
        fps,
        stable_count=0,
        mission_state="HEDEF_ARIYOR"
    ):

        src_height, src_width, _ = frame.shape
        scale_x = DISPLAY_WIDTH / src_width
        scale_y = DISPLAY_HEIGHT / src_height

        if src_width == DISPLAY_WIDTH and src_height == DISPLAY_HEIGHT:
            display_frame = frame
            scaled_target = target_data
        else:
            display_frame = cv2.resize(frame, (DISPLAY_WIDTH, DISPLAY_HEIGHT))
            scaled_target = self._scale_target_data(target_data, scale_x, scale_y)

        frame_height, frame_width, _ = display_frame.shape

        frame_center_x = frame_width // 2
        frame_center_y = frame_height // 2

        cv2.circle(
            display_frame,
            (frame_center_x, frame_center_y),
            7,
            (255, 0, 0),
            -1
        )

        cv2.line(
            display_frame,
            (frame_center_x - 24, frame_center_y),
            (frame_center_x + 24, frame_center_y),
            (255, 0, 0),
            2
        )

        cv2.line(
            display_frame,
            (frame_center_x, frame_center_y - 24),
            (frame_center_x, frame_center_y + 24),
            (255, 0, 0),
            2
        )

        payload_name, servo_name = self.get_payload_info(current_target)

        if current_target is None:
            payload_status = "TUM YUKLER BIRAKILDI"
        else:
            payload_status = f"{payload_name} | {servo_name}"

        confidence_text = "-"
        selected_target = "YOK"

        if scaled_target is not None:
            selected_target = scaled_target["class_name"]
            confidence_text = f"{scaled_target['confidence']:.2f}"

        panel_info = {
            "mission_state": mission_state,
            "searched_target": current_target if current_target is not None else "YOK",
            "selected_target": selected_target,
            "confidence_text": confidence_text,
            "direction": direction,
            "stability": f"{stable_count}/{STABLE_LIMIT}",
            "payload_status": payload_status,
            "fps": fps,
        }

        self.draw_mission_panel(display_frame, panel_info)

        if scaled_target is not None:

            x1, y1, x2, y2 = scaled_target["box"]
            target_center_x, target_center_y = scaled_target["target_center"]
            class_name = scaled_target["class_name"]
            confidence = scaled_target["confidence"]
            error_x = scaled_target["error_x"]
            error_y = scaled_target["error_y"]

            cv2.rectangle(
                display_frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            cv2.circle(
                display_frame,
                (target_center_x, target_center_y),
                6,
                (0, 0, 255),
                -1
            )

            cv2.line(
                display_frame,
                (frame_center_x, frame_center_y),
                (target_center_x, target_center_y),
                (255, 255, 255),
                2
            )

            cv2.putText(
                display_frame,
                f"{class_name} {confidence:.2f}",
                (x1, max(30, y1 - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.50,
                (0, 255, 0),
                2,
                cv2.LINE_AA
            )

            info_x1 = 10
            info_y1 = frame_height - 110
            info_x2 = min(frame_width - 10, 380)
            info_y2 = frame_height - 10

            cv2.rectangle(
                display_frame,
                (info_x1, info_y1),
                (info_x2, info_y2),
                (40, 40, 40),
                -1
            )

            cv2.rectangle(
                display_frame,
                (info_x1, info_y1),
                (info_x2, info_y2),
                (0, 255, 0),
                1
            )

            self.draw_text(
                display_frame,
                f"ALGILANAN: {class_name}",
                22,
                frame_height - 78,
                (0, 255, 0),
                scale=0.42
            )

            self.draw_text(
                display_frame,
                f"GUVEN: {confidence:.2f}",
                22,
                frame_height - 52,
                (0, 255, 0),
                scale=0.42
            )

            self.draw_text(
                display_frame,
                f"X: {error_x}   Y: {error_y}",
                22,
                frame_height - 26,
                (255, 255, 255),
                scale=0.42
            )

        else:

            self.draw_text(
                display_frame,
                "DOGRU HEDEF ALGILANMADI",
                20,
                frame_height - 28,
                (0, 255, 255),
                scale=0.48,
                thickness=1
            )

        return display_frame