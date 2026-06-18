# camera.py

import cv2

from config import (
    CAMERA_INDEX,
    FRAME_WIDTH,
    FRAME_HEIGHT
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

                self.picam2.configure(
                    self.picam2.create_preview_configuration(
                        main={
                            "size": (FRAME_WIDTH, FRAME_HEIGHT),
                            "format": "RGB888"
                        }
                    )
                )

                self.picam2.start()

                self.use_picamera = True

                print("Raspberry Pi Camera aktif.")

            except Exception as e:

                print("Picamera acilamadi.")
                print(e)
                print("OpenCV webcam moduna geciliyor.")

                self.use_picamera = False

        if not self.use_picamera:

            self.cap = cv2.VideoCapture(CAMERA_INDEX)

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

            print("OpenCV webcam modu aktif.")

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

        if self.use_picamera:

            if self.picam2 is not None:
                self.picam2.stop()

        else:

            if self.cap is not None:
                self.cap.release()