import cv2

from config import (
    FRAME_WIDTH,
    FRAME_HEIGHT,
    CAMERA_INDEX,
)


CAMERA_TARGET_FPS = 30


class CameraSystem:
    """Logitech C920 icin dusuk gecikmeli V4L2 kamera yonetimi."""

    def __init__(self):
        self.cap = cv2.VideoCapture(
            CAMERA_INDEX,
            cv2.CAP_V4L2,
        )

        if self.cap.isOpened():
            self.cap.set(
                cv2.CAP_PROP_FOURCC,
                cv2.VideoWriter_fourcc(*"MJPG"),
            )
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
            self.cap.set(cv2.CAP_PROP_FPS, CAMERA_TARGET_FPS)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            print(
                "Logitech C920 aktif | "
                f"V4L2 MJPG {FRAME_WIDTH}x{FRAME_HEIGHT} "
                f"{CAMERA_TARGET_FPS} FPS | buffer=1"
            )
        else:
            print(
                "Logitech C920 acilamadi | "
                f"/dev/video{CAMERA_INDEX}"
            )

    def is_opened(self):
        return self.cap is not None and self.cap.isOpened()

    def read_frame(self):
        if not self.is_opened():
            return None

        ret, frame = self.cap.read()

        if not ret or frame is None:
            return None

        return frame

    def get_width(self):
        return FRAME_WIDTH

    def get_height(self):
        return FRAME_HEIGHT

    def release(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None

        print("Kamera kapatildi.")
