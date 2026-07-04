import time
import cv2

from config import (
    FRAME_WIDTH,
    FRAME_HEIGHT,
    CAMERA_INDEX
)


try:
    from picamera2 import Picamera2
    PICAMERA_AVAILABLE = True
except Exception:
    PICAMERA_AVAILABLE = False


class CameraSystem:

    def __init__(self):

        self.use_picamera = False
        self.picam2 = None
        self.cap = None

        if PICAMERA_AVAILABLE:

            try:
                self.picam2 = Picamera2()

                camera_config = self.picam2.create_video_configuration(
                    main={
                        "size": (FRAME_WIDTH, FRAME_HEIGHT),
                        "format": "RGB888"
                    }
                )

                self.picam2.configure(camera_config)
                self.picam2.start()

                time.sleep(1)

                self.use_picamera = True

                print("Raspberry Pi Camera aktif.")

            except Exception as e:

                print("Picamera acilamadi.")
                print("Hata:", e)
                print("USB kamera deneniyor...")

                self.use_picamera = False
                self.picam2 = None

        if not self.use_picamera:

            self.cap = cv2.VideoCapture(CAMERA_INDEX)

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

            if self.cap.isOpened():
                print("USB kamera aktif.")
            else:
                print("Kamera acilamadi.")

    def is_opened(self):

        if self.use_picamera:
            return self.picam2 is not None

        if self.cap is None:
            return False

        return self.cap.isOpened()

    def read_frame(self):

        if self.use_picamera:

            frame = self.picam2.capture_array()

            if frame is None:
                return None

            if len(frame.shape) == 3 and frame.shape[2] == 4:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)

            elif len(frame.shape) == 3 and frame.shape[2] == 3:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            return frame

        ret, frame = self.cap.read()

        if not ret:
            return None

        return frame

    def get_width(self):

        return FRAME_WIDTH

    def get_height(self):

        return FRAME_HEIGHT

    def release(self):

        if self.use_picamera and self.picam2 is not None:

            try:
                self.picam2.stop()
            except Exception:
                pass

            self.picam2 = None

        if self.cap is not None:

            self.cap.release()
            self.cap = None

        print("Kamera kapatildi.")