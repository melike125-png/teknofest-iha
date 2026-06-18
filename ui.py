# ui.py

import cv2


class UISystem:

    def __init__(self):
        pass

    def draw(self, frame, target_data, current_target, status, direction, fps):

        frame_height, frame_width, _ = frame.shape

        frame_center_x = frame_width // 2
        frame_center_y = frame_height // 2

        # Kamera merkezi: mavi nokta
        cv2.circle(
            frame,
            (frame_center_x, frame_center_y),
            7,
            (255, 0, 0),
            -1
        )

        # Merkez referans çizgileri
        cv2.line(
            frame,
            (frame_center_x - 25, frame_center_y),
            (frame_center_x + 25, frame_center_y),
            (255, 0, 0),
            2
        )

        cv2.line(
            frame,
            (frame_center_x, frame_center_y - 25),
            (frame_center_x, frame_center_y + 25),
            (255, 0, 0),
            2
        )

        y = 35

        # Sıradaki hedef bilgisi
        if current_target is not None:

            cv2.putText(
                frame,
                f"SIRADAKI HEDEF: {current_target}",
                (20, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 0),
                2
            )

        else:

            cv2.putText(
                frame,
                "SIRADAKI HEDEF: YOK",
                (20, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 0),
                2
            )

        y += 35

        # Eğer doğru sıradaki hedef algılandıysa kutu çizilir.
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

            # Hedef merkezi: kırmızı nokta
            cv2.circle(
                frame,
                (target_center_x, target_center_y),
                5,
                (0, 0, 255),
                -1
            )

            # Kamera merkezi ile hedef merkezi arasındaki çizgi
            cv2.line(
                frame,
                (frame_center_x, frame_center_y),
                (target_center_x, target_center_y),
                (255, 255, 255),
                2
            )

            cv2.putText(
                frame,
                f"HEDEF: {class_name} {confidence:.2f}",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                f"ALGILANAN: {class_name}",
                (20, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            y += 35

            cv2.putText(
                frame,
                f"GUVEN: {confidence:.2f}",
                (20, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            y += 35

            cv2.putText(
                frame,
                f"X HATA: {error_x}",
                (20, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            y += 35

            cv2.putText(
                frame,
                f"Y HATA: {error_y}",
                (20, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            y += 35

        else:

            cv2.putText(
                frame,
                "DOGRU HEDEF ALGILANMADI",
                (20, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2
            )

            y += 35

        # Durum bilgisi
        cv2.putText(
            frame,
            f"DURUM: {status}",
            (20, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2
        )

        y += 35

        # Yön bilgisi
        cv2.putText(
            frame,
            f"YON: {direction}",
            (20, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2
        )

        y += 35

        # FPS bilgisi
        cv2.putText(
            frame,
            f"FPS: {fps:.1f}",
            (20, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

