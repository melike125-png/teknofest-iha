# ui.py

import cv2

from config import (
    TARGET_BLUE_HEXAGON,
    TARGET_RED_TRIANGLE,
    STABLE_LIMIT
)


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

    def draw(
        self,
        frame,
        target_data,
        current_target,
        status,
        direction,
        fps,
        stable_count=0
    ):

        frame_height, frame_width, _ = frame.shape

        frame_center_x = frame_width // 2
        frame_center_y = frame_height // 2

        # Kamera merkezi
        cv2.circle(
            frame,
            (frame_center_x, frame_center_y),
            5,
            (255, 0, 0),
            -1
        )

        cv2.line(
            frame,
            (frame_center_x - 18, frame_center_y),
            (frame_center_x + 18, frame_center_y),
            (255, 0, 0),
            2
        )

        cv2.line(
            frame,
            (frame_center_x, frame_center_y - 18),
            (frame_center_x, frame_center_y + 18),
            (255, 0, 0),
            2
        )

        payload_name, servo_name = self.get_payload_info(current_target)

        # Sol üst kompakt görev paneli
        panel_x1 = 10
        panel_y1 = 10
        panel_x2 = min(frame_width - 10, 410)
        panel_y2 = 230

        cv2.rectangle(
            frame,
            (panel_x1, panel_y1),
            (panel_x2, panel_y2),
            (0, 0, 0),
            -1
        )

        cv2.rectangle(
            frame,
            (panel_x1, panel_y1),
            (panel_x2, panel_y2),
            (255, 255, 255),
            1
        )

        x = 22
        y = 32
        line_gap = 24

        self.draw_text(
            frame,
            "TEKNOFEST IHA GOREV SISTEMI",
            x,
            y,
            (0, 255, 255),
            scale=0.50,
            thickness=1
        )

        y += line_gap

        self.draw_text(
            frame,
            "GOREV: 2 - YUK BIRAKMA",
            x,
            y,
            (255, 255, 255)
        )

        y += line_gap

        self.draw_text(
            frame,
            f"SIRADAKI: {current_target if current_target is not None else 'YOK'}",
            x,
            y,
            (255, 255, 0)
        )

        y += line_gap

        self.draw_text(
            frame,
            f"YUK: {payload_name}   SERVO: {servo_name}",
            x,
            y,
            (0, 255, 255)
        )

        y += line_gap

        self.draw_text(
            frame,
            f"DURUM: {status}",
            x,
            y,
            (0, 255, 255)
        )

        y += line_gap

        self.draw_text(
            frame,
            f"YON: {direction}",
            x,
            y,
            (0, 255, 255)
        )

        y += line_gap

        # Profesyonel kilit sayacı
        self.draw_text(
            frame,
            f"KILIT: {stable_count}/{STABLE_LIMIT}",
            x,
            y,
            (0, 255, 0)
        )

        y += line_gap

        self.draw_text(
            frame,
            f"FPS: {fps:.1f}",
            x,
            y,
            (255, 255, 255)
        )

        # Doğru hedef algılandıysa kutu ve hedef bilgisi çizilir.
        if target_data is not None:

            x1, y1, x2, y2 = target_data["box"]
            target_center_x, target_center_y = target_data["target_center"]
            class_name = target_data["class_name"]
            confidence = target_data["confidence"]
            error_x = target_data["error_x"]
            error_y = target_data["error_y"]

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            cv2.circle(
                frame,
                (target_center_x, target_center_y),
                5,
                (0, 0, 255),
                -1
            )

            cv2.line(
                frame,
                (frame_center_x, frame_center_y),
                (target_center_x, target_center_y),
                (255, 255, 255),
                2
            )

            cv2.putText(
                frame,
                f"{class_name} {confidence:.2f}",
                (x1, max(25, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 0),
                2,
                cv2.LINE_AA
            )

            # Alt sol küçük hedef paneli
            info_x1 = 10
            info_y1 = frame_height - 95
            info_x2 = min(frame_width - 10, 360)
            info_y2 = frame_height - 10

            cv2.rectangle(
                frame,
                (info_x1, info_y1),
                (info_x2, info_y2),
                (0, 0, 0),
                -1
            )

            cv2.rectangle(
                frame,
                (info_x1, info_y1),
                (info_x2, info_y2),
                (0, 255, 0),
                1
            )

            self.draw_text(
                frame,
                f"ALGILANAN: {class_name}",
                22,
                frame_height - 68,
                (0, 255, 0),
                scale=0.48
            )

            self.draw_text(
                frame,
                f"GUVEN: {confidence:.2f}",
                22,
                frame_height - 43,
                (0, 255, 0),
                scale=0.48
            )

            self.draw_text(
                frame,
                f"X: {error_x}   Y: {error_y}",
                22,
                frame_height - 18,
                (255, 255, 255),
                scale=0.48
            )

        else:

            self.draw_text(
                frame,
                "DOGRU HEDEF ALGILANMADI",
                20,
                frame_height - 25,
                (0, 255, 255),
                scale=0.55,
                thickness=2
            )