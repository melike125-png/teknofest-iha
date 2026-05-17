# ui.py

import cv2


class UISystem:

    def __init__(self):
        pass

    def draw(self, frame, target_data, current_target, status, direction, fps):

        frame_height, frame_width, _ = frame.shape

        frame_center_x = frame_width // 2
        frame_center_y = frame_height // 2

        cv2.circle(
            frame,
            (frame_center_x, frame_center_y),
            7,
            (255, 0, 0),
            -1
        )

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
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                f"Sinif: {class_name}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            cv2.putText(
                frame,
                f"X hata: {error_x}",
                (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            cv2.putText(
                frame,
                f"Y hata: {error_y}",
                (20, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

        if current_target is not None:

            cv2.putText(
                frame,
                f"AKTIF HEDEF: {current_target}",
                (20, 140),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 0),
                2
            )

        else:

            cv2.putText(
                frame,
                "GOREV TAMAMLANDI",
                (20, 140),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                3
            )

        cv2.putText(
            frame,
            status,
            (20, 180),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"YON: {direction}",
            (20, 220),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"FPS: {fps:.1f}",
            (20, 260),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )